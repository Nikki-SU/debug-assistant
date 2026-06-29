"""API 路由集合。"""
from .report import router as report_router
from .resolve import router as resolve_router
from .search import router as search_router

__all__ = ["report_router", "resolve_router", "search_router"]
