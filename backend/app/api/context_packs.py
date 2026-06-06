from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.context_pack import ContextPack, ContextPackItem
from app.models.fragment import Fragment, Topic
from app.schemas.context_pack import (
    ContextPackCreate,
    ContextPackExport,
    ContextPackRead,
    ContextPackSuggestJobRead,
    ContextPackSuggestRequest,
    ContextPackSuggestResult,
    ContextPackUpdate,
)
from app.services.context_builder import export_context_pack
from app.services.context_pack_ai_service import suggest_topic_context_pack
from app.services.context_pack_ai_job_service import (
    read_context_pack_suggest_job,
    start_context_pack_suggest_job,
)
from app.services.ids import slugify, unique_model_id
from app.services.markdown_vault import delete_context_pack_markdown

router = APIRouter(prefix="/api/context-packs", tags=["context-packs"])


@router.get("", response_model=list[ContextPackRead])
def api_list_context_packs(db: Session = Depends(get_db)):
    return list(db.execute(select(ContextPack).order_by(ContextPack.updated_at.desc())).scalars())


@router.post("", response_model=ContextPackRead, status_code=201)
def api_create_context_pack(payload: ContextPackCreate, db: Session = Depends(get_db)):
    if payload.topic_id is not None and db.get(Topic, payload.topic_id) is None:
        raise HTTPException(status_code=400, detail=f"Unknown topic: {payload.topic_id}")
    context_pack = ContextPack(
        id=unique_model_id(db, ContextPack, f"ctx_{slugify(payload.title)}"),
        topic_id=payload.topic_id,
        title=payload.title,
        objective=payload.objective,
        task_prompt=payload.task_prompt,
        body=payload.body,
    )
    db.add(context_pack)
    db.flush()
    for item_payload in payload.items:
        if db.get(Fragment, item_payload.fragment_id) is None:
            raise HTTPException(
                status_code=400, detail=f"Unknown fragment: {item_payload.fragment_id}"
            )
        db.add(
            ContextPackItem(
                context_pack_id=context_pack.id,
                fragment_id=item_payload.fragment_id,
                order_index=item_payload.order_index,
                reason=item_payload.reason,
            )
        )
    db.commit()
    db.refresh(context_pack)
    return context_pack


@router.post("/ai/suggest", response_model=ContextPackSuggestResult)
def api_suggest_context_pack(payload: ContextPackSuggestRequest, db: Session = Depends(get_db)):
    try:
        return suggest_topic_context_pack(db, payload)
    except ValueError as exc:
        status_code = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/ai/suggestion-jobs", response_model=ContextPackSuggestJobRead, status_code=202)
def api_start_context_pack_suggest_job(payload: ContextPackSuggestRequest):
    return start_context_pack_suggest_job(payload)


@router.get("/ai/suggestion-jobs/{job_id}", response_model=ContextPackSuggestJobRead)
def api_get_context_pack_suggest_job(job_id: str):
    try:
        return read_context_pack_suggest_job(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{context_pack_id}", response_model=ContextPackRead)
def api_get_context_pack(context_pack_id: str, db: Session = Depends(get_db)):
    context_pack = db.get(ContextPack, context_pack_id)
    if context_pack is None:
        raise HTTPException(status_code=404, detail="Context pack not found")
    return context_pack


@router.patch("/{context_pack_id}", response_model=ContextPackRead)
def api_update_context_pack(
    context_pack_id: str,
    payload: ContextPackUpdate,
    db: Session = Depends(get_db),
):
    context_pack = db.get(ContextPack, context_pack_id)
    if context_pack is None:
        raise HTTPException(status_code=404, detail="Context pack not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(context_pack, key, value)
    db.commit()
    db.refresh(context_pack)
    return context_pack


@router.post("/{context_pack_id}/export", response_model=ContextPackExport)
def api_export_context_pack(
    context_pack_id: str,
    git_commit: bool = False,
    db: Session = Depends(get_db),
):
    context_pack = db.get(ContextPack, context_pack_id)
    if context_pack is None:
        raise HTTPException(status_code=404, detail="Context pack not found")
    return export_context_pack(db, context_pack, git_commit=git_commit)


@router.delete("/{context_pack_id}", status_code=204)
def api_delete_context_pack(context_pack_id: str, db: Session = Depends(get_db)):
    context_pack = db.get(ContextPack, context_pack_id)
    if context_pack is None:
        raise HTTPException(status_code=404, detail="Context pack not found")
    delete_context_pack_markdown(context_pack)
    db.delete(context_pack)
    db.commit()
    return None
