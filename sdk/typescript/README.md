# debug-assistant TypeScript SDK

```typescript
import { Debugger } from 'debug-assistant-sdk';

const dbg = new Debugger({ project: 'PaperAssistant', module: 'frontend', port: 8765 });

window.addEventListener('error', (e) => dbg.report({ error: e.error }));

try { await api.upload(file); }
catch (error) { dbg.report({ error, context: { file_name: file.name } }); }
```

对应 SPEC：项目一 §六.2 TypeScript SDK
