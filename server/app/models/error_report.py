"""错误报告 Pydantic 模型。

对应 SPEC §四.1 HTTP API 的请求体定义。
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------- 请求 / 响应模型 ----------


class ReportCreate(BaseModel):
    """POST /api/report 请求体。"""

    project: str = Field(..., description="项目名，作为存储目录第一级")
    module: str = Field(..., description="模块名，作为存储目录第二级（如 backend / frontend）")
    error_type: str = Field(..., description="错误类型短标识，如 MinerUConversionTimeout")
    error_message: str = Field(..., description="错误信息一行摘要")

    # —— 以下为可选字段 ——
    severity: str = Field(default="error", description="严重程度：info/warning/error/critical")
    user_action: Optional[str] = Field(default=None, description="用户当时的操作")
    stage: Optional[str] = Field(default=None, description="业务阶段（如 文献综述）")

    session_id: Optional[str] = None
    project_display_name: Optional[str] = Field(default=None, description="项目人类可读名（不同于目录名）")
    dialog_round: Optional[int] = None
    extra_context_table: dict[str, str] = Field(default_factory=dict, description="额外的上下文键值，逐行渲染")

    operation_path: Optional[str] = Field(default=None, description="操作链路文本，多行")
    input_data: dict[str, Any] = Field(default_factory=dict, description="输入数据，YAML 风格写入")
    logs: list[str] = Field(default_factory=list, description="最近 N 行日志")
    stack_trace: Optional[str] = None

    env: dict[str, str] = Field(default_factory=dict, description="环境信息表，键=项目，值=内容")


class ReportResolve(BaseModel):
    """POST /api/resolve 请求体。"""

    error_id: str = Field(..., description="ERR-YYYYMMDD-HHMMSS-XXXX")
    solution: str = Field(..., description="解决方案，支持 Markdown")
    related_changes: Optional[str] = Field(default=None, description="相关代码改动，支持 Markdown")


# ---------- 内部索引行 ----------


class IndexRow(BaseModel):
    """index.csv 一行。"""

    error_id: str
    project: str
    module: str
    date: str  # YYYY-MM-DD
    created_at: str  # YYYY-MM-DD HH:MM:SS
    resolved_at: str = ""  # 同上格式，未解决为空
    status: str = "open"  # open / resolved
    severity: str = "error"
    error_type: str = ""
    error_message: str = ""
    relpath: str = ""  # 相对 data_root 的报告路径

    @staticmethod
    def headers() -> list[str]:
        return [
            "error_id",
            "project",
            "module",
            "date",
            "created_at",
            "resolved_at",
            "status",
            "severity",
            "error_type",
            "error_message",
            "relpath",
        ]


# ---------- API 响应 ----------


class ReportCreated(BaseModel):
    error_id: str
    path: str  # 绝对路径，便于 GUI/CLI 打开
    url: str   # GUI 内的 URL（如 file:// 或 内部 route）


class ResolveResult(BaseModel):
    error_id: str
    status: str
    resolved_at: str


class SearchHit(BaseModel):
    error_id: str
    project: str
    module: str
    date: str
    created_at: str
    resolved_at: str
    status: str
    severity: str
    error_type: str
    error_message: str
    relpath: str


class SearchResponse(BaseModel):
    total: int
    hits: list[SearchHit]
