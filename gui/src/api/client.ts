/** GUI 调用本地 server 的 API 客户端。 */

const BASE = "http://127.0.0.1:8765";

export interface ReportSummary {
  error_id: string;
  project: string;
  module: string;
  date: string;
  created_at: string;
  resolved_at: string;
  status: "open" | "resolved" | string;
  severity: string;
  error_type: string;
  error_message: string;
  relpath: string;
}

export interface SearchResp {
  total: number;
  hits: ReportSummary[];
}

export interface ReportDetail {
  error_id: string;
  meta: ReportSummary;
  markdown: string;
  path: string;
}

async function jsonFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(url, init);
  if (!resp.ok) {
    const detail = await resp.text().catch(() => "");
    throw new Error(`HTTP ${resp.status}: ${detail || resp.statusText}`);
  }
  return resp.json() as Promise<T>;
}

export const api = {
  health: () => jsonFetch<{ ok: boolean; data_root: string; port: number }>(`${BASE}/api/health`),

  search: (params: {
    keyword?: string;
    project?: string;
    module?: string;
    status?: string;
    limit?: number;
  }): Promise<SearchResp> => {
    const qs = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== "") qs.set(k, String(v));
    }
    return jsonFetch<SearchResp>(`${BASE}/api/search?${qs.toString()}`);
  },

  detail: (errorId: string) =>
    jsonFetch<ReportDetail>(`${BASE}/api/report/${encodeURIComponent(errorId)}`),

  projects: () =>
    jsonFetch<{ projects: Record<string, Record<string, number>> }>(`${BASE}/api/projects`),

  createReport: (body: Record<string, unknown>) =>
    jsonFetch<{ error_id: string; path: string }>(`${BASE}/api/report`, {
      method: "POST",
      headers: { "Content-Type": "application/json; charset=utf-8" },
      body: JSON.stringify(body),
    }),

  resolve: (body: { error_id: string; solution: string; related_changes?: string }) =>
    jsonFetch<{ error_id: string; status: string; resolved_at: string }>(`${BASE}/api/resolve`, {
      method: "POST",
      headers: { "Content-Type": "application/json; charset=utf-8" },
      body: JSON.stringify(body),
    }),
};
