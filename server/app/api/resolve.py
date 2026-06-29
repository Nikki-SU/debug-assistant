"""POST /api/resolve —— 回传解决方案，闭环。"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from ..config import Settings, get_settings
from ..models.error_report import ReportResolve, ResolveResult
from ..storage import (
    append_resolution,
    load_index,
    read_report,
    update_index_row,
    write_report,
)

router = APIRouter(tags=["resolve"])


def _locate_report(settings: Settings, error_id: str) -> Path:
    """通过 index.csv 找到报告文件路径。"""
    for r in load_index(settings.index_csv):
        if r.error_id == error_id:
            p = settings.data_root / r.relpath
            if p.exists():
                return p
    raise HTTPException(status_code=404, detail=f"error_id 不存在或文件丢失: {error_id}")


@router.post("/api/resolve", response_model=ResolveResult)
def resolve_report(payload: ReportResolve, settings: Settings = Depends(get_settings)) -> ResolveResult:
    if not payload.solution.strip():
        raise HTTPException(status_code=400, detail="solution 不能为空")

    path = _locate_report(settings, payload.error_id)
    resolved_at = datetime.now()
    ts = resolved_at.strftime("%Y-%m-%d %H:%M:%S")

    md = read_report(path)
    md = append_resolution(md, payload, resolved_at)
    write_report(path, md)

    updated = update_index_row(
        settings.index_csv,
        payload.error_id,
        status="resolved",
        resolved_at=ts,
    )
    if updated is None:
        # 索引被外部删除，但报告仍写了；不抛 500，反映真实状态
        raise HTTPException(status_code=500, detail="索引更新失败，但报告已追加解决方案")

    return ResolveResult(error_id=payload.error_id, status="resolved", resolved_at=ts)
