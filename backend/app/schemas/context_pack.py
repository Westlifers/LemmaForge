from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ContextPackItemCreate(BaseModel):
    fragment_id: str
    order_index: int = Field(ge=0)
    reason: str | None = None


class ContextPackItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    context_pack_id: str
    fragment_id: str
    order_index: int
    reason: str | None


class ContextPackCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    objective: str = Field(min_length=1)
    body: str = ""
    items: list[ContextPackItemCreate] = Field(default_factory=list)


class ContextPackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    objective: str
    body: str
    created_at: datetime
    updated_at: datetime
    items: list[ContextPackItemRead] = Field(default_factory=list)


class ContextPackExport(BaseModel):
    context_pack_id: str
    markdown: str
    path: str | None = None

