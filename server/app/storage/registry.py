"""projects_registry.csv 读写。

注册表用途：绑定 project 名 ↔ 本地路径 + 打开方式，让 GUI 能把 stack trace
里的相对/绝对路径还原成"可点击复制 / 跳 IDE / 资源管理器"等动作。

文件位置：{data_root}/config/projects_registry.csv
列：name, local_path, open_with, custom_cmd, created_at
    - name        项目名（与 ReportCreate.project 对齐，主键，大小写敏感）
    - local_path  本地仓库根目录（绝对路径，可为空）
    - open_with   打开方式：none / copy_path / explorer / vscode / custom；空 → 跟随全局默认
    - custom_cmd  open_with=custom 时的命令模板，支持 {path} {line} 占位
    - created_at  YYYY-MM-DD HH:MM:SS

设计原则：
- 与 index.csv 解耦——index 由 report 创建驱动，registry 由用户主动维护。
- 注册表里没有的 project 名照样能写报告（保持零门槛接入）。
"""
from __future__ import annotations

import csv
import io
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..models.error_report import ProjectRegistry

_LOCK = threading.Lock()

HEADERS = ["name", "local_path", "open_with", "custom_cmd", "created_at"]


def _ensure_header(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(HEADERS)


def load_registry(path: Path) -> list[ProjectRegistry]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        out: list[ProjectRegistry] = []
        for r in reader:
            try:
                out.append(
                    ProjectRegistry(
                        name=r.get("name", "").strip(),
                        local_path=r.get("local_path", "").strip(),
                        open_with=r.get("open_with", "").strip(),
                        custom_cmd=r.get("custom_cmd", ""),
                        created_at=r.get("created_at", ""),
                    )
                )
            except Exception:
                continue
        return [x for x in out if x.name]


def _rewrite(path: Path, rows: list[ProjectRegistry]) -> None:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(HEADERS)
    for r in rows:
        writer.writerow([r.name, r.local_path, r.open_with, r.custom_cmd, r.created_at])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(buf.getvalue(), encoding="utf-8")


def get_one(path: Path, name: str) -> Optional[ProjectRegistry]:
    for r in load_registry(path):
        if r.name == name:
            return r
    return None


def upsert(path: Path, item: ProjectRegistry) -> ProjectRegistry:
    """按 name 主键 upsert。返回最终落库的行。"""
    with _LOCK:
        _ensure_header(path)
        rows = load_registry(path)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        found = False
        for i, r in enumerate(rows):
            if r.name == item.name:
                # 更新（保留 created_at）
                merged = ProjectRegistry(
                    name=item.name,
                    local_path=item.local_path,
                    open_with=item.open_with,
                    custom_cmd=item.custom_cmd,
                    created_at=r.created_at or now,
                )
                rows[i] = merged
                found = True
                break
        if not found:
            item.created_at = item.created_at or now
            rows.append(item)
        _rewrite(path, rows)
        for r in rows:
            if r.name == item.name:
                return r
        return item  # 理论上不可达


def delete(path: Path, name: str) -> bool:
    with _LOCK:
        rows = load_registry(path)
        new_rows = [r for r in rows if r.name != name]
        if len(new_rows) == len(rows):
            return False
        _rewrite(path, new_rows)
        return True
