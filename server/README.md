# debug-assistant / server

FastAPI 服务，监听 `localhost:8765`，接收错误报告与解决方案回传。

## 启动
```bash
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8765
```

## 接口
| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/report` | 创建错误报告 |
| POST | `/api/resolve` | 回传解决方案 |
| GET  | `/api/search` | 跨项目检索错误报告 |
| GET  | `/api/health` | 健康检查 |

对应 SPEC：项目一 §四. 三种使用方式 / §五. 闭环机制
