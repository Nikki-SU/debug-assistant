# debug-assistant Python SDK

零外部依赖，仅标准库。失败静默降级，绝不让业务崩。

## 🚀 一行接入（推荐）

业务代码 0 改动，全部接入工作交给 CLI 一键完成：

```bash
# 在 debug-assistant 仓库 venv 里装好 SDK + CLI 之后：
debugger install G:\PaperAssistant
```

它会做这些事：

1. 自动定位项目入口文件（`main.py` / `app.py` / `api.py` / `server.py`，
   也会扫 `src-tauri/sidecar/` / `python/` / `backend/` / `src/`）。
2. 把 `debug_assistant/` 包**拷**到 `<project>/vendor/debug_assistant/` —— 绕过
   pip，PyInstaller 打包无忧。
3. **默认仅打印** patch 片段（保守策略），加 `--auto-patch` 才真改入口文件。
4. 已 patch 过则**幂等跳过**。

常用开关：

| 选项 | 作用 |
|------|------|
| `--auto-patch` | 实际写入 patch 到入口文件（生成 `.debug-assistant.bak` 备份） |
| `--no-patch`   | 仅 vendor，不打印 patch 提示 |
| `--dry-run`    | 只打印将要做的事，不写任何文件 |
| `--entry <文件>` | 跳过自动检测，显式指定入口 |
| `--name <项目名>` | 覆盖 project 名（默认取目录 basename） |

patch 片段长这样（加进入口文件顶部即可）：

```python
# === debug-assistant auto-install ===
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'vendor'))
try:
    import debug_assistant
    debug_assistant.auto_install(project="PaperAssistant")
except Exception:
    pass
# === /debug-assistant ===
```

接入后：

- 主线程未捕获异常 → `severity="error"`, `stage="uncaught"` 自动上报。
- 子线程（`threading.Thread`）未捕获异常 → `stage="uncaught-thread"` 自动上报。
- 检测到 FastAPI / Flask 已 import，会 monkey-patch 它们的 `__init__`，
  让以后 `FastAPI()` / `Flask(...)` 创建的 app **自动**挂上 exception handler
  （上报后异常仍按原样抛出，业务行为不变）。
- 任何环节失败一律静默，绝不连累宿主进程。

## ✋ 显式接入（FastAPI / Flask）

如果你想完全掌控时机：

```python
from fastapi import FastAPI
from debug_assistant import auto_install, install_fastapi

app = FastAPI()
auto_install(project="PaperAssistant")   # 注册全局 excepthook
install_fastapi(app)                      # 给这个 app 挂 exception handler
```

```python
from flask import Flask
from debug_assistant import auto_install, install_flask

app = Flask(__name__)
auto_install(project="MyService")
install_flask(app)
```

## 🛠 进阶用法（手动 Debugger）

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

## 环境变量

| 变量 | 说明 |
|------|------|
| `DEBUG_ASSISTANT_PROJECT` | 项目名（`auto_install(project=...)` 会自动写入） |
| `DEBUG_ASSISTANT_MODULE`  | 模块名 |
| `DEBUG_ASSISTANT_HOST`    | server 地址（默认 `127.0.0.1`） |
| `DEBUG_ASSISTANT_PORT`    | server 端口（默认 `8765`） |
| `DEBUG_ASSISTANT_ENABLED` | `false` 时全部静默 |

## 设计铁律

- **SDK 任何 HTTP 失败都不抛出**，只记 `logging.warning`。
- **业务侧零侵入**：所有钩子都重新抛出原异常。
- **不强依赖三方包**：FastAPI / Flask / Django 都是嗅探后再 `try import`。
- **幂等**：`auto_install` / `install_fastapi` / `install_flask` 重复调用安全。
