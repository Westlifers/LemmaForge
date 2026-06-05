from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.fragment import Topic
from app.schemas.fragment import TopicCreate, TopicUpdate
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
    db.delete(topic)
    db.commit()

