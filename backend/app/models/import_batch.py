from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.fragment import utc_now


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    raw_excerpt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    topic_hint: Mapped[str | None] = mapped_column(String(240))
    citekey: Mapped[str | None] = mapped_column(String(160), index=True)
    locator: Mapped[str | None] = mapped_column(String(200))
    patch_json: Mapped[str | None] = mapped_column(Text)
    warnings_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    commit_result_json: Mapped[str | None] = mapped_column(Text)
    ai_draft_result_json: Mapped[str | None] = mapped_column(Text)
    relation_proposals_json: Mapped[str | None] = mapped_column(Text)
    review_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
