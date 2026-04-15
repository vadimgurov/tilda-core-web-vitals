import requests

from .config import Config

TILDA_API_BASE = "https://api.tildacdn.info/v1"


def _call(method: str, cfg: Config, **params) -> dict | list:
    params.update({"publickey": cfg.tilda_public_key, "secretkey": cfg.tilda_secret_key})
    try:
        resp = requests.get(f"{TILDA_API_BASE}/{method}/", params=params, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Ошибка сети при обращении к Tilda API: {e}") from e

    data = resp.json()
    if data.get("status") != "FOUND":
        raise RuntimeError(f"Tilda API вернул ошибку ({method}): {data}")
    return data["result"]


def get_pages(cfg: Config) -> list[dict]:
    """Возвращает список всех страниц проекта."""
    return _call("getpageslist", cfg, projectid=cfg.project_id)


def get_page_full(cfg: Config, pageid: str) -> dict:
    """Возвращает полные данные страницы."""
    return _call("getpagefull", cfg, pageid=pageid)
