"""Markdown 报告生成器。

对应 SPEC：项目一 §三.2 错误报告格式
"""
from __future__ import annotations
from pathlib import Path
from datetime import datetime
from ..models.error_report import ErrorReportCreate


def generate_error_id(now: datetime | None = None) -> str:
    """生成 ERR-YYYYMMDD-HHMMSS-XXXX 格式 ID（XXXX 为 4 位短哈希）。"""
    # TODO: 实现短哈希逻辑（基于 error_message + stack_trace 取前 4 位 hex）
    raise NotImplementedError


def render_report_markdown(error_id: str, payload: ErrorReportCreate) -> str:
    """按 SPEC §三.2 模板渲染完整 Markdown 报告（含八个章节）。"""
    # TODO: 填入模板，章节分别为：摘要、上下文、操作路径、输入数据、日志、错误栈、环境、解决方案占位
    raise NotImplementedError


def write_report(root: Path, error_id: str, project: str, module: str, content: str) -> Path:
    """落盘到 root/projects/{project}/{module}/{date}/{error_id}.md。"""
    # TODO: 实现路径构造 + mkdir -p + 写入
    raise NotImplementedError


def append_solution(report_path: Path, solution: str, related_changes: str | None) -> None:
    """把解决方案追加到现有报告的"八、解决方案"章节末尾，状态切到 🟢。"""
    # TODO: 读取原报告 → 替换状态行 → 追加解决方案 → 写回
    raise NotImplementedError
