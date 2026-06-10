from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import agent, attempts, context_packs, fragments, import_patch, problems, relations, sources, topics, zotero
from app.config import ensure_local_directories, get_settings
from app.db import init_db

app = FastAPI(title="LemmaForge API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(fragments.router)
app.include_router(relations.router)
app.include_router(sources.router)
app.include_router(topics.router)
app.include_router(import_patch.router)
app.include_router(context_packs.router)
app.include_router(zotero.router)
app.include_router(agent.router)
app.include_router(problems.router)
app.include_router(attempts.router)


@app.on_event("startup")
def on_startup() -> None:
    ensure_local_directories()
    init_db()


@app.get("/api/health")
def health():
    settings = get_settings()
    database_path = _sqlite_path_from_url(settings.database_url)
    database_bytes = _file_size(database_path)
    vault_bytes = _directory_size(settings.vault_dir)
    disk_usage_path = settings.vault_dir if settings.vault_dir.exists() else settings.vault_dir.parent
    disk_usage = shutil.disk_usage(disk_usage_path)
    return {
        "ok": True,
        "storage": {
            "database_bytes": database_bytes,
            "vault_bytes": vault_bytes,
            "app_bytes": database_bytes + vault_bytes,
            "disk_total_bytes": disk_usage.total,
            "disk_free_bytes": disk_usage.free,
        },
    }


def _sqlite_path_from_url(database_url: str) -> Path | None:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return None
    return Path(database_url.removeprefix(prefix))


def _file_size(path: Path | None) -> int:
    if path is None or not path.exists() or not path.is_file():
        return 0
    return path.stat().st_size


def _directory_size(path: Path) -> int:
    if not path.exists() or not path.is_dir():
        return 0
    total = 0
    for child in path.rglob("*"):
        if child.is_file():
            try:
                total += child.stat().st_size
            except OSError:
                continue
    return total
