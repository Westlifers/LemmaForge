from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.fragment import utc_now


class ContextPack(Base):
    __tablename__ = "context_packs"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    topic_id: Mapped[str | None] = mapped_column(
        String(80), ForeignKey("topics.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    task_prompt: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    items: Mapped[list["ContextPackItem"]] = relationship(
        back_populates="context_pack",
        cascade="all, delete-orphan",
        order_by="ContextPackItem.order_index",
    )


class ContextPackItem(Base):
    __tablename__ = "context_pack_items"

    context_pack_id: Mapped[str] = mapped_column(
        String(120), ForeignKey("context_packs.id", ondelete="CASCADE"), primary_key=True
    )
    fragment_id: Mapped[str] = mapped_column(
        String(120), ForeignKey("fragments.id", ondelete="CASCADE"), primary_key=True
    )
    order_index: Mapped[int] = mapped_column(nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)

    context_pack: Mapped[ContextPack] = relationship(back_populates="items")
    fragment = relationship("Fragment")
