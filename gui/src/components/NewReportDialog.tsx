import React, { useEffect, useState } from "react";
import { api } from "../api/client";

interface Props {
  onClose: () => void;
  onCreated: (errorId: string) => void;
  /** 当前从侧边栏选中的 project，作为默认值 */
  defaultProject?: string;
}

export function NewReportDialog({ onClose, onCreated, defaultProject }: Props) {
  const [form, setForm] = useState({
    project: defaultProject || "",
    module: "",
    error_type: "",
    error_message: "",
    severity: "error",
    stage: "",
    user_action: "",
    stack_trace: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [projectCandidates, setProjectCandidates] = useState<string[]>([]);
  const [moduleCandidates, setModuleCandidates] = useState<string[]>([]);
  // project → modules 映射，用于动态联动 module 候选
  const [projModMap, setProjModMap] = useState<Record<string, string[]>>({});

  useEffect(() => {
    void (async () => {
      try {
        const [p, r] = await Promise.all([api.projects(), api.registryList()]);
        const map: Record<string, string[]> = {};
        for (const [proj, mods] of Object.entries(p.projects)) {
          map[proj] = Object.keys(mods);
        }
        // 把 registry 里的项目名补齐
        for (const it of r.items) {
          if (!map[it.name]) map[it.name] = [];
        }
        setProjModMap(map);
        setProjectCandidates(Object.keys(map).sort((a, b) => a.localeCompare(b)));
      } catch {
        // 静默：候选拉不到只是少了联想，不影响裸 input
      }
    })();
  }, []);

  useEffect(() => {
    const mods = projModMap[form.project] || [];
    setModuleCandidates(mods);
  }, [form.project, projModMap]);

  const update =
    (k: keyof typeof form) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
      setForm({ ...form, [k]: e.target.value });
    };

  const onSubmit = async () => {
    if (!form.project || !form.module || !form.error_type || !form.error_message) {
      setError("project / module / error_type / error_message 必填");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      const r = await api.createReport(form);
      onCreated(r.error_id);
    } catch (e) {
      setError(String((e as Error).message ?? e));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>＋ 新建错误报告</h3>

        <div className="grid-2">
          <div>
            <label>项目 *</label>
            <input
              value={form.project}
              onChange={update("project")}
              placeholder="PaperAssistant"
              list="proj-candidates"
            />
            <datalist id="proj-candidates">
              {projectCandidates.map((p) => (
                <option key={p} value={p} />
              ))}
            </datalist>
            {projectCandidates.length > 0 && (
              <div className="muted xsmall">已有 {projectCandidates.length} 个项目可选，输入即联想</div>
            )}
          </div>
          <div>
            <label>模块 *</label>
            <input
              value={form.module}
              onChange={update("module")}
              placeholder="backend"
              list="mod-candidates"
            />
            <datalist id="mod-candidates">
              {moduleCandidates.map((m) => (
                <option key={m} value={m} />
              ))}
            </datalist>
          </div>
          <div>
            <label>错误类型 *</label>
            <input value={form.error_type} onChange={update("error_type")} placeholder="TimeoutError" />
          </div>
          <div>
            <label>严重程度</label>
            <select value={form.severity} onChange={update("severity")}>
              <option value="info">ℹ️ info</option>
              <option value="warning">⚠️ warning</option>
              <option value="error">🔴 error</option>
              <option value="critical">💥 critical</option>
            </select>
          </div>
          <div>
            <label>当前阶段</label>
            <input value={form.stage} onChange={update("stage")} placeholder="文献综述" />
          </div>
          <div>
            <label>用户操作</label>
            <input value={form.user_action} onChange={update("user_action")} placeholder="上传 PDF" />
          </div>
        </div>

        <label>错误信息 *</label>
        <input value={form.error_message} onChange={update("error_message")} placeholder="一行摘要" />

        <label>错误栈</label>
        <textarea rows={6} value={form.stack_trace} onChange={update("stack_trace")} placeholder="Traceback ..." />

        {error && <div className="error-banner">⚠️ {error}</div>}

        <div className="modal-actions">
          <div className="spacer" />
          <button onClick={onClose}>取消</button>
          <button className="primary" onClick={() => void onSubmit()} disabled={submitting}>
            {submitting ? "提交中…" : "创建"}
          </button>
        </div>
      </div>
    </div>
  );
}
