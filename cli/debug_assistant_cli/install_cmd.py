"""``debugger install <项目路径>``：一键 vendor SDK + 可选 patch 入口文件。

设计取舍：
- 默认行为**保守**：vendor SDK + 打印 patch 片段让用户自己贴。
- 加 ``--auto-patch`` 才会真改入口文件（并生成 ``.debug-assistant.bak`` 备份）。
- ``--dry-run`` 只打印将要做的事，不写任何文件。
- ``--no-patch`` 仅 vendor，连 patch 提示都不打印。

vendor 模式（拷源码进 ``<project>/vendor/debug_assistant/``）绕过 pip，
PyInstaller / sidecar 打包无忧 —— 这是 Rosa 给 PaperAssistant 选的策略。
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import List, Optional

import typer

PATCH_MARKER_BEGIN = "# === debug-assistant auto-install ==="
PATCH_MARKER_END = "# === /debug-assistant ==="

ENTRY_CANDIDATES = ["main.py", "app.py", "api.py", "server.py"]
# 搜索子目录的顺序：项目根 > sidecar > python/backend/src
PROJECT_SUBDIRS = ["", "src-tauri/sidecar", "python", "backend", "src"]

VENV_CANDIDATES = [
    ".venv",
    "venv",
    "env",
    "src-tauri/sidecar/.venv",
    "src-tauri/sidecar/venv",
    "python/.venv",
    "backend/.venv",
]


def _find_sdk_source() -> Optional[Path]:
    """定位当前进程能 import 到的 ``debug_assistant`` 包的源码目录。"""
    try:
        import debug_assistant  # type: ignore
        f = getattr(debug_assistant, "__file__", None)
        if not f:
            return None
        return Path(f).resolve().parent
    except Exception:  # noqa: BLE001
        return None


def _find_entry_files(project_dir: Path) -> List[Path]:
    """按 PROJECT_SUBDIRS × ENTRY_CANDIDATES 的顺序搜入口文件。"""
    found: List[Path] = []
    seen: set[Path] = set()
    for sub in PROJECT_SUBDIRS:
        for name in ENTRY_CANDIDATES:
            base = project_dir / sub if sub else project_dir
            p = (base / name).resolve()
            if p.exists() and p.is_file() and p not in seen:
                seen.add(p)
                found.append(p)
    return found


def _find_venv(project_dir: Path) -> Optional[Path]:
    for c in VENV_CANDIDATES:
        p = project_dir / c
        if p.exists() and p.is_dir():
            return p
    return None


def _build_patch(project_name: str) -> str:
    """生成要插入到入口文件顶部的 patch 片段（带幂等标记）。"""
    return (
        f"{PATCH_MARKER_BEGIN}\n"
        "import sys as _sys, os as _os\n"
        "_sys.path.insert(0, _os.path.join("
        "_os.path.dirname(_os.path.abspath(__file__)), 'vendor'))\n"
        "try:\n"
        "    import debug_assistant\n"
        f"    debug_assistant.auto_install(project={project_name!r})\n"
        "except Exception:\n"
        "    pass\n"
        f"{PATCH_MARKER_END}\n"
    )


def _has_patch(content: str) -> bool:
    return PATCH_MARKER_BEGIN in content


def _insert_patch(content: str, patch: str) -> str:
    """在 shebang / encoding 声明之后、其他 import 之前插入 patch。"""
    lines = content.splitlines(keepends=True)
    insert_at = 0
    # PEP 263：shebang 必须在第 1 行；encoding 在第 1 或第 2 行。
    if lines and lines[0].startswith("#!"):
        insert_at = 1
    # 扫前两行找 "coding" 声明
    for i in range(0, min(2, len(lines))):
        if "coding" in lines[i] and (":" in lines[i] or "=" in lines[i]):
            insert_at = max(insert_at, i + 1)
    # 确保 patch 前面有换行
    head = "".join(lines[:insert_at])
    tail = "".join(lines[insert_at:])
    if head and not head.endswith("\n"):
        head += "\n"
    return head + patch + tail


def install_command(
    project_path: str = typer.Argument(..., help="目标项目根目录"),
    auto_patch: bool = typer.Option(
        False, "--auto-patch",
        help="实际修改入口文件（默认仅打印 patch 片段，不动文件）。",
    ),
    no_patch: bool = typer.Option(
        False, "--no-patch",
        help="仅 vendor，不打印 patch 提示也不改文件。",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run",
        help="只打印将要做的事，不写任何文件。",
    ),
    entry: Optional[str] = typer.Option(
        None, "--entry", "-e",
        help="显式指定入口文件路径（跳过自动检测）。",
    ),
    project_name: Optional[str] = typer.Option(
        None, "--name",
        help="覆盖 project 名（默认取目录 basename）。",
    ),
) -> None:
    """一键把 debug-assistant SDK 接入目标 Python 项目。

    步骤：

    1. 拷贝 ``debug_assistant/`` 包到 ``<project>/vendor/debug_assistant/``。
    2. 自动检测入口文件（``main.py`` / ``app.py`` / ``api.py`` / ``server.py``），
       默认只**打印** patch 片段；加 ``--auto-patch`` 才真改。
    3. 已有 patch 标记则幂等跳过。
    """
    proj = Path(project_path).expanduser().resolve()
    if not proj.exists() or not proj.is_dir():
        typer.echo(f"❌ 项目路径不存在或不是目录：{proj}", err=True)
        raise typer.Exit(code=2)

    name = project_name or proj.name
    typer.echo(f"🔧 debug-assistant install → {proj}")
    typer.echo(f"   项目名：{name}")
    if dry_run:
        typer.echo("   模式：--dry-run（不写任何文件）")

    # 1) 定位 SDK 源码
    sdk_src = _find_sdk_source()
    if sdk_src is None:
        typer.echo(
            "❌ 找不到 debug_assistant 包源码。"
            "请先在当前环境 `pip install debug-assistant-sdk`。",
            err=True,
        )
        raise typer.Exit(code=2)
    typer.echo(f"   📦 SDK 源：{sdk_src}")

    # 2) venv 提示（vendor 模式不强依赖 venv，仅信息）
    venv = _find_venv(proj)
    if venv:
        typer.echo(f"   🐍 检测到 venv：{venv}")
    else:
        typer.echo("   🐍 未检测到 venv（vendor 模式无需 pip，可忽略）")

    # 3) vendor SDK
    vendor_dest = proj / "vendor" / "debug_assistant"
    if dry_run:
        typer.echo(f"   [dry-run] 将复制 {sdk_src} → {vendor_dest}")
    else:
        try:
            vendor_dest.parent.mkdir(parents=True, exist_ok=True)
            if vendor_dest.exists():
                shutil.rmtree(vendor_dest)
            shutil.copytree(
                sdk_src,
                vendor_dest,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
            )
            typer.echo(f"   ✅ vendor 完成：{vendor_dest}")
        except Exception as e:  # noqa: BLE001
            typer.echo(f"❌ vendor 失败：{e}", err=True)
            raise typer.Exit(code=2)

    # 4) 入口文件检测
    if entry:
        entries = [Path(entry).expanduser().resolve()]
        if not entries[0].exists():
            typer.echo(f"❌ 指定入口文件不存在：{entries[0]}", err=True)
            raise typer.Exit(code=2)
    else:
        entries = _find_entry_files(proj)

    patch = _build_patch(name)

    if no_patch:
        typer.echo("   ⏭  --no-patch：跳过 patch 阶段")
        typer.echo("🎉 vendor 完成。")
        return

    if not entries:
        typer.echo(
            "   ⚠️  未自动检测到入口文件（main.py/app.py/api.py/server.py）。"
        )
        typer.echo("      可加 --entry <文件> 显式指定，或手动把下面片段粘贴到入口顶部：\n")
        typer.echo("─" * 60)
        typer.echo(patch.rstrip())
        typer.echo("─" * 60)
        return

    if len(entries) > 1 and not entry:
        typer.echo("   📂 检测到多个候选入口：")
        for i, p in enumerate(entries):
            typer.echo(f"      [{i}] {p}")
        idx_str = typer.prompt("选择编号（输入数字）", default="0")
        try:
            entries = [entries[int(idx_str)]]
        except Exception:
            typer.echo("❌ 选择无效", err=True)
            raise typer.Exit(code=2)

    target = entries[0]
    typer.echo(f"   🎯 入口文件：{target}")

    try:
        content = target.read_text(encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        typer.echo(f"❌ 无法读取入口文件：{e}", err=True)
        raise typer.Exit(code=2)

    if _has_patch(content):
        typer.echo("   ✅ 入口文件已包含 debug-assistant patch（幂等跳过）")
        typer.echo("🎉 完成。")
        return

    if auto_patch and not dry_run:
        try:
            backup = target.with_name(target.name + ".debug-assistant.bak")
            backup.write_text(content, encoding="utf-8")
            new_content = _insert_patch(content, patch)
            target.write_text(new_content, encoding="utf-8")
            typer.echo(f"   ✅ 已写入 patch（原文件备份：{backup.name}）")
        except Exception as e:  # noqa: BLE001
            typer.echo(f"❌ 写入失败：{e}", err=True)
            raise typer.Exit(code=2)
    else:
        if dry_run:
            typer.echo("   [dry-run] 将插入以下片段到入口文件顶部：")
        else:
            typer.echo(
                "   📋 默认保守策略：不直接修改入口文件。"
                "请把以下片段贴到入口顶部（shebang/encoding 后、其他 import 前），"
                "或重跑命令加 --auto-patch 让 CLI 自动写入：\n"
            )
        typer.echo("─" * 60)
        typer.echo(patch.rstrip())
        typer.echo("─" * 60)

    typer.echo(
        "🎉 完成。重启该项目 Python 进程后，未捕获异常会自动上报到 debug-assistant server。"
    )


__all__ = ["install_command"]
