from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .research_patch import ImportCommitResult, ResearchPatch

ImportBatchStatus = Literal["draft", "validated", "committed", "rejected"]


class ImportBatchCreate(BaseModel):
    raw_excerpt: str = ""
    topic_hint: str | None = None
    citekey: str | None = None
    locator: str | None = None
    patch: ResearchPatch | None = None
    review_note: str | None = None

    @model_validator(mode="after")
    def require_content(self) -> "ImportBatchCreate":
        if not self.raw_excerpt.strip() and self.patch is None:
            raise ValueError("Import batch requires raw_excerpt or patch")
        return self


class ImportBatchUpdate(BaseModel):
    raw_excerpt: str | None = None
    topic_hint: str | None = None
    citekey: str | None = None
    locator: str | None = None
    patch: ResearchPatch | None = None
    status: ImportBatchStatus | None = None
    review_note: str | None = None


class ImportBatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    raw_excerpt: str
    topic_hint: str | None
    citekey: str | None
    locator: str | None
    patch: ResearchPatch | None
    warnings: list[str]
    commit_result: ImportCommitResult | None
    review_note: str | None
    created_at: datetime
    updated_at: datetime
    reviewed_at: datetime | None


class DuplicateSuggestion(BaseModel):
    local_id: str
    fragment_id: str
    title: str
    type: str
    status: str
    origin_classification: str
    exactness: str
    score: float = Field(ge=0, le=1)
    reason: str


class ImportBatchSuggestionRead(BaseModel):
    batch_id: str
    suggestions: list[DuplicateSuggestion]

