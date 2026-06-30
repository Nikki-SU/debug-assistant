# debug-assistant

> 跨项目的错误记录与闭环解决工具（独立全局工具）

🔬 这是一个独立桌面工具，用于记录、管理和闭环解决代码错误。任何项目（Python / Rust / Tauri / 前端 / 后端 / 脚本）都可以接入。

- **HTTP API**：`POST /api/report` 记录、`POST /api/resolve` 闭环、`GET /api/search` 检索（监听 `127.0.0.1:8765`）
- **SDK**：Python / TypeScript / Rust 三套，失败静默降级，绝不让业务崩
- **CLI**：`debugger install` 一键接入；`debugger report/resolve/search/show/projects/health`
- **GUI**：Tauri v2 + React 18，左列表 / 右详情，一键复制、一键解决

数据格式：**只用 Markdown（报告）+ CSV（索引/配置）**，绝不使用 JSON 作为持久化格式。
详见 [`docs/SPEC.md`](docs/SPEC.md) / [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)。

---

## 🚀 Quick Start（Windows）

```powershell
# 1) 拉代码
git clone https://github.com/Nikki-SU/debug-assistant.git G:\debug-assistant
cd G:\debug-assistant

# 2) 一键启动（首次会自动建 venv + npm install）
.\dev.ps1
```

`dev.ps1` 会做这些事：
1. 创建 `.venv` 并安装 `server / sdk / cli` 依赖
2. 在 `gui/` 下 `npm install`
3. 启动 server（后台 Job）+ GUI vite dev（前台）

默认数据目录：`%USERPROFILE%\DebugAssistant\`（首次启动自动创建）。

## 手动启动

```powershell
# Server
cd server
py -3 -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.main

# GUI（另开终端）
cd gui
npm install
npm run dev
```

## 🪄 给你的项目接入：一行 + 一条命令

debug-assistant 的设计目标是**业务代码 0 改动**。Python 项目接入只需要：

```powershell
# 在 debug-assistant 的 venv 里：
debugger install G:\YourProject
```

CLI 会：

1. 自动找到入口文件（`main.py` / `app.py` / `api.py` / `server.py`，也扫 `src-tauri/sidecar/` / `python/` / `backend/`）。
2. 把 SDK 拷到 `<YourProject>\vendor\debug_assistant\` —— 绕过 pip，PyInstaller 打包无忧。
3. 默认**只打印** patch 片段让你自己贴；加 `--auto-patch` 才真改入口文件。

接入后的入口文件长这样：

```python
# === debug-assistant auto-install ===
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'vendor'))
try:
    import debug_assistant
    debug_assistant.auto_install(project="YourProject")
except Exception:
    pass
# === /debug-assistant ===
```

`auto_install` 会自动：注册主/子线程未捕获异常钩子；嗅探到 FastAPI / Flask 时
给它们的 `__init__` 打 monkey-patch，让以后 new 出来的 app **自动**挂上
exception handler。**任何失败一律静默，绝不连累宿主进程。**

详见 [`sdk/python/README.md`](sdk/python/README.md)。

## SDK 用法

- [Python](sdk/python/README.md) — 一行接入 + CLI 一键 vendor
- [TypeScript](sdk/typescript/README.md)
- [Rust](sdk/rust/README.md)
- [CLI](cli/README.md)

## License

[AGPL-3.0](LICENSE)
