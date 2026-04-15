from pathlib import Path

from pydantic import BaseModel, field_validator
import json

CONFIG_DIR = Path.home() / ".tilda-vitals"
CONFIG_PATH = CONFIG_DIR / "config.json"
SESSION_PATH = CONFIG_DIR / "session.json"


class Config(BaseModel):
    site_url: str
    project_id: str
    tilda_public_key: str
    tilda_secret_key: str

    @field_validator("site_url")
    @classmethod
    def strip_trailing_slash(cls, v: str) -> str:
        return v.rstrip("/")


def load_config() -> Config | None:
    if not CONFIG_PATH.exists():
        return None
    try:
        data = json.loads(CONFIG_PATH.read_text())
        return Config(**data)
    except Exception:
        return None


def save_config(cfg: Config) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(cfg.model_dump_json(indent=2))
