import { useState } from "react";
import { api } from "../api/client";

interface Props {
  errorId: string;
  onClose: () => void;
  onResolved: () => void;
}

export function ResolveDialog({ errorId, onClose, onResolved }: Props) {
  const [solution, setSolution] = useState("");
  const [changes, setChanges] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const onPaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      setSolution((prev) => (prev ? prev + "\n" + text : text));
    } catch (e) {
      setError("剪贴板读取失败：" + String((e as Error).message ?? e));
    }
  };

  const onSubmit = async () => {
    if (!solution.trim()) {
      setError("解决方案不能为空");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      await api.resolve({
        error_id: errorId,
        solution,
        related_changes: changes || undefined,
      });
      onResolved();
    } catch (e) {
      setError(String((e as Error).message ?? e));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>✅ 问题已解决</h3>
        <div className="modal-eid">错误ID：{errorId}</div>

        <label>解决方案（支持 Markdown）</label>
        <textarea
          rows={8}
          value={solution}
          onChange={(e) => setSolution(e.target.value)}
          placeholder="粘贴 AI 给出的解决方案，或自己描述"
        />

        <label>相关修改（可选）</label>
        <textarea
          rows={4}
          value={changes}
          onChange={(e) => setChanges(e.target.value)}
          placeholder="- 改了 xxx 文件\n- 调整了 yyy 参数"
        />

        {error && <div className="error-banner">⚠️ {error}</div>}

        <div className="modal-actions">
          <button onClick={() => void onPaste()}>📋 一键粘贴</button>
          <div className="spacer" />
          <button onClick={onClose}>取消</button>
          <button className="primary" onClick={() => void onSubmit()} disabled={submitting}>
            {submitting ? "提交中…" : "确认"}
          </button>
        </div>
      </div>
    </div>
  );
}
