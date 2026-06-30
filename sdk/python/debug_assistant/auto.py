"""一行接入：``debug_assistant.auto_install(project="X")``。

特点：
- 注册 ``sys.excepthook`` + ``threading.excepthook`` + ``atexit``，
  让主线程 / 子线程未捕获异常自动上报。
- 嗅探已 import 的 FastAPI / Flask，monkey-patch 它们的 ``__init__``，
  让以后创建的 app 自动挂上 exception handler；同时提供显式
  ``install_fastapi(app)`` / ``install_flask(app)``。
- 任何环节都是 ``try/except``，绝不抛出 —— 接入失败也不能让宿主崩。
- 不强依赖 fastapi / flask / django 等三方包，SDK 仍保持零依赖。
- 幂等：重复调用不重复注册钩子，重复 patch 同一个 app 也安全。

用法（一行）::

    import debug_assistant
    debug_assistant.auto_install(project="PaperAssistant")

如果业务进程是 FastAPI／Flask，也可以显式接管：

    from fastapi import FastAPI
    from debug_assistant import auto_install, install_fastapi
    app = FastAPI()
    auto_install(project="PaperAssistant")        # 全局钩子
    install_fastapi(app)                          # 显式给这个 app 挂 handler
"""
from __future__ import annotations

import atexit
import logging
import os
import sys
import threading
from typing import Any, Optional

from .client import Debugger, get_default

log = logging.getLogger("debug_assistant.auto")

# 全局安装状态（进程内单例）。所有写入都拿 _installed_lock。
_installed_lock = threading.Lock()
_installed_state: dict[str, Any] = {
    "hooks_active": False,        # 主/子线程 excepthook 是否已挂
    "prev_excepthook": None,
    "prev_threading_hook": None,
    "atexit_registered": False,
    "fastapi_patched": False,     # FastAPI.__init__ 是否已 monkey-patch
    "flask_patched": False,       # Flask.__init__ 是否已 monkey-patch
    "patched_apps": set(),        # 已显式注册 handler 的 app id（去重）
}


# ---------------- 内部工具 ----------------

def _safe_get_debugger(
    project: Optional[str],
    module: Optional[str],
    **kwargs: Any,
) -> Optional[Debugger]:
    """构造或获取 Debugger。任何失败返回 None，绝不抛。"""
    try:
        # 显式传入的 project/module 写进环境变量，确保 get_default 单例能用上。
        # 用 setdefault，不覆盖外部已配置的值。
        if project:
            os.environ.setdefault("DEBUG_ASSISTANT_PROJECT", str(project))
        if module:
            os.environ.setdefault("DEBUG_ASSISTANT_MODULE", str(module))
        d = get_default()
        if d is None and project:
            # 兜底：环境变量都没配的极端场景下，直接构造一个临时实例。
            try:
                d = Debugger(project=project, module=module, **kwargs)
            except Exception as e:  # noqa: BLE001
                log.debug("debug-assistant auto: fallback Debugger() 失败：%s", e)
                d = None
        return d
    except Exception as e:  # noqa: BLE001
        log.debug("debug-assistant auto: 取 Debugger 失败：%s", e)
        return None


def _install_excepthooks(debugger: Debugger) -> None:
    """挂主线程 + 子线程的 excepthook + atexit flush。幂等。"""
    if _installed_state["hooks_active"]:
        return

    prev_excepthook = sys.excepthook

    def _hook(exc_type, exc_value, exc_tb):
        # KeyboardInterrupt / SystemExit 不上报，按默认 hook 走
        try:
            if not issubclass(exc_type, (KeyboardInterrupt, SystemExit)):
                err = exc_value if isinstance(exc_value, BaseException) else exc_type(str(exc_value))
                debugger.report(error=err, severity="error", stage="uncaught")
        except Exception:  # noqa: BLE001
            pass
        try:
            prev_excepthook(exc_type, exc_value, exc_tb)
        except Exception:  # noqa: BLE001
            pass

    try:
        sys.excepthook = _hook
        _installed_state["prev_excepthook"] = prev_excepthook
    except Exception:  # noqa: BLE001
        pass

    # 子线程 hook（Python 3.8+）
    if hasattr(threading, "excepthook"):
        prev_thread_hook = threading.excepthook

        def _thread_hook(args):  # type: ignore[no-untyped-def]
            try:
                exc_type = args.exc_type
                if not issubclass(exc_type, (SystemExit,)):
                    err = args.exc_value if args.exc_value is not None else exc_type()
                    debugger.report(
                        error=err,
                        severity="error",
                        stage="uncaught-thread",
                        context={"thread": getattr(args.thread, "name", "?")},
                    )
            except Exception:  # noqa: BLE001
                pass
            try:
                prev_thread_hook(args)
            except Exception:  # noqa: BLE001
                pass

        try:
            threading.excepthook = _thread_hook  # type: ignore[assignment]
            _installed_state["prev_threading_hook"] = prev_thread_hook
        except Exception:  # noqa: BLE001
            pass

    # atexit：当前 SDK 无 buffer，钩子接口为未来 flush 预留
    if not _installed_state["atexit_registered"]:
        def _flush() -> None:
            try:
                flush = getattr(debugger, "flush", None)
                if callable(flush):
                    flush()
            except Exception:  # noqa: BLE001
                pass
        try:
            atexit.register(_flush)
            _installed_state["atexit_registered"] = True
        except Exception:  # noqa: BLE001
            pass

    _installed_state["hooks_active"] = True


# ---------------- 框架 monkey-patch ----------------

def _patch_fastapi(debugger: Debugger) -> None:
    """monkey-patch ``FastAPI.__init__``，让以后 new 的 app 自动挂 handler。幂等。"""
    if _installed_state["fastapi_patched"]:
        return
    try:
        from fastapi import FastAPI  # type: ignore
    except Exception:  # noqa: BLE001
        return

    original_init = FastAPI.__init__

    def _patched_init(self, *args: Any, **kwargs: Any) -> None:  # type: ignore[no-untyped-def]
        original_init(self, *args, **kwargs)
        try:
            install_fastapi(self)
        except Exception:  # noqa: BLE001
            pass

    try:
        FastAPI.__init__ = _patched_init  # type: ignore[method-assign]
        _installed_state["fastapi_patched"] = True
    except Exception:  # noqa: BLE001
        pass


def _patch_flask(debugger: Debugger) -> None:
    """monkey-patch ``Flask.__init__``。幂等。"""
    if _installed_state["flask_patched"]:
        return
    try:
        from flask import Flask  # type: ignore
    except Exception:  # noqa: BLE001
        return

    original_init = Flask.__init__

    def _patched_init(self, *args: Any, **kwargs: Any) -> None:  # type: ignore[no-untyped-def]
        original_init(self, *args, **kwargs)
        try:
            install_flask(self)
        except Exception:  # noqa: BLE001
            pass

    try:
        Flask.__init__ = _patched_init  # type: ignore[method-assign]
        _installed_state["flask_patched"] = True
    except Exception:  # noqa: BLE001
        pass


def _sniff_and_patch_frameworks(debugger: Debugger) -> None:
    """嗅探 sys.modules，对已 import 的框架做 monkey-patch。"""
    try:
        if "fastapi" in sys.modules or "starlette" in sys.modules:
            _patch_fastapi(debugger)
    except Exception:  # noqa: BLE001
        pass
    try:
        if "flask" in sys.modules:
            _patch_flask(debugger)
    except Exception:  # noqa: BLE001
        pass
    # TODO: Django 的 settings 系统比较重，先 PASS。
    # 后续可做：注册一个 middleware 通过 process_exception 上报。
    if "django" in sys.modules:
        log.debug("debug-assistant auto: 检测到 django（TODO，暂未自动接入）")


# ---------------- 公共 API ----------------

def install_fastapi(app: Any, **kwargs: Any) -> bool:
    """显式给 FastAPI app 挂 exception handler。幂等。

    handler 上报后会重新抛出异常，让 FastAPI 默认的 500 处理继续走 ——
    debug-assistant 只观测，不改变业务行为。
    """
    try:
        debugger = get_default() or _safe_get_debugger(
            project=kwargs.get("project"),
            module=kwargs.get("module"),
        )
        if debugger is None:
            return False

        marker = f"fastapi:{id(app)}"
        if marker in _installed_state["patched_apps"]:
            return True

        async def _handler(request, exc):  # type: ignore[no-untyped-def]
            try:
                ctx: dict[str, Any] = {}
                try:
                    ctx["path"] = str(getattr(request, "url", ""))
                    ctx["method"] = getattr(request, "method", "")
                except Exception:  # noqa: BLE001
                    pass
                debugger.report(
                    error=exc,
                    severity="error",
                    stage="fastapi-exception",
                    context=ctx,
                )
            except Exception:  # noqa: BLE001
                pass
            # 重新抛出，让 FastAPI 默认 500 处理继续走
            raise exc

        try:
            app.add_exception_handler(Exception, _handler)
            _installed_state["patched_apps"].add(marker)
            return True
        except Exception as e:  # noqa: BLE001
            log.debug("install_fastapi: add_exception_handler 失败：%s", e)
            return False
    except Exception:  # noqa: BLE001
        return False


def install_flask(app: Any, **kwargs: Any) -> bool:
    """显式给 Flask app 挂 errorhandler。幂等。"""
    try:
        debugger = get_default() or _safe_get_debugger(
            project=kwargs.get("project"),
            module=kwargs.get("module"),
        )
        if debugger is None:
            return False

        marker = f"flask:{id(app)}"
        if marker in _installed_state["patched_apps"]:
            return True

        def _handler(e):  # type: ignore[no-untyped-def]
            ctx: dict[str, Any] = {}
            try:
                from flask import request  # type: ignore
                ctx["path"] = str(getattr(request, "path", ""))
                ctx["method"] = getattr(request, "method", "")
            except Exception:  # noqa: BLE001
                pass
            try:
                debugger.report(
                    error=e,
                    severity="error",
                    stage="flask-exception",
                    context=ctx,
                )
            except Exception:  # noqa: BLE001
                pass
            # 重新抛出，让 Flask 默认 500 处理继续走
            raise e

        try:
            app.register_error_handler(Exception, _handler)
            _installed_state["patched_apps"].add(marker)
            return True
        except Exception as ex:  # noqa: BLE001
            log.debug("install_flask: register_error_handler 失败：%s", ex)
            return False
    except Exception:  # noqa: BLE001
        return False


def auto_install(
    project: Optional[str] = None,
    module: Optional[str] = None,
    **kwargs: Any,
) -> Optional[Debugger]:
    """一行接入入口。

    具体做这些事（任一失败都静默）：

    1. 通过 ``get_default()`` 构造/获取 ``Debugger`` 单例。
    2. 挂 ``sys.excepthook`` + ``threading.excepthook`` + ``atexit``。
    3. 嗅探 ``sys.modules`` 里的 FastAPI / Flask，monkey-patch 它们的
       ``__init__``，让后续 new 出来的 app 自动挂 exception handler。

    :param project: 项目名。等价于设置环境变量 ``DEBUG_ASSISTANT_PROJECT``。
    :param module:  模块名。等价于设置环境变量 ``DEBUG_ASSISTANT_MODULE``。
    :param kwargs:  透传给 :class:`Debugger`（如 host / port / timeout）。
    :return: 安装好的 Debugger 实例；失败返回 None。
    """
    with _installed_lock:
        try:
            debugger = _safe_get_debugger(project, module, **kwargs)
            if debugger is None:
                # 没拿到 debugger 也别让上层崩 —— 静默返回
                return None
            _install_excepthooks(debugger)
            _sniff_and_patch_frameworks(debugger)
            return debugger
        except Exception as e:  # noqa: BLE001
            log.debug("debug-assistant auto_install 整体失败：%s", e)
            return None


__all__ = ["auto_install", "install_fastapi", "install_flask"]
