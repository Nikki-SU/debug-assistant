"""POST /api/report —— 新建错误报告。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..config import Settings, get_settings
from ..models.error_report import IndexRow, ReportCreate, ReportCreated
from ..storage import append_index_row, write_new_report

router = APIRouter(tags=["report"])


@router.post("/api/report", response_model=ReportCreated, status_code=201)
def create_report(payload: ReportCreate, settings: Settings = Depends(get_settings)) -> ReportCreated:
    if not payload.project or not payload.module:
        raise HTTPException(status_code=400, detail="project / module 不能为空")

    error_id, abs_path, created_at = write_new_report(settings, payload)

    # 写索引
    rel = abs_path.relative_to(settings.data_root).as_posix()
    row = IndexRow(
        error_id=error_id,
        project=payload.project,
        module=payload.module,
        date=created_at.strftime("%Y-%m-%d"),
        created_at=created_at.strftime("%Y-%m-%d %H:%M:%S"),
        resolved_at="",
        status="open",
        severity=payload.severity or "error",
        error_type=payload.error_type,
        error_message=payload.error_message,
        relpath=rel,
    )
    append_index_row(settings.index_csv, row)

    return ReportCreated(
        error_id=error_id,
        path=str(abs_path),
        url=f"/report/{error_id}",
    )
