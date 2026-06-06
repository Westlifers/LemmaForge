from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.context_pack import ContextPackRead
from app.schemas.fragment import TopicCreate, TopicGraphLayoutUpdate, TopicGraphRead, TopicRead, TopicUpdate
from app.services.context_builder import list_context_packs_for_topic
from app.services.topic_service import (
    create_topic,
    delete_topic,
    get_topic_graph,
    get_topic,
    list_topics,
    update_topic_graph_layout,
    update_topic,
)

router = APIRouter(prefix="/api/topics", tags=["topics"])


@router.get("", response_model=list[TopicRead])
def api_list_topics(db: Session = Depends(get_db)):
    return list_topics(db)


@router.post("", response_model=TopicRead, status_code=201)
def api_create_topic(payload: TopicCreate, db: Session = Depends(get_db)):
    return create_topic(db, payload)


@router.get("/{topic_id}", response_model=TopicRead)
def api_get_topic(topic_id: str, db: Session = Depends(get_db)):
    topic = get_topic(db, topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@router.get("/{topic_id}/graph", response_model=TopicGraphRead)
def api_get_topic_graph(topic_id: str, db: Session = Depends(get_db)):
    topic = get_topic(db, topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    return get_topic_graph(db, topic)


@router.get("/{topic_id}/context-packs", response_model=list[ContextPackRead])
def api_list_topic_context_packs(topic_id: str, db: Session = Depends(get_db)):
    topic = get_topic(db, topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    return list_context_packs_for_topic(db, topic_id)


@router.patch("/{topic_id}/graph-layout", response_model=TopicGraphRead)
def api_update_topic_graph_layout(
    topic_id: str,
    payload: TopicGraphLayoutUpdate,
    db: Session = Depends(get_db),
):
    topic = get_topic(db, topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    try:
        return update_topic_graph_layout(db, topic, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/{topic_id}", response_model=TopicRead)
def api_update_topic(topic_id: str, payload: TopicUpdate, db: Session = Depends(get_db)):
    topic = get_topic(db, topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    return update_topic(db, topic, payload)


@router.delete("/{topic_id}", status_code=204)
def api_delete_topic(topic_id: str, db: Session = Depends(get_db)):
    topic = get_topic(db, topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")
    delete_topic(db, topic)
    return None
