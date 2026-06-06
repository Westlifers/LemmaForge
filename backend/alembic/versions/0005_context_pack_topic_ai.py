"""Add topic-linked AI context pack fields."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005_context_pack_topic_ai"
down_revision = "0004_topic_graph_layout"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("context_packs", sa.Column("topic_id", sa.String(length=80), nullable=True))
    op.add_column("context_packs", sa.Column("task_prompt", sa.Text(), nullable=True))
    op.create_index("ix_context_packs_topic_id", "context_packs", ["topic_id"])


def downgrade() -> None:
    op.drop_index("ix_context_packs_topic_id", table_name="context_packs")
    op.drop_column("context_packs", "task_prompt")
    op.drop_column("context_packs", "topic_id")
