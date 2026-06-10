from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.problem import AttemptFragmentLink
from app.schemas.problem import (
    AttemptCreate,
    AttemptFragmentLinkCreate,
    AttemptFragmentLinkRead,
    AttemptFragmentLinkUpdate,
    AttemptRead,
    AttemptUpdate,
    AttemptWorkspaceRead,
)
from app.services.attempt_service import (
    add_attempt_fragment_link,
    create_attempt,
    delete_attempt,
    get_attempt,
    get_attempt_workspace,
    list_attempt_fragment_links,
    list_attempts_for_problem,
    remove_attempt_fragment_link,
    update_attempt,
    update_attempt_fragment_link,
)
from app.services.problem_service import get_problem

router = APIRouter(tags=["attempts"])


@router.get("/api/problems/{problem_id}/attempts", response_model=list[AttemptRead])
def api_list_problem_attempts(problem_id: str, db: Session = Depends(get_db)):
    if get_problem(db, problem_id) is None:
        raise HTTPException(status_code=404, detail="Problem not found")
    return list_attempts_for_problem(db, problem_id)


@router.post("/api/problems/{problem_id}/attempts", response_model=AttemptRead, status_code=201)
def api_create_attempt(problem_id: str, payload: AttemptCreate, db: Session = Depends(get_db)):
    problem = get_problem(db, problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail="Problem not found")
    return create_attempt(db, problem, payload)


@router.get("/api/attempts/{attempt_id}", response_model=AttemptRead)
def api_get_attempt(attempt_id: str, db: Session = Depends(get_db)):
    attempt = get_attempt(db, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="Attempt not found")
    return attempt


@router.get("/api/attempts/{attempt_id}/workspace", response_model=AttemptWorkspaceRead)
def api_get_attempt_workspace(attempt_id: str, db: Session = Depends(get_db)):
    attempt = get_attempt(db, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="Attempt not found")
    try:
        return get_attempt_workspace(db, attempt)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/api/attempts/{attempt_id}", response_model=AttemptRead)
def api_update_attempt(attempt_id: str, payload: AttemptUpdate, db: Session = Depends(get_db)):
    attempt = get_attempt(db, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="Attempt not found")
    return update_attempt(db, attempt, payload)


@router.delete("/api/attempts/{attempt_id}", status_code=204)
def api_delete_attempt(attempt_id: str, db: Session = Depends(get_db)):
    attempt = get_attempt(db, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="Attempt not found")
    delete_attempt(db, attempt)
    return None


@router.get("/api/attempts/{attempt_id}/fragments", response_model=list[AttemptFragmentLinkRead])
def api_list_attempt_fragments(attempt_id: str, db: Session = Depends(get_db)):
    if get_attempt(db, attempt_id) is None:
        raise HTTPException(status_code=404, detail="Attempt not found")
    return list_attempt_fragment_links(db, attempt_id)


@router.post("/api/attempts/{attempt_id}/fragments", response_model=AttemptFragmentLinkRead, status_code=201)
def api_add_attempt_fragment(
    attempt_id: str,
    payload: AttemptFragmentLinkCreate,
    db: Session = Depends(get_db),
):
    attempt = get_attempt(db, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="Attempt not found")
    try:
        return add_attempt_fragment_link(db, attempt, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/api/attempts/{attempt_id}/fragments/{link_id}", response_model=AttemptFragmentLinkRead)
def api_update_attempt_fragment(
    attempt_id: str,
    link_id: str,
    payload: AttemptFragmentLinkUpdate,
    db: Session = Depends(get_db),
):
    if get_attempt(db, attempt_id) is None:
        raise HTTPException(status_code=404, detail="Attempt not found")
    link = db.get(AttemptFragmentLink, link_id)
    if link is None or link.attempt_id != attempt_id:
        raise HTTPException(status_code=404, detail="Attempt fragment link not found")
    return update_attempt_fragment_link(db, link, payload)


@router.delete("/api/attempts/{attempt_id}/fragments/{link_id}", status_code=204)
def api_remove_attempt_fragment(attempt_id: str, link_id: str, db: Session = Depends(get_db)):
    if get_attempt(db, attempt_id) is None:
        raise HTTPException(status_code=404, detail="Attempt not found")
    link = db.get(AttemptFragmentLink, link_id)
    if link is None or link.attempt_id != attempt_id:
        raise HTTPException(status_code=404, detail="Attempt fragment link not found")
    remove_attempt_fragment_link(db, link)
    return None
