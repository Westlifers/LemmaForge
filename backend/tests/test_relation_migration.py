from __future__ import annotations

import json

import pytest
from pydantic import ValidationError
from sqlalchemy import text

from app.db import _ensure_lightweight_sqlite_migrations
from app.models.relation import Relation
from app.schemas.relation import RelationCreate
from app.schemas.fragment import FragmentCreate
from app.services.fragment_service import create_fragment


def _fragment(db, title: str):
    return create_fragment(
        db,
        FragmentCreate(
            type="Definition",
            title=title,
            status="working",
            body=f"{title} body.",
            origin_classification="user_original",
            exactness="original",
        ),
    )


def test_relation_schema_accepts_new_kinds_and_rejects_removed_kinds():
    for kind in [
        "depends_on",
        "proof_of",
        "refines",
        "replaces",
        "contradicts",
        "generalizes",
        "is_example_of",
        "is_counterexample_to",
        "uses_notation",
        "questions",
        "compares_with",
        "inspired_by",
    ]:
        assert RelationCreate(source_fragment_id="a", relation_kind=kind, target_fragment_id="b").relation_kind == kind

    with pytest.raises(ValidationError):
        RelationCreate(source_fragment_id="a", relation_kind="uses", target_fragment_id="b")


def test_lightweight_migration_maps_swaps_and_archives_legacy_relations(db_session):
    db, tmp_path = db_session
    first = _fragment(db, "First migration fragment")
    second = _fragment(db, "Second migration fragment")
    third = _fragment(db, "Third migration fragment")
    db.execute(
        text(
            "INSERT INTO relations (id, source_fragment_id, relation_kind, target_fragment_id, confidence, created_at) "
            "VALUES "
            "('rel_uses', :first, 'uses', :second, 0.5, CURRENT_TIMESTAMP), "
            "('rel_specializes', :first, 'specializes_to', :third, 0.7, CURRENT_TIMESTAMP), "
            "('rel_quotes', :second, 'quotes', :third, 0.8, CURRENT_TIMESTAMP)"
        ),
        {"first": first.id, "second": second.id, "third": third.id},
    )
    db.commit()

    _ensure_lightweight_sqlite_migrations()

    relations = {relation.id: relation for relation in db.query(Relation).all()}
    assert relations["rel_uses"].relation_kind == "depends_on"
    assert relations["rel_uses"].source_fragment_id == first.id
    assert relations["rel_uses"].target_fragment_id == second.id
    assert relations["rel_specializes"].relation_kind == "generalizes"
    assert relations["rel_specializes"].source_fragment_id == third.id
    assert relations["rel_specializes"].target_fragment_id == first.id
    assert "rel_quotes" not in relations

    archive_path = tmp_path / "data" / "relation_migration_archive.json"
    archived = json.loads(archive_path.read_text(encoding="utf-8"))
    assert [entry["id"] for entry in archived] == ["rel_quotes"]
    assert archived[0]["old_kind"] == "quotes"

    _ensure_lightweight_sqlite_migrations()
    archived_again = json.loads(archive_path.read_text(encoding="utf-8"))
    assert [entry["id"] for entry in archived_again] == ["rel_quotes"]
