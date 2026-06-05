from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .enums import (
    Exactness,
    FragmentType,
    ImportFragmentStatus,
    OriginClassification,
    RelationKind,
    SourceType,
)


class ResearchPatchMetadata(BaseModel):
    source_kind: str = Field(default="unknown")
    topic_hint: str | None = None
    created_by: str = Field(default="codex_import_agent")
    requires_user_review: Literal[True] = True


class ResearchPatchFragment(BaseModel):
    local_id: str = Field(min_length=1)
    type: FragmentType
    title: str = Field(min_length=1, max_length=300)
    status: ImportFragmentStatus
    origin_classification: OriginClassification
    exactness: Exactness
    body: str = Field(min_length=1)
    assumptions: list[str] = Field(default_factory=list)
    conclusion: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    source_excerpt: str | None = None


class ResearchPatchRelation(BaseModel):
    source: str = Field(min_length=1)
    kind: RelationKind
    target: str = Field(min_length=1)
    confidence: float | None = Field(default=None, ge=0, le=1)


class ResearchPatchSource(BaseModel):
    source_type: SourceType = "unknown"
    title: str | None = None
    authors: str | None = None
    year: int | None = Field(default=None, ge=0, le=3000)
    citekey: str | None = None
    zotero_item_key: str | None = None
    url: str | None = None


class ResearchPatchSourcePointer(BaseModel):
    fragment_local_id: str = Field(min_length=1)
    citekey: str | None = None
    source: ResearchPatchSource | None = None
    locator: str | None = None
    exactness: Exactness
    quote_text: str | None = None
    note: str | None = None


class ResearchPatch(BaseModel):
    patch_type: Literal["ResearchPatch"] = "ResearchPatch"
    metadata: ResearchPatchMetadata = Field(default_factory=ResearchPatchMetadata)
    fragments: list[ResearchPatchFragment] = Field(default_factory=list)
    relations: list[ResearchPatchRelation] = Field(default_factory=list)
    source_pointers: list[ResearchPatchSourcePointer] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_local_references(self) -> "ResearchPatch":
        local_ids = [fragment.local_id for fragment in self.fragments]
        duplicates = sorted({local_id for local_id in local_ids if local_ids.count(local_id) > 1})
        if duplicates:
            raise ValueError(f"Duplicate fragment local_id values: {', '.join(duplicates)}")

        local_id_set = set(local_ids)
        for relation in self.relations:
            if relation.source not in local_id_set and relation.target not in local_id_set:
                raise ValueError(
                    "At least one side of each relation must refer to a patch fragment local_id"
                )
        for pointer in self.source_pointers:
            if pointer.fragment_local_id not in local_id_set:
                raise ValueError(
                    f"Source pointer fragment '{pointer.fragment_local_id}' is not in patch fragments"
                )
            if not pointer.citekey and not pointer.source:
                raise ValueError("Source pointers require either citekey or source metadata")
        return self


class ImportPreview(BaseModel):
    valid: bool
    fragment_count: int
    relation_count: int
    source_pointer_count: int
    warnings: list[str]
    patch: ResearchPatch


class ImportCommitResult(BaseModel):
    fragment_ids: list[str]
    relation_ids: list[str]
    source_pointer_ids: list[str]
    warnings: list[str]
