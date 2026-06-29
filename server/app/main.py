"""FastAPI 入口：debug-assistant server。

启动：
    cd server
    pip install -r requirements.txt
    python -m app.main          # 默认 127.0.0.1:8765
    或
    uvicorn app.main:app --host 127.0.0.1 --port 8765 --reload
"""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import report_router, resolve_router, search_router
from .config import get_settings

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("debug-assistant")

app = FastAPI(
    title="Debug Assistant",
    version="0.1.0",
    description="独立的错误记录 / 闭环解决工具",
)

# 本地 GUI / sidecar 调用，CORS 全开（仅监听 127.0.0.1）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(report_router)
app.include_router(resolve_router)
app.include_router(search_router)


@app.get("/api/health")
def health() -> dict:
    return {
        "ok": True,
        "version": "0.1.0",
        "data_root": str(settings.data_root),
        "host": settings.host,
        "port": settings.port,
    }


def main() -> None:
    """脚本入口：python -m app.main"""
    import uvicorn

    log.info("data_root = %s", settings.data_root)
    log.info("listen    = %s:%s", settings.host, settings.port)
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
