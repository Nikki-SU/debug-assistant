"""debug-assistant 客户端 SDK（Python）。

最小用法（手动）::

    from debug_assistant import Debugger
    debugger = Debugger(project="PaperAssistant", module="backend")

    @debugger.catch
    def my_function():
        ...

    try:
        result = mineru_client.convert(file_path)
    except Exception as e:
        debugger.report(error=e, context={"file_name": file_path})

    debugger.resolve(error_id="ERR-...", solution="拆分文件后上传")

一行接入（推荐，业务代码 0 改动）::

    import debug_assistant
    debug_assistant.auto_install(project="PaperAssistant")

铁律：SDK 任何 HTTP 失败都不抛出，只记 logging.warning。业务侧零侵入。
"""
from .client import Debugger, DebuggerConfig, get_default
from .decorators import catch
from .auto import auto_install, install_fastapi, install_flask

__all__ = [
    "Debugger",
    "DebuggerConfig",
    "get_default",
    "catch",
    "auto_install",
    "install_fastapi",
    "install_flask",
]
__version__ = "0.2.0"
