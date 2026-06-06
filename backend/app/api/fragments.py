from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.fragment import (
    FragmentBulkDeleteResult,
    FragmentBulkUpdate,
    FragmentCreate,
    FragmentRead,
    FragmentUpdate,
    FragmentVersionCreate,
    FragmentVersionRead,
)
from app.schemas.source import SourcePointerRead
from app.services.fragment_service import (
    bulk_delete_fragments,
    bulk_update_fragments,
    create_fragment,
    create_fragment_version,
    delete_fragment,
    get_fragment,
    list_fragments,
    update_fragment,
)
from app.models.fragment import Topic
from app.services.markdown_vault import write_fragment_markdown
from app.services.source_service import list_source_pointers_for_fragment

router = APIRouter(prefix="/api/fragments", tags=["fragments"])


@router.get("", response_model=list[FragmentRead])
def api_list_fragments(
    search: str | None = None,
    type: str | None = None,
    status: str | None = None,
    topic_id: str | None = None,
    origin_classification: str | None = None,
    exactness: str | None = None,
    source_citekey: str | None = None,
    db: Session = Depends(get_db),
):
    return list_fragments(
        db,
        search=search,
        type=type,
        status=status,
        topic_id=topic_id,
        origin_classification=origin_classification,
        exactness=exactness,
        source_citekey=source_citekey,
    )


@router.post("", response_model=FragmentRead, status_code=201)
def api_create_fragment(payload: FragmentCreate, db: Session = Depends(get_db)):
    return create_fragment(db, payload)


@router.patch("/bulk", response_model=list[FragmentRead])
def api_bulk_update_fragments(payload: FragmentBulkUpdate, db: Session = Depends(get_db)):
    missing = [fragment_id for fragment_id in payload.ids if get_fragment(db, fragment_id) is None]
    if missing:
        raise HTTPException(status_code=404, detail=f"Unknown fragments: {', '.join(missing)}")
    if "topic_id" in payload.model_fields_set and payload.topic_id and db.get(Topic, payload.topic_id) is None:
        raise HTTPException(status_code=400, detail=f"Unknown topic: {payload.topic_id}")

    changes: dict[str, object] = {}
    if "topic_id" in payload.model_fields_set:
        changes["topic_id"] = payload.topic_id
    if payload.status is not None:
        changes["status"] = payload.status
    if payload.change_note is not None:
        changes["change_note"] = payload.change_note
    if not changes:
        raise HTTPException(status_code=400, detail="No bulk changes requested")
    return bulk_update_fragments(db, payload.ids, FragmentUpdate(**changes))


@router.delete("/bulk", response_model=FragmentBulkDeleteResult)
def api_bulk_delete_fragments(ids: list[str] = Body(...), db: Session = Depends(get_db)):
    return FragmentBulkDeleteResult(deleted_ids=bulk_delete_fragments(db, ids))


@router.get("/{fragment_id}", response_model=FragmentRead)
def api_get_fragment(fragment_id: str, db: Session = Depends(get_db)):
    fragment = get_fragment(db, fragment_id)
    if fragment is None:
        raise HTTPException(status_code=404, detail="Fragment not found")
    return fragment


@router.patch("/{fragment_id}", response_model=FragmentRead)
def api_update_fragment(fragment_id: str, payload: FragmentUpdate, db: Session = Depends(get_db)):
    fragment = get_fragment(db, fragment_id)
    if fragment is None:
        raise HTTPException(status_code=404, detail="Fragment not found")
    return update_fragment(db, fragment, payload)


@router.delete("/{fragment_id}", status_code=204)
def api_delete_fragment(fragment_id: str, db: Session = Depends(get_db)):
    fragment = get_fragment(db, fragment_id)
    if fragment is None:
        raise HTTPException(status_code=404, detail="Fragment not found")
    delete_fragment(db, fragment)
    return None


@router.get("/{fragment_id}/versions", response_model=list[FragmentVersionRead])
def api_list_versions(fragment_id: str, db: Session = Depends(get_db)):
    fragment = get_fragment(db, fragment_id)
    if fragment is None:
        raise HTTPException(status_code=404, detail="Fragment not found")
    return fragment.versions


@router.get("/{fragment_id}/source-pointers", response_model=list[SourcePointerRead])
def api_list_source_pointers(fragment_id: str, db: Session = Depends(get_db)):
    fragment = get_fragment(db, fragment_id)
    if fragment is None:
        raise HTTPException(status_code=404, detail="Fragment not found")
    return list_source_pointers_for_fragment(db, fragment_id)


@router.post("/{fragment_id}/versions", response_model=FragmentVersionRead, status_code=201)
def api_create_version(
    fragment_id: str,
    payload: FragmentVersionCreate,
    db: Session = Depends(get_db),
):
    fragment = get_fragment(db, fragment_id)
    if fragment is None:
        raise HTTPException(status_code=404, detail="Fragment not found")
    fragment.body = payload.body
    version = create_fragment_version(db, fragment, payload, commit=False)
    fragment.current_version_id = version.id
    db.commit()
    db.refresh(version)
    write_fragment_markdown(fragment)
    return version
