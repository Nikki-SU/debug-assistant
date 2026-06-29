# 🐛 Debug Assistant

跨项目通用的错误记录与闭环解决工具。

## 定位

- 独立桌面工具，**不绑定**任何具体应用
- 任何项目（Python / Rust / Tauri / 前端 / 后端 / 脚本）都可接入
- 核心：**记录错误 + 一键复制给 AI + 闭环回传解决方案**

## 三种接入方式

| 方式 | 说明 |
|------|------|
| HTTP API | 推荐，监听 `localhost:8765`，程序自动上报 |
| CLI | 适合脚本/快速记录 |
| GUI | 适合无法自动捕获的场景 |

## 技术栈

- **前端 GUI**：Tauri v2 + React + TypeScript
- **后端服务**：Python 3.11+ + FastAPI（监听 8765）
- **数据格式**：Markdown（报告）+ CSV（索引/配置），**绝不使用 JSON 落盘**
- **打包**：独立 EXE（Windows）

## 三种 SDK

- Python SDK：`debug_assistant`
- TypeScript SDK：`debug-assistant-sdk`（适配 Tauri 前端）
- Rust SDK：`debug-assistant-sdk`（Rust crate）

## 闭环机制

```
错误发生 → 记录报告（🔴 待解决）→ 复制给 AI 诊断 → 用户回传解决方案 → 状态 🟢 已解决
```

## 项目状态

🚧 **正在从零搭建中**（2026-06-29 启动）

详细技术规格见 [`docs/SPEC.md`](docs/SPEC.md)。

## License

[AGPL-3.0](LICENSE)
