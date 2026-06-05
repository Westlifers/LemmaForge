"""Initial local research schema.

Revision ID: 0001_initial
Revises: None
Create Date: 2026-06-05
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "topics",
        sa.Column("id", sa.String(length=80), primary_key=True),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "fragments",
        sa.Column("id", sa.String(length=120), primary_key=True),
        sa.Column("type", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("topic_id", sa.String(length=80), sa.ForeignKey("topics.id"), nullable=True),
        sa.Column("origin_classification", sa.String(length=40), nullable=False),
        sa.Column("exactness", sa.String(length=40), nullable=False),
        sa.Column("current_version_id", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_fragments_type", "fragments", ["type"])
    op.create_index("ix_fragments_title", "fragments", ["title"])
    op.create_index("ix_fragments_status", "fragments", ["status"])
    op.create_table(
        "fragment_versions",
        sa.Column("id", sa.String(length=120), primary_key=True),
        sa.Column(
            "fragment_id",
            sa.String(length=120),
            sa.ForeignKey("fragments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("change_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_fragment_versions_fragment_id", "fragment_versions", ["fragment_id"])
    op.create_table(
        "relations",
        sa.Column("id", sa.String(length=120), primary_key=True),
        sa.Column(
            "source_fragment_id",
            sa.String(length=120),
            sa.ForeignKey("fragments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("relation_kind", sa.String(length=60), nullable=False),
        sa.Column(
            "target_fragment_id",
            sa.String(length=120),
            sa.ForeignKey("fragments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_relations_source_fragment_id", "relations", ["source_fragment_id"])
    op.create_index("ix_relations_target_fragment_id", "relations", ["target_fragment_id"])
    op.create_index("ix_relations_relation_kind", "relations", ["relation_kind"])
    op.create_table(
        "sources",
        sa.Column("id", sa.String(length=120), primary_key=True),
        sa.Column("source_type", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=400), nullable=False),
        sa.Column("authors", sa.Text(), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("citekey", sa.String(length=160), nullable=True),
        sa.Column("zotero_item_key", sa.String(length=80), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_sources_source_type", "sources", ["source_type"])
    op.create_index("ix_sources_citekey", "sources", ["citekey"], unique=True)
    op.create_table(
        "source_pointers",
        sa.Column("id", sa.String(length=120), primary_key=True),
        sa.Column(
            "fragment_id",
            sa.String(length=120),
            sa.ForeignKey("fragments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_id",
            sa.String(length=120),
            sa.ForeignKey("sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("locator", sa.String(length=200), nullable=True),
        sa.Column("exactness", sa.String(length=40), nullable=False),
        sa.Column("quote_text", sa.Text(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
    )
    op.create_index("ix_source_pointers_fragment_id", "source_pointers", ["fragment_id"])
    op.create_index("ix_source_pointers_source_id", "source_pointers", ["source_id"])
    op.create_table(
        "context_packs",
        sa.Column("id", sa.String(length=120), primary_key=True),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "context_pack_items",
        sa.Column(
            "context_pack_id",
            sa.String(length=120),
            sa.ForeignKey("context_packs.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "fragment_id",
            sa.String(length=120),
            sa.ForeignKey("fragments.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("context_pack_items")
    op.drop_table("context_packs")
    op.drop_index("ix_source_pointers_source_id", table_name="source_pointers")
    op.drop_index("ix_source_pointers_fragment_id", table_name="source_pointers")
    op.drop_table("source_pointers")
    op.drop_index("ix_sources_citekey", table_name="sources")
    op.drop_index("ix_sources_source_type", table_name="sources")
    op.drop_table("sources")
    op.drop_index("ix_relations_relation_kind", table_name="relations")
    op.drop_index("ix_relations_target_fragment_id", table_name="relations")
    op.drop_index("ix_relations_source_fragment_id", table_name="relations")
    op.drop_table("relations")
    op.drop_index("ix_fragment_versions_fragment_id", table_name="fragment_versions")
    op.drop_table("fragment_versions")
    op.drop_index("ix_fragments_status", table_name="fragments")
    op.drop_index("ix_fragments_title", table_name="fragments")
    op.drop_index("ix_fragments_type", table_name="fragments")
    op.drop_table("fragments")
    op.drop_table("topics")

