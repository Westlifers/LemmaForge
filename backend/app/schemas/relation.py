from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .enums import RelationKind


class RelationCreate(BaseModel):
    source_fragment_id: str = Field(min_length=1)
    relation_kind: RelationKind
    target_fragment_id: str = Field(min_length=1)
    confidence: float | None = Field(default=None, ge=0, le=1)


class RelationUpdate(BaseModel):
    relation_kind: RelationKind | None = None
    target_fragment_id: str | None = Field(default=None, min_length=1)
    confidence: float | None = Field(default=None, ge=0, le=1)


class RelationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_fragment_id: str
    relation_kind: str
    target_fragment_id: str
    confidence: float | None
    created_at: datetime
