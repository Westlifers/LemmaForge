from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models.fragment import Fragment
from app.models.relation import Relation
from app.models.source import SourcePointer
from app.schemas.import_batch import AICreateDraftsRequest, AIApplyRelationsRequest, AIExtractRequest
from app.schemas.research_patch import ResearchPatch
from app.services import codex_import_service
from app.services.codex_import_service import (
    CodexImportError,
    CodexImportUnavailable,
    _CodexProcessResult,
    extract_research_patch_with_codex,
)
from app.services.import_batch_service import (
    apply_ai_relation_proposals,
    create_ai_drafts_from_patch,
    create_import_batch,
    get_import_batch,
)
from app.schemas.import_batch import ImportBatchCreate


def ai_patch() -> ResearchPatch:
    return ResearchPatch.model_validate(
        {
            "patch_type": "ResearchPatch",
            "metadata": {
                "source_kind": "conversation",
                "topic_hint": "Lattice theory",
                "created_by": "codex_import_agent",
                "requires_user_review": True,
            },
            "fragments": [
                {
                    "local_id": "canonical_extension",
                    "type": "Definition",
                    "title": "Canonical extension",
                    "status": "candidate",
                    "origin_classification": "assistant_generated",
                    "exactness": "interpretation",
                    "body": "The canonical extension L^sigma is a dense and compact completion.",
                    "assumptions": [],
                    "conclusion": None,
                    "confidence": 0.8,
                    "source_excerpt": "canonical extension",
                },
                {
                    "local_id": "downset_lattice",
                    "type": "Construction",
                    "title": "Downset lattice construction",
                    "status": "raw",
                    "origin_classification": "external_source",
                    "exactness": "paraphrase",
                    "body": "The downsets ordered by inclusion form a complete lattice.",
                    "assumptions": [],
                    "conclusion": None,
                    "confidence": 0.7,
                    "source_excerpt": "downsets",
                },
            ],
            "relations": [
                {
                    "source": "canonical_extension",
                    "kind": "depends_on",
                    "target": "downset_lattice",
                    "confidence": 0.6,
                }
            ],
            "source_pointers": [
                {
                    "fragment_local_id": "canonical_extension",
                    "citekey": "Gehrke2026",
                    "locator": "Definition 2.1",
                    "exactness": "paraphrase",
                    "quote_text": None,
                    "note": "AI extracted.",
                }
            ],
            "warnings": ["Review relation direction."],
        }
    )


def test_codex_cli_success_returns_valid_patch(monkeypatch):
    patch_json = ai_patch().model_dump_json()
    monkeypatch.setattr(codex_import_service.shutil, "which", lambda name: "codex")

    def fake_run(command, prompt, cwd, timeout_seconds, on_log):
        output_path = command[command.index("--output-last-message") + 1]
        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write(patch_json)
        if on_log:
            on_log("[stderr] thinking")
        return _CodexProcessResult(0, "", "", ["[stderr] thinking"])

    monkeypatch.setattr(codex_import_service, "_run_codex_command", fake_run)
    logs = []

    patch = extract_research_patch_with_codex(
        AIExtractRequest(raw_excerpt="Define canonical extension."),
        on_log=logs.append,
    )

    assert patch.fragments[0].title == "Canonical extension"
    assert logs == ["[stderr] thinking"]


def test_codex_cli_unavailable(monkeypatch):
    monkeypatch.setattr(codex_import_service.shutil, "which", lambda name: None)

    with pytest.raises(CodexImportUnavailable):
        extract_research_patch_with_codex(AIExtractRequest(raw_excerpt="Any note."))


def test_codex_cli_timeout(monkeypatch):
    monkeypatch.setattr(codex_import_service.shutil, "which", lambda name: "codex")

    def fake_run(*args, **kwargs):
        raise CodexImportError("Codex extraction timed out.", logs=["Starting Codex CLI extraction."])

    monkeypatch.setattr(codex_import_service, "_run_codex_command", fake_run)

    with pytest.raises(CodexImportError, match="timed out") as exc_info:
        extract_research_patch_with_codex(AIExtractRequest(raw_excerpt="Any note."))
    assert exc_info.value.logs == ["Starting Codex CLI extraction."]


def test_codex_cli_schema_invalid_output(monkeypatch):
    monkeypatch.setattr(codex_import_service.shutil, "which", lambda name: "codex")

    def fake_run(command, prompt, cwd, timeout_seconds, on_log):
        output_path = command[command.index("--output-last-message") + 1]
        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write('{"patch_type":"ResearchPatch","fragments":[{"status":"stable"}]}')
        return _CodexProcessResult(0, "", "", ["invalid schema"])

    monkeypatch.setattr(codex_import_service, "_run_codex_command", fake_run)

    with pytest.raises(CodexImportError) as exc_info:
        extract_research_patch_with_codex(AIExtractRequest(raw_excerpt="Any note."))
    assert exc_info.value.logs == ["invalid schema"]


def test_ai_create_drafts_stores_proposals_without_creating_relations(db_session):
    db, _tmp_path = db_session
    created = create_import_batch(db, ImportBatchCreate(raw_excerpt="Conversation.", patch=ai_patch()))

    result = create_ai_drafts_from_patch(db, AICreateDraftsRequest(batch_id=created.id))

    fragments = list(db.execute(select(Fragment)).scalars())
    assert [fragment.status for fragment in fragments] == ["draft", "draft"]
    assert {fragment.origin_classification for fragment in fragments} == {
        "assistant_generated",
        "mixed",
    }
    assert len(result.fragment_ids) == 2
    assert len(result.source_pointer_ids) == 1
    assert len(result.relation_proposals) == 1
    assert db.execute(select(Relation)).scalars().all() == []
    assert len(db.execute(select(SourcePointer)).scalars().all()) == 1

    batch = get_import_batch(db, created.id)
    assert batch is not None
    assert batch.ai_draft_result_json is not None
    assert batch.relation_proposals_json is not None


def test_ai_create_drafts_only_keeps_selected_fragments(db_session):
    db, _tmp_path = db_session
    created = create_import_batch(db, ImportBatchCreate(raw_excerpt="Conversation.", patch=ai_patch()))

    result = create_ai_drafts_from_patch(
        db,
        AICreateDraftsRequest(
            batch_id=created.id,
            selected_local_ids=["canonical_extension"],
        ),
    )

    fragments = list(db.execute(select(Fragment)).scalars())
    assert len(fragments) == 1
    assert fragments[0].id == result.local_to_fragment_id["canonical_extension"]
    assert "downset_lattice" not in result.local_to_fragment_id
    assert result.source_pointer_ids
    assert result.relation_proposals == []
    assert db.execute(select(Relation)).scalars().all() == []


def test_ai_create_drafts_rejects_empty_selection(db_session):
    db, _tmp_path = db_session
    created = create_import_batch(db, ImportBatchCreate(raw_excerpt="Conversation.", patch=ai_patch()))

    with pytest.raises(ValueError, match="Select at least one"):
        create_ai_drafts_from_patch(
            db,
            AICreateDraftsRequest(batch_id=created.id, selected_local_ids=[]),
        )


def test_ai_create_drafts_is_idempotent_for_batch(db_session):
    db, _tmp_path = db_session
    created = create_import_batch(db, ImportBatchCreate(raw_excerpt="Conversation.", patch=ai_patch()))

    first = create_ai_drafts_from_patch(db, AICreateDraftsRequest(batch_id=created.id))
    second = create_ai_drafts_from_patch(db, AICreateDraftsRequest(batch_id=created.id))

    assert first.fragment_ids == second.fragment_ids
    assert len(db.execute(select(Fragment)).scalars().all()) == 2


def test_apply_ai_relation_proposals_creates_selected_relations(db_session):
    db, _tmp_path = db_session
    created = create_import_batch(db, ImportBatchCreate(raw_excerpt="Conversation.", patch=ai_patch()))
    draft_result = create_ai_drafts_from_patch(db, AICreateDraftsRequest(batch_id=created.id))
    batch = get_import_batch(db, created.id)
    assert batch is not None

    result = apply_ai_relation_proposals(
        db,
        batch,
        AIApplyRelationsRequest(proposal_ids=[draft_result.relation_proposals[0].proposal_id]),
    )

    assert len(result.relation_ids) == 1
    assert len(db.execute(select(Relation)).scalars().all()) == 1
    assert result.relation_proposals[0].applied_relation_id == result.relation_ids[0]
