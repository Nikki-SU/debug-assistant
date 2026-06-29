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

/** /api/registry 单行（project_registry.csv 一行） */
export interface RegistryItem {
  name: string;
  local_path: string;
  open_with: string;       // "" / none / copy_path / explorer / vscode / custom
  custom_cmd: string;
  created_at: string;
}

export interface RegistryListResp {
  total: number;
  items: RegistryItem[];
}

export type OpenWith = "none" | "copy_path" | "explorer" | "vscode" | "custom";

export interface SettingsView {
  default_open_with: OpenWith;
  default_custom_cmd: string;
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

  // ----- 项目注册表 -----
  registryList: () => jsonFetch<RegistryListResp>(`${BASE}/api/registry`),

  registryUpsert: (item: {
    name: string;
    local_path?: string;
    open_with?: string;
    custom_cmd?: string;
  }) =>
    jsonFetch<RegistryItem>(`${BASE}/api/registry`, {
      method: "POST",
      headers: { "Content-Type": "application/json; charset=utf-8" },
      body: JSON.stringify(item),
    }),

  registryDelete: (name: string) =>
    jsonFetch<{ ok: boolean; name: string }>(`${BASE}/api/registry/${encodeURIComponent(name)}`, {
      method: "DELETE",
    }),

  // ----- 全局设置 -----
  settingsGet: () => jsonFetch<SettingsView>(`${BASE}/api/settings`),

  settingsPut: (patch: Partial<SettingsView>) =>
    jsonFetch<SettingsView>(`${BASE}/api/settings`, {
      method: "PUT",
      headers: { "Content-Type": "application/json; charset=utf-8" },
      body: JSON.stringify(patch),
    }),
};
