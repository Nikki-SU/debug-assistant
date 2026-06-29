"""Debugger 客户端：连不上 server 时静默降级，绝不让业务崩。

依赖：仅 Python 标准库（urllib + json）。这样在 sidecar / 离线场景下不引入额外包。
"""
from __future__ import annotations

import json
import logging
import os
import platform
import socket
import sys
import threading
import traceback
import urllib.error
import urllib.request
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Iterator, Optional

log = logging.getLogger("debug_assistant")

DEFAULT_TIMEOUT = 2.0  # SDK 调用 server 的超时（秒）——拖累业务的容忍度极低


# ---------------- 配置 ----------------


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.environ.get(name)
    return v if v not in (None, "") else default


@dataclass
class DebuggerConfig:
    project: str
    module: str
    host: str = "127.0.0.1"
    port: int = 8765
    enabled: bool = True
    timeout: float = DEFAULT_TIMEOUT
    extra_env: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_env(
        cls,
        project: Optional[str] = None,
        module: Optional[str] = None,
        **overrides: Any,
    ) -> "DebuggerConfig":
        p = project or _env("DEBUG_ASSISTANT_PROJECT")
        m = module or _env("DEBUG_ASSISTANT_MODULE")
        # 兜底：project 从 cwd basename 推断；module 默认 "main"。
        # —— 仅在仍为空时启用，保持显式传参的优先级。
        if not p:
            try:
                p = os.path.basename(os.getcwd()) or None
            except Exception:
                p = None
        if not m:
            m = "main"
        if not p:
            raise ValueError(
                "Debugger 需要 project（构造参数 / DEBUG_ASSISTANT_PROJECT 环境变量 / "
                "可推断的 cwd basename 三者至少一个）。"
            )
        host = overrides.pop("host", None) or _env("DEBUG_ASSISTANT_HOST", "127.0.0.1")
        port = int(overrides.pop("port", None) or _env("DEBUG_ASSISTANT_PORT", "8765"))
        enabled = overrides.pop("enabled", None)
        if enabled is None:
            enabled_str = _env("DEBUG_ASSISTANT_ENABLED", "true")
            enabled = str(enabled_str).strip().lower() not in ("0", "false", "no", "off")
        timeout = float(overrides.pop("timeout", None) or DEFAULT_TIMEOUT)
        return cls(
            project=p,
            module=m,
            host=host,
            port=port,
            enabled=enabled,
            timeout=timeout,
            **overrides,
        )

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


# ---------------- 客户端 ----------------


class Debugger:
    """同步 HTTP 客户端。线程安全（无共享可变状态）。"""

    def __init__(
        self,
        project: Optional[str] = None,
        module: Optional[str] = None,
        *,
        host: Optional[str] = None,
        port: Optional[int] = None,
        enabled: Optional[bool] = None,
        timeout: Optional[float] = None,
        extra_env: Optional[dict[str, str]] = None,
        config: Optional[DebuggerConfig] = None,
    ) -> None:
        if config is None:
            kwargs: dict[str, Any] = {}
            if host is not None:
                kwargs["host"] = host
            if port is not None:
                kwargs["port"] = port
            if enabled is not None:
                kwargs["enabled"] = enabled
            if timeout is not None:
                kwargs["timeout"] = timeout
            if extra_env:
                kwargs["extra_env"] = extra_env
            config = DebuggerConfig.from_env(project=project, module=module, **kwargs)
        self.config = config

    # ---- 私有 HTTP ----

    def _post(self, path: str, body: dict) -> Optional[dict]:
        if not self.config.enabled:
            return None
        url = self.config.base_url + path
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            url, data=data, method="POST",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:  # 4xx / 5xx：读 body 帮助排查
            try:
                detail = e.read().decode("utf-8", errors="replace")
            except Exception:
                detail = str(e)
            log.warning("debug-assistant POST %s 失败：HTTP %s %s", path, e.code, detail[:200])
            return None
        except (urllib.error.URLError, socket.timeout, ConnectionError) as e:
            log.warning("debug-assistant POST %s 连接失败：%s（已降级）", path, e)
            return None
        except Exception as e:
            log.warning("debug-assistant POST %s 异常：%s（已降级）", path, e)
            return None

    def _get(self, path: str) -> Optional[dict]:
        if not self.config.enabled:
            return None
        url = self.config.base_url + path
        try:
            with urllib.request.urlopen(url, timeout=self.config.timeout) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except Exception as e:
            log.warning("debug-assistant GET %s 失败：%s（已降级）", path, e)
            return None

    # ---- 公共 API ----

    def health(self) -> Optional[dict]:
        return self._get("/api/health")

    def report(
        self,
        error: Optional[BaseException] = None,
        *,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
        stack_trace: Optional[str] = None,
        severity: str = "error",
        context: Optional[dict[str, Any]] = None,
        user_action: Optional[str] = None,
        stage: Optional[str] = None,
        session_id: Optional[str] = None,
        project_display_name: Optional[str] = None,
        dialog_round: Optional[int] = None,
        operation_path: Optional[str] = None,
        input_data: Optional[dict[str, Any]] = None,
        logs: Optional[list[str]] = None,
        env: Optional[dict[str, str]] = None,
    ) -> Optional[str]:
        """新建错误报告，返回 error_id 或 None（失败已降级）。

        ``error`` 给出时，自动抽取 error_type / error_message / stack_trace。
        """
        if error is not None:
            if error_type is None:
                error_type = type(error).__name__
            if error_message is None:
                error_message = str(error) or repr(error)
            if stack_trace is None:
                stack_trace = "".join(
                    traceback.format_exception(type(error), error, error.__traceback__)
                )
        if not error_type:
            error_type = "UnknownError"
        if error_message is None:
            error_message = ""

        full_env = {
            "Python": platform.python_version(),
            "OS": f"{platform.system()} {platform.release()}",
            "SDK": "debug-assistant-py/0.1.0",
        }
        if self.config.extra_env:
            full_env.update(self.config.extra_env)
        if env:
            full_env.update(env)

        body = {
            "project": self.config.project,
            "module": self.config.module,
            "error_type": error_type,
            "error_message": error_message,
            "severity": severity,
            "user_action": user_action,
            "stage": stage,
            "session_id": session_id,
            "project_display_name": project_display_name,
            "dialog_round": dialog_round,
            "extra_context_table": {str(k): str(v) for k, v in (context or {}).items()},
            "operation_path": operation_path,
            "input_data": input_data or {},
            "logs": logs or [],
            "stack_trace": stack_trace,
            "env": full_env,
        }
        body = {k: v for k, v in body.items() if v is not None}

        resp = self._post("/api/report", body)
        if resp:
            return resp.get("error_id")
        return None

    def resolve(
        self,
        error_id: str,
        solution: str,
        related_changes: Optional[str] = None,
    ) -> bool:
        resp = self._post(
            "/api/resolve",
            {
                "error_id": error_id,
                "solution": solution,
                "related_changes": related_changes,
            },
        )
        return bool(resp and resp.get("status") == "resolved")

    # ---- 装饰器 ----

    def catch(
        self,
        func: Optional[Callable[..., Any]] = None,
        *,
        reraise: bool = True,
        severity: str = "error",
        stage: Optional[str] = None,
    ) -> Callable[..., Any]:
        """装饰器：自动上报异常，默认仍重新抛出（不吃掉异常）。

        用法 1：
            @debugger.catch
            def f(): ...

        用法 2（带参数）：
            @debugger.catch(reraise=False, stage="文献综述")
            def f(): ...
        """

        def _wrap(fn: Callable[..., Any]) -> Callable[..., Any]:
            from functools import wraps

            @wraps(fn)
            def inner(*args: Any, **kwargs: Any) -> Any:
                try:
                    return fn(*args, **kwargs)
                except BaseException as e:  # noqa: BLE001
                    try:
                        self.report(
                            error=e,
                            severity=severity,
                            stage=stage,
                            context={"function": fn.__qualname__},
                        )
                    except Exception:  # 双层兜底：上报失败也不能影响业务
                        log.exception("debug-assistant catch 自身异常")
                    if reraise:
                        raise
                    return None

            return inner

        if func is None:
            return _wrap
        return _wrap(func)

    # ---- 上下文管理器 ----

    @contextmanager
    def context(
        self,
        *,
        reraise: bool = True,
        severity: str = "error",
        stage: Optional[str] = None,
        user_action: Optional[str] = None,
        extra: Optional[dict[str, Any]] = None,
    ) -> Iterator[None]:
        """with debugger.context(stage="文献综述"): ..."""
        try:
            yield
        except BaseException as e:  # noqa: BLE001
            try:
                self.report(
                    error=e,
                    severity=severity,
                    stage=stage,
                    user_action=user_action,
                    context=extra,
                )
            except Exception:
                log.exception("debug-assistant context 自身异常")
            if reraise:
                raise


# ---------------- 全局默认实例（懒构造） ----------------

_default_lock = threading.Lock()
_default_debugger: Optional[Debugger] = None


def get_default() -> Optional[Debugger]:
    """读取环境变量构造单例；失败返回 None（不抛）。"""
    global _default_debugger
    with _default_lock:
        if _default_debugger is None:
            try:
                _default_debugger = Debugger()
            except Exception as e:
                log.debug("debug-assistant 默认实例未初始化：%s", e)
                return None
        return _default_debugger
