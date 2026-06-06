from __future__ import annotations

from sqlalchemy import Select, delete, exists, func, or_, select
from sqlalchemy.orm import Session

from app.models.context_pack import ContextPackItem
from app.models.fragment import Fragment, FragmentVersion
from app.models.relation import Relation
from app.models.source import Source, SourcePointer
from app.schemas.fragment import FragmentCreate, FragmentUpdate, FragmentVersionCreate
from app.services.ids import fragment_id_base, short_uuid, slugify, unique_model_id
from app.services.markdown_vault import delete_fragment_markdown, write_fragment_markdown
from app.services.search_service import delete_fragment_index, fragment_search_ids, index_fragment


def list_fragments(
    db: Session,
    *,
    search: str | None = None,
    type: str | None = None,
    status: str | None = None,
    topic_id: str | None = None,
    origin_classification: str | None = None,
    exactness: str | None = None,
    source_citekey: str | None = None,
) -> list[Fragment]:
    query: Select[tuple[Fragment]] = select(Fragment).order_by(Fragment.updated_at.desc())
    if search:
        fts_ids = fragment_search_ids(db, search)
        if fts_ids:
            query = query.where(Fragment.id.in_(fts_ids))
        else:
            needle = f"%{search}%"
            query = query.where(or_(Fragment.title.ilike(needle), Fragment.body.ilike(needle)))
    if type:
        query = query.where(Fragment.type == type)
    if status:
        query = query.where(Fragment.status == status)
    if topic_id:
        query = query.where(Fragment.topic_id == topic_id)
    if origin_classification:
        query = query.where(Fragment.origin_classification == origin_classification)
    if exactness:
        query = query.where(Fragment.exactness == exactness)
    if source_citekey:
        query = query.where(
            exists()
            .where(SourcePointer.fragment_id == Fragment.id)
            .where(SourcePointer.source_id == Source.id)
            .where(Source.citekey == source_citekey)
        )
    return list(db.execute(query).scalars())


def get_fragment(db: Session, fragment_id: str) -> Fragment | None:
    return db.get(Fragment, fragment_id)


def create_fragment(
    db: Session,
    payload: FragmentCreate,
    *,
    id_hint: str | None = None,
    commit: bool = True,
    write_markdown: bool = True,
) -> Fragment:
    base = id_hint or fragment_id_base(payload.type, payload.title)
    fragment = Fragment(
        id=unique_model_id(db, Fragment, base),
        type=payload.type,
        title=payload.title,
        status=payload.status,
        body=payload.body,
        topic_id=payload.topic_id,
        origin_classification=payload.origin_classification,
        exactness=payload.exactness,
    )
    db.add(fragment)
    db.flush()
    version = create_fragment_version(
        db,
        fragment,
        FragmentVersionCreate(body=payload.body, change_note="Initial version"),
        commit=False,
    )
    fragment.current_version_id = version.id
    db.flush()
    index_fragment(db, fragment)
    if commit:
        db.commit()
        db.refresh(fragment)
    if write_markdown:
        write_fragment_markdown(fragment)
    return fragment


def update_fragment(
    db: Session,
    fragment: Fragment,
    payload: FragmentUpdate,
    *,
    commit: bool = True,
    write_markdown: bool = True,
) -> Fragment:
    changes = payload.model_dump(exclude_unset=True, exclude={"change_note"})
    body_changed = "body" in changes and changes["body"] != fragment.body
    for key, value in changes.items():
        setattr(fragment, key, value)
    if body_changed:
        version = create_fragment_version(
            db,
            fragment,
            FragmentVersionCreate(
                body=fragment.body,
                change_note=payload.change_note or "Updated fragment body",
            ),
            commit=False,
        )
        fragment.current_version_id = version.id
    db.flush()
    index_fragment(db, fragment)
    if commit:
        db.commit()
        db.refresh(fragment)
    if write_markdown:
        write_fragment_markdown(fragment)
    return fragment


def bulk_update_fragments(
    db: Session,
    fragment_ids: list[str],
    payload: FragmentUpdate,
) -> list[Fragment]:
    unique_ids = list(dict.fromkeys(fragment_ids))
    fragments = [fragment for fragment in (db.get(Fragment, fragment_id) for fragment_id in unique_ids) if fragment]
    for fragment in fragments:
        update_fragment(db, fragment, payload, commit=False, write_markdown=False)
    db.commit()
    for fragment in fragments:
        db.refresh(fragment)
        write_fragment_markdown(fragment)
    return fragments


def bulk_delete_fragments(db: Session, fragment_ids: list[str]) -> list[str]:
    unique_ids = list(dict.fromkeys(fragment_ids))
    fragments = [fragment for fragment in (db.get(Fragment, fragment_id) for fragment_id in unique_ids) if fragment]
    deleted_ids: list[str] = []
    for fragment in fragments:
        _delete_fragment_records(db, fragment)
        deleted_ids.append(fragment.id)
    db.commit()
    for fragment in fragments:
        delete_fragment_markdown(fragment)
    return deleted_ids


def _delete_fragment_records(db: Session, fragment: Fragment) -> None:
    fragment_id = fragment.id
    delete_fragment_index(db, fragment_id)
    db.execute(delete(ContextPackItem).where(ContextPackItem.fragment_id == fragment_id))
    db.execute(
        delete(Relation).where(
            or_(
                Relation.source_fragment_id == fragment_id,
                Relation.target_fragment_id == fragment_id,
            )
        )
    )
    db.execute(delete(SourcePointer).where(SourcePointer.fragment_id == fragment_id))
    db.execute(delete(FragmentVersion).where(FragmentVersion.fragment_id == fragment_id))
    db.delete(fragment)


def delete_fragment(db: Session, fragment: Fragment) -> None:
    _delete_fragment_records(db, fragment)
    db.commit()
    delete_fragment_markdown(fragment)


def create_fragment_version(
    db: Session,
    fragment: Fragment,
    payload: FragmentVersionCreate,
    *,
    commit: bool = True,
) -> FragmentVersion:
    current_max = db.execute(
        select(func.max(FragmentVersion.version_number)).where(
            FragmentVersion.fragment_id == fragment.id
        )
    ).scalar_one()
    next_number = (current_max or 0) + 1
    version = FragmentVersion(
        id=unique_model_id(db, FragmentVersion, f"{slugify(fragment.id)}_v{next_number}"),
        fragment_id=fragment.id,
        version_number=next_number,
        body=payload.body,
        change_note=payload.change_note,
    )
    db.add(version)
    db.flush()
    fragment.current_version_id = version.id
    if commit:
        db.commit()
        db.refresh(version)
    return version


def delete_fragment_version_suffix() -> str:
    return short_uuid()
