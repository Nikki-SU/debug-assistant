"""服务配置加载。

来源优先级：环境变量 > 默认值
对应 SPEC：项目一 §七. 环境变量配置
"""
from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    enabled: bool = True
    host: str = "127.0.0.1"
    port: int = 8765
    log_level: str = "INFO"
    # 数据根目录：用户首次启动时指定；这里给个默认占位
    data_root: Path = Path(os.path.expanduser("~/.debug-assistant"))


def load_settings() -> Settings:
    return Settings(
        enabled=os.getenv("DEBUG_ASSISTANT_ENABLED", "true").lower() == "true",
        host=os.getenv("DEBUG_ASSISTANT_HOST", "127.0.0.1"),
        port=int(os.getenv("DEBUG_ASSISTANT_PORT", "8765")),
        log_level=os.getenv("DEBUG_ASSISTANT_LOG_LEVEL", "INFO"),
        data_root=Path(os.getenv("DEBUG_ASSISTANT_DATA_ROOT", os.path.expanduser("~/.debug-assistant"))),
    )


SETTINGS = load_settings()
