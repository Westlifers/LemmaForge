"""Add research problems."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0006_research_problems"
down_revision = "0005_context_pack_topic_ai"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "research_problems",
        sa.Column("id", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("current_formulation", sa.Text(), nullable=True),
        sa.Column("motivation", sa.Text(), nullable=True),
        sa.Column("why_it_matters", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_research_problems_title", "research_problems", ["title"])
    op.create_index("ix_research_problems_status", "research_problems", ["status"])

    op.create_table(
        "problem_topic_links",
        sa.Column("id", sa.String(length=120), nullable=False),
        sa.Column("problem_id", sa.String(length=120), nullable=False),
        sa.Column("topic_id", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["problem_id"], ["research_problems.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("problem_id", "topic_id", name="uq_problem_topic_link"),
    )
    op.create_index("ix_problem_topic_links_problem_id", "problem_topic_links", ["problem_id"])
    op.create_index("ix_problem_topic_links_topic_id", "problem_topic_links", ["topic_id"])

    op.create_table(
        "problem_fragment_links",
        sa.Column("id", sa.String(length=120), nullable=False),
        sa.Column("problem_id", sa.String(length=120), nullable=False),
        sa.Column("fragment_id", sa.String(length=120), nullable=False),
        sa.Column("role", sa.String(length=60), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["problem_id"], ["research_problems.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["fragment_id"], ["fragments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("problem_id", "fragment_id", name="uq_problem_fragment_link"),
    )
    op.create_index("ix_problem_fragment_links_problem_id", "problem_fragment_links", ["problem_id"])
    op.create_index("ix_problem_fragment_links_fragment_id", "problem_fragment_links", ["fragment_id"])
    op.create_index("ix_problem_fragment_links_role", "problem_fragment_links", ["role"])

    op.create_table(
        "problem_graph_node_positions",
        sa.Column("problem_id", sa.String(length=120), nullable=False),
        sa.Column("node_key", sa.String(length=180), nullable=False),
        sa.Column("x", sa.Float(), nullable=False),
        sa.Column("y", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["problem_id"], ["research_problems.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("problem_id", "node_key"),
    )

    op.create_table(
        "attempts",
        sa.Column("id", sa.String(length=120), nullable=False),
        sa.Column("problem_id", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("strategy", sa.Text(), nullable=False),
        sa.Column("expected_outcome", sa.Text(), nullable=True),
        sa.Column("result_summary", sa.Text(), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("next_step", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["problem_id"], ["research_problems.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_attempts_problem_id", "attempts", ["problem_id"])
    op.create_index("ix_attempts_title", "attempts", ["title"])
    op.create_index("ix_attempts_status", "attempts", ["status"])

    op.create_table(
        "attempt_fragment_links",
        sa.Column("id", sa.String(length=120), nullable=False),
        sa.Column("attempt_id", sa.String(length=120), nullable=False),
        sa.Column("fragment_id", sa.String(length=120), nullable=False),
        sa.Column("role", sa.String(length=60), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["attempt_id"], ["attempts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["fragment_id"], ["fragments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("attempt_id", "fragment_id", name="uq_attempt_fragment_link"),
    )
    op.create_index("ix_attempt_fragment_links_attempt_id", "attempt_fragment_links", ["attempt_id"])
    op.create_index("ix_attempt_fragment_links_fragment_id", "attempt_fragment_links", ["fragment_id"])
    op.create_index("ix_attempt_fragment_links_role", "attempt_fragment_links", ["role"])


def downgrade() -> None:
    op.drop_index("ix_attempt_fragment_links_role", table_name="attempt_fragment_links")
    op.drop_index("ix_attempt_fragment_links_fragment_id", table_name="attempt_fragment_links")
    op.drop_index("ix_attempt_fragment_links_attempt_id", table_name="attempt_fragment_links")
    op.drop_table("attempt_fragment_links")

    op.drop_index("ix_attempts_status", table_name="attempts")
    op.drop_index("ix_attempts_title", table_name="attempts")
    op.drop_index("ix_attempts_problem_id", table_name="attempts")
    op.drop_table("attempts")

    op.drop_table("problem_graph_node_positions")

    op.drop_index("ix_problem_fragment_links_role", table_name="problem_fragment_links")
    op.drop_index("ix_problem_fragment_links_fragment_id", table_name="problem_fragment_links")
    op.drop_index("ix_problem_fragment_links_problem_id", table_name="problem_fragment_links")
    op.drop_table("problem_fragment_links")

    op.drop_index("ix_problem_topic_links_topic_id", table_name="problem_topic_links")
    op.drop_index("ix_problem_topic_links_problem_id", table_name="problem_topic_links")
    op.drop_table("problem_topic_links")

    op.drop_index("ix_research_problems_status", table_name="research_problems")
    op.drop_index("ix_research_problems_title", table_name="research_problems")
    op.drop_table("research_problems")
