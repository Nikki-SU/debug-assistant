"""错误报告数据模型。

对应 SPEC：项目一 §三.2 错误报告格式（Markdown）
注意：内部落盘是 Markdown + CSV，这些模型只在 HTTP 层使用，不写入 JSON 文件。
"""
from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field


class ErrorReportCreate(BaseModel):
    project: str = Field(..., description="项目名，如 PaperAssistant")
    module: str = Field(..., description="模块名，如 backend / frontend")
    error_type: str = Field(..., description="错误类型，如 TimeoutError")
    error_message: str = Field(..., description="错误信息")
    stack_trace: str | None = Field(None, description="错误栈")
    severity: str = Field("error", description="严重程度：info / warn / error / critical")
    context: dict[str, Any] = Field(default_factory=dict, description="上下文信息（session_id、stage 等）")
    input_data: dict[str, Any] = Field(default_factory=dict, description="出错时的输入数据")
    logs: list[str] = Field(default_factory=list, description="最近 N 行日志")
    environment: dict[str, str] = Field(default_factory=dict, description="OS / 版本 / 运行环境")


class ErrorReportResponse(BaseModel):
    error_id: str  # 形如 ERR-20260629-143052-A3F9
    report_path: str  # 落盘的 Markdown 相对路径
    status: str  # "pending" / "resolved"
