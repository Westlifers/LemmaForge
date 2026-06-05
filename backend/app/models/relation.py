from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.fragment import utc_now


class Relation(Base):
    __tablename__ = "relations"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    source_fragment_id: Mapped[str] = mapped_column(
        String(120), ForeignKey("fragments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relation_kind: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    target_fragment_id: Mapped[str] = mapped_column(
        String(120), ForeignKey("fragments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    confidence: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    source_fragment = relationship(
        "Fragment", back_populates="outgoing_relations", foreign_keys=[source_fragment_id]
    )
    target_fragment = relationship(
        "Fragment", back_populates="incoming_relations", foreign_keys=[target_fragment_id]
    )

