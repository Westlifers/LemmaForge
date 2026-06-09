from __future__ import annotations

import json
from collections.abc import Generator
from datetime import UTC, datetime

from sqlalchemy import bindparam, create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import ensure_local_directories, get_settings


class Base(DeclarativeBase):
    pass


_engine = None
_session_factory: sessionmaker[Session] | None = None


def get_engine():
    global _engine
    if _engine is None:
        ensure_local_directories()
        settings = get_settings()
        connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
        _engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(),
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
            future=True,
        )
    return _session_factory


def reset_engine_for_tests() -> None:
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None


def get_db() -> Generator[Session, None, None]:
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from . import models  # noqa: F401
    from .services.search_service import ensure_search_indexes

    ensure_local_directories()
    Base.metadata.create_all(bind=get_engine())
    _ensure_lightweight_sqlite_migrations()
    db = get_session_factory()()
    try:
        ensure_search_indexes(db)
    finally:
        db.close()


def _ensure_lightweight_sqlite_migrations() -> None:
    engine = get_engine()
    if engine.dialect.name != "sqlite":
        return
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    with engine.begin() as connection:
        if "import_batches" in table_names:
            existing_columns = {column["name"] for column in inspector.get_columns("import_batches")}
            pending_columns = {
                "ai_draft_result_json": "TEXT",
                "relation_proposals_json": "TEXT",
            }
            for column_name, column_type in pending_columns.items():
                if column_name not in existing_columns:
                    connection.execute(
                        text(f"ALTER TABLE import_batches ADD COLUMN {column_name} {column_type}")
                    )
        if "topic_graph_node_positions" not in table_names:
            connection.execute(
                text(
                    "CREATE TABLE topic_graph_node_positions ("
                    "topic_id VARCHAR(80) NOT NULL, "
                    "fragment_id VARCHAR(120) NOT NULL, "
                    "x FLOAT NOT NULL, "
                    "y FLOAT NOT NULL, "
                    "updated_at DATETIME NOT NULL, "
                    "PRIMARY KEY (topic_id, fragment_id), "
                    "FOREIGN KEY(topic_id) REFERENCES topics (id) ON DELETE CASCADE, "
                    "FOREIGN KEY(fragment_id) REFERENCES fragments (id) ON DELETE CASCADE"
                    ")"
                )
            )
        if "context_packs" in table_names:
            existing_columns = {column["name"] for column in inspector.get_columns("context_packs")}
            pending_columns = {
                "topic_id": "VARCHAR(80)",
                "task_prompt": "TEXT",
            }
            for column_name, column_type in pending_columns.items():
                if column_name not in existing_columns:
                    connection.execute(
                        text(f"ALTER TABLE context_packs ADD COLUMN {column_name} {column_type}")
                    )
        if "relations" in table_names:
            _migrate_relation_kinds(connection)


def _migrate_relation_kinds(connection) -> None:
    archive_kinds = {"cites", "quotes", "paraphrases", "restates", "came_from"}
    archive_rows = connection.execute(
        text(
            "SELECT id, relation_kind, source_fragment_id, target_fragment_id, confidence, created_at "
            "FROM relations WHERE relation_kind IN :kinds"
        ).bindparams(bindparam("kinds", expanding=True)),
        {"kinds": tuple(archive_kinds)},
    ).mappings().all()
    if archive_rows:
        _archive_legacy_relations([dict(row) for row in archive_rows])
        connection.execute(
            text("DELETE FROM relations WHERE relation_kind IN :kinds").bindparams(
                bindparam("kinds", expanding=True)
            ),
            {"kinds": tuple(archive_kinds)},
        )

    kind_map = {
        "uses": "depends_on",
        "proves": "proof_of",
        "adopts_notation_from": "uses_notation",
        "depends_on_notation": "uses_notation",
        "questions_external_claim": "questions",
        "generalizes_external_result": "generalizes",
    }
    for old_kind, new_kind in kind_map.items():
        connection.execute(
            text(
                "UPDATE relations SET relation_kind = :new_kind "
                "WHERE relation_kind = :old_kind"
            ),
            {"old_kind": old_kind, "new_kind": new_kind},
        )

    swap_kinds = ("specializes_to", "specializes_external_result")
    connection.execute(
        text(
            "UPDATE relations "
            "SET relation_kind = 'generalizes', "
            "source_fragment_id = target_fragment_id, "
            "target_fragment_id = source_fragment_id "
            "WHERE relation_kind IN :kinds"
        ).bindparams(bindparam("kinds", expanding=True)),
        {"kinds": swap_kinds},
    )


def _archive_legacy_relations(rows: list[dict]) -> None:
    settings = get_settings()
    archive_path = settings.vault_dir.parent / "data" / "relation_migration_archive.json"
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    existing: list[dict] = []
    if archive_path.exists():
        try:
            parsed = json.loads(archive_path.read_text(encoding="utf-8"))
            existing = parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, OSError):
            existing = []
    archived_ids = {entry.get("id") for entry in existing}
    archived_at = datetime.now(UTC).isoformat()
    for row in rows:
        if row["id"] in archived_ids:
            continue
        existing.append(
            {
                "id": row["id"],
                "old_kind": row["relation_kind"],
                "source_fragment_id": row["source_fragment_id"],
                "target_fragment_id": row["target_fragment_id"],
                "confidence": row["confidence"],
                "created_at": str(row["created_at"]) if row["created_at"] is not None else None,
                "archive_reason": "Provenance-style relation moved out of active mathematical graph.",
                "archived_at": archived_at,
            }
        )
    archive_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
