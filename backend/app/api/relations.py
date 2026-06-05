from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.relation import RelationCreate, RelationRead, RelationUpdate
from app.services.fragment_service import get_fragment
from app.services.relation_service import (
    create_relation,
    delete_relation,
    list_incoming_relations,
    list_outgoing_relations,
    list_relations_for_fragment,
    update_relation,
)

router = APIRouter(tags=["relations"])


@router.get("/api/fragments/{fragment_id}/relations", response_model=list[RelationRead])
def api_fragment_relations(fragment_id: str, db: Session = Depends(get_db)):
    if get_fragment(db, fragment_id) is None:
        raise HTTPException(status_code=404, detail="Fragment not found")
    return list_relations_for_fragment(db, fragment_id)


@router.get("/api/fragments/{fragment_id}/relations/outgoing", response_model=list[RelationRead])
def api_fragment_outgoing_relations(fragment_id: str, db: Session = Depends(get_db)):
    if get_fragment(db, fragment_id) is None:
        raise HTTPException(status_code=404, detail="Fragment not found")
    return list_outgoing_relations(db, fragment_id)


@router.get("/api/fragments/{fragment_id}/relations/incoming", response_model=list[RelationRead])
def api_fragment_incoming_relations(fragment_id: str, db: Session = Depends(get_db)):
    if get_fragment(db, fragment_id) is None:
        raise HTTPException(status_code=404, detail="Fragment not found")
    return list_incoming_relations(db, fragment_id)


@router.post("/api/relations", response_model=RelationRead, status_code=201)
def api_create_relation(payload: RelationCreate, db: Session = Depends(get_db)):
    try:
        return create_relation(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/api/relations/{relation_id}", response_model=RelationRead)
def api_update_relation(
    relation_id: str,
    payload: RelationUpdate,
    db: Session = Depends(get_db),
):
    from app.models.relation import Relation

    relation = db.get(Relation, relation_id)
    if relation is None:
        raise HTTPException(status_code=404, detail="Relation not found")
    try:
        return update_relation(db, relation, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/api/relations/{relation_id}", status_code=204)
def api_delete_relation(relation_id: str, db: Session = Depends(get_db)):
    if not delete_relation(db, relation_id):
        raise HTTPException(status_code=404, detail="Relation not found")
    return None
