from __future__ import annotations

import json

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi import Depends

from app.config import project_root
from app.db import get_db
from app.schemas.source import SourceRead
from app.services.source_service import sync_references_to_sources
from app.services.zotero_service import search_references, status

router = APIRouter(prefix="/api/zotero", tags=["zotero"])


class ZoteroSettingsPayload(BaseModel):
    zotero_data_dir: str | None = None
    references_bib: str | None = None


@router.get("/status")
def api_zotero_status():
    return status()


@router.post("/settings")
def api_zotero_settings(payload: ZoteroSettingsPayload):
    settings_path = project_root() / "data" / "zotero_settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        json.dumps(payload.model_dump(), indent=2),
        encoding="utf-8",
    )
    return {"saved": True, "path": str(settings_path)}


@router.get("/search")
def api_zotero_search(query: str):
    return {"query": query, "results": search_references(query)}


@router.post("/sync", response_model=list[SourceRead])
def api_zotero_sync(db: Session = Depends(get_db)):
    references = status().references_bib
    from pathlib import Path

    path = Path(references)
    if not path.exists():
        return []
    return sync_references_to_sources(db, path.read_text(encoding="utf-8", errors="ignore"))
