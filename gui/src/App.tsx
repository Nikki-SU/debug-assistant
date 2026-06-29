import { useEffect, useState } from "react";
import { api } from "./api/client";
import { ReportList } from "./components/ReportList";
import { ReportDetail } from "./components/ReportDetail";
import { NewReportDialog } from "./components/NewReportDialog";

export default function App() {
  const [selected, setSelected] = useState<string | undefined>();
  const [tick, setTick] = useState(0);
  const [newOpen, setNewOpen] = useState(false);
  const [health, setHealth] = useState<{ ok: boolean; data_root?: string } | null>(null);
  const [healthErr, setHealthErr] = useState<string>("");

  useEffect(() => {
    void api
      .health()
      .then((h) => setHealth({ ok: h.ok, data_root: h.data_root }))
      .catch((e) => setHealthErr(String(e.message ?? e)));
  }, [tick]);

  return (
    <div className="app">
      <header>
        <div className="title">🔧 Debug Assistant</div>
        <div className="health">
          {health ? (
            <span className="ok">● 已连接 · {health.data_root}</span>
          ) : (
            <span className="bad">○ 未连接 server: {healthErr || "(loading...)"}</span>
          )}
        </div>
        <div className="spacer" />
        <button className="primary" onClick={() => setNewOpen(true)}>＋ 新建报告</button>
        <button onClick={() => setTick((t) => t + 1)}>🔄 刷新</button>
      </header>

      <div className="body">
        <aside className="sidebar">
          <ReportList selected={selected} onSelect={setSelected} refreshTick={tick} />
        </aside>
        <main className="main">
          <ReportDetail
            errorId={selected}
            onResolved={() => setTick((t) => t + 1)}
          />
        </main>
      </div>

      {newOpen && (
        <NewReportDialog
          onClose={() => setNewOpen(false)}
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
