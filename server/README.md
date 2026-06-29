# debug-assistant · server

本地 FastAPI 服务，监听 `127.0.0.1:8765`，提供：

- `POST /api/report` 新建错误报告
- `POST /api/resolve` 回传解决方案（闭环）
- `GET /api/search` 全局检索
- `GET /api/report/{error_id}` 单条详情
- `GET /api/projects` 项目/模块 聚合
- `GET /api/health` 健康检查

## 启动

```bash
cd server
python -m venv .venv
.venv\Scripts\activate            # Windows PowerShell
pip install -r requirements.txt
python -m app.main
```

## 配置

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `DEBUG_ASSISTANT_DATA_ROOT` | `~/DebugAssistant` | 数据根目录 |
| `DEBUG_ASSISTANT_HOST` | `127.0.0.1` | 监听地址 |
| `DEBUG_ASSISTANT_PORT` | `8765` | 监听端口 |
| `DEBUG_ASSISTANT_LOG_LEVEL` | `INFO` | 日志级别 |

数据格式：`Markdown`（报告）+ `CSV`（索引/配置），**绝不使用 JSON 持久化**。
