"""全局配置: 一切环境相关取值从这里走,代码里禁止直接读 os.environ。

LLM_API_KEY / LLM_BASE_URL / LLM_MODEL: LLM 网关(OpenAI 兼容协议)
DATABASE_URL: SQLAlchemy 连接串(psycopg3 方言)
APP_PROFILE: dev 允许 penalty_crawler;prod 禁止(架构红线第 4 条)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_dotenv(path: Path) -> None:
    """极简 .env 加载(不引入 python-dotenv 依赖);已存在的环境变量优先。"""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(_REPO_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    llm_api_key: str
    llm_base_url: str
    llm_model: str
    database_url: str
    app_profile: str = "dev"

    @property
    def is_dev(self) -> bool:
        return self.app_profile == "dev"


def get_settings() -> Settings:
    return Settings(
        llm_api_key=os.environ.get("LLM_API_KEY", ""),
        llm_base_url=os.environ.get("LLM_BASE_URL", ""),
        llm_model=os.environ.get("LLM_MODEL", ""),
        database_url=os.environ.get(
            "DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5433/penalties"
        ),
        app_profile=os.environ.get("APP_PROFILE", "dev"),
    )


REPO_ROOT = _REPO_ROOT
DATA_DIR = _REPO_ROOT / "data"
ARTIFACTS_DIR = _REPO_ROOT / "artifacts"
