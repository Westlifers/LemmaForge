from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.config import get_settings
from app.schemas.fragment import FragmentRead
from app.schemas.source import SourceCreate, SourceRead, SourceUpdate
from app.services.source_service import (
    create_source,
    get_source,
    list_fragments_for_source,
    list_sources,
    sync_references_to_sources,
    update_source,
)

router = APIRouter(prefix="/api/sources", tags=["sources"])


@router.get("", response_model=list[SourceRead])
def api_list_sources(search: str | None = None, db: Session = Depends(get_db)):
    return list_sources(db, search=search)


@router.post("", response_model=SourceRead, status_code=201)
def api_create_source(payload: SourceCreate, db: Session = Depends(get_db)):
    return create_source(db, payload)


@router.get("/{source_id}", response_model=SourceRead)
def api_get_source(source_id: str, db: Session = Depends(get_db)):
    source = get_source(db, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@router.patch("/{source_id}", response_model=SourceRead)
def api_update_source(source_id: str, payload: SourceUpdate, db: Session = Depends(get_db)):
    source = get_source(db, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return update_source(db, source, payload)


@router.get("/{source_id}/fragments", response_model=list[FragmentRead])
def api_source_fragments(source_id: str, db: Session = Depends(get_db)):
    if get_source(db, source_id) is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return list_fragments_for_source(db, source_id)


@router.post("/sync-bibtex", response_model=list[SourceRead])
def api_sync_bibtex_sources(db: Session = Depends(get_db)):
    settings = get_settings()
    if not settings.references_bib.exists():
        raise HTTPException(status_code=404, detail="references.bib not found")
    return sync_references_to_sources(
        db,
        settings.references_bib.read_text(encoding="utf-8", errors="ignore"),
    )
