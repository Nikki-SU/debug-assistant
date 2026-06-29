"""HTTP 客户端，封装 /api/report 与 /api/resolve。

对应 SPEC：项目一 §六.1 Python SDK
"""
from __future__ import annotations
import functools
import traceback
from typing import Any, Callable
import httpx


class Debugger:
    def __init__(
        self,
        project: str,
        module: str,
        host: str = "127.0.0.1",
        port: int = 8765,
        enabled: bool = True,
        timeout: float = 3.0,
    ):
        self.project = project
        self.module = module
        self.base_url = f"http://{host}:{port}"
        self.enabled = enabled
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout)

    def report(
        self,
        error: BaseException | None = None,
        error_type: str | None = None,
        error_message: str | None = None,
        context: dict[str, Any] | None = None,
        input_data: dict[str, Any] | None = None,
        logs: list[str] | None = None,
    ) -> str | None:
        """上报错误，返回 error_id（失败返回 None，不影响业务流）。"""
        if not self.enabled:
            return None
        # TODO: 组装 payload + POST /api/report + 容错（连不上时降级写本地文件）
        raise NotImplementedError

    def resolve(
        self,
        error_id: str,
        solution: str,
        related_changes: str | None = None,
    ) -> bool:
        """回传解决方案。"""
        # TODO: POST /api/resolve
        raise NotImplementedError

    def catch(self, func: Callable) -> Callable:
        """装饰器：自动捕获异常并上报，不吞异常（重新抛出）。"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except BaseException as e:
                self.report(error=e)
                raise
        return wrapper

    def close(self) -> None:
        self._client.close()
