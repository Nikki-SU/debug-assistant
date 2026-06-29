# debug-assistant Rust SDK

```rust
use debug_assistant_sdk::{Debugger, ReportPayload};

let dbg = Debugger::new("PaperAssistant", "backend");

if let Err(e) = mineru.convert(&path) {
    let _ = dbg.report(&ReportPayload {
        error_type: "TimeoutError",
        error_message: &e.to_string(),
        stage: Some("文献综述"),
        context: vec![("file_name".into(), path.display().to_string())],
        ..Default::default()
    });
}
```

依赖 `ureq`（同步 HTTP）。失败仅打印 stderr 警告，不向上传播。
