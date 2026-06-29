"""错误报告 Markdown 读写器。

对应 SPEC §三.2 错误报告格式（八章节模板）。
新建报告 / 回传解决方案 / 读取报告全部走这里。
"""
from __future__ import annotations

import platform
import random
import re
import string
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..config import Settings
from ..models.error_report import ReportCreate, ReportResolve

# ---------------- 工具 ----------------

_ID_RE = re.compile(r"^ERR-(\d{8})-(\d{6})-([0-9A-F]{4})$")
SEVERITY_ICON = {
    "info": "ℹ️ 信息",
    "warning": "⚠️ 警告",
    "error": "🔴 错误",
    "critical": "💥 严重",
}


def generate_error_id(now: Optional[datetime] = None) -> str:
    """生成 ERR-YYYYMMDD-HHMMSS-XXXX；XXXX 为 4 位大写十六进制随机数。"""
    now = now or datetime.now()
    rand = "".join(random.choices(string.hexdigits[:16].upper(), k=4))
    return f"ERR-{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}-{rand}"


def parse_error_id(error_id: str) -> tuple[str, str, str]:
    """拆出 (date_yyyy_mm_dd, time_hhmmss, rand)。"""
    m = _ID_RE.match(error_id.strip())
    if not m:
        raise ValueError(f"invalid error_id: {error_id!r}")
    d, t, r = m.groups()
    return f"{d[0:4]}-{d[4:6]}-{d[6:8]}", t, r


# ---------------- 渲染：八章节模板 ----------------

_REPORT_TEMPLATE = """# 🔴 错误报告

> **错误ID**：`{error_id}`
> **项目**：{project}
> **模块**：{module}
> **状态**：🔴 待解决
> **生成时间**：{created_at}
> **解决时间**：-
> **报告版本**：v1.0


## 一、错误摘要

| 项目 | 内容 |
|------|------|
| 错误类型 | `{error_type}` |
| 严重程度 | {severity_label} |
| 错误信息 | {error_message} |
| 用户操作 | {user_action} |
| 当前阶段 | {stage} |


## 二、上下文信息

{context_table}


## 三、操作路径

```
{operation_path}
```


## 四、输入数据

```yaml
{input_data_yaml}
```


## 五、日志（最近{log_count}行）

```
{logs_block}
```


## 六、错误栈

```
{stack_trace}
```


## 七、环境信息

| 项目 | 内容 |
|------|------|
{env_table}


## 八、解决方案

此部分在问题解决后由用户回传填写。

- 解决状态：⬜ 待解决
- 解决时间：-
- 解决方式：-

相关修改：-
"""


def _yaml_block(d: dict) -> str:
    if not d:
        return "# (无输入数据)"
    lines = []
    for k, v in d.items():
        # 字符串带引号；其他原样
        if isinstance(v, str):
            esc = v.replace('"', '\\"')
            lines.append(f'{k}: "{esc}"')
        else:
            lines.append(f"{k}: {v}")
    return "\n".join(lines)


def _kv_table(d: dict[str, str], default_rows: list[tuple[str, str]] | None = None) -> str:
    rows = list(default_rows or [])
    for k, v in (d or {}).items():
        rows.append((str(k), str(v)))
    if not rows:
        return "| - | (无) |"
    return "\n".join(f"| {k} | {v} |" for k, v in rows)


def _env_table(env: dict[str, str]) -> str:
    # 默认带上 OS / Python / 解释器
    base = {
        "OS": f"{platform.system()} {platform.release()}",
        "Python": platform.python_version(),
        "Platform": platform.platform(),
    }
    base.update(env or {})
    return "\n".join(f"| {k} | {v} |" for k, v in base.items())


def render_report(payload: ReportCreate, error_id: str, created_at: datetime) -> str:
    """根据 ReportCreate + error_id 渲染完整 Markdown。"""
    sev = (payload.severity or "error").lower()
    sev_icon = SEVERITY_ICON.get(sev, "🔴 错误")

    ctx_rows: list[tuple[str, str]] = []
    if payload.session_id:
        ctx_rows.append(("Session ID", f"`{payload.session_id}`"))
    if payload.project_display_name:
        ctx_rows.append(("项目名称", payload.project_display_name))
    if payload.stage:
        ctx_rows.append(("当前阶段", payload.stage))
    if payload.dialog_round is not None:
        ctx_rows.append(("对话轮次", f"第{payload.dialog_round}轮"))

    context_table = "| 项目 | 内容 |\n|------|------|\n" + _kv_table(
        payload.extra_context_table, ctx_rows
    )

    logs = payload.logs or []
    logs_block = "\n".join(logs) if logs else "(无日志)"

    return _REPORT_TEMPLATE.format(
        error_id=error_id,
        project=payload.project,
        module=payload.module,
        created_at=created_at.strftime("%Y-%m-%d %H:%M:%S"),
        error_type=payload.error_type,
        severity_label=sev_icon,
        error_message=payload.error_message,
        user_action=payload.user_action or "-",
        stage=payload.stage or "-",
        context_table=context_table,
        operation_path=payload.operation_path or "(未提供)",
        input_data_yaml=_yaml_block(payload.input_data),
        log_count=len(logs),
        logs_block=logs_block,
        stack_trace=payload.stack_trace or "(无错误栈)",
        env_table=_env_table(payload.env),
    )


# ---------------- 文件路径 / 读写 ----------------


def report_path(settings: Settings, project: str, module: str, error_id: str) -> Path:
    """{data_root}/projects/{project}/{module}/{YYYY-MM-DD}/{error_id}.md"""
    date_str, _, _ = parse_error_id(error_id)
    return (
        settings.projects_dir
        / _safe_seg(project)
        / _safe_seg(module)
        / date_str
        / f"{error_id}.md"
    )


def _safe_seg(s: str) -> str:
    """避免 / \\ : * ? \" < > | 等危险字符进入路径段。"""
    bad = '/\\:*?"<>|'
    out = "".join("_" if ch in bad else ch for ch in s.strip())
    return out or "_"


def write_new_report(settings: Settings, payload: ReportCreate) -> tuple[str, Path, datetime]:
    """生成 error_id、渲染、写文件，返回 (error_id, abs_path, created_at)。"""
    created_at = datetime.now()
    error_id = generate_error_id(created_at)
    text = render_report(payload, error_id, created_at)
    path = report_path(settings, payload.project, payload.module, error_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return error_id, path, created_at


# ---------------- 八、解决方案：追加 ----------------

_HEADER_LINE_STATUS = re.compile(r"^>\s*\*\*状态\*\*：.*$", re.MULTILINE)
_HEADER_LINE_RESOLVED_AT = re.compile(r"^>\s*\*\*解决时间\*\*：.*$", re.MULTILINE)
_SECTION_8_RE = re.compile(r"##\s*八、解决方案.*\Z", re.DOTALL)


def append_resolution(md_text: str, payload: ReportResolve, resolved_at: datetime) -> str:
    """将解决方案追加到第八章，并更新页头的状态/解决时间。"""
    ts = resolved_at.strftime("%Y-%m-%d %H:%M:%S")

    md_text = _HEADER_LINE_STATUS.sub("> **状态**：🟢 已解决", md_text, count=1)
    md_text = _HEADER_LINE_RESOLVED_AT.sub(f"> **解决时间**：{ts}", md_text, count=1)

    new_section = (
        "## 八、解决方案\n\n"
        f"- 解决状态：✅ 已解决\n"
        f"- 解决时间：{ts}\n"
        "- 解决方式：见下文\n\n"
        "### 解决方案\n\n"
        f"{payload.solution.strip()}\n\n"
        "### 相关修改\n\n"
        f"{(payload.related_changes or '-').strip()}\n"
    )

    if _SECTION_8_RE.search(md_text):
        md_text = _SECTION_8_RE.sub(new_section, md_text)
    else:
        md_text = md_text.rstrip() + "\n\n" + new_section
    return md_text


def read_report(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_report(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")
