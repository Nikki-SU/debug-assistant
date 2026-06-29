import { useEffect, useState } from "react";
import { api, ReportDetail as Detail } from "../api/client";
import { ResolveDialog } from "./ResolveDialog";

interface Props {
  errorId?: string;
  onResolved: () => void;
}

export function ReportDetail({ errorId, onResolved }: Props) {
  const [detail, setDetail] = useState<Detail | null>(null);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const [resolveOpen, setResolveOpen] = useState(false);

  useEffect(() => {
    if (!errorId) {
      setDetail(null);
      return;
    }
    setError("");
    void api
      .detail(errorId)
      .then(setDetail)
      .catch((e) => setError(String(e.message ?? e)));
  }, [errorId]);

  if (!errorId) {
    return <div className="detail-empty">← 从左侧选择一条报告</div>;
  }
  if (error) return <div className="detail-empty error-banner">⚠️ {error}</div>;
  if (!detail) return <div className="detail-empty">加载中…</div>;

  const onCopy = async () => {
    try {
      await navigator.clipboard.writeText(detail.markdown);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // 在 Tauri WebView 中 clipboard 可能受限，回退到选区复制
      const ta = document.createElement("textarea");
      ta.value = detail.markdown;
      document.body.appendChild(ta);
      ta.select();
      try {
        document.execCommand("copy");
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      } finally {
        ta.remove();
      }
    }
  };

  return (
    <div className="report-detail">
      <div className="detail-toolbar">
        <span className="detail-eid">{detail.error_id}</span>
        <span className={`badge ${detail.meta.status}`}>
          {detail.meta.status === "resolved" ? "🟢 已解决" : "🔴 待解决"}
        </span>
        <div className="spacer" />
        <button onClick={() => void onCopy()}>
          {copied ? "✅ 已复制" : "📋 一键复制"}
        </button>
        {detail.meta.status !== "resolved" && (
          <button className="primary" onClick={() => setResolveOpen(true)}>
            ✅ 问题已解决
          </button>
        )}
      </div>

      <pre className="markdown-pane">{detail.markdown}</pre>

      <div className="path-bar">📁 {detail.path}</div>

      {resolveOpen && (
        <ResolveDialog
          errorId={detail.error_id}
          onClose={() => setResolveOpen(false)}
          onResolved={() => {
            setResolveOpen(false);
            void api.detail(detail.error_id).then(setDetail);
            onResolved();
          }}
        />
      )}
    </div>
  );
}
