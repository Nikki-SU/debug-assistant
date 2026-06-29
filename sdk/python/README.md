# debug-assistant Python SDK

```python
from debug_assistant import Debugger

debugger = Debugger(project="PaperAssistant", module="backend", port=8765)

@debugger.catch
def my_func(): ...

try:
    risky()
except Exception as e:
    debugger.report(error=e, context={"stage": "文献综述"})

debugger.resolve(error_id="ERR-...", solution="...")
```

对应 SPEC：项目一 §六.1 Python SDK
