from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    fragments: Mapped[list["Fragment"]] = relationship(back_populates="topic")


class Fragment(Base):
    __tablename__ = "fragments"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    topic_id: Mapped[str | None] = mapped_column(String(80), ForeignKey("topics.id"), nullable=True)
    origin_classification: Mapped[str] = mapped_column(String(40), nullable=False)
    exactness: Mapped[str] = mapped_column(String(40), nullable=False)
    current_version_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    topic: Mapped[Topic | None] = relationship(back_populates="fragments")
    versions: Mapped[list["FragmentVersion"]] = relationship(
        back_populates="fragment",
        cascade="all, delete-orphan",
        order_by="FragmentVersion.version_number",
    )
    outgoing_relations = relationship(
        "Relation",
        back_populates="source_fragment",
        cascade="all, delete-orphan",
        foreign_keys="Relation.source_fragment_id",
    )
    incoming_relations = relationship(
        "Relation",
        back_populates="target_fragment",
        cascade="all, delete-orphan",
        foreign_keys="Relation.target_fragment_id",
    )
    source_pointers = relationship(
        "SourcePointer",
        back_populates="fragment",
        cascade="all, delete-orphan",
    )


class FragmentVersion(Base):
    __tablename__ = "fragment_versions"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    fragment_id: Mapped[str] = mapped_column(
        String(120), ForeignKey("fragments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    change_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    fragment: Mapped[Fragment] = relationship(back_populates="versions")


class TopicGraphNodePosition(Base):
    __tablename__ = "topic_graph_node_positions"

    topic_id: Mapped[str] = mapped_column(
        String(80), ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True
    )
    fragment_id: Mapped[str] = mapped_column(
        String(120), ForeignKey("fragments.id", ondelete="CASCADE"), primary_key=True
    )
    x: Mapped[float] = mapped_column(nullable=False)
    y: Mapped[float] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
