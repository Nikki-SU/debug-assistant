import { useEffect, useState } from "react";
import { api, RegistryItem } from "../api/client";

interface Props {
  /** 当前选中的 project（用于高亮 + 联动报告列表过滤），undefined = 全部 */
  selectedProject?: string;
  onSelectProject: (project: string | undefined) => void;
  refreshTick: number;
}

/**
 * 左侧"项目树"。
 *  - 数据合并：/api/projects 聚合 + /api/registry 注册（取并集，registry 标识 ⚙️）
 *  - 点击"全部"或某个 project 触发筛选
 */
export function Sidebar({ selectedProject, onSelectProject, refreshTick }: Props) {
  const [tree, setTree] = useState<Record<string, Record<string, number>>>({});
  const [registry, setRegistry] = useState<Record<string, RegistryItem>>({});
  const [error, setError] = useState("");

  useEffect(() => {
    void (async () => {
      try {
        const [p, r] = await Promise.all([api.projects(), api.registryList()]);
        setTree(p.projects || {});
        const rmap: Record<string, RegistryItem> = {};
        for (const it of r.items) rmap[it.name] = it;
        setRegistry(rmap);
        setError("");
      } catch (e) {
        setError(String((e as Error).message ?? e));
      }
    })();
  }, [refreshTick]);

  // 合并：所有 index 出现过的 + 所有 registry 出现过的 project 名
  const names = Array.from(
    new Set<string>([...Object.keys(tree), ...Object.keys(registry)])
  ).sort((a, b) => a.localeCompare(b));

  const totalAll = Object.values(tree).reduce(
    (sum, mods) => sum + Object.values(mods).reduce((a, b) => a + b, 0),
    0
  );

  return (
    <div className="proj-tree">
      <div className="proj-tree-title">📁 项目</div>
      {error && <div className="error-banner">⚠️ {error}</div>}
      <ul>
        <li
          className={!selectedProject ? "active" : ""}
          onClick={() => onSelectProject(undefined)}
        >
          <span className="proj-name">全部</span>
          <span className="proj-count">{totalAll}</span>
        </li>
        {names.map((name) => {
          const mods = tree[name] || {};
          const sum = Object.values(mods).reduce((a, b) => a + b, 0);
          const reg = registry[name];
          return (
            <li
              key={name}
              className={selectedProject === name ? "active" : ""}
              onClick={() => onSelectProject(name)}
              title={reg?.local_path || "未注册本地路径"}
            >
              <span className="proj-name">
                {reg ? "⚙️ " : ""}
                {name}
              </span>
              <span className="proj-count">{sum}</span>
            </li>
          );
        })}
        {names.length === 0 && <li className="empty">（暂无项目）</li>}
      </ul>
    </div>
  );
}
