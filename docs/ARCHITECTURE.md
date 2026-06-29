# debug-assistant 架构总览

## 模块划分

```
debug-assistant/
├── server/   # FastAPI 服务（监听 8765），核心
├── sdk/      # Python / TypeScript / Rust 三个客户端 SDK
├── gui/      # Tauri v2 + React GUI（手动操作 + 报告浏览）
├── cli/      # 命令行（thin wrapper over HTTP API）
└── docs/     # SPEC + 架构说明
```

## 数据流

```
业务程序 ──SDK──┐
CLI ──────────┼──> HTTP API (8765) ──> server/app/api ──> server/app/storage
GUI ──────────┘                                            ├─ markdown_writer.py (Markdown 报告)
                                                           └─ csv_index.py (CSV 索引)
                                                                    │
                                                                    ▼
                                          {data_root}/projects/{project}/{module}/{date}/ERR-xxx.md
                                          {data_root}/projects/index.csv
```

## 铁律
- 所有落盘只能 Markdown + CSV，**绝不使用 JSON**（JSON 仅用于 HTTP API 在途传输）
- SDK 失败必须降级（不能因为 server 没启而让业务侧崩溃）
- 默认绑定 127.0.0.1，不监听 0.0.0.0（本机工具）
