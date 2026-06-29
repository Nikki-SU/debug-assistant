# debug-assistant 架构

## 概览

```
┌──────────────────┐   HTTP   ┌────────────────────────┐
│  业务侧（SDK）    │ ───────▶ │  Local Server (8765)   │
│  Python / TS /   │          │  FastAPI               │
│  Rust            │ ◀─────── │  Pydantic              │
└──────────────────┘          └─────┬──────────────────┘
                                    │ 文件 IO
                                    ▼
                       ┌────────────────────────────┐
                       │  Data Root                 │
                       │   ├ projects/              │
                       │   │   ├ {proj}/{mod}/      │
                       │   │   │   └ {date}/        │
                       │   │   │       └ ERR-*.md   │
                       │   │   └ index.csv          │
                       │   └ config/                │
                       │       └ debugger_config.csv│
                       └────────────────────────────┘
                                    ▲
                                    │ 同一台机器
                       ┌────────────┴───────────┐
                       │  GUI (Tauri + React)   │
                       │  • 列表 / 详情          │
                       │  • 新建报告 / 解决回传   │
                       │  • 一键复制 Markdown    │
                       └────────────────────────┘
```

## 模块边界

| 模块 | 路径 | 说明 |
|------|------|------|
| Server | `server/app/` | FastAPI，提供 HTTP API，管理存储 |
| Storage | `server/app/storage/` | Markdown 八章节模板 + CSV 索引读写 |
| Models | `server/app/models/` | Pydantic 请求/响应/索引模型 |
| Python SDK | `sdk/python/debug_assistant/` | 仅标准库；连不上 server 静默降级 |
| TypeScript SDK | `sdk/typescript/src/` | fetch + AbortController；浏览器/Tauri/Node 通用 |
| Rust SDK | `sdk/rust/src/` | ureq 同步 HTTP |
| CLI | `cli/debug_assistant_cli/` | typer，依赖 Python SDK |
| GUI | `gui/src/` | Tauri v2 + React 18 + Vite |

## 数据流：错误闭环

```
1. 业务侧出错
   → SDK.report(error=e, context=...)
   → POST /api/report
   → markdown_writer.write_new_report (八章节模板 + ERR-id)
   → csv_index.append_index_row (status=open)
   → 返回 error_id

2. 用户复制 Markdown（GUI / CLI 都支持），粘贴给 AI
   → AI 给出解决方案

3. 用户在 GUI「✅ 问题已解决」对话框粘贴解决方案
   → POST /api/resolve { error_id, solution, related_changes }
   → 定位文件 → append_resolution（更新页头状态 + 追加第八章）
   → csv_index.update_index_row (status=resolved, resolved_at)
```

## 端口

| 服务 | 端口 |
|------|------|
| server | 8765 |
| GUI vite dev | 1420 |

## 数据格式铁律

- 持久化：Markdown（报告全文）+ CSV（index / config）
- 在途：JSON（仅 HTTP body）

数据库？不需要。文件系统就够了。
