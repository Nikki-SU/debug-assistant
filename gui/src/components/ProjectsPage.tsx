import { useEffect, useState } from "react";
import { api, OpenWith, RegistryItem } from "../api/client";

const OPEN_WITH_DISPLAY: Record<string, string> = {
  "": "↪ 跟随全局",
  none: "🚫 不跳转",
  copy_path: "📋 复制路径",
  explorer: "📂 资源管理器",
  vscode: "🆚 VSCode",
  custom: "🛠 自定义",
};

interface EditForm {
  name: string;
  local_path: string;
  open_with: "" | OpenWith;
  custom_cmd: string;
  isNew: boolean;
}

const EMPTY_FORM: EditForm = {
  name: "",
  local_path: "",
  open_with: "",
  custom_cmd: "",
  isNew: true,
};

export function ProjectsPage() {
  const [items, setItems] = useState<RegistryItem[]>([]);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState<EditForm | null>(null);
  const [busy, setBusy] = useState(false);

  const load = async () => {
    try {
      const r = await api.registryList();
      setItems(r.items);
      setError("");
    } catch (e) {
      setError(String((e as Error).message ?? e));
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const onSave = async () => {
    if (!editing) return;
    if (!editing.name.trim()) {
      setError("项目名不能为空");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await api.registryUpsert({
        name: editing.name.trim(),
        local_path: editing.local_path.trim(),
        open_with: editing.open_with,
        custom_cmd: editing.custom_cmd,
      });
      setEditing(null);
      await load();
    } catch (e) {
      setError(String((e as Error).message ?? e));
    } finally {
      setBusy(false);
    }
  };

  const onDelete = async (name: string) => {
    if (!confirm(`确认删除项目注册 "${name}"？\n（仅删除路径绑定，不影响已有报告）`)) return;
    setBusy(true);
    try {
      await api.registryDelete(name);
      await load();
    } catch (e) {
      setError(String((e as Error).message ?? e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="projects-page">
      <div className="page-header">
        <h2>📁 项目注册表</h2>
        <div className="spacer" />
        <button
          className="primary"
          onClick={() => setEditing({ ...EMPTY_FORM })}
        >
          ＋ 新建注册
        </button>
      </div>

      <p className="muted small">
        给项目名绑定<b>本地仓库路径</b>，stack trace 里的相对路径就能自动拼成可点击的绝对路径。
        没注册的项目不影响报告写入，只是 stack 行的"跳转"功能失效。
      </p>

      {error && <div className="error-banner">⚠️ {error}</div>}

      <table className="registry-table">
        <thead>
          <tr>
            <th>项目名</th>
            <th>本地路径</th>
            <th>打开方式</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          {items.map((it) => (
            <tr key={it.name}>
              <td><b>{it.name}</b></td>
              <td className="mono small">{it.local_path || <span className="muted">（未填）</span>}</td>
              <td>{OPEN_WITH_DISPLAY[it.open_with] ?? it.open_with}</td>
              <td className="muted small">{it.created_at}</td>
              <td>
                <button
                  onClick={() =>
                    setEditing({
                      name: it.name,
                      local_path: it.local_path,
                      open_with: (it.open_with || "") as "" | OpenWith,
                      custom_cmd: it.custom_cmd,
                      isNew: false,
                    })
                  }
                >
                  ✎ 编辑
                </button>
                <button
                  onClick={() => void onDelete(it.name)}
                  disabled={busy}
                  style={{ marginLeft: 6 }}
                >
                  🗑 删除
                </button>
              </td>
            </tr>
          ))}
          {items.length === 0 && (
            <tr>
              <td colSpan={5} className="muted" style={{ textAlign: "center", padding: 24 }}>
                （暂无项目注册，点右上角"＋ 新建注册"开始）
              </td>
            </tr>
          )}
        </tbody>
      </table>

      {editing && (
        <div className="modal-overlay" onClick={() => setEditing(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>{editing.isNew ? "＋ 新建项目注册" : "✎ 编辑项目注册"}</h3>

            <label>项目名 *</label>
            <input
              value={editing.name}
              disabled={!editing.isNew}
              onChange={(e) => setEditing({ ...editing, name: e.target.value })}
              placeholder="PaperAssistant"
            />
            {!editing.isNew && (
              <div className="muted small">项目名是主键，建好后不可改；如需改名请先删除再新建。</div>
            )}

            <label>本地仓库根目录</label>
            <input
              value={editing.local_path}
              onChange={(e) => setEditing({ ...editing, local_path: e.target.value })}
              placeholder="G:\\PaperAssistant"
            />
            <div className="muted small">
              stack trace 里的相对路径会基于这里拼接成绝对路径。Windows 反斜杠或正斜杠都行。
            </div>

            <label>打开方式</label>
            <select
              value={editing.open_with}
              onChange={(e) =>
                setEditing({ ...editing, open_with: e.target.value as "" | OpenWith })
              }
            >
              <option value="">↪ 跟随全局默认</option>
              <option value="copy_path">📋 复制路径</option>
              <option value="none">🚫 不跳转</option>
              <option value="explorer">📂 资源管理器（预留）</option>
              <option value="vscode">🆚 VSCode</option>
              <option value="custom">🛠 自定义命令</option>
            </select>

            {editing.open_with === "custom" && (
              <>
                <label>自定义命令</label>
                <input
                  value={editing.custom_cmd}
                  onChange={(e) => setEditing({ ...editing, custom_cmd: e.target.value })}
                  placeholder={'例：trae --goto "{path}:{line}"'}
                />
                <div className="muted small">支持占位符 {"{path}"} / {"{line}"}</div>
              </>
            )}

            <div className="modal-actions">
              <div className="spacer" />
              <button onClick={() => setEditing(null)}>取消</button>
              <button className="primary" onClick={() => void onSave()} disabled={busy}>
                {busy ? "保存中…" : "保存"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
