from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.import_batch import (
    ImportBatchCreate,
    ImportBatchRead,
    ImportBatchSuggestionRead,
    ImportBatchUpdate,
)
from app.schemas.research_patch import ImportCommitResult, ImportPreview, ResearchPatch
from app.services.import_batch_service import (
    commit_import_batch,
    create_import_batch,
    duplicate_suggestions,
    get_import_batch,
    list_import_batches,
    read_import_batch,
    reject_import_batch,
    update_import_batch,
    validate_import_batch,
)
from app.services.import_service import commit_patch, preview_patch

router = APIRouter(prefix="/api/import", tags=["import"])


@router.post("/validate", response_model=ImportPreview)
def api_validate_patch(patch: ResearchPatch):
    return preview_patch(patch)


@router.post("/preview", response_model=ImportPreview)
def api_preview_patch(patch: ResearchPatch):
    return preview_patch(patch)


@router.post("/commit", response_model=ImportCommitResult)
def api_commit_patch(
    patch: ResearchPatch,
    git_commit: bool = False,
    db: Session = Depends(get_db),
):
    try:
        return commit_patch(db, patch, git_commit=git_commit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/batches", response_model=ImportBatchRead, status_code=201)
def api_create_import_batch(payload: ImportBatchCreate, db: Session = Depends(get_db)):
    return create_import_batch(db, payload)


@router.get("/batches", response_model=list[ImportBatchRead])
def api_list_import_batches(db: Session = Depends(get_db)):
    return list_import_batches(db)


@router.get("/batches/{batch_id}", response_model=ImportBatchRead)
def api_get_import_batch(batch_id: str, db: Session = Depends(get_db)):
    batch = get_import_batch(db, batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Import batch not found")
    return read_import_batch(batch)


@router.patch("/batches/{batch_id}", response_model=ImportBatchRead)
def api_update_import_batch(
    batch_id: str,
    payload: ImportBatchUpdate,
    db: Session = Depends(get_db),
):
    batch = get_import_batch(db, batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Import batch not found")
    return update_import_batch(db, batch, payload)


@router.post("/batches/{batch_id}/validate", response_model=ImportBatchRead)
def api_validate_import_batch(batch_id: str, db: Session = Depends(get_db)):
    batch = get_import_batch(db, batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Import batch not found")
    try:
        return validate_import_batch(db, batch)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/batches/{batch_id}/commit", response_model=ImportBatchRead)
def api_commit_import_batch(
    batch_id: str,
    git_commit: bool = False,
    db: Session = Depends(get_db),
):
    batch = get_import_batch(db, batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Import batch not found")
    try:
        return commit_import_batch(db, batch, git_commit=git_commit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/batches/{batch_id}/reject", response_model=ImportBatchRead)
def api_reject_import_batch(
    batch_id: str,
    payload: ImportBatchUpdate | None = None,
    db: Session = Depends(get_db),
):
    batch = get_import_batch(db, batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Import batch not found")
    return reject_import_batch(db, batch, payload.review_note if payload else None)


@router.get("/batches/{batch_id}/suggestions", response_model=ImportBatchSuggestionRead)
def api_import_batch_suggestions(batch_id: str, db: Session = Depends(get_db)):
    batch = get_import_batch(db, batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Import batch not found")
    try:
        return duplicate_suggestions(db, batch)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
