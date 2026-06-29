import { useState } from "react";

/**
 * Debug Assistant GUI 主界面骨架。
 * 对应 SPEC：项目一 §四.3 GUI 手动填写 / §五.1 回传对话框
 */
export default function App() {
  const [activeTab, setActiveTab] = useState<"reports" | "new" | "settings">("reports");

  return (
    <div className="app">
      <aside className="sidebar">
        <h1>🐛 Debug Assistant</h1>
        <nav>
          <button onClick={() => setActiveTab("reports")} className={activeTab === "reports" ? "active" : ""}>📋 报告列表</button>
          <button onClick={() => setActiveTab("new")} className={activeTab === "new" ? "active" : ""}>➕ 新建报告</button>
          <button onClick={() => setActiveTab("settings")} className={activeTab === "settings" ? "active" : ""}>⚙️ 设置</button>
        </nav>
      </aside>
      <main className="main">
        {activeTab === "reports" && <div>TODO: 报告列表（按项目 + 状态分组）</div>}
        {activeTab === "new" && <div>TODO: 手动新建报告表单</div>}
        {activeTab === "settings" && <div>TODO: 数据根目录、端口、API 配置</div>}
      </main>
    </div>
  );
}
