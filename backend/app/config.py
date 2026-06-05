from __future__ import annotations

import os
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
    zotero_data_dir: Path | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        root = project_root()
        data_dir = root / "data"
        default_db = f"sqlite:///{(data_dir / 'research.db').as_posix()}"
        zotero_dir = os.getenv("RESEARCH_ZOTERO_DATA_DIR")
        return cls(
            database_url=os.getenv("RESEARCH_DB_URL", default_db),
            vault_dir=Path(os.getenv("RESEARCH_VAULT_DIR", root / "vault")),
            references_bib=Path(
                os.getenv("RESEARCH_REFERENCES_BIB", root / "references" / "references.bib")
            ),
            zotero_data_dir=Path(zotero_dir) if zotero_dir else None,
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


def _sqlite_path_from_url(database_url: str) -> Path | None:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return None
    return Path(database_url.removeprefix(prefix))

