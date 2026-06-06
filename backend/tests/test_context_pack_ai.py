from __future__ import annotations

import time
from pathlib import Path

import pytest
from sqlalchemy import select

from app.models.context_pack import ContextPack
from app.models.fragment import Fragment
from app.models.relation import Relation
from app.schemas.context_pack import (
    ContextPackCreate,
    ContextPackSuggestRequest,
    ContextPackSuggestion,
    ContextPackSuggestionItem,
    ContextPackUpdate,
)
from app.schemas.fragment import FragmentCreate, TopicCreate
from app.schemas.relation import RelationCreate
from app.services import context_pack_ai_service
from app.services.codex_import_service import CodexImportError, CodexImportUnavailable
from app.services.context_builder import build_context_markdown, export_context_pack, list_context_packs_for_topic
from app.services.fragment_service import create_fragment
from app.services.relation_service import create_relation
from app.services.context_pack_ai_service import suggest_topic_context_pack
from app.services.context_pack_ai_job_service import read_context_pack_suggest_job, start_context_pack_suggest_job
from app.services.topic_service import create_topic
from app.api.context_packs import api_create_context_pack, api_delete_context_pack, api_update_context_pack


def _fragment(db, title: str, topic_id: str, *, status: str = "working", type_: str = "Definition"):
    return create_fragment(
        db,
        FragmentCreate(
            type=type_,
            title=title,
            status=status,
            body=f"{title} body with $x$.",
            topic_id=topic_id,
            origin_classification="user_original",
            exactness="original",
        ),
    )


def test_ai_context_pack_suggestion_is_advisory_and_validated(db_session, monkeypatch):
    db, _tmp_path = db_session
    topic = create_topic(db, TopicCreate(title="AI context topic"))
    definition = _fragment(db, "Core definition", topic.id, type_="Definition")
    theorem = _fragment(db, "Useful theorem", topic.id, type_="Theorem")
    rejected = _fragment(db, "Rejected note", topic.id, status="rejected", type_="Remark")
    create_relation(
        db,
        RelationCreate(
            source_fragment_id=theorem.id,
            relation_kind="depends_on",
            target_fragment_id=definition.id,
        ),
    )

    def fake_suggest(payload, topic_arg, fragments, relations):
        assert topic_arg.id == topic.id
        assert {fragment.id for fragment in fragments} == {definition.id, theorem.id}
        assert rejected.id not in {fragment.id for fragment in fragments}
        assert len(relations) == 1
        return ContextPackSuggestion(
            topic_id=topic.id,
            objective=payload.objective,
            task_prompt=payload.task_prompt,
            items=[
                ContextPackSuggestionItem(
                    fragment_id=definition.id,
                    order_index=0,
                    reason="Needed before the theorem.",
                ),
                ContextPackSuggestionItem(
                    fragment_id=theorem.id,
                    order_index=1,
                    reason="Main usable claim.",
                ),
            ],
            warnings=["The theorem needs review."],
            missing_context_questions=["Is there a proof sketch?"],
        )

    monkeypatch.setattr(context_pack_ai_service, "suggest_context_pack_with_codex", fake_suggest)

    result = suggest_topic_context_pack(
        db,
        ContextPackSuggestRequest(
            topic_id=topic.id,
            objective="Prove the target result.",
            task_prompt="Find gaps.",
        ),
    )

    assert result.available is True
    assert result.suggestion is not None
    assert [item.fragment_id for item in result.suggestion.items] == [definition.id, theorem.id]
    assert db.execute(select(ContextPack)).scalars().all() == []
    assert db.execute(select(Fragment)).scalars().all()
    assert len(db.execute(select(Relation)).scalars().all()) == 1


def test_ai_context_pack_suggestion_reports_codex_failures(db_session, monkeypatch):
    db, _tmp_path = db_session
    topic = create_topic(db, TopicCreate(title="Failure context topic"))
    _fragment(db, "Failure fragment", topic.id)

    def unavailable(*args, **kwargs):
        raise CodexImportUnavailable("Codex CLI is not available on PATH.")

    monkeypatch.setattr(context_pack_ai_service, "suggest_context_pack_with_codex", unavailable)
    unavailable_result = suggest_topic_context_pack(
        db,
        ContextPackSuggestRequest(topic_id=topic.id, objective="Objective", task_prompt="Task"),
    )
    assert unavailable_result.available is False

    def invalid(*args, **kwargs):
        raise CodexImportError("Invalid JSON", logs=["bad output"])

    monkeypatch.setattr(context_pack_ai_service, "suggest_context_pack_with_codex", invalid)
    invalid_result = suggest_topic_context_pack(
        db,
        ContextPackSuggestRequest(topic_id=topic.id, objective="Objective", task_prompt="Task"),
    )
    assert invalid_result.available is True
    assert invalid_result.error == "Invalid JSON"
    assert invalid_result.logs == ["bad output"]


def test_context_pack_save_export_and_topic_history(db_session):
    db, tmp_path = db_session
    topic = create_topic(db, TopicCreate(title="Export context topic"))
    definition = _fragment(db, "Export definition", topic.id, status="draft", type_="Definition")
    theorem = _fragment(db, "Export theorem", topic.id, type_="Theorem")
    outside = _fragment(db, "Outside export fragment", topic.id, type_="Question")
    create_relation(
        db,
        RelationCreate(
            source_fragment_id=theorem.id,
            relation_kind="depends_on",
            target_fragment_id=definition.id,
        ),
    )
    create_relation(
        db,
        RelationCreate(
            source_fragment_id=theorem.id,
            relation_kind="uses",
            target_fragment_id=outside.id,
        ),
    )

    pack = api_create_context_pack(
        ContextPackCreate(
            title="Export context pack",
            topic_id=topic.id,
            objective="Prove the export theorem.",
            task_prompt="Check whether the theorem follows.",
            items=[
                {"fragment_id": definition.id, "order_index": 0, "reason": "Definition first."},
                {"fragment_id": theorem.id, "order_index": 1, "reason": "Main theorem."},
            ],
        ),
        db=db,
    )

    assert pack.topic_id == topic.id
    assert pack.task_prompt == "Check whether the theorem follows."
    assert [stored.id for stored in list_context_packs_for_topic(db, topic.id)] == [pack.id]

    markdown = build_context_markdown(db, pack)
    assert "## Task For AI" in markdown
    assert "Check whether the theorem follows." in markdown
    assert "Export definition body with $x$." in markdown
    assert "Export theorem body with $x$." in markdown
    assert markdown.index("Export definition body with $x$.") < markdown.index(
        "Export theorem body with $x$."
    )
    assert "depends_on" in markdown
    assert "uses" not in markdown
    assert f"`{definition.id}` is `draft`" in markdown

    result = export_context_pack(db, pack)
    assert result.path is not None
    assert (tmp_path / "vault" / "context_packs").exists()


def test_context_pack_delete_removes_record_and_vault_export(db_session):
    db, _tmp_path = db_session
    topic = create_topic(db, TopicCreate(title="Delete context topic"))
    fragment = _fragment(db, "Delete context fragment", topic.id)
    pack = api_create_context_pack(
        ContextPackCreate(
            title="Delete context pack",
            topic_id=topic.id,
            objective="Objective.",
            task_prompt="Task.",
            items=[{"fragment_id": fragment.id, "order_index": 0, "reason": "Needed."}],
        ),
        db=db,
    )
    result = export_context_pack(db, pack)
    assert result.path is not None

    api_delete_context_pack(pack.id, db=db)

    assert db.get(ContextPack, pack.id) is None
    assert not Path(result.path).exists()


def test_context_pack_can_be_renamed(db_session):
    db, _tmp_path = db_session
    topic = create_topic(db, TopicCreate(title="Rename context topic"))
    fragment = _fragment(db, "Rename context fragment", topic.id)
    pack = api_create_context_pack(
        ContextPackCreate(
            title="Old context pack name",
            topic_id=topic.id,
            objective="Objective.",
            task_prompt="Task.",
            items=[{"fragment_id": fragment.id, "order_index": 0, "reason": "Needed."}],
        ),
        db=db,
    )

    updated = api_update_context_pack(
        pack.id,
        ContextPackUpdate(title="New context pack name"),
        db=db,
    )

    assert updated.title == "New context pack name"
    assert db.get(ContextPack, pack.id).title == "New context pack name"


def test_context_pack_suggestion_rejects_unknown_ids(db_session):
    db, _tmp_path = db_session
    topic = create_topic(db, TopicCreate(title="Unknown id topic"))
    _fragment(db, "Known fragment", topic.id)

    with pytest.raises(CodexImportError, match="unknown fragments"):
        context_pack_ai_service._validate_suggestion(
            topic.id,
            list(db.execute(select(Fragment)).scalars()),
            ContextPackSuggestion(
                topic_id=topic.id,
                objective="Objective",
                task_prompt="Task",
                items=[
                    ContextPackSuggestionItem(
                        fragment_id="missing_fragment",
                        order_index=0,
                        reason="Not allowed.",
                    )
                ],
                warnings=[],
                missing_context_questions=[],
            ),
        )


def test_context_pack_suggestion_job_reports_logs_and_does_not_mutate(db_session, monkeypatch):
    db, _tmp_path = db_session
    topic = create_topic(db, TopicCreate(title="Job context topic"))
    fragment = _fragment(db, "Job fragment", topic.id)

    def fake_suggest(payload, topic_arg, fragments, relations, on_log=None):
        if on_log:
            on_log("Choosing useful fragments.")
        return ContextPackSuggestion(
            topic_id=topic_arg.id,
            objective=payload.objective,
            task_prompt=payload.task_prompt,
            items=[
                ContextPackSuggestionItem(
                    fragment_id=fragments[0].id,
                    order_index=0,
                    reason="Only relevant fragment.",
                )
            ],
            warnings=[],
            missing_context_questions=[],
        )

    monkeypatch.setattr(
        "app.services.context_pack_ai_job_service.suggest_context_pack_with_codex",
        fake_suggest,
    )

    started = start_context_pack_suggest_job(
        ContextPackSuggestRequest(topic_id=topic.id, objective="Objective", task_prompt="Task")
    )

    for _ in range(30):
        read = read_context_pack_suggest_job(started.job_id)
        if read.status == "succeeded":
            break
        time.sleep(0.05)
    else:
        pytest.fail("Context pack suggestion job did not finish")

    assert read.result is not None
    assert read.result.suggestion is not None
    assert read.result.suggestion.items[0].fragment_id == fragment.id
    assert read.logs == ["Choosing useful fragments."]
    assert db.execute(select(ContextPack)).scalars().all() == []
