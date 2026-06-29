import { useEffect, useState } from "react";
import { api } from "./api/client";
import { ReportList } from "./components/ReportList";
import { ReportDetail } from "./components/ReportDetail";
import { NewReportDialog } from "./components/NewReportDialog";
import { Sidebar } from "./components/Sidebar";
import { SettingsPage } from "./components/SettingsPage";
import { ProjectsPage } from "./components/ProjectsPage";

type Tab = "reports" | "projects" | "settings";

const HINT_DISMISS_KEY = "debug-assistant.hint.dismissed.v1";

export default function App() {
  const [tab, setTab] = useState<Tab>("reports");
  const [selected, setSelected] = useState<string | undefined>();
  const [selectedProject, setSelectedProject] = useState<string | undefined>();
  const [tick, setTick] = useState(0);
  const [newOpen, setNewOpen] = useState(false);
  const [health, setHealth] = useState<{ ok: boolean; data_root?: string } | null>(null);
  const [healthErr, setHealthErr] = useState<string>("");
  const [registryCount, setRegistryCount] = useState(0);
  const [showHint, setShowHint] = useState(true);

  useEffect(() => {
    setShowHint(localStorage.getItem(HINT_DISMISS_KEY) !== "1");
  }, []);

  useEffect(() => {
    void api
      .health()
      .then((h) => setHealth({ ok: h.ok, data_root: h.data_root }))
      .catch((e) => setHealthErr(String(e.message ?? e)));
    void api
      .registryList()
      .then((r) => setRegistryCount(r.total))
      .catch(() => setRegistryCount(0));
  }, [tick]);

  const dismissHint = () => {
    localStorage.setItem(HINT_DISMISS_KEY, "1");
    setShowHint(false);
  };

  return (
    <div className="app">
      <header>
        <div className="title">🔧 Debug Assistant</div>
        <nav className="tabs">
          <button
            className={tab === "reports" ? "tab active" : "tab"}
            onClick={() => setTab("reports")}
          >
            📋 报告
          </button>
          <button
            className={tab === "projects" ? "tab active" : "tab"}
            onClick={() => setTab("projects")}
          >
            📁 项目注册
            {registryCount > 0 && <span className="tab-badge">{registryCount}</span>}
          </button>
          <button
            className={tab === "settings" ? "tab active" : "tab"}
            onClick={() => setTab("settings")}
          >
            ⚙️ 设置
          </button>
        </nav>
        <div className="health">
          {health ? (
            <span className="ok">● 已连接 · {health.data_root}</span>
          ) : (
            <span className="bad">○ 未连接 server: {healthErr || "(loading...)"}</span>
          )}
        </div>
        <div className="spacer" />
        {tab === "reports" && (
          <>
            <button className="primary" onClick={() => setNewOpen(true)}>＋ 新建报告</button>
            <button onClick={() => setTick((t) => t + 1)}>🔄 刷新</button>
          </>
        )}
      </header>

      {showHint && tab === "reports" && registryCount === 0 && (
        <div className="header-hint">
          💡 想让 stack trace 行号可点击复制？去
          <a onClick={() => setTab("projects")}> 📁 项目注册 </a>
          绑定本地路径；默认行为是<b>复制 "path:line"</b>到剪贴板，可在
          <a onClick={() => setTab("settings")}> ⚙️ 设置 </a>切换。
          <span className="spacer" />
          <button className="link" onClick={dismissHint}>知道了 ✕</button>
        </div>
      )}

      {tab === "reports" && (
        <div className="body">
          <aside className="sidebar tree-pane">
            <Sidebar
              selectedProject={selectedProject}
              onSelectProject={(p) => {
                setSelectedProject(p);
                setSelected(undefined);
              }}
              refreshTick={tick}
            />
          </aside>
          <aside className="sidebar list-pane">
            <ReportList
              selected={selected}
              onSelect={setSelected}
              refreshTick={tick}
              filterProject={selectedProject}
            />
          </aside>
          <main className="main">
            <ReportDetail
              errorId={selected}
              onResolved={() => setTick((t) => t + 1)}
            />
          </main>
        </div>
      )}

      {tab === "projects" && (
        <div className="body single-pane">
          <main className="main"><ProjectsPage /></main>
        </div>
      )}

      {tab === "settings" && (
        <div className="body single-pane">
          <main className="main"><SettingsPage /></main>
        </div>
      )}

      {newOpen && (
        <NewReportDialog
          onClose={() => setNewOpen(false)}
          defaultProject={selectedProject}
          onCreated={(eid) => {
            setNewOpen(false);
            setSelected(eid);
            setTick((t) => t + 1);
          }}
        />
      )}
    </div>
  );
}
