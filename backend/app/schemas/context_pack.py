from __future__ import annotations

from datetime import datetime
from typing import Literal

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
    topic_id: str | None = None
    objective: str = Field(min_length=1)
    task_prompt: str | None = None
    body: str = ""
    items: list[ContextPackItemCreate] = Field(default_factory=list)


class ContextPackUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    objective: str | None = Field(default=None, min_length=1)
    task_prompt: str | None = None
    body: str | None = None


class ContextPackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    topic_id: str | None
    title: str
    objective: str
    task_prompt: str | None
    body: str
    created_at: datetime
    updated_at: datetime
    items: list[ContextPackItemRead] = Field(default_factory=list)


class ContextPackExport(BaseModel):
    context_pack_id: str
    markdown: str
    path: str | None = None


class ContextPackSuggestionItem(BaseModel):
    fragment_id: str
    order_index: int = Field(ge=0)
    reason: str = Field(min_length=1)


class ContextPackSuggestion(BaseModel):
    topic_id: str
    objective: str
    task_prompt: str
    items: list[ContextPackSuggestionItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    missing_context_questions: list[str] = Field(default_factory=list)


class ContextPackSuggestRequest(BaseModel):
    topic_id: str
    objective: str = Field(min_length=1)
    task_prompt: str = Field(min_length=1)
    timeout_seconds: int = Field(default=900, ge=30, le=1800)


class ContextPackSuggestResult(BaseModel):
    available: bool = True
    suggestion: ContextPackSuggestion | None = None
    error: str | None = None
    logs: list[str] = Field(default_factory=list)


class ContextPackSuggestJobRead(BaseModel):
    job_id: str
    status: Literal["queued", "running", "succeeded", "failed"]
    logs: list[str] = Field(default_factory=list)
    result: ContextPackSuggestResult | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime
