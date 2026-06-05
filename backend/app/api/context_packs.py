from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.context_pack import ContextPack, ContextPackItem
from app.models.fragment import Fragment
from app.schemas.context_pack import ContextPackCreate, ContextPackExport, ContextPackRead
from app.services.context_builder import export_context_pack
from app.services.ids import slugify, unique_model_id

router = APIRouter(prefix="/api/context-packs", tags=["context-packs"])


@router.get("", response_model=list[ContextPackRead])
def api_list_context_packs(db: Session = Depends(get_db)):
    return list(db.execute(select(ContextPack).order_by(ContextPack.updated_at.desc())).scalars())


@router.post("", response_model=ContextPackRead, status_code=201)
def api_create_context_pack(payload: ContextPackCreate, db: Session = Depends(get_db)):
    context_pack = ContextPack(
        id=unique_model_id(db, ContextPack, f"ctx_{slugify(payload.title)}"),
        title=payload.title,
        objective=payload.objective,
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


@router.get("/{context_pack_id}", response_model=ContextPackRead)
def api_get_context_pack(context_pack_id: str, db: Session = Depends(get_db)):
    context_pack = db.get(ContextPack, context_pack_id)
    if context_pack is None:
        raise HTTPException(status_code=404, detail="Context pack not found")
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
