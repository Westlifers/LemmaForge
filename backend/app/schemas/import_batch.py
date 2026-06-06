from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .research_patch import ImportCommitResult, ImportPreview, ResearchPatch

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
    ai_draft_result: "AIDraftCreationResult | None" = None
    relation_proposals: list["AIRelationProposal"] = Field(default_factory=list)
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


class AIExtractRequest(BaseModel):
    raw_excerpt: str = Field(min_length=1)
    topic_hint: str | None = None
    citekey: str | None = None
    locator: str | None = None
    source_kind: str = "conversation"
    timeout_seconds: int = Field(default=480, ge=30, le=1200)


class AIExtractResult(BaseModel):
    available: bool
    preview: "ImportPreview | None" = None
    batch: ImportBatchRead | None = None
    error: str | None = None
    logs: list[str] = Field(default_factory=list)


class AIExtractJobRead(BaseModel):
    job_id: str
    status: Literal["queued", "running", "succeeded", "failed"]
    logs: list[str] = Field(default_factory=list)
    result: AIExtractResult | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime


class AICreateDraftsRequest(BaseModel):
    batch_id: str | None = None
    patch: ResearchPatch | None = None
    raw_excerpt: str = ""
    topic_hint: str | None = None
    citekey: str | None = None
    locator: str | None = None
    selected_local_ids: list[str] | None = None

    @model_validator(mode="after")
    def require_batch_or_patch(self) -> "AICreateDraftsRequest":
        if not self.batch_id and self.patch is None:
            raise ValueError("AI draft creation requires batch_id or patch")
        return self


class AIDraftCreationResult(BaseModel):
    batch_id: str
    fragment_ids: list[str]
    local_to_fragment_id: dict[str, str]
    source_pointer_ids: list[str]
    relation_proposals: list["AIRelationProposal"]
    warnings: list[str]


class AIRelationProposal(BaseModel):
    proposal_id: str
    source: str
    kind: str
    target: str
    confidence: float | None = Field(default=None, ge=0, le=1)
    source_fragment_id: str | None = None
    target_fragment_id: str | None = None
    applied_relation_id: str | None = None


class AIApplyRelationsRequest(BaseModel):
    proposal_ids: list[str] = Field(default_factory=list)


class AIApplyRelationsResult(BaseModel):
    batch_id: str
    relation_ids: list[str]
    relation_proposals: list[AIRelationProposal]
    warnings: list[str] = Field(default_factory=list)
