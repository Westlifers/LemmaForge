from __future__ import annotations

from sqlalchemy import select

from app.models.context_pack import ContextPack, ContextPackItem
from app.models.fragment import Fragment
from app.models.relation import Relation
from app.models.source import Source, SourcePointer
from app.schemas.fragment import FragmentCreate, FragmentUpdate, TopicCreate
from app.schemas.relation import RelationCreate
from app.schemas.research_patch import ResearchPatch
from app.services.fragment_service import create_fragment, delete_fragment, list_fragments, update_fragment
from app.services.import_service import commit_patch
from app.services.markdown_vault import fragment_markdown_path
from app.services.relation_service import create_relation
from app.services.topic_service import create_topic


def patch_with_relation_and_pointer() -> ResearchPatch:
    return ResearchPatch.model_validate(
        {
            "patch_type": "ResearchPatch",
            "metadata": {
                "source_kind": "reading_note",
                "topic_hint": "Quantaloids",
                "created_by": "codex_import_agent",
                "requires_user_review": True,
            },
            "fragments": [
                {
                    "local_id": "def_good_quantaloid_candidate",
                    "type": "Definition",
                    "title": "Good quantaloid",
                    "status": "candidate",
                    "origin_classification": "mixed",
                    "exactness": "interpretation",
                    "body": "A good quantaloid is a provisional working definition.",
                    "assumptions": [],
                    "conclusion": None,
                    "confidence": 0.78,
                    "source_excerpt": "A good quantaloid is ...",
                },
                {
                    "local_id": "remark_good_quantaloid",
                    "type": "Remark",
                    "title": "Good quantaloid is provisional",
                    "status": "candidate",
                    "origin_classification": "user_original",
                    "exactness": "original",
                    "body": "The name good quantaloid is provisional.",
                    "assumptions": [],
                    "conclusion": None,
                    "confidence": 0.9,
                    "source_excerpt": None,
                },
            ],
            "relations": [
                {
                    "source": "remark_good_quantaloid",
                    "kind": "depends_on",
                    "target": "def_good_quantaloid_candidate",
                    "confidence": 0.7,
                }
            ],
            "source_pointers": [
                {
                    "fragment_local_id": "def_good_quantaloid_candidate",
                    "citekey": "StreetWalters1978",
                    "locator": "p. 354",
                    "exactness": "paraphrase",
                    "quote_text": None,
                    "note": "Imported from a reading excerpt.",
                }
            ],
            "warnings": ["The source text appears provisional. Do not mark as stable."],
        }
    )


def test_importing_patch_creates_fragments_relations_pointers_and_markdown(db_session):
    db, tmp_path = db_session
    result = commit_patch(db, patch_with_relation_and_pointer())

    assert len(result.fragment_ids) == 2
    assert len(result.relation_ids) == 1
    assert len(result.source_pointer_ids) == 1

    fragments = list(db.execute(select(Fragment)).scalars())
    relations = list(db.execute(select(Relation)).scalars())
    pointers = list(db.execute(select(SourcePointer)).scalars())

    assert {fragment.status for fragment in fragments} == {"candidate"}
    assert relations[0].relation_kind == "depends_on"
    assert pointers[0].locator == "p. 354"

    markdown_files = list((tmp_path / "vault" / "fragments").glob("*.md"))
    assert len(markdown_files) == 2
    assert "# Good quantaloid" in markdown_files[0].read_text(encoding="utf-8") or (
        "# Good quantaloid" in markdown_files[1].read_text(encoding="utf-8")
    )


def test_fragment_version_is_created_on_update(db_session):
    db, _tmp_path = db_session
    fragment = create_fragment(
        db,
        FragmentCreate(
            type="Definition",
            title="Versioned definition",
            status="working",
            body="Initial body.",
            origin_classification="user_original",
            exactness="original",
        ),
    )

    updated = update_fragment(
        db,
        fragment,
        FragmentUpdate(body="Updated body.", change_note="Clarified the definition."),
    )

    assert updated.body == "Updated body."
    assert len(updated.versions) == 2
    assert updated.versions[-1].change_note == "Clarified the definition."


def test_fragment_can_be_created_as_draft_and_filtered_by_topic(db_session):
    db, _tmp_path = db_session
    topic = create_topic(db, TopicCreate(title="Canonical extensions"))

    fragment = create_fragment(
        db,
        FragmentCreate(
            type="Definition",
            title="Draft canonical extension",
            status="draft",
            body="A canonical extension draft awaits review.",
            topic_id=topic.id,
            origin_classification="user_original",
            exactness="original",
        ),
    )

    assert fragment.status == "draft"
    assert fragment.topic_id == topic.id
    assert list_fragments(db, status="draft", topic_id=topic.id)[0].id == fragment.id


def test_delete_fragment_removes_related_records_and_markdown(db_session):
    db, _tmp_path = db_session
    fragment = create_fragment(
        db,
        FragmentCreate(
            type="Definition",
            title="Delete me carefully",
            status="rejected",
            body="This fragment should be removed.",
            origin_classification="user_original",
            exactness="original",
        ),
    )
    target = create_fragment(
        db,
        FragmentCreate(
            type="Remark",
            title="Keep me",
            status="working",
            body="This fragment should remain.",
            origin_classification="user_original",
            exactness="original",
        ),
    )
    create_relation(
        db,
        RelationCreate(
            source_fragment_id=fragment.id,
            relation_kind="depends_on",
            target_fragment_id=target.id,
        ),
    )
    source = Source(id="source_delete_test", source_type="paper", title="Delete test source")
    db.add(source)
    db.flush()
    db.add(
        SourcePointer(
            id="pointer_delete_test",
            fragment_id=fragment.id,
            source_id=source.id,
            exactness="quote",
        )
    )
    context_pack = ContextPack(
        id="ctx_delete_test",
        title="Delete test context",
        objective="Check delete cleanup.",
        body="",
    )
    db.add(context_pack)
    db.add(
        ContextPackItem(
            context_pack_id=context_pack.id,
            fragment_id=fragment.id,
            order_index=0,
            reason="Cleanup test.",
        )
    )
    db.commit()

    markdown_path = fragment_markdown_path(fragment)
    assert markdown_path.exists()

    delete_fragment(db, fragment)

    assert db.get(Fragment, fragment.id) is None
    assert db.get(Fragment, target.id) is not None
    assert db.execute(select(Relation)).scalars().all() == []
    assert db.execute(select(SourcePointer)).scalars().all() == []
    assert db.execute(select(ContextPackItem)).scalars().all() == []
    assert not markdown_path.exists()
