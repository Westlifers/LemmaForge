from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.fragment import Fragment
from app.models.source import Source


def ensure_search_indexes(db: Session) -> None:
    if not _fts_available(db):
        return
    db.execute(
        text(
            "CREATE VIRTUAL TABLE IF NOT EXISTS fragment_fts "
            "USING fts5(fragment_id UNINDEXED, title, body)"
        )
    )
    db.execute(
        text(
            "CREATE VIRTUAL TABLE IF NOT EXISTS source_fts "
            "USING fts5(source_id UNINDEXED, title, authors, citekey)"
        )
    )
    db.commit()


def index_fragment(db: Session, fragment: Fragment) -> None:
    if not _table_exists(db, "fragment_fts"):
        return
    db.execute(text("DELETE FROM fragment_fts WHERE fragment_id = :id"), {"id": fragment.id})
    db.execute(
        text(
            "INSERT INTO fragment_fts(fragment_id, title, body) "
            "VALUES (:id, :title, :body)"
        ),
        {"id": fragment.id, "title": fragment.title, "body": fragment.body},
    )


def delete_fragment_index(db: Session, fragment_id: str) -> None:
    if not _table_exists(db, "fragment_fts"):
        return
    db.execute(text("DELETE FROM fragment_fts WHERE fragment_id = :id"), {"id": fragment_id})


def index_source(db: Session, source: Source) -> None:
    if not _table_exists(db, "source_fts"):
        return
    db.execute(text("DELETE FROM source_fts WHERE source_id = :id"), {"id": source.id})
    db.execute(
        text(
            "INSERT INTO source_fts(source_id, title, authors, citekey) "
            "VALUES (:id, :title, :authors, :citekey)"
        ),
        {
            "id": source.id,
            "title": source.title,
            "authors": source.authors or "",
            "citekey": source.citekey or "",
        },
    )


def fragment_search_ids(db: Session, query: str) -> list[str]:
    if not _table_exists(db, "fragment_fts"):
        return []
    rows = db.execute(
        text(
            "SELECT fragment_id FROM fragment_fts "
            "WHERE fragment_fts MATCH :query "
            "ORDER BY rank"
        ),
        {"query": _fts_query(query)},
    ).all()
    return [row[0] for row in rows]


def source_search_ids(db: Session, query: str) -> list[str]:
    if not _table_exists(db, "source_fts"):
        return []
    rows = db.execute(
        text(
            "SELECT source_id FROM source_fts "
            "WHERE source_fts MATCH :query "
            "ORDER BY rank"
        ),
        {"query": _fts_query(query)},
    ).all()
    return [row[0] for row in rows]


def rebuild_search_indexes(db: Session) -> None:
    ensure_search_indexes(db)
    if _table_exists(db, "fragment_fts"):
        db.execute(text("DELETE FROM fragment_fts"))
        for fragment in db.query(Fragment).all():
            index_fragment(db, fragment)
    if _table_exists(db, "source_fts"):
        db.execute(text("DELETE FROM source_fts"))
        for source in db.query(Source).all():
            index_source(db, source)
    db.commit()


def _fts_available(db: Session) -> bool:
    try:
        db.execute(text("CREATE VIRTUAL TABLE IF NOT EXISTS _fts_probe USING fts5(value)"))
        db.execute(text("DROP TABLE IF EXISTS _fts_probe"))
        return True
    except Exception:
        db.rollback()
        return False


def _table_exists(db: Session, name: str) -> bool:
    row = db.execute(
        text("SELECT name FROM sqlite_master WHERE type IN ('table', 'view') AND name = :name"),
        {"name": name},
    ).first()
    return row is not None


def _fts_query(query: str) -> str:
    terms = [term.strip().replace('"', "") for term in query.split() if term.strip()]
    return " OR ".join(f'"{term}"' for term in terms) or '""'
