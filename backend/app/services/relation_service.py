from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.fragment import Fragment
from app.models.relation import Relation
from app.schemas.relation import RelationCreate, RelationUpdate
from app.services.ids import unique_model_id


def list_relations_for_fragment(db: Session, fragment_id: str) -> list[Relation]:
    query = select(Relation).where(
        or_(
            Relation.source_fragment_id == fragment_id,
            Relation.target_fragment_id == fragment_id,
        )
    )
    return list(db.execute(query).scalars())


def list_outgoing_relations(db: Session, fragment_id: str) -> list[Relation]:
    return list(
        db.execute(
            select(Relation).where(Relation.source_fragment_id == fragment_id)
        ).scalars()
    )


def list_incoming_relations(db: Session, fragment_id: str) -> list[Relation]:
    return list(
        db.execute(
            select(Relation).where(Relation.target_fragment_id == fragment_id)
        ).scalars()
    )


def create_relation(
    db: Session,
    payload: RelationCreate,
    *,
    commit: bool = True,
) -> Relation:
    if db.get(Fragment, payload.source_fragment_id) is None:
        raise ValueError(f"Unknown source fragment: {payload.source_fragment_id}")
    if db.get(Fragment, payload.target_fragment_id) is None:
        raise ValueError(f"Unknown target fragment: {payload.target_fragment_id}")
    relation = Relation(
        id=unique_model_id(
            db,
            Relation,
            f"{payload.relation_kind}_{payload.source_fragment_id}_{payload.target_fragment_id}",
        ),
        source_fragment_id=payload.source_fragment_id,
        relation_kind=payload.relation_kind,
        target_fragment_id=payload.target_fragment_id,
        confidence=payload.confidence,
    )
    db.add(relation)
    db.flush()
    if commit:
        db.commit()
        db.refresh(relation)
    return relation


def delete_relation(db: Session, relation_id: str) -> bool:
    relation = db.get(Relation, relation_id)
    if relation is None:
        return False
    db.delete(relation)
    db.commit()
    return True


def update_relation(db: Session, relation: Relation, payload: RelationUpdate) -> Relation:
    changes = payload.model_dump(exclude_unset=True)
    if "target_fragment_id" in changes and db.get(Fragment, changes["target_fragment_id"]) is None:
        raise ValueError(f"Unknown target fragment: {changes['target_fragment_id']}")
    for key, value in changes.items():
        if key == "relation_kind":
            relation.relation_kind = value
        else:
            setattr(relation, key, value)
    db.commit()
    db.refresh(relation)
    return relation

