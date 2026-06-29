# debug-assistant TypeScript SDK

用于 Tauri 前端或 Node.js 业务侧。失败静默降级，不抛错到业务。

```ts
import { Debugger } from "debug-assistant-sdk";

const dbg = new Debugger({ project: "PaperAssistant", module: "frontend" });
dbg.installGlobalHandlers();           // 自动捕获 window.onerror / unhandledrejection

try {
  await api.uploadFile(file);
} catch (e) {
  const eid = await dbg.report({ error: e, context: { file_name: file.name } });
}

await dbg.resolve({ error_id: eid!, solution: "解决方式" });
```

构建：

```bash
cd sdk/typescript
npm install
npm run build
```
