/**
 * HTTP 客户端，封装 /api/report 与 /api/resolve。
 * 对应 SPEC：项目一 §六.2
 */

export interface DebuggerOptions {
  project: string;
  module: string;
  host?: string;
  port?: number;
  enabled?: boolean;
  timeout?: number;
}

export interface ReportPayload {
  error?: unknown;
  errorType?: string;
  errorMessage?: string;
  context?: Record<string, unknown>;
  inputData?: Record<string, unknown>;
  logs?: string[];
}

export interface ResolvePayload {
  errorId: string;
  solution: string;
  relatedChanges?: string;
}

export class Debugger {
  private readonly baseUrl: string;
  private readonly enabled: boolean;
  private readonly project: string;
  private readonly module: string;

  constructor(opts: DebuggerOptions) {
    this.project = opts.project;
    this.module = opts.module;
    this.baseUrl = `http://${opts.host ?? "127.0.0.1"}:${opts.port ?? 8765}`;
    this.enabled = opts.enabled ?? true;
  }

  async report(payload: ReportPayload): Promise<string | null> {
    if (!this.enabled) return null;
    // TODO: fetch POST /api/report，组装 payload，失败降级（不要把异常上报失败再抛给业务）
    throw new Error("Not implemented yet");
  }

  async resolve(payload: ResolvePayload): Promise<boolean> {
    // TODO: fetch POST /api/resolve
    throw new Error("Not implemented yet");
  }
}
