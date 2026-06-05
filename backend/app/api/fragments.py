from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.fragment import (
    FragmentCreate,
    FragmentRead,
    FragmentUpdate,
    FragmentVersionCreate,
    FragmentVersionRead,
)
from app.schemas.source import SourcePointerRead
from app.services.fragment_service import (
    create_fragment,
    create_fragment_version,
    delete_fragment,
    get_fragment,
    list_fragments,
    update_fragment,
)
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
