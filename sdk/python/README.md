# debug-assistant Python SDK

零外部依赖，仅标准库。失败静默降级，绝不让业务崩。

```python
from debug_assistant import Debugger

debugger = Debugger(project="PaperAssistant", module="backend")

@debugger.catch
def convert(file_path):
    ...

with debugger.context(stage="文献综述", user_action="上传PDF"):
    risky()

try:
    work()
except Exception as e:
    eid = debugger.report(error=e, context={"file_name": "a.pdf"})

debugger.resolve(error_id=eid, solution="拆分文件后上传")
```

环境变量：

| 变量 | 说明 |
|------|------|
| `DEBUG_ASSISTANT_PROJECT` | 项目名 |
| `DEBUG_ASSISTANT_MODULE`  | 模块名 |
| `DEBUG_ASSISTANT_HOST`    | server 地址（默认 127.0.0.1） |
| `DEBUG_ASSISTANT_PORT`    | server 端口（默认 8765） |
| `DEBUG_ASSISTANT_ENABLED` | `false` 时全部静默 |
