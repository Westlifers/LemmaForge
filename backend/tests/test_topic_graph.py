from __future__ import annotations

import pytest

from app.models.fragment import Fragment, TopicGraphNodePosition
from app.models.relation import Relation
from app.schemas.fragment import FragmentCreate, TopicCreate, TopicGraphLayoutUpdate
from app.schemas.relation import RelationCreate, RelationUpdate
from app.services.fragment_service import create_fragment, delete_fragment
from app.services.relation_service import create_relation, update_relation
from app.services.topic_service import create_topic, delete_topic, get_topic_graph, update_topic_graph_layout


def _fragment(db, title: str, topic_id: str | None = None) -> Fragment:
    return create_fragment(
        db,
        FragmentCreate(
            type="Definition",
            title=title,
            status="working",
            body=f"{title} body.",
            topic_id=topic_id,
            origin_classification="user_original",
            exactness="original",
        ),
    )


def test_topic_graph_returns_internal_fragments_relations_and_positions(db_session):
    db, _tmp_path = db_session
    topic = create_topic(db, TopicCreate(title="Graph topic"))
    first = _fragment(db, "First graph fragment", topic.id)
    second = _fragment(db, "Second graph fragment", topic.id)
    outside = _fragment(db, "Outside graph fragment")
    internal = create_relation(
        db,
        RelationCreate(
            source_fragment_id=first.id,
            relation_kind="depends_on",
            target_fragment_id=second.id,
        ),
    )
    create_relation(
        db,
        RelationCreate(
            source_fragment_id=first.id,
            relation_kind="depends_on",
            target_fragment_id=outside.id,
        ),
    )
    update_topic_graph_layout(
        db,
        topic,
        TopicGraphLayoutUpdate(
            positions={
                first.id: {"fragment_id": first.id, "x": 120, "y": 80},
                second.id: {"fragment_id": second.id, "x": 360, "y": 120},
            }
        ),
    )

    graph = get_topic_graph(db, topic)

    assert {fragment.id for fragment in graph.fragments} == {first.id, second.id}
    assert [relation.id for relation in graph.relations] == [internal.id]
    assert graph.positions[first.id].x == 120
    assert graph.positions[second.id].y == 120


def test_topic_graph_layout_rejects_fragments_outside_topic(db_session):
    db, _tmp_path = db_session
    topic = create_topic(db, TopicCreate(title="Layout topic"))
    outside = _fragment(db, "Outside layout fragment")

    with pytest.raises(ValueError):
        update_topic_graph_layout(
            db,
            topic,
            TopicGraphLayoutUpdate(
                positions={outside.id: {"fragment_id": outside.id, "x": 0, "y": 0}}
            ),
        )


def test_relation_update_can_reconnect_source_and_target(db_session):
    db, _tmp_path = db_session
    source = _fragment(db, "Original source")
    target = _fragment(db, "Original target")
    next_source = _fragment(db, "Next source")
    next_target = _fragment(db, "Next target")
    relation = create_relation(
        db,
        RelationCreate(
            source_fragment_id=source.id,
            relation_kind="depends_on",
            target_fragment_id=target.id,
        ),
    )

    updated = update_relation(
        db,
        relation,
        RelationUpdate(
            source_fragment_id=next_source.id,
            relation_kind="refines",
            target_fragment_id=next_target.id,
            confidence=0.75,
        ),
    )

    assert updated.source_fragment_id == next_source.id
    assert updated.target_fragment_id == next_target.id
    assert updated.relation_kind == "refines"
    assert updated.confidence == 0.75


def test_topic_graph_layout_is_removed_when_fragment_or_topic_is_deleted(db_session):
    db, _tmp_path = db_session
    topic = create_topic(db, TopicCreate(title="Cleanup graph topic"))
    fragment = _fragment(db, "Cleanup graph fragment", topic.id)
    update_topic_graph_layout(
        db,
        topic,
        TopicGraphLayoutUpdate(
            positions={fragment.id: {"fragment_id": fragment.id, "x": 24, "y": 48}}
        ),
    )

    delete_fragment(db, fragment)

    assert db.get(TopicGraphNodePosition, (topic.id, fragment.id)) is None

    next_fragment = _fragment(db, "Cleanup topic fragment", topic.id)
    update_topic_graph_layout(
        db,
        topic,
        TopicGraphLayoutUpdate(
            positions={next_fragment.id: {"fragment_id": next_fragment.id, "x": 24, "y": 48}}
        ),
    )
    delete_topic(db, topic)

    assert db.get(TopicGraphNodePosition, (topic.id, next_fragment.id)) is None
    assert db.query(Relation).count() == 0
