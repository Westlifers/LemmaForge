from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.fragment import utc_now


class ResearchProblem(Base):
    __tablename__ = "research_problems"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    current_formulation: Mapped[str | None] = mapped_column(Text)
    motivation: Mapped[str | None] = mapped_column(Text)
    why_it_matters: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    topic_links: Mapped[list["ProblemTopicLink"]] = relationship(
        back_populates="problem",
        cascade="all, delete-orphan",
        order_by="ProblemTopicLink.created_at",
    )
    fragment_links: Mapped[list["ProblemFragmentLink"]] = relationship(
        back_populates="problem",
        cascade="all, delete-orphan",
        order_by="ProblemFragmentLink.created_at",
    )
    attempts: Mapped[list["Attempt"]] = relationship(
        back_populates="problem",
        cascade="all, delete-orphan",
        order_by="Attempt.updated_at.desc()",
    )
    graph_positions: Mapped[list["ProblemGraphNodePosition"]] = relationship(
        back_populates="problem",
        cascade="all, delete-orphan",
    )


class ProblemTopicLink(Base):
    __tablename__ = "problem_topic_links"
    __table_args__ = (UniqueConstraint("problem_id", "topic_id", name="uq_problem_topic_link"),)
    __mapper_args__ = {"confirm_deleted_rows": False}

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    problem_id: Mapped[str] = mapped_column(
        String(120), ForeignKey("research_problems.id", ondelete="CASCADE"), nullable=False, index=True
    )
    topic_id: Mapped[str] = mapped_column(
        String(80), ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    problem: Mapped[ResearchProblem] = relationship(back_populates="topic_links")
    topic = relationship("Topic")


class ProblemFragmentLink(Base):
    __tablename__ = "problem_fragment_links"
    __table_args__ = (
        UniqueConstraint("problem_id", "fragment_id", name="uq_problem_fragment_link"),
    )
    __mapper_args__ = {"confirm_deleted_rows": False}

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    problem_id: Mapped[str] = mapped_column(
        String(120), ForeignKey("research_problems.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fragment_id: Mapped[str] = mapped_column(
        String(120), ForeignKey("fragments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    problem: Mapped[ResearchProblem] = relationship(back_populates="fragment_links")
    fragment = relationship("Fragment")


class ProblemGraphNodePosition(Base):
    __tablename__ = "problem_graph_node_positions"

    problem_id: Mapped[str] = mapped_column(
        String(120), ForeignKey("research_problems.id", ondelete="CASCADE"), primary_key=True
    )
    node_key: Mapped[str] = mapped_column(String(180), primary_key=True)
    x: Mapped[float] = mapped_column(nullable=False)
    y: Mapped[float] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    problem: Mapped[ResearchProblem] = relationship(back_populates="graph_positions")


class Attempt(Base):
    __tablename__ = "attempts"
    __mapper_args__ = {"confirm_deleted_rows": False}

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    problem_id: Mapped[str] = mapped_column(
        String(120), ForeignKey("research_problems.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    strategy: Mapped[str] = mapped_column(Text, nullable=False)
    expected_outcome: Mapped[str | None] = mapped_column(Text)
    result_summary: Mapped[str | None] = mapped_column(Text)
    failure_reason: Mapped[str | None] = mapped_column(Text)
    next_step: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    problem: Mapped[ResearchProblem] = relationship(back_populates="attempts")
    fragment_links: Mapped[list["AttemptFragmentLink"]] = relationship(
        back_populates="attempt",
        cascade="all, delete-orphan",
        order_by="AttemptFragmentLink.created_at",
    )
    graph_positions: Mapped[list["AttemptGraphNodePosition"]] = relationship(
        back_populates="attempt",
        cascade="all, delete-orphan",
    )


class AttemptGraphNodePosition(Base):
    __tablename__ = "attempt_graph_node_positions"

    attempt_id: Mapped[str] = mapped_column(
        String(120), ForeignKey("attempts.id", ondelete="CASCADE"), primary_key=True
    )
    node_key: Mapped[str] = mapped_column(String(180), primary_key=True)
    x: Mapped[float] = mapped_column(nullable=False)
    y: Mapped[float] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    attempt: Mapped[Attempt] = relationship(back_populates="graph_positions")


class AttemptFragmentLink(Base):
    __tablename__ = "attempt_fragment_links"
    __table_args__ = (
        UniqueConstraint("attempt_id", "fragment_id", name="uq_attempt_fragment_link"),
    )
    __mapper_args__ = {"confirm_deleted_rows": False}

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    attempt_id: Mapped[str] = mapped_column(
        String(120), ForeignKey("attempts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fragment_id: Mapped[str] = mapped_column(
        String(120), ForeignKey("fragments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    attempt: Mapped[Attempt] = relationship(back_populates="fragment_links")
    fragment = relationship("Fragment")
