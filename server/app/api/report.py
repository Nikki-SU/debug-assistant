"""POST /api/report —— 创建错误报告。

对应 SPEC：项目一 §四.1 HTTP API
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException

from ..models.error_report import ErrorReportCreate, ErrorReportResponse
# from ..storage import markdown_writer, csv_index  # TODO: 实现后启用

router = APIRouter()


@router.post("/report", response_model=ErrorReportResponse)
def create_report(payload: ErrorReportCreate) -> ErrorReportResponse:
    """接收错误数据 → 生成 ERR-{时间}-{短哈希} 报告 ID → 写 Markdown + CSV 索引。"""
    # TODO: 1) 生成 error_id；2) 渲染 Markdown 报告；3) 写入 projects/{project}/{module}/{date}/{error_id}.md
    # TODO: 4) 追加一行到 index.csv
    raise HTTPException(status_code=501, detail="Not implemented yet")
