"""POST /api/resolve —— 回传解决方案，状态置为 🟢 已解决。

对应 SPEC：项目一 §五. 闭环机制
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


class ResolvePayload(BaseModel):
    error_id: str
    solution: str
    related_changes: str | None = None


class ResolveResponse(BaseModel):
    error_id: str
    status: str  # "resolved"


router = APIRouter()


@router.post("/resolve", response_model=ResolveResponse)
def resolve_report(payload: ResolvePayload) -> ResolveResponse:
    """把解决方案追加到原报告 Markdown 的"八、解决方案"章节末尾，状态切到 🟢。"""
    # TODO: 1) 通过 error_id 定位 Markdown 文件
    # TODO: 2) 替换/追加"解决状态"与"解决方案"段
    # TODO: 3) 更新 index.csv 中该行的 status 列
    raise HTTPException(status_code=501, detail="Not implemented yet")
