import { useEffect, useState } from "react";
import { api, ReportSummary } from "../api/client";

interface Props {
  selected?: string;
  onSelect: (errorId: string) => void;
  refreshTick: number;
}

export function ReportList({ selected, onSelect, refreshTick }: Props) {
  const [keyword, setKeyword] = useState("");
  const [status, setStatus] = useState<"" | "open" | "resolved">("");
  const [hits, setHits] = useState<ReportSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const r = await api.search({
        keyword: keyword || undefined,
        status: status || undefined,
        limit: 100,
      });
      setHits(r.hits);
      setTotal(r.total);
    } catch (e) {
      setError(String((e as Error).message ?? e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshTick, status]);

  return (
    <div className="report-list">
      <div className="filters">
        <input
          placeholder="搜索 error_id / type / message"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") void load();
          }}
        />
        <select value={status} onChange={(e) => setStatus(e.target.value as "" | "open" | "resolved")}>
          <option value="">全部状态</option>
          <option value="open">🔴 待解决</option>
          <option value="resolved">🟢 已解决</option>
        </select>
        <button onClick={() => void load()} disabled={loading}>
          {loading ? "搜索中…" : "搜索"}
        </button>
      </div>

      {error && <div className="error-banner">⚠️ {error}</div>}

      <div className="list-stats">共 {total} 条</div>

      <ul className="hit-list">
        {hits.map((h) => (
          <li
            key={h.error_id}
            className={selected === h.error_id ? "active" : ""}
            onClick={() => onSelect(h.error_id)}
          >
            <div className="hit-line-1">
              <span className={`badge ${h.status}`}>
                {h.status === "resolved" ? "🟢" : "🔴"}
              </span>
              <span className="hit-type">{h.error_type}</span>
              <span className="hit-time">{h.created_at}</span>
            </div>
            <div className="hit-line-2">
              <span className="hit-proj">{h.project} / {h.module}</span>
            </div>
            <div className="hit-msg">{h.error_message}</div>
          </li>
        ))}
        {!loading && hits.length === 0 && <li className="empty">（无匹配结果）</li>}
      </ul>
    </div>
  );
}
