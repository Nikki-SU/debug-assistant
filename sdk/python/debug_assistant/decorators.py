"""模块级 @catch 装饰器，使用环境变量自动构造的默认 Debugger。"""
from __future__ import annotations

from typing import Any, Callable, Optional

from .client import get_default


def catch(
    func: Optional[Callable[..., Any]] = None,
    *,
    reraise: bool = True,
    severity: str = "error",
    stage: Optional[str] = None,
) -> Callable[..., Any]:
    """模块级装饰器：

        from debug_assistant import catch

        @catch
        def f(): ...

    依赖环境变量 ``DEBUG_ASSISTANT_PROJECT`` / ``DEBUG_ASSISTANT_MODULE``。
    如果未配置，等价于不做任何事（无副作用）。
    """
    def _wrap(fn: Callable[..., Any]) -> Callable[..., Any]:
        from functools import wraps

        @wraps(fn)
        def inner(*args: Any, **kwargs: Any) -> Any:
            try:
                return fn(*args, **kwargs)
            except BaseException as e:  # noqa: BLE001
                d = get_default()
                if d is not None:
                    try:
                        d.report(error=e, severity=severity, stage=stage,
                                 context={"function": fn.__qualname__})
                    except Exception:
                        pass
                if reraise:
                    raise
                return None
        return inner

    if func is None:
        return _wrap
    return _wrap(func)
