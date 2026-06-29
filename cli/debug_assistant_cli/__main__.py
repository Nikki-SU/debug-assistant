"""CLI entrypoint - thin wrapper over HTTP API."""
from __future__ import annotations
import typer

app = typer.Typer(help="debug-assistant CLI")


@app.command()
def report(
    project: str = typer.Option(..., "--project"),
    module: str = typer.Option(..., "--module"),
    error_type: str = typer.Option(..., "--type"),
    message: str = typer.Option(..., "--message"),
    context: str = typer.Option("{}", "--context", help="JSON 字符串（仅 CLI 入参传输用，落盘仍 Markdown+CSV）"),
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8765, "--port"),
):
    """创建错误报告（调用 HTTP API）。"""
    # TODO: 解析 context → POST /api/report → 打印 error_id
    typer.echo("Not implemented yet")
    raise typer.Exit(code=1)


@app.command()
def resolve(
    error_id: str = typer.Option(..., "--id"),
    solution: str = typer.Option(..., "--solution"),
    related_changes: str = typer.Option(None, "--changes"),
):
    """回传解决方案。"""
    # TODO: POST /api/resolve
    typer.echo("Not implemented yet")
    raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
