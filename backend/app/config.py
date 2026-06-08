from __future__ import annotations

import os
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    database_url: str
    vault_dir: Path
    references_bib: Path
    zotero_local_api_url: str
    zotero_data_dir: Path | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        root = project_root()
        data_dir = root / "data"
        default_db = f"sqlite:///{(data_dir / 'research.db').as_posix()}"
        zotero_dir = os.getenv("RESEARCH_ZOTERO_DATA_DIR")
        saved_settings = _saved_zotero_settings(root)
        return cls(
            database_url=os.getenv("RESEARCH_DB_URL", default_db),
            vault_dir=Path(os.getenv("RESEARCH_VAULT_DIR", root / "vault")),
            references_bib=Path(
                os.getenv(
                    "RESEARCH_REFERENCES_BIB",
                    saved_settings.get("references_bib") or root / "references" / "references.bib",
                )
            ),
            zotero_local_api_url=os.getenv(
                "RESEARCH_ZOTERO_LOCAL_API_URL",
                saved_settings.get("zotero_local_api_url") or "http://127.0.0.1:23119",
            ).rstrip("/"),
            zotero_data_dir=Path(zotero_dir or saved_settings["zotero_data_dir"]) if zotero_dir or saved_settings.get("zotero_data_dir") else None,
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()


def reset_settings_cache() -> None:
    get_settings.cache_clear()


def ensure_local_directories() -> None:
    settings = get_settings()
    db_path = _sqlite_path_from_url(settings.database_url)
    if db_path:
        db_path.parent.mkdir(parents=True, exist_ok=True)
    for child in ("fragments", "sources", "context_packs", "imports"):
        (settings.vault_dir / child).mkdir(parents=True, exist_ok=True)
    settings.references_bib.parent.mkdir(parents=True, exist_ok=True)


def _saved_zotero_settings(root: Path) -> dict[str, str | None]:
    path = root / "data" / "zotero_settings.json"
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(parsed, dict):
        return {}
    return {
        "zotero_data_dir": parsed.get("zotero_data_dir") if isinstance(parsed.get("zotero_data_dir"), str) else None,
        "references_bib": parsed.get("references_bib") if isinstance(parsed.get("references_bib"), str) else None,
        "zotero_local_api_url": parsed.get("zotero_local_api_url") if isinstance(parsed.get("zotero_local_api_url"), str) else None,
    }


def _sqlite_path_from_url(database_url: str) -> Path | None:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return None
    return Path(database_url.removeprefix(prefix))
