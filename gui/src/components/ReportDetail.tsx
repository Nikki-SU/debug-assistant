import { useEffect, useMemo, useState } from "react";
import { api, ReportDetail as Detail, RegistryItem, SettingsView } from "../api/client";
import { ResolveDialog } from "./ResolveDialog";

interface Props {
  errorId?: string;
  onResolved: () => void;
}

/** stack trace 单行解析结果 */
interface StackHit {
  raw: string;       // 原始整行
  before: string;    // 行内"匹配位置"之前的部分
  matched: string;   // 匹配出的 "file:line" 子串（原文）
  after: string;     // 行内"匹配位置"之后的部分
  filePath: string;  // 提取到的路径（原始的，可能为相对路径）
  line: number;      // 行号
}

/** 全平台 stack 行号正则：
 *  1) Python:   File "G:\\xx\\a.py", line 42      ← 注意带引号
 *  2) JS/TS V8: at xxx (G:\\xx\\a.js:42:7)
 *  3) JS/TS V8: at G:\\xx\\a.js:42:7
 *  4) Rust:     at xx/main.rs:42
 *  覆盖 Windows 反斜杠 + Unix 正斜杠。
 */
const PATTERNS: RegExp[] = [
  /File\s+"([^"]+)",\s*line\s+(\d+)/i,                          // Python
  /\(([^():\s]+(?::[A-Za-z]:[\\/][^():]*|[^():]*)):(\d+)(?::\d+)?\)/, // (path:line:col)
  /([A-Za-z]:[\\/][^\s():"']+):(\d+)(?::\d+)?/,                 // Windows 绝对路径 path:line[:col]
  /([./\w-]+(?:[\\/][\w.\-+]+)+\.[A-Za-z]+):(\d+)(?::\d+)?/,    // 相对/Unix 路径 path:line[:col]
];

function parseStackLine(raw: string): StackHit | null {
  for (const re of PATTERNS) {
    const m = re.exec(raw);
    if (m) {
      const filePath = m[1];
      const line = parseInt(m[2], 10);
      if (!Number.isFinite(line)) continue;
      const matched = m[0];
      const idx = raw.indexOf(matched);
      return {
        raw,
        before: raw.slice(0, idx),
        matched,
        after: raw.slice(idx + matched.length),
        filePath,
        line,
      };
    }
  }
  return null;
}

/** 从 markdown 中抽取"## 错误栈"小节的纯文本块（不含 ```fence）。 */
function extractStackBlock(md: string): { stack: string; before: string; after: string } | null {
  // 兼容 "## 错误栈"、"## 7. 错误栈"、"## 错误堆栈" 等若干写法
  const re = /(^|\n)(#{1,6}\s*(?:\d+\.?\s*)?(?:错误栈|错误堆栈|Stack Trace|Stacktrace)[^\n]*\n)([\s\S]*?)(?=\n#{1,6}\s|$)/i;
  const m = re.exec(md);
  if (!m) return null;
  const headerStart = m.index + (m[1] ? m[1].length : 0);
  const headerLine = m[2];
  const body = m[3] || "";
  // 去掉首尾的 ``` 围栏
  const cleaned = body
    .replace(/^\s*```[^\n]*\n/, "")
    .replace(/\n```\s*$/, "");
  const sectionStart = headerStart;
  const sectionEnd = m.index + m[0].length;
  return {
    stack: cleaned,
    before: md.slice(0, sectionStart) + headerLine,
    after: md.slice(sectionEnd),
  };
}

/** 解析项目的"打开方式"（项目级 > 全局默认） */
function resolveOpenWith(
  reg: RegistryItem | undefined,
  settings: SettingsView | null
): { mode: string; customCmd: string } {
  const mode = (reg?.open_with || "").trim() || settings?.default_open_with || "copy_path";
  const customCmd =
    reg?.open_with === "custom"
      ? reg.custom_cmd || ""
      : settings?.default_custom_cmd || "";
  return { mode, customCmd };
}

/** 拼接绝对路径：若已绝对，原样返回；否则拼到 registry.local_path 下。 */
function resolveAbsPath(filePath: string, basePath: string | undefined): string {
  const isAbs = /^[A-Za-z]:[\\/]/.test(filePath) || filePath.startsWith("/");
  if (isAbs || !basePath) return filePath;
  const sep = basePath.includes("\\") || /^[A-Za-z]:/.test(basePath) ? "\\" : "/";
  const trimmedBase = basePath.replace(/[\\/]+$/, "");
  const trimmedFile = filePath.replace(/^[\\/]+/, "");
  return trimmedBase + sep + trimmedFile.replace(/[\\/]/g, sep);
}

async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    const ta = document.createElement("textarea");
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand("copy");
      return true;
    } finally {
      ta.remove();
    }
  }
}

export function ReportDetail({ errorId, onResolved }: Props) {
  const [detail, setDetail] = useState<Detail | null>(null);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const [lineFlash, setLineFlash] = useState<string>("");
  const [resolveOpen, setResolveOpen] = useState(false);
  const [registryMap, setRegistryMap] = useState<Record<string, RegistryItem>>({});
  const [settings, setSettings] = useState<SettingsView | null>(null);

  useEffect(() => {
    // 注册表 + 全局设置，详情页生命周期内拉一次即可（项目页改完会切 tab 重新挂载）
    void (async () => {
      try {
        const [r, s] = await Promise.all([api.registryList(), api.settingsGet()]);
        const map: Record<string, RegistryItem> = {};
        for (const it of r.items) map[it.name] = it;
        setRegistryMap(map);
        setSettings(s);
      } catch {
        // 全局设置拉取失败不影响详情查看，沉默降级到默认 copy_path
        setSettings({ default_open_with: "copy_path", default_custom_cmd: "" });
      }
    })();
  }, []);

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

  const stackSection = useMemo(
    () => (detail ? extractStackBlock(detail.markdown) : null),
    [detail]
  );

  if (!errorId) {
    return <div className="detail-empty">← 从左侧选择一条报告</div>;
  }
  if (error) return <div className="detail-empty error-banner">⚠️ {error}</div>;
  if (!detail) return <div className="detail-empty">加载中…</div>;

  const onCopyAll = async () => {
    const ok = await copyToClipboard(detail.markdown);
    if (ok) {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    }
  };

  const reg = registryMap[detail.meta.project];
  const { mode, customCmd } = resolveOpenWith(reg, settings);

  const onClickStackLine = async (hit: StackHit) => {
    if (mode === "none") return;
    const abs = resolveAbsPath(hit.filePath, reg?.local_path);

    let payload = `${abs}:${hit.line}`;
    if (mode === "vscode") {
      // VSCode URI 用正斜杠更稳
      payload = `vscode://file/${abs.replace(/\\/g, "/")}:${hit.line}`;
    } else if (mode === "custom") {
      payload = (customCmd || "{path}:{line}")
        .replace(/\{path\}/g, abs)
        .replace(/\{line\}/g, String(hit.line));
    } else if (mode === "explorer") {
      // 资源管理器需要 server 端真正调起进程，当前先复制命令
      payload = `explorer /select,"${abs}"`;
    }

    if (mode === "vscode") {
      // 直接尝试打开协议 URL，浏览器不允许跨域，但 Tauri WebView 通常会拦截到 OS
      try {
        window.open(payload, "_self");
      } catch {
        await copyToClipboard(payload);
      }
    } else {
      await copyToClipboard(payload);
    }
    setLineFlash(`${abs}:${hit.line}`);
    setTimeout(() => setLineFlash(""), 1500);
  };

  const renderStack = () => {
    if (!stackSection) return null;
    const lines = stackSection.stack.split("\n");
    return (
      <div className="stack-block">
        {lines.map((raw, i) => {
          const hit = parseStackLine(raw);
          if (!hit || mode === "none") {
            return (
              <div className="stack-line plain" key={i}>
                {raw || "\u00A0"}
              </div>
            );
          }
          return (
            <div className="stack-line clickable" key={i} onClick={() => void onClickStackLine(hit)}>
              <span>{hit.before}</span>
              <span className="stack-match" title={`点击：${mode}`}>{hit.matched}</span>
              <span>{hit.after}</span>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="report-detail">
      <div className="detail-toolbar">
        <span className="detail-eid">{detail.error_id}</span>
        <span className={`badge ${detail.meta.status}`}>
          {detail.meta.status === "resolved" ? "🟢 已解决" : "🔴 待解决"}
        </span>
        <span className="muted small">
          {reg
            ? `⚙️ 已注册 · ${reg.local_path || "(未填路径)"}`
            : "○ 项目未注册路径"}
          {" · "}
          点击行为：<b>{mode}</b>
        </span>
        <div className="spacer" />
        {lineFlash && <span className="ok small">✅ 已复制 {lineFlash}</span>}
        <button onClick={() => void onCopyAll()}>
          {copied ? "✅ 已复制" : "📋 一键复制"}
        </button>
        {detail.meta.status !== "resolved" && (
          <button className="primary" onClick={() => setResolveOpen(true)}>
            ✅ 问题已解决
          </button>
        )}
      </div>

      {stackSection ? (
        <div className="markdown-pane">
          <pre className="md-text">{stackSection.before}</pre>
          {renderStack()}
          <pre className="md-text">{stackSection.after}</pre>
        </div>
      ) : (
        <pre className="markdown-pane plain-md">{detail.markdown}</pre>
      )}

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
