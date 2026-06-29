import { useEffect, useState } from "react";
import { api, OpenWith, SettingsView } from "../api/client";

const OPEN_WITH_OPTIONS: { value: OpenWith; label: string; hint: string }[] = [
  { value: "copy_path", label: "📋 复制路径", hint: "复制 {file}:{line} 到剪贴板（默认）" },
  { value: "none", label: "🚫 不跳转", hint: "stack 行不可点击，仅查看" },
  { value: "explorer", label: "📂 资源管理器", hint: "Windows 资源管理器定位文件（需 server 支持，预留）" },
  { value: "vscode", label: "🆚 VSCode", hint: "调用 vscode://file/{path}:{line} 协议（需装 VSCode）" },
  {
    value: "custom",
    label: "🛠 自定义命令",
    hint: "命令模板，支持 {path} 和 {line} 占位符（Trae/IDEA 等 IDE 用）",
  },
];

export function SettingsPage() {
  const [data, setData] = useState<SettingsView | null>(null);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [savedFlash, setSavedFlash] = useState(false);

  const load = async () => {
    try {
      const s = await api.settingsGet();
      setData(s);
      setError("");
    } catch (e) {
      setError(String((e as Error).message ?? e));
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const save = async () => {
    if (!data) return;
    setSaving(true);
    setError("");
    try {
      const s = await api.settingsPut({
        default_open_with: data.default_open_with,
        default_custom_cmd: data.default_custom_cmd,
      });
      setData(s);
      setSavedFlash(true);
      setTimeout(() => setSavedFlash(false), 1500);
    } catch (e) {
      setError(String((e as Error).message ?? e));
    } finally {
      setSaving(false);
    }
  };

  if (!data) return <div className="detail-empty">{error ? <span className="error-banner">⚠️ {error}</span> : "加载中…"}</div>;

  const active = OPEN_WITH_OPTIONS.find((o) => o.value === data.default_open_with);

  return (
    <div className="settings-page">
      <h2>⚙️ 全局默认设置</h2>
      <p className="muted">
        当 stack trace 行被点击时，未为单个项目单独设置的，统一走这里的"全局默认"。
      </p>

      <label className="block-label">默认打开方式</label>
      <div className="open-with-grid">
        {OPEN_WITH_OPTIONS.map((opt) => (
          <div
            key={opt.value}
            className={`open-with-card ${data.default_open_with === opt.value ? "active" : ""}`}
            onClick={() => setData({ ...data, default_open_with: opt.value })}
          >
            <div className="ow-label">{opt.label}</div>
            <div className="ow-hint">{opt.hint}</div>
          </div>
        ))}
      </div>

      {data.default_open_with === "custom" && (
        <>
          <label className="block-label">自定义命令模板</label>
          <input
            value={data.default_custom_cmd}
            onChange={(e) => setData({ ...data, default_custom_cmd: e.target.value })}
            placeholder={'例：trae --goto "{path}:{line}"'}
          />
          <div className="muted small">
            支持占位符：<code>{"{path}"}</code> 文件绝对路径、<code>{"{line}"}</code> 行号。
            <br />
            注：custom 模式当前仅在 GUI 端将渲染后的命令复制到剪贴板，由你手动粘贴到终端执行；
            后续会接入 server 端真正调用。
          </div>
        </>
      )}

      {error && <div className="error-banner">⚠️ {error}</div>}

      <div className="modal-actions">
        <div className="spacer" />
        {savedFlash && <span className="ok">✅ 已保存</span>}
        <button className="primary" onClick={() => void save()} disabled={saving}>
          {saving ? "保存中…" : "保存"}
        </button>
      </div>

      <hr />

      <h3>📖 当前生效</h3>
      <ul className="muted small">
        <li>default_open_with = <b>{data.default_open_with}</b>（{active?.label}）</li>
        <li>default_custom_cmd = <code>{data.default_custom_cmd || "(空)"}</code></li>
      </ul>
    </div>
  );
}
