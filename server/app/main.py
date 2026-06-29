"""debug-assistant FastAPI 入口。

监听 localhost:8765，提供错误报告创建、解决方案回传、跨项目检索能力。
"""
from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import SETTINGS
from .api import report, resolve, search

app = FastAPI(
    title="debug-assistant",
    version="0.1.0",
    description="Cross-project error logging and closed-loop resolution tool",
)

# CORS：允许本地任意端口（GUI、其他项目）访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(report.router, prefix="/api")
app.include_router(resolve.router, prefix="/api")
app.include_router(search.router, prefix="/api")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}


def run() -> None:
    """CLI 入口，等同于 uvicorn 启动。"""
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=SETTINGS.host,
        port=SETTINGS.port,
        log_level=SETTINGS.log_level.lower(),
    )


if __name__ == "__main__":
    run()
