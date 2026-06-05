from __future__ import annotations

import json

import pytest
from sqlalchemy import select

from app.models.fragment import Fragment
from app.models.import_batch import ImportBatch
from app.schemas.fragment import FragmentCreate
from app.schemas.import_batch import ImportBatchCreate, ImportBatchUpdate
from app.schemas.research_patch import ResearchPatch
from app.services.fragment_service import create_fragment
from app.services.import_batch_service import (
    commit_import_batch,
    create_import_batch,
    duplicate_suggestions,
    get_import_batch,
    list_import_batches,
    reject_import_batch,
    update_import_batch,
    validate_import_batch,
)


def batch_patch(title: str = "Candidate compact object") -> ResearchPatch:
    return ResearchPatch.model_validate(
        {
            "patch_type": "ResearchPatch",
            "metadata": {
                "source_kind": "chatgpt_excerpt",
                "topic_hint": "Category theory",
                "created_by": "codex_import_agent",
                "requires_user_review": True,
            },
            "fragments": [
                {
                    "local_id": "candidate_compact_object",
                    "type": "Definition",
                    "title": title,
                    "status": "candidate",
                    "origin_classification": "assistant_generated",
                    "exactness": "interpretation",
                    "body": "A compact object candidate awaits review.",
                    "assumptions": [],
                    "conclusion": None,
                    "confidence": 0.7,
                    "source_excerpt": "A compact object candidate awaits review.",
                }
            ],
            "relations": [],
            "source_pointers": [
                {
                    "fragment_local_id": "candidate_compact_object",
                    "citekey": "Example2026",
                    "locator": "Definition 1.1",
                    "exactness": "paraphrase",
                    "quote_text": None,
                    "note": "Test pointer.",
                }
            ],
            "warnings": ["Review before use."],
        }
    )


def test_create_list_read_update_import_batches(db_session):
    db, _tmp_path = db_session
    created = create_import_batch(
        db,
        ImportBatchCreate(raw_excerpt="Raw note.", topic_hint="Topic"),
    )

    assert created.status == "draft"
    assert created.patch is not None
    assert list_import_batches(db)[0].id == created.id

    batch = get_import_batch(db, created.id)
    assert batch is not None
    updated = update_import_batch(
        db,
        batch,
        ImportBatchUpdate(review_note="Look carefully.", topic_hint="Updated topic"),
    )

    assert updated.review_note == "Look carefully."
    assert updated.topic_hint == "Updated topic"


def test_validate_batch_rejects_stable_import_status(db_session):
    db, _tmp_path = db_session
    batch = ImportBatch(
        id="imp_invalid_status",
        status="draft",
        raw_excerpt="Invalid.",
        patch_json=json.dumps(
            {
                "patch_type": "ResearchPatch",
                "metadata": {
                    "source_kind": "chatgpt_excerpt",
                    "created_by": "codex_import_agent",
                    "requires_user_review": True,
                },
                "fragments": [
                    {
                        "local_id": "bad",
                        "type": "Definition",
                        "title": "Bad",
                        "status": "stable",
                        "origin_classification": "assistant_generated",
                        "exactness": "interpretation",
                        "body": "Bad.",
                    }
                ],
                "relations": [],
                "source_pointers": [],
                "warnings": [],
            }
        ),
        warnings_json="[]",
    )
    db.add(batch)
    db.commit()

    with pytest.raises(ValueError):
        validate_import_batch(db, batch)


def test_update_with_null_patch_rebuilds_from_raw_excerpt(db_session):
    db, _tmp_path = db_session
    created = create_import_batch(
        db,
        ImportBatchCreate(raw_excerpt="An initial note."),
    )
    batch = get_import_batch(db, created.id)
    assert batch is not None
    batch.patch_json = None
    db.commit()

    updated = update_import_batch(
        db,
        batch,
        ImportBatchUpdate(
            raw_excerpt="Given a distributive lattice L, its canonical extension is a candidate definition.",
            patch=None,
        ),
    )

    assert updated.patch is not None
    assert updated.patch.fragments[0].status == "candidate"

    validated = validate_import_batch(db, batch)
    assert validated.status == "validated"


def test_reject_batch_does_not_create_fragments(db_session):
    db, _tmp_path = db_session
    created = create_import_batch(db, ImportBatchCreate(patch=batch_patch()))
    batch = get_import_batch(db, created.id)
    assert batch is not None

    rejected = reject_import_batch(db, batch, "Not useful.")

    assert rejected.status == "rejected"
    assert db.execute(select(Fragment)).scalars().all() == []


def test_commit_batch_creates_outputs_and_stores_result(db_session):
    db, tmp_path = db_session
    created = create_import_batch(db, ImportBatchCreate(patch=batch_patch()))
    batch = get_import_batch(db, created.id)
    assert batch is not None
    validate_import_batch(db, batch)

    committed = commit_import_batch(db, batch)

    assert committed.status == "committed"
    assert committed.commit_result is not None
    assert len(committed.commit_result.fragment_ids) == 1
    assert len(committed.commit_result.source_pointer_ids) == 1
    assert list((tmp_path / "vault" / "fragments").glob("*.md"))


def test_duplicate_suggestions_do_not_mutate_existing_fragments(db_session):
    db, _tmp_path = db_session
    existing = create_fragment(
        db,
        FragmentCreate(
            type="Definition",
            title="Compact object",
            status="stable",
            body="An existing compact object definition.",
            origin_classification="user_original",
            exactness="original",
        ),
    )
    created = create_import_batch(db, ImportBatchCreate(patch=batch_patch("Compact object")))
    batch = get_import_batch(db, created.id)
    assert batch is not None

    suggestions = duplicate_suggestions(db, batch)

    assert suggestions.suggestions
    assert suggestions.suggestions[0].fragment_id == existing.id
    assert db.get(Fragment, existing.id).body == "An existing compact object definition."
