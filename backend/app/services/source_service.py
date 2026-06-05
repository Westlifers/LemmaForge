from __future__ import annotations

import re

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.fragment import Fragment
from app.models.source import Source, SourcePointer
from app.schemas.source import SourceCreate, SourcePointerCreate, SourceUpdate
from app.services.ids import slugify, unique_model_id
from app.services.search_service import index_source, source_search_ids


def list_sources(db: Session, *, search: str | None = None) -> list[Source]:
    query = select(Source).order_by(Source.updated_at.desc())
    if search:
        fts_ids = source_search_ids(db, search)
        if fts_ids:
            query = query.where(Source.id.in_(fts_ids))
        else:
            needle = f"%{search}%"
            query = query.where(
                or_(
                    Source.title.ilike(needle),
                    Source.authors.ilike(needle),
                    Source.citekey.ilike(needle),
                )
            )
    return list(db.execute(query).scalars())


def list_source_pointers_for_fragment(db: Session, fragment_id: str) -> list[SourcePointer]:
    return list(
        db.execute(
            select(SourcePointer).where(SourcePointer.fragment_id == fragment_id)
        ).scalars()
    )


def list_fragments_for_source(db: Session, source_id: str) -> list[Fragment]:
    return list(
        db.execute(
            select(Fragment)
            .join(SourcePointer, SourcePointer.fragment_id == Fragment.id)
            .where(SourcePointer.source_id == source_id)
            .order_by(Fragment.updated_at.desc())
        ).scalars()
    )


def get_source(db: Session, source_id: str) -> Source | None:
    return db.get(Source, source_id)


def get_source_by_citekey(db: Session, citekey: str) -> Source | None:
    return db.execute(select(Source).where(Source.citekey == citekey)).scalar_one_or_none()


def create_source(db: Session, payload: SourceCreate, *, commit: bool = True) -> Source:
    base = payload.citekey or payload.title
    source = Source(
        id=unique_model_id(db, Source, f"src_{slugify(base)}"),
        source_type=payload.source_type,
        title=payload.title,
        authors=payload.authors,
        year=payload.year,
        citekey=payload.citekey,
        zotero_item_key=payload.zotero_item_key,
        url=payload.url,
    )
    db.add(source)
    db.flush()
    index_source(db, source)
    if commit:
        db.commit()
        db.refresh(source)
    return source


def update_source(db: Session, source: Source, payload: SourceUpdate) -> Source:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(source, key, value)
    index_source(db, source)
    db.commit()
    db.refresh(source)
    return source


def create_source_pointer(
    db: Session,
    payload: SourcePointerCreate,
    *,
    commit: bool = True,
) -> SourcePointer:
    pointer = SourcePointer(
        id=unique_model_id(db, SourcePointer, f"ptr_{payload.fragment_id}_{payload.source_id}"),
        fragment_id=payload.fragment_id,
        source_id=payload.source_id,
        locator=payload.locator,
        exactness=payload.exactness,
        quote_text=payload.quote_text,
        note=payload.note,
    )
    db.add(pointer)
    db.flush()
    if commit:
        db.commit()
        db.refresh(pointer)
    return pointer


def get_or_create_source_from_citekey(db: Session, citekey: str) -> Source:
    existing = get_source_by_citekey(db, citekey)
    if existing:
        return existing
    return create_source(
        db,
        SourceCreate(source_type="unknown", title=citekey, citekey=citekey),
        commit=False,
    )


def sync_references_to_sources(db: Session, bib_text: str) -> list[Source]:
    synced: list[Source] = []
    for entry in _parse_bib_entries(bib_text):
        citekey = entry.get("citekey")
        if not citekey:
            continue
        existing = get_source_by_citekey(db, citekey)
        payload = SourceCreate(
            source_type=_source_type_from_entry(entry.get("entry_type")),
            title=entry.get("title") or citekey,
            authors=entry.get("author"),
            year=int(entry["year"]) if entry.get("year", "").isdigit() else None,
            citekey=citekey,
            url=entry.get("url"),
        )
        if existing:
            existing.source_type = payload.source_type
            existing.title = payload.title
            existing.authors = payload.authors
            existing.year = payload.year
            existing.url = payload.url
            index_source(db, existing)
            synced.append(existing)
        else:
            synced.append(create_source(db, payload, commit=False))
    db.commit()
    return synced


def _parse_bib_entries(text: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for match in re.finditer(r"@(?P<type>\w+)\s*\{\s*(?P<citekey>[^,\s]+)\s*,", text):
        start = match.end()
        next_match = re.search(r"\n\s*@", text[start:])
        end = start + next_match.start() if next_match else len(text)
        body = text[start:end]
        entry = {"entry_type": match.group("type").lower(), "citekey": match.group("citekey")}
        for field_match in re.finditer(
            r"(?P<key>\w+)\s*=\s*(?P<value>\{(?:[^{}]|\{[^{}]*\})*\}|\"[^\"]*\"|[^,\n]+)",
            body,
            re.DOTALL,
        ):
            value = field_match.group("value").strip().strip(",")
            if value.startswith("{") and value.endswith("}"):
                value = value[1:-1]
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            entry[field_match.group("key").lower()] = re.sub(r"\s+", " ", value).strip()
        entries.append(entry)
    return entries


def _source_type_from_entry(entry_type: str | None) -> str:
    if entry_type in {"book", "inbook"}:
        return "book"
    if entry_type in {"online", "misc", "webpage"}:
        return "webpage"
    return "paper"
