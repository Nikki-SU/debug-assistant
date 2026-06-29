"""CSV 索引读写。

projects/index.csv 字段：error_id,project,module,error_type,severity,status,created_at,resolved_at,report_path
"""
from __future__ import annotations
import csv
from pathlib import Path

INDEX_HEADERS = [
    "error_id", "project", "module", "error_type",
    "severity", "status", "created_at", "resolved_at", "report_path",
]


def ensure_index(index_path: Path) -> None:
    """若 index.csv 不存在则创建并写入表头。"""
    # TODO: 实现
    raise NotImplementedError


def append_index_row(index_path: Path, row: dict) -> None:
    """向 index.csv 追加一行。"""
    # TODO: 实现
    raise NotImplementedError


def update_index_status(index_path: Path, error_id: str, status: str, resolved_at: str) -> None:
    """更新指定 error_id 的状态和解决时间。需要原子写（写临时文件 → 替换）。"""
    # TODO: 实现
    raise NotImplementedError


def search_index(index_path: Path, **filters) -> list[dict]:
    """读取 index.csv → 按 filters 过滤 → 返回行列表。"""
    # TODO: 实现
    raise NotImplementedError
