"""GET /api/search —— 跨项目检索错误报告。

对应 SPEC：项目一 §二. 核心功能 - 全局检索
"""
from __future__ import annotations
from fastapi import APIRouter, Query

router = APIRouter()


@router.get("/search")
def search_reports(
    project: str | None = Query(None, description="按项目过滤"),
    module: str | None = Query(None, description="按模块过滤"),
    status: str | None = Query(None, description="待解决/已解决"),
    keyword: str | None = Query(None, description="错误信息关键词"),
) -> dict:
    """读取 index.csv → 按条件过滤 → 返回报告头信息列表。"""
    # TODO: 实现 CSV 过滤逻辑
    return {"results": [], "count": 0}
