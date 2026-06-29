"""GET /api/search —— 全局检索 + 单条读取。"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..config import Settings, get_settings
from ..models.error_report import SearchHit, SearchResponse
from ..storage import load_index, read_report, search_index

router = APIRouter(tags=["search"])


@router.get("/api/search", response_model=SearchResponse)
def search(
    keyword: Optional[str] = Query(default=None),
    project: Optional[str] = None,
    module: Optional[str] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    settings: Settings = Depends(get_settings),
) -> SearchResponse:
    total, rows = search_index(
        settings.index_csv,
        keyword=keyword,
        project=project,
        module=module,
        status=status,
        severity=severity,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
    return SearchResponse(
        total=total,
        hits=[SearchHit(**r.model_dump()) for r in rows],
    )


@router.get("/api/report/{error_id}")
def get_report(error_id: str, settings: Settings = Depends(get_settings)) -> dict:
    for r in load_index(settings.index_csv):
        if r.error_id == error_id:
            p = settings.data_root / r.relpath
            if not p.exists():
                raise HTTPException(status_code=404, detail="报告文件丢失")
            return {
                "error_id": error_id,
                "meta": r.model_dump(),
                "markdown": read_report(p),
                "path": str(p),
            }
    raise HTTPException(status_code=404, detail=f"error_id 不存在: {error_id}")


@router.get("/api/projects")
def list_projects(settings: Settings = Depends(get_settings)) -> dict:
    """聚合：项目 → 模块 → 错误数。GUI 左侧导航用。"""
    tree: dict[str, dict[str, int]] = {}
    for r in load_index(settings.index_csv):
        tree.setdefault(r.project, {}).setdefault(r.module, 0)
        tree[r.project][r.module] += 1
    return {"projects": tree}
