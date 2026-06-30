"""debug-assistant CLI 入口（typer）。

示例：

    debugger report \\
        --project PaperAssistant --module backend \\
        --type TimeoutError --message "转换超时" \\
        --context '{"stage":"文献综述"}'

    debugger resolve ERR-20260629-143052-A3F9 \\
        --solution "拆分文件" --changes "调大超时到 600s"

    debugger search --keyword Mineru --status open
    debugger show ERR-20260629-143052-A3F9
    debugger projects
    debugger health

    # 一键接入到目标项目（vendor SDK + 可选 patch 入口）
    debugger install G:\\PaperAssistant
    debugger install G:\\PaperAssistant --auto-patch
"""
from __future__ import annotations

import json
import os
import sys
from typing import Optional

import typer

from debug_assistant import Debugger, DebuggerConfig

from .install_cmd import install_command

app = typer.Typer(
    name="debugger",
    add_completion=False,
    help="Debug Assistant 命令行：记录、闭环、检索错误报告。",
)


def _make_debugger(project: Optional[str], module: Optional[str],
                   host: Optional[str], port: Optional[int]) -> Debugger:
    cfg = DebuggerConfig.from_env(
        project=project or os.environ.get("DEBUG_ASSISTANT_PROJECT"),
        module=module or os.environ.get("DEBUG_ASSISTANT_MODULE"),
        host=host,
        port=port,
    )
    return Debugger(config=cfg)


def _parse_kv(s: Optional[str]) -> dict:
    if not s:
        return {}
    s = s.strip()
    if not s:
        return {}
    try:
        v = json.loads(s)
        if isinstance(v, dict):
            return {str(k): str(vv) for k, vv in v.items()}
    except Exception:
        pass
    # 退化为 k=v,k=v
    out: dict[str, str] = {}
    for piece in s.split(","):
        if "=" in piece:
            k, v = piece.split("=", 1)
            out[k.strip()] = v.strip()
    return out


@app.command(help="新建错误报告")
def report(
    project: str = typer.Option(..., "--project", "-p", help="项目名（目录第一级）"),
    module: str = typer.Option(..., "--module", "-m", help="模块名（目录第二级）"),
    type_: str = typer.Option(..., "--type", "-t", help="错误类型短标识"),
    message: str = typer.Option(..., "--message", "-M", help="错误信息一行摘要"),
    severity: str = typer.Option("error", "--severity", "-s"),
    stage: Optional[str] = typer.Option(None, "--stage"),
    user_action: Optional[str] = typer.Option(None, "--user-action"),
    context: Optional[str] = typer.Option(None, "--context", "-c",
                                          help='JSON 或 k=v,k=v'),
    log_file: Optional[str] = typer.Option(None, "--log-file"),
    stack: Optional[str] = typer.Option(None, "--stack"),
    host: Optional[str] = typer.Option(None, "--host"),
    port: Optional[int] = typer.Option(None, "--port"),
) -> None:
    d = _make_debugger(project, module, host, port)
    logs: list[str] = []
    if log_file:
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
                logs = lines[-20:]
        except Exception as e:
            typer.echo(f"[警告] 读取日志文件失败：{e}", err=True)
    eid = d.report(
        error_type=type_,
        error_message=message,
        severity=severity,
        stage=stage,
        user_action=user_action,
        context=_parse_kv(context),
        logs=logs,
        stack_trace=stack,
    )
    if eid:
        typer.echo(eid)
    else:
        typer.echo("[失败] 报告未能创建（server 不可达？已降级）", err=True)
        raise typer.Exit(code=2)


@app.command(help="回传解决方案，闭环")
def resolve(
    error_id: str = typer.Argument(...),
    solution: str = typer.Option(..., "--solution", "-S", help="支持 Markdown"),
    changes: Optional[str] = typer.Option(None, "--changes", "-c"),
    project: Optional[str] = typer.Option(None, "--project"),
    module: Optional[str] = typer.Option(None, "--module"),
    host: Optional[str] = typer.Option(None, "--host"),
    port: Optional[int] = typer.Option(None, "--port"),
) -> None:
    # project/module 不参与 resolve 的实际逻辑，只是 SDK 必填
    d = _make_debugger(project or "_cli_", module or "_cli_", host, port)
    if d.resolve(error_id=error_id, solution=solution, related_changes=changes):
        typer.echo(f"✅ resolved: {error_id}")
    else:
        typer.echo(f"❌ resolve 失败（server 不可达或 error_id 不存在）", err=True)
        raise typer.Exit(code=2)


@app.command(help="检索错误报告")
def search(
    keyword: Optional[str] = typer.Option(None, "--keyword", "-k"),
    project: Optional[str] = typer.Option(None, "--project", "-p"),
    module: Optional[str] = typer.Option(None, "--module", "-m"),
    status: Optional[str] = typer.Option(None, "--status", "-s"),
    severity: Optional[str] = typer.Option(None, "--severity"),
    limit: int = typer.Option(20, "--limit", "-n"),
    host: Optional[str] = typer.Option(None, "--host"),
    port: Optional[int] = typer.Option(None, "--port"),
) -> None:
    d = _make_debugger("_cli_", "_cli_", host, port)
    params = {}
    if keyword: params["keyword"] = keyword
    if project: params["project"] = project
    if module: params["module"] = module
    if status: params["status"] = status
    if severity: params["severity"] = severity
    params["limit"] = str(limit)
    import urllib.parse, urllib.request
    qs = urllib.parse.urlencode(params)
    url = f"{d.config.base_url}/api/search?{qs}"
    try:
        with urllib.request.urlopen(url, timeout=d.config.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        typer.echo(f"[失败] {e}", err=True)
        raise typer.Exit(code=2)
    hits = data.get("hits", [])
    total = data.get("total", 0)
    typer.echo(f"共 {total} 条，显示前 {len(hits)}：")
    for h in hits:
        mark = "🟢" if h["status"] == "resolved" else "🔴"
        typer.echo(
            f"  {mark} {h['error_id']}  [{h['project']}/{h['module']}]  "
            f"{h['error_type']}  {h['error_message'][:60]}"
        )


@app.command(help="查看单个报告的 Markdown 内容")
def show(
    error_id: str = typer.Argument(...),
    host: Optional[str] = typer.Option(None, "--host"),
    port: Optional[int] = typer.Option(None, "--port"),
) -> None:
    d = _make_debugger("_cli_", "_cli_", host, port)
    import urllib.request
    url = f"{d.config.base_url}/api/report/{error_id}"
    try:
        with urllib.request.urlopen(url, timeout=d.config.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        typer.echo(f"[失败] {e}", err=True)
        raise typer.Exit(code=2)
    typer.echo(f"# 文件路径：{data.get('path')}\n")
    typer.echo(data.get("markdown", ""))


@app.command(help="列出所有项目 / 模块及错误数")
def projects(
    host: Optional[str] = typer.Option(None, "--host"),
    port: Optional[int] = typer.Option(None, "--port"),
) -> None:
    d = _make_debugger("_cli_", "_cli_", host, port)
    import urllib.request
    url = f"{d.config.base_url}/api/projects"
    try:
        with urllib.request.urlopen(url, timeout=d.config.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        typer.echo(f"[失败] {e}", err=True)
        raise typer.Exit(code=2)
    for proj, mods in data.get("projects", {}).items():
        typer.echo(f"📁 {proj}")
        for m, n in mods.items():
            typer.echo(f"   └─ {m}: {n} 条")


@app.command(help="检查 server 健康")
def health(
    host: Optional[str] = typer.Option(None, "--host"),
    port: Optional[int] = typer.Option(None, "--port"),
) -> None:
    d = _make_debugger("_cli_", "_cli_", host, port)
    h = d.health()
    if h is None:
        typer.echo("❌ server 不可达", err=True)
        raise typer.Exit(code=2)
    typer.echo(json.dumps(h, ensure_ascii=False, indent=2))


# 一键接入子命令：debugger install <项目路径>
app.command("install", help="一键 vendor SDK 到目标项目（默认仅打印 patch，加 --auto-patch 才改入口文件）")(install_command)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
