from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import project_root, reset_settings_cache
from app.db import get_db
from app.schemas.source import SourceRead
from app.services.source_service import sync_references_to_sources, sync_zotero_items_to_sources
from app.services.zotero_service import (
    ZoteroLocalApiError,
    get_local_item,
    get_local_items_by_keys,
    list_local_items,
    search_local_items,
    search_references,
    status,
)

router = APIRouter(prefix="/api/zotero", tags=["zotero"])


class ZoteroSettingsPayload(BaseModel):
    zotero_data_dir: str | None = None
    references_bib: str | None = None
    zotero_local_api_url: str | None = None


class ZoteroSyncPayload(BaseModel):
    item_keys: list[str] | None = None
    limit: int = Field(default=50, ge=1, le=100)


class ZoteroSyncResult(BaseModel):
    available: bool
    synced_count: int
    sources: list[SourceRead]
    error: str | None = None


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
    reset_settings_cache()
    return {"saved": True, "path": str(settings_path)}


@router.get("/search")
def api_zotero_search(query: str = "", limit: int = 20):
    try:
        return {
            "query": query,
            "available": True,
            "error": None,
            "results": [_zotero_item_read(item) for item in search_local_items(query, limit=limit)],
        }
    except ZoteroLocalApiError as caught:
        return {"query": query, "available": False, "error": str(caught), "results": []}


@router.get("/items/{item_key}")
def api_zotero_item(item_key: str):
    try:
        item = get_local_item(item_key)
        return {"available": True, "error": None, "item": _zotero_item_read(item)}
    except ZoteroLocalApiError as caught:
        return {"available": False, "error": str(caught), "item": None}


@router.post("/sync", response_model=ZoteroSyncResult)
def api_zotero_sync(payload: ZoteroSyncPayload | None = None, db: Session = Depends(get_db)):
    payload = payload or ZoteroSyncPayload()
    try:
        items = (
            get_local_items_by_keys(payload.item_keys)
            if payload.item_keys
            else list_local_items(limit=payload.limit)
        )
        sources = sync_zotero_items_to_sources(db, items)
        return ZoteroSyncResult(
            available=True,
            synced_count=len(sources),
            sources=sources,
        )
    except ZoteroLocalApiError as caught:
        return ZoteroSyncResult(available=False, synced_count=0, sources=[], error=str(caught))


@router.get("/search-bibtex")
def api_zotero_bibtex_search(query: str):
    return {"query": query, "results": search_references(query)}


@router.post("/sync-bibtex", response_model=list[SourceRead])
def api_zotero_bibtex_sync(db: Session = Depends(get_db)):
    references = status().references_bib
    path = Path(references)
    if not path.exists():
        return []
    return sync_references_to_sources(db, path.read_text(encoding="utf-8", errors="ignore"))


def _zotero_item_read(item: dict[str, Any]) -> dict[str, Any]:
    data = item.get("data") or {}
    meta = item.get("meta") or {}
    links = item.get("links") or {}
    return {
        "key": data.get("key") or item.get("key"),
        "version": item.get("version"),
        "item_type": data.get("itemType"),
        "title": data.get("title") or data.get("shortTitle") or "Untitled Zotero item",
        "creators": data.get("creators") or [],
        "creator_summary": meta.get("creatorSummary"),
        "date": data.get("date"),
        "year": _year_from_date(data.get("date") or meta.get("parsedDate")),
        "url": data.get("url"),
        "doi": data.get("DOI"),
        "abstract_note": data.get("abstractNote"),
        "citation_key": data.get("citationKey"),
        "collections": data.get("collections") or [],
        "tags": data.get("tags") or [],
        "attachment_count": meta.get("numChildren", 0),
        "attachments": item.get("attachments") or [],
        "zotero_url": (links.get("alternate") or {}).get("href"),
    }


def _year_from_date(value: str | None) -> int | None:
    if not value:
        return None
    import re

    match = re.search(r"\b(\d{4})\b", value)
    return int(match.group(1)) if match else None
