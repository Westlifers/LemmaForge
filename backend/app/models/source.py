from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.fragment import utc_now


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(400), nullable=False)
    authors: Mapped[str | None] = mapped_column(Text)
    year: Mapped[int | None] = mapped_column(Integer)
    citekey: Mapped[str | None] = mapped_column(String(160), unique=True, index=True)
    zotero_item_key: Mapped[str | None] = mapped_column(String(80))
    url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    pointers: Mapped[list["SourcePointer"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )


class SourcePointer(Base):
    __tablename__ = "source_pointers"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    fragment_id: Mapped[str] = mapped_column(
        String(120), ForeignKey("fragments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_id: Mapped[str] = mapped_column(
        String(120), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    locator: Mapped[str | None] = mapped_column(String(200))
    exactness: Mapped[str] = mapped_column(String(40), nullable=False)
    quote_text: Mapped[str | None] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)

    fragment = relationship("Fragment", back_populates="source_pointers")
    source = relationship("Source", back_populates="pointers")

