from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.fragment import Fragment, Topic, TopicGraphNodePosition, utc_now
from app.models.relation import Relation
from app.schemas.fragment import TopicCreate, TopicGraphLayoutUpdate, TopicGraphRead, TopicUpdate
from app.services.ids import slugify, unique_model_id


def list_topics(db: Session) -> list[Topic]:
    return list(db.execute(select(Topic).order_by(Topic.title)).scalars())


def get_topic(db: Session, topic_id: str) -> Topic | None:
    return db.get(Topic, topic_id)


def create_topic(db: Session, payload: TopicCreate) -> Topic:
    topic = Topic(
        id=unique_model_id(db, Topic, f"topic_{slugify(payload.title)}"),
        title=payload.title,
        description=payload.description,
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic


def update_topic(db: Session, topic: Topic, payload: TopicUpdate) -> Topic:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(topic, key, value)
    db.commit()
    db.refresh(topic)
    return topic


def delete_topic(db: Session, topic: Topic) -> None:
    db.execute(delete(TopicGraphNodePosition).where(TopicGraphNodePosition.topic_id == topic.id))
    db.delete(topic)
    db.commit()


def get_topic_graph(db: Session, topic: Topic) -> TopicGraphRead:
    fragments = list(
        db.execute(
            select(Fragment)
            .where(Fragment.topic_id == topic.id)
            .order_by(Fragment.updated_at.desc())
        ).scalars()
    )
    fragment_ids = {fragment.id for fragment in fragments}
    relations: list[Relation] = []
    if fragment_ids:
        relations = list(
            db.execute(
                select(Relation)
                .where(Relation.source_fragment_id.in_(fragment_ids))
                .where(Relation.target_fragment_id.in_(fragment_ids))
                .order_by(Relation.created_at.desc())
            ).scalars()
        )
    positions = {
        position.fragment_id: {
            "fragment_id": position.fragment_id,
            "x": position.x,
            "y": position.y,
        }
        for position in db.execute(
            select(TopicGraphNodePosition).where(TopicGraphNodePosition.topic_id == topic.id)
        ).scalars()
        if position.fragment_id in fragment_ids
    }
    return TopicGraphRead(
        topic=topic,
        fragments=fragments,
        relations=relations,
        positions=positions,
    )


def update_topic_graph_layout(
    db: Session,
    topic: Topic,
    payload: TopicGraphLayoutUpdate,
) -> TopicGraphRead:
    topic_fragment_ids = set(
        db.execute(select(Fragment.id).where(Fragment.topic_id == topic.id)).scalars()
    )
    unknown_ids = sorted(set(payload.positions) - topic_fragment_ids)
    if unknown_ids:
        raise ValueError(f"Fragments are not assigned to this topic: {', '.join(unknown_ids)}")
    for fragment_id, position in payload.positions.items():
        existing = db.get(TopicGraphNodePosition, (topic.id, fragment_id))
        if existing is None:
            db.add(
                TopicGraphNodePosition(
                    topic_id=topic.id,
                    fragment_id=fragment_id,
                    x=position.x,
                    y=position.y,
                    updated_at=utc_now(),
                )
            )
        else:
            existing.x = position.x
            existing.y = position.y
            existing.updated_at = utc_now()
    db.commit()
    return get_topic_graph(db, topic)
