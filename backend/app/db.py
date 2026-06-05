from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
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
    db = get_session_factory()()
    try:
        ensure_search_indexes(db)
    finally:
        db.close()
