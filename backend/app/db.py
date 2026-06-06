from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
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
