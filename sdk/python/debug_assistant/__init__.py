"""debug-assistant 客户端 SDK（Python）。

最小用法：

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

铁律：SDK 任何 HTTP 失败都不抛出，只记 logging.warning。业务侧零侵入。
"""
from .client import Debugger, DebuggerConfig
from .decorators import catch

__all__ = ["Debugger", "DebuggerConfig", "catch"]
__version__ = "0.1.0"
