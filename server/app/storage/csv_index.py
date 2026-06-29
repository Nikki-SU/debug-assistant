"""index.csv 读写。

CSV 是单一全局索引（{data_root}/projects/index.csv）。
列顺序见 models.IndexRow.headers()。
"""
from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Iterable, Optional

from ..models.error_report import IndexRow

# 同一进程内的写锁（FastAPI 默认线程池下足以避免 csv 行交错）
import threading

_LOCK = threading.Lock()


def _ensure_header(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(IndexRow.headers())


def append_index_row(path: Path, row: IndexRow) -> None:
    with _LOCK:
        _ensure_header(path)
        with path.open("a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([getattr(row, h) for h in IndexRow.headers()])


def load_index(path: Path) -> list[IndexRow]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows: list[IndexRow] = []
        for r in reader:
            try:
                rows.append(IndexRow(**{h: r.get(h, "") for h in IndexRow.headers()}))
            except Exception:
                # 跳过坏行
                continue
        return rows


def update_index_row(path: Path, error_id: str, **patches: str) -> Optional[IndexRow]:
    """按 error_id 定位并更新若干字段；返回更新后的行；找不到返回 None。"""
    with _LOCK:
        rows = load_index(path)
        target: Optional[IndexRow] = None
        for r in rows:
            if r.error_id == error_id:
                for k, v in patches.items():
                    if k in IndexRow.headers():
                        setattr(r, k, v)
                target = r
                break
        if target is None:
            return None
        # 重写整个文件
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(IndexRow.headers())
        for r in rows:
            writer.writerow([getattr(r, h) for h in IndexRow.headers()])
        path.write_text(buf.getvalue(), encoding="utf-8")
        return target


def search_index(
    path: Path,
    *,
    keyword: Optional[str] = None,
    project: Optional[str] = None,
    module: Optional[str] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    date_from: Optional[str] = None,  # YYYY-MM-DD
    date_to: Optional[str] = None,
    limit: int = 200,
    offset: int = 0,
) -> tuple[int, list[IndexRow]]:
    """对全局 index.csv 做关键字 + 过滤。

    keyword 匹配 error_id / error_type / error_message（不区分大小写）。
    """
    rows = load_index(path)
    if project:
        rows = [r for r in rows if r.project == project]
    if module:
        rows = [r for r in rows if r.module == module]
    if status:
        rows = [r for r in rows if r.status == status]
    if severity:
        rows = [r for r in rows if r.severity == severity]
    if date_from:
        rows = [r for r in rows if r.date >= date_from]
    if date_to:
        rows = [r for r in rows if r.date <= date_to]
    if keyword:
        kw = keyword.lower()
        rows = [
            r
            for r in rows
            if kw in r.error_id.lower()
            or kw in r.error_type.lower()
            or kw in r.error_message.lower()
        ]
    # 倒序：新的在前
    rows.sort(key=lambda r: r.created_at, reverse=True)
    total = len(rows)
    return total, rows[offset : offset + limit]
