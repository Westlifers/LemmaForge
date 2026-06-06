"""Add topic graph layout positions.

Revision ID: 0004_topic_graph_layout
Revises: 0003_import_batch_ai_state
Create Date: 2026-06-06
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0004_topic_graph_layout"
down_revision = "0003_import_batch_ai_state"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "topic_graph_node_positions",
        sa.Column("topic_id", sa.String(length=80), nullable=False),
        sa.Column("fragment_id", sa.String(length=120), nullable=False),
        sa.Column("x", sa.Float(), nullable=False),
        sa.Column("y", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["fragment_id"], ["fragments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("topic_id", "fragment_id"),
    )


def downgrade() -> None:
    op.drop_table("topic_graph_node_positions")
