from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .enums import Exactness, FragmentStatus, FragmentType, OriginClassification


class FragmentCreate(BaseModel):
    type: FragmentType
    title: str = Field(min_length=1, max_length=300)
    status: FragmentStatus = "candidate"
    body: str = Field(min_length=1)
    topic_id: str | None = None
    origin_classification: OriginClassification = "unknown"
    exactness: Exactness = "interpretation"
    source_citekey: str | None = None
    source_locator: str | None = None


class FragmentUpdate(BaseModel):
    type: FragmentType | None = None
    title: str | None = Field(default=None, min_length=1, max_length=300)
    status: FragmentStatus | None = None
    body: str | None = Field(default=None, min_length=1)
    topic_id: str | None = None
    origin_classification: OriginClassification | None = None
    exactness: Exactness | None = None
    change_note: str | None = None


class FragmentBulkUpdate(BaseModel):
    ids: list[str] = Field(min_length=1)
    topic_id: str | None = None
    status: FragmentStatus | None = None
    change_note: str | None = None


class FragmentBulkDeleteResult(BaseModel):
    deleted_ids: list[str]


class FragmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str
    title: str
    status: str
    body: str
    topic_id: str | None
    origin_classification: str
    exactness: str
    current_version_id: str | None
    created_at: datetime
    updated_at: datetime


class FragmentVersionCreate(BaseModel):
    body: str = Field(min_length=1)
    change_note: str | None = None


class FragmentVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    fragment_id: str
    version_number: int
    body: str
    change_note: str | None
    created_at: datetime


class TopicCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    description: str | None = None


class TopicUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=240)
    description: str | None = None


class TopicRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class TopicGraphNodePositionRead(BaseModel):
    fragment_id: str
    x: float
    y: float


class TopicGraphLayoutUpdate(BaseModel):
    positions: dict[str, TopicGraphNodePositionRead]


class TopicGraphRead(BaseModel):
    topic: TopicRead
    fragments: list[FragmentRead]
    relations: list["RelationRead"]
    positions: dict[str, TopicGraphNodePositionRead]


from .relation import RelationRead  # noqa: E402

TopicGraphRead.model_rebuild()
