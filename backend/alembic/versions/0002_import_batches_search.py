"""Add import batches and search indexes.

Revision ID: 0002_import_batches_search
Revises: 0001_initial
Create Date: 2026-06-05
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002_import_batches_search"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "import_batches",
        sa.Column("id", sa.String(length=120), primary_key=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("raw_excerpt", sa.Text(), nullable=False),
        sa.Column("topic_hint", sa.String(length=240), nullable=True),
        sa.Column("citekey", sa.String(length=160), nullable=True),
        sa.Column("locator", sa.String(length=200), nullable=True),
        sa.Column("patch_json", sa.Text(), nullable=True),
        sa.Column("warnings_json", sa.Text(), nullable=False),
        sa.Column("commit_result_json", sa.Text(), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_import_batches_status", "import_batches", ["status"])
    op.create_index("ix_import_batches_citekey", "import_batches", ["citekey"])
    op.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS fragment_fts "
        "USING fts5(fragment_id UNINDEXED, title, body)"
    )
    op.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS source_fts "
        "USING fts5(source_id UNINDEXED, title, authors, citekey)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS source_fts")
    op.execute("DROP TABLE IF EXISTS fragment_fts")
    op.drop_index("ix_import_batches_citekey", table_name="import_batches")
    op.drop_index("ix_import_batches_status", table_name="import_batches")
    op.drop_table("import_batches")

