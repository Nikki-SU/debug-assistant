/**
 * debug-assistant TypeScript SDK.
 *
 * 用于 Tauri 前端 / Node.js 业务侧。失败静默降级，绝不抛到业务。
 */

export interface DebuggerConfig {
  project: string;
  module: string;
  host?: string;
  port?: number;
  enabled?: boolean;
  /** HTTP 超时（毫秒）。默认 2000。 */
  timeoutMs?: number;
}

export interface ReportPayload {
  error?: Error | unknown;
  error_type?: string;
  error_message?: string;
  stack_trace?: string;
  severity?: "info" | "warning" | "error" | "critical";
  context?: Record<string, unknown>;
  user_action?: string;
  stage?: string;
  session_id?: string;
  project_display_name?: string;
  dialog_round?: number;
  operation_path?: string;
  input_data?: Record<string, unknown>;
  logs?: string[];
  env?: Record<string, string>;
}

export interface ReportCreated {
  error_id: string;
  path: string;
  url: string;
}

export interface ResolvePayload {
  error_id: string;
  solution: string;
  related_changes?: string;
}

function readEnv(key: string): string | undefined {
  // 兼容 Node / Browser / Tauri
  const g = globalThis as { process?: { env?: Record<string, string> } };
  if (g.process?.env?.[key]) {
    return g.process!.env![key];
  }
  return undefined;
}

function warn(msg: string, e?: unknown): void {
  if (typeof console !== "undefined") {
    (console as { warn?: (...a: unknown[]) => void }).warn?.(`[debug-assistant] ${msg}`, e ?? "");
  }
}

export class Debugger {
  readonly config: Required<Omit<DebuggerConfig, "host" | "port" | "timeoutMs">> & {
    host: string;
    port: number;
    timeoutMs: number;
  };

  constructor(cfg: DebuggerConfig) {
    if (!cfg.project || !cfg.module) {
      throw new Error("Debugger 需要 project / module");
    }
    this.config = {
      project: cfg.project,
      module: cfg.module,
      host: cfg.host ?? readEnv("DEBUG_ASSISTANT_HOST") ?? "127.0.0.1",
      port: cfg.port ?? Number(readEnv("DEBUG_ASSISTANT_PORT") ?? 8765),
      enabled:
        cfg.enabled ?? (readEnv("DEBUG_ASSISTANT_ENABLED") ?? "true")
          .toString()
          .toLowerCase() !== "false",
      timeoutMs: cfg.timeoutMs ?? 2000,
    };
  }

  private get baseUrl(): string {
    return `http://${this.config.host}:${this.config.port}`;
  }

  private async _post<T = unknown>(path: string, body: unknown): Promise<T | null> {
    if (!this.config.enabled) return null;
    const ac = new AbortController();
    const tm = setTimeout(() => ac.abort(), this.config.timeoutMs);
    try {
      const resp = await fetch(this.baseUrl + path, {
        method: "POST",
        headers: { "Content-Type": "application/json; charset=utf-8" },
        body: JSON.stringify(body),
        signal: ac.signal,
      });
      if (!resp.ok) {
        warn(`POST ${path} HTTP ${resp.status}（已降级）`);
        return null;
      }
      return (await resp.json()) as T;
    } catch (e) {
      warn(`POST ${path} 失败（已降级）`, e);
      return null;
    } finally {
      clearTimeout(tm);
    }
  }

  private async _get<T = unknown>(path: string): Promise<T | null> {
    if (!this.config.enabled) return null;
    const ac = new AbortController();
    const tm = setTimeout(() => ac.abort(), this.config.timeoutMs);
    try {
      const resp = await fetch(this.baseUrl + path, { signal: ac.signal });
      if (!resp.ok) return null;
      return (await resp.json()) as T;
    } catch (e) {
      warn(`GET ${path} 失败（已降级）`, e);
      return null;
    } finally {
      clearTimeout(tm);
    }
  }

  health(): Promise<unknown | null> {
    return this._get("/api/health");
  }

  async report(payload: ReportPayload): Promise<string | null> {
    const { error } = payload;
    let error_type = payload.error_type;
    let error_message = payload.error_message;
    let stack_trace = payload.stack_trace;

    if (error instanceof Error) {
      error_type = error_type ?? error.name ?? "Error";
      error_message = error_message ?? error.message ?? String(error);
      stack_trace = stack_trace ?? error.stack ?? undefined;
    } else if (error !== undefined && error !== null) {
      error_message = error_message ?? String(error);
    }

    error_type = error_type ?? "UnknownError";
    error_message = error_message ?? "";

    const env: Record<string, string> = {
      SDK: "debug-assistant-ts/0.1.0",
      Runtime: typeof window !== "undefined" ? "browser" : "node",
      ...(payload.env ?? {}),
    };

    const body: Record<string, unknown> = {
      project: this.config.project,
      module: this.config.module,
      error_type,
      error_message,
      severity: payload.severity ?? "error",
      user_action: payload.user_action,
      stage: payload.stage,
      session_id: payload.session_id,
      project_display_name: payload.project_display_name,
      dialog_round: payload.dialog_round,
      extra_context_table: Object.fromEntries(
        Object.entries(payload.context ?? {}).map(([k, v]) => [k, String(v)]),
      ),
      operation_path: payload.operation_path,
      input_data: payload.input_data ?? {},
      logs: payload.logs ?? [],
      stack_trace,
      env,
    };
    // 过滤 undefined
    for (const k of Object.keys(body)) {
      if (body[k] === undefined) delete body[k];
    }

    const resp = await this._post<ReportCreated>("/api/report", body);
    return resp?.error_id ?? null;
  }

  async resolve(payload: ResolvePayload): Promise<boolean> {
    const resp = await this._post<{ status?: string }>("/api/resolve", payload);
    return resp?.status === "resolved";
  }

  /**
   * 安装到 window.onerror / unhandledrejection 上的便捷方法（仅浏览器/Tauri 环境）。
   */
  installGlobalHandlers(): void {
    if (typeof window === "undefined") return;
    window.addEventListener("error", (event) => {
      const err = (event as ErrorEvent).error ?? new Error((event as ErrorEvent).message);
      void this.report({ error: err });
    });
    window.addEventListener("unhandledrejection", (event) => {
      const reason = (event as PromiseRejectionEvent).reason;
      const err = reason instanceof Error ? reason : new Error(String(reason));
      void this.report({ error: err, error_type: "UnhandledRejection" });
    });
  }
}
