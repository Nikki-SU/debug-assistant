"""配置加载（CSV 持久化 + 环境变量覆盖）。

配置文件位置：{data_root}/config/debugger_config.csv
首次启动时由 user 通过 GUI / CLI / 环境变量指定 data_root，
之后写入 ~/.debug_assistant_root 作为指针。

环境变量覆盖（运行期）：
    DEBUG_ASSISTANT_DATA_ROOT       数据根目录
    DEBUG_ASSISTANT_HOST            监听 host（默认 127.0.0.1）
    DEBUG_ASSISTANT_PORT            监听 port（默认 8765）
    DEBUG_ASSISTANT_LOG_LEVEL       日志级别（默认 INFO）

对应 SPEC §三.1 / §七
"""
from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

POINTER_FILE = Path.home() / ".debug_assistant_root"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
DEFAULT_OPEN_WITH = "copy_path"
VALID_OPEN_WITH = {"none", "copy_path", "explorer", "vscode", "custom"}


@dataclass
class Settings:
    data_root: Path
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    log_level: str = "INFO"
    # 全局默认：stack 行点击时的打开方式
    default_open_with: str = DEFAULT_OPEN_WITH
    default_custom_cmd: str = ""
    # 派生目录
    projects_dir: Path = field(init=False)
    config_dir: Path = field(init=False)
    index_csv: Path = field(init=False)
    config_csv: Path = field(init=False)
    registry_csv: Path = field(init=False)

    def __post_init__(self) -> None:
        self.data_root = Path(self.data_root).expanduser().resolve()
        self.projects_dir = self.data_root / "projects"
        self.config_dir = self.data_root / "config"
        self.index_csv = self.projects_dir / "index.csv"
        self.config_csv = self.config_dir / "debugger_config.csv"
        self.registry_csv = self.config_dir / "projects_registry.csv"

    def ensure_dirs(self) -> None:
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)


def _read_pointer() -> Optional[Path]:
    if POINTER_FILE.exists():
        line = POINTER_FILE.read_text(encoding="utf-8").strip()
        if line:
            return Path(line)
    return None


def _write_pointer(p: Path) -> None:
    POINTER_FILE.write_text(str(p), encoding="utf-8")


def _read_config_csv(csv_path: Path) -> dict[str, str]:
    if not csv_path.exists():
        return {}
    out: dict[str, str] = {}
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 2 and row[0] and not row[0].startswith("#"):
                out[row[0].strip()] = row[1].strip()
    return out


def _write_config_csv(csv_path: Path, data: dict[str, str]) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["key", "value"])
        for k, v in data.items():
            writer.writerow([k, v])


def _dump_settings(s: Settings) -> None:
    """把当前 Settings 完整写回 config.csv（保持可读性 + 向后兼容老配置）。"""
    _write_config_csv(
        s.config_csv,
        {
            "host": s.host,
            "port": str(s.port),
            "log_level": s.log_level,
            "default_open_with": s.default_open_with,
            "default_custom_cmd": s.default_custom_cmd,
        },
    )


def load_settings(data_root: Optional[str | os.PathLike] = None) -> Settings:
    """加载配置。优先级：函数参数 > 环境变量 > 指针文件 > 默认（用户主目录/DebugAssistant）。"""
    # 1) 解析 data_root
    chosen: Optional[Path] = None
    if data_root:
        chosen = Path(data_root)
    elif os.environ.get("DEBUG_ASSISTANT_DATA_ROOT"):
        chosen = Path(os.environ["DEBUG_ASSISTANT_DATA_ROOT"])
    else:
        chosen = _read_pointer()
    if chosen is None:
        chosen = Path.home() / "DebugAssistant"

    chosen = chosen.expanduser().resolve()
    _write_pointer(chosen)

    # 2) 加载各字段：环境变量 > config.csv > 默认
    cfg = _read_config_csv(chosen / "config" / "debugger_config.csv")
    host = os.environ.get("DEBUG_ASSISTANT_HOST") or cfg.get("host") or DEFAULT_HOST
    port = int(os.environ.get("DEBUG_ASSISTANT_PORT") or cfg.get("port") or DEFAULT_PORT)
    log_level = os.environ.get("DEBUG_ASSISTANT_LOG_LEVEL") or cfg.get("log_level") or "INFO"
    default_open_with = (cfg.get("default_open_with") or DEFAULT_OPEN_WITH).strip()
    if default_open_with not in VALID_OPEN_WITH:
        default_open_with = DEFAULT_OPEN_WITH
    default_custom_cmd = cfg.get("default_custom_cmd") or ""

    s = Settings(
        data_root=chosen,
        host=host,
        port=port,
        log_level=log_level,
        default_open_with=default_open_with,
        default_custom_cmd=default_custom_cmd,
    )
    s.ensure_dirs()
    # 写回 config.csv（自动迁移老配置：补全 default_open_with / default_custom_cmd 两个 key）
    _dump_settings(s)
    return s


# 全局单例（延迟加载）
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings


def set_data_root(path: str | os.PathLike) -> Settings:
    """切换数据根目录（GUI/CLI 首次启动用）。"""
    global _settings
    _settings = load_settings(path)
    return _settings


def update_global_settings(updates: dict[str, str]) -> Settings:
    """修改全局默认设置，原地更新当前进程的 Settings 单例并落库。

    目前支持的 key：default_open_with / default_custom_cmd。
    其他 key 静默忽略，避免误改 host / port 等启动期字段。
    """
    s = get_settings()
    if "default_open_with" in updates:
        v = (updates["default_open_with"] or "").strip()
        if v in VALID_OPEN_WITH:
            s.default_open_with = v
    if "default_custom_cmd" in updates:
        s.default_custom_cmd = updates["default_custom_cmd"] or ""
    _dump_settings(s)
    return s
