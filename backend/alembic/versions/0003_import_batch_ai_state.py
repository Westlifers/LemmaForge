"""Add AI draft state to import batches.

Revision ID: 0003_import_batch_ai_state
Revises: 0002_import_batches_search
Create Date: 2026-06-06
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0003_import_batch_ai_state"
down_revision = "0002_import_batches_search"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("import_batches", sa.Column("ai_draft_result_json", sa.Text(), nullable=True))
    op.add_column("import_batches", sa.Column("relation_proposals_json", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("import_batches", "relation_proposals_json")
    op.drop_column("import_batches", "ai_draft_result_json")
