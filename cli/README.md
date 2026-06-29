# debug-assistant CLI

```bash
debugger health
debugger projects
debugger search --keyword timeout --status open
debugger report -p PaperAssistant -m backend -t TimeoutError -M "转换超时" --stage 文献综述
debugger show ERR-20260629-143052-A3F9
debugger resolve ERR-20260629-143052-A3F9 -S "拆分文件" -c "调大超时"
```

依赖：`typer` + `debug-assistant-sdk`（在 server 跑起来后再用）。
