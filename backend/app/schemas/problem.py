from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.fragment import FragmentRead, TopicRead
from app.schemas.relation import RelationRead


ProblemStatus = Literal["open", "active", "blocked", "partially_solved", "solved", "abandoned"]
AttemptStatus = Literal["planned", "in_progress", "succeeded", "failed", "blocked", "superseded"]
ProblemFragmentRole = Literal[
    "main_question",
    "active_definition",
    "candidate_definition",
    "claim",
    "proof",
    "example",
    "counterexample",
    "background",
    "source_note",
    "gap",
    "result",
    "notation",
    "other",
]
AttemptFragmentRole = Literal[
    "input",
    "assumption",
    "produced",
    "blocked_by",
    "motivated",
    "refuted_by",
    "needs_revision",
    "other",
]


class ResearchProblemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    status: ProblemStatus = "open"
    objective: str = Field(min_length=1)
    current_formulation: str | None = None
    motivation: str | None = None
    why_it_matters: str | None = None


class ResearchProblemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    status: ProblemStatus | None = None
    objective: str | None = Field(default=None, min_length=1)
    current_formulation: str | None = None
    motivation: str | None = None
    why_it_matters: str | None = None


class ProblemTopicLinkCreate(BaseModel):
    topic_id: str = Field(min_length=1)


class ProblemTopicLinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    problem_id: str
    topic_id: str
    created_at: datetime
    topic: TopicRead | None = None


class ProblemFragmentLinkCreate(BaseModel):
    fragment_id: str = Field(min_length=1)
    role: ProblemFragmentRole = "other"
    note: str | None = None


class ProblemFragmentLinkUpdate(BaseModel):
    role: ProblemFragmentRole | None = None
    note: str | None = None


class ProblemFragmentLinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    problem_id: str
    fragment_id: str
    role: str
    note: str | None
    created_at: datetime
    fragment: FragmentRead | None = None


class ProblemGraphNodePositionRead(BaseModel):
    node_key: str
    x: float
    y: float


class ProblemGraphLayoutUpdate(BaseModel):
    positions: dict[str, ProblemGraphNodePositionRead]


class AttemptCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    status: AttemptStatus = "planned"
    strategy: str = Field(min_length=1)
    expected_outcome: str | None = None
    result_summary: str | None = None
    failure_reason: str | None = None
    next_step: str | None = None


class AttemptUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    status: AttemptStatus | None = None
    strategy: str | None = Field(default=None, min_length=1)
    expected_outcome: str | None = None
    result_summary: str | None = None
    failure_reason: str | None = None
    next_step: str | None = None


class AttemptFragmentLinkCreate(BaseModel):
    fragment_id: str = Field(min_length=1)
    role: AttemptFragmentRole = "other"
    note: str | None = None


class AttemptFragmentLinkUpdate(BaseModel):
    role: AttemptFragmentRole | None = None
    note: str | None = None


class AttemptFragmentLinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    attempt_id: str
    fragment_id: str
    role: str
    note: str | None
    created_at: datetime
    fragment: FragmentRead | None = None


class AttemptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    problem_id: str
    title: str
    status: str
    strategy: str
    expected_outcome: str | None
    result_summary: str | None
    failure_reason: str | None
    next_step: str | None
    created_at: datetime
    updated_at: datetime
    fragment_links: list[AttemptFragmentLinkRead] = Field(default_factory=list)


class ResearchProblemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    status: str
    objective: str
    current_formulation: str | None
    motivation: str | None
    why_it_matters: str | None
    created_at: datetime
    updated_at: datetime
    topic_links: list[ProblemTopicLinkRead] = Field(default_factory=list)
    fragment_links: list[ProblemFragmentLinkRead] = Field(default_factory=list)
    attempts: list[AttemptRead] = Field(default_factory=list)


class ProblemWorkspaceRead(BaseModel):
    problem: ResearchProblemRead
    topic_links: list[ProblemTopicLinkRead] = Field(default_factory=list)
    fragment_links: list[ProblemFragmentLinkRead] = Field(default_factory=list)
    relations: list[RelationRead] = Field(default_factory=list)
    attempts: list[AttemptRead] = Field(default_factory=list)
    positions: dict[str, ProblemGraphNodePositionRead] = Field(default_factory=dict)


class AttemptWorkspaceRead(BaseModel):
    attempt: AttemptRead
    problem: ResearchProblemRead
    fragment_links: list[AttemptFragmentLinkRead] = Field(default_factory=list)
    relations: list[RelationRead] = Field(default_factory=list)


class ProblemSuggestedFragmentRole(BaseModel):
    fragment_id: str
    role: ProblemFragmentRole
    note: str | None = None


class ProblemSummaryProposal(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    objective: str = Field(min_length=1)
    current_formulation: str | None = None
    motivation: str | None = None
    why_it_matters: str | None = None
    suggested_fragment_roles: list[ProblemSuggestedFragmentRole] = Field(default_factory=list)
    open_gaps: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ProblemSummaryRequest(BaseModel):
    topic_ids: list[str] = Field(default_factory=list)
    fragment_ids: list[str] = Field(default_factory=list)
    title_hint: str | None = None
    objective_hint: str | None = None
    timeout_seconds: int = Field(default=900, ge=30, le=1800)

    @model_validator(mode="after")
    def require_context(self) -> "ProblemSummaryRequest":
        if not self.topic_ids and not self.fragment_ids:
            raise ValueError("Select at least one topic or fragment for problem summary")
        return self


class ProblemSummaryResult(BaseModel):
    available: bool = True
    proposal: ProblemSummaryProposal | None = None
    error: str | None = None
    logs: list[str] = Field(default_factory=list)


class ProblemSummaryJobRead(BaseModel):
    job_id: str
    status: Literal["queued", "running", "succeeded", "failed"]
    logs: list[str] = Field(default_factory=list)
    result: ProblemSummaryResult | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime
