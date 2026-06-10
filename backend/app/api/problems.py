from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.problem import ProblemFragmentLink
from app.schemas.problem import (
    ProblemFragmentLinkCreate,
    ProblemFragmentLinkRead,
    ProblemFragmentLinkUpdate,
    ProblemGraphLayoutUpdate,
    ProblemSummaryJobRead,
    ProblemSummaryRequest,
    ProblemSummaryResult,
    ProblemTopicLinkCreate,
    ProblemTopicLinkRead,
    ProblemWorkspaceRead,
    ResearchProblemCreate,
    ResearchProblemRead,
    ResearchProblemUpdate,
)
from app.services.problem_ai_service import suggest_problem_summary
from app.services.problem_ai_job_service import read_problem_summary_job, start_problem_summary_job
from app.services.problem_service import (
    add_problem_fragment_link,
    add_problem_topic_link,
    create_problem,
    delete_problem,
    get_problem,
    list_problem_fragment_links,
    list_problem_topic_links,
    list_problems,
    get_problem_workspace,
    remove_problem_fragment_link,
    remove_problem_topic_link,
    update_problem,
    update_problem_graph_layout,
    update_problem_fragment_link,
)

router = APIRouter(prefix="/api/problems", tags=["problems"])


@router.get("", response_model=list[ResearchProblemRead])
def api_list_problems(
    search: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    return list_problems(db, search=search, status=status)


@router.post("", response_model=ResearchProblemRead, status_code=201)
def api_create_problem(payload: ResearchProblemCreate, db: Session = Depends(get_db)):
    return create_problem(db, payload)


@router.post("/ai/summarize", response_model=ProblemSummaryResult)
def api_suggest_problem_summary(payload: ProblemSummaryRequest, db: Session = Depends(get_db)):
    try:
        return suggest_problem_summary(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/ai/summary-jobs", response_model=ProblemSummaryJobRead, status_code=202)
def api_start_problem_summary_job(payload: ProblemSummaryRequest):
    return start_problem_summary_job(payload)


@router.get("/ai/summary-jobs/{job_id}", response_model=ProblemSummaryJobRead)
def api_read_problem_summary_job(job_id: str):
    try:
        return read_problem_summary_job(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{problem_id}", response_model=ResearchProblemRead)
def api_get_problem(problem_id: str, db: Session = Depends(get_db)):
    problem = get_problem(db, problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem


@router.get("/{problem_id}/workspace", response_model=ProblemWorkspaceRead)
def api_get_problem_workspace(problem_id: str, db: Session = Depends(get_db)):
    problem = get_problem(db, problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail="Problem not found")
    return get_problem_workspace(db, problem)


@router.patch("/{problem_id}/graph-layout", response_model=ProblemWorkspaceRead)
def api_update_problem_graph_layout(
    problem_id: str,
    payload: ProblemGraphLayoutUpdate,
    db: Session = Depends(get_db),
):
    problem = get_problem(db, problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail="Problem not found")
    try:
        return update_problem_graph_layout(db, problem, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/{problem_id}", response_model=ResearchProblemRead)
def api_update_problem(
    problem_id: str,
    payload: ResearchProblemUpdate,
    db: Session = Depends(get_db),
):
    problem = get_problem(db, problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail="Problem not found")
    return update_problem(db, problem, payload)


@router.delete("/{problem_id}", status_code=204)
def api_delete_problem(problem_id: str, db: Session = Depends(get_db)):
    problem = get_problem(db, problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail="Problem not found")
    delete_problem(db, problem)
    return None


@router.get("/{problem_id}/topics", response_model=list[ProblemTopicLinkRead])
def api_list_problem_topics(problem_id: str, db: Session = Depends(get_db)):
    if get_problem(db, problem_id) is None:
        raise HTTPException(status_code=404, detail="Problem not found")
    return list_problem_topic_links(db, problem_id)


@router.post("/{problem_id}/topics", response_model=ProblemTopicLinkRead, status_code=201)
def api_add_problem_topic(
    problem_id: str,
    payload: ProblemTopicLinkCreate,
    db: Session = Depends(get_db),
):
    problem = get_problem(db, problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail="Problem not found")
    try:
        return add_problem_topic_link(db, problem, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{problem_id}/topics/{topic_id}", status_code=204)
def api_remove_problem_topic(problem_id: str, topic_id: str, db: Session = Depends(get_db)):
    if get_problem(db, problem_id) is None:
        raise HTTPException(status_code=404, detail="Problem not found")
    if not remove_problem_topic_link(db, problem_id, topic_id):
        raise HTTPException(status_code=404, detail="Topic link not found")
    return None


@router.get("/{problem_id}/fragments", response_model=list[ProblemFragmentLinkRead])
def api_list_problem_fragments(problem_id: str, db: Session = Depends(get_db)):
    if get_problem(db, problem_id) is None:
        raise HTTPException(status_code=404, detail="Problem not found")
    return list_problem_fragment_links(db, problem_id)


@router.post("/{problem_id}/fragments", response_model=ProblemFragmentLinkRead, status_code=201)
def api_add_problem_fragment(
    problem_id: str,
    payload: ProblemFragmentLinkCreate,
    db: Session = Depends(get_db),
):
    problem = get_problem(db, problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail="Problem not found")
    try:
        return add_problem_fragment_link(db, problem, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/{problem_id}/fragments/{link_id}", response_model=ProblemFragmentLinkRead)
def api_update_problem_fragment(
    problem_id: str,
    link_id: str,
    payload: ProblemFragmentLinkUpdate,
    db: Session = Depends(get_db),
):
    if get_problem(db, problem_id) is None:
        raise HTTPException(status_code=404, detail="Problem not found")
    link = db.get(ProblemFragmentLink, link_id)
    if link is None or link.problem_id != problem_id:
        raise HTTPException(status_code=404, detail="Fragment link not found")
    return update_problem_fragment_link(db, link, payload)


@router.delete("/{problem_id}/fragments/{link_id}", status_code=204)
def api_remove_problem_fragment(problem_id: str, link_id: str, db: Session = Depends(get_db)):
    if get_problem(db, problem_id) is None:
        raise HTTPException(status_code=404, detail="Problem not found")
    link = db.get(ProblemFragmentLink, link_id)
    if link is None or link.problem_id != problem_id:
        raise HTTPException(status_code=404, detail="Fragment link not found")
    remove_problem_fragment_link(db, link)
    return None
