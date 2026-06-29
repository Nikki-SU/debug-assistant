# debug-assistant Rust SDK

```rust
use debug_assistant_sdk::Debugger;

let dbg = Debugger::new("PaperAssistant", "backend", "127.0.0.1", 8765);

if let Err(e) = risky_op() {
    dbg.report(&e, &context, &logs);
}
```

对应 SPEC：项目一 §六.3 Rust SDK
