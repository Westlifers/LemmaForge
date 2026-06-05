from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .enums import Exactness, SourceType


class SourceCreate(BaseModel):
    source_type: SourceType = "unknown"
    title: str = Field(min_length=1, max_length=400)
    authors: str | None = None
    year: int | None = Field(default=None, ge=0, le=3000)
    citekey: str | None = None
    zotero_item_key: str | None = None
    url: str | None = None


class SourceUpdate(BaseModel):
    source_type: SourceType | None = None
    title: str | None = Field(default=None, min_length=1, max_length=400)
    authors: str | None = None
    year: int | None = Field(default=None, ge=0, le=3000)
    citekey: str | None = None
    zotero_item_key: str | None = None
    url: str | None = None


class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_type: str
    title: str
    authors: str | None
    year: int | None
    citekey: str | None
    zotero_item_key: str | None
    url: str | None
    created_at: datetime
    updated_at: datetime


class SourcePointerCreate(BaseModel):
    fragment_id: str
    source_id: str
    locator: str | None = None
    exactness: Exactness
    quote_text: str | None = None
    note: str | None = None


class SourcePointerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    fragment_id: str
    source_id: str
    locator: str | None
    exactness: str
    quote_text: str | None
    note: str | None

