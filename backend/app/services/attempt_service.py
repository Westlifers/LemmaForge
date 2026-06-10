from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.models.fragment import Fragment
from app.models.problem import Attempt, AttemptFragmentLink, ResearchProblem
from app.models.relation import Relation
from app.schemas.problem import (
    AttemptCreate,
    AttemptFragmentLinkCreate,
    AttemptFragmentLinkUpdate,
    AttemptUpdate,
    AttemptWorkspaceRead,
)
from app.services.ids import slugify, unique_model_id
from app.services.problem_service import get_problem


def list_attempts_for_problem(db: Session, problem_id: str) -> list[Attempt]:
    return list(
        db.execute(
            select(Attempt)
            .where(Attempt.problem_id == problem_id)
            .options(selectinload(Attempt.fragment_links).selectinload(AttemptFragmentLink.fragment))
            .order_by(Attempt.updated_at.desc())
        ).scalars()
    )


def get_attempt(db: Session, attempt_id: str) -> Attempt | None:
    return db.execute(
        select(Attempt)
        .where(Attempt.id == attempt_id)
        .options(selectinload(Attempt.fragment_links).selectinload(AttemptFragmentLink.fragment))
        .execution_options(populate_existing=True)
    ).scalar_one_or_none()


def create_attempt(db: Session, problem: ResearchProblem, payload: AttemptCreate) -> Attempt:
    attempt = Attempt(
        id=unique_model_id(db, Attempt, f"att_{slugify(payload.title)}"),
        problem_id=problem.id,
        title=payload.title,
        status=payload.status,
        strategy=payload.strategy,
        expected_outcome=payload.expected_outcome,
        result_summary=payload.result_summary,
        failure_reason=payload.failure_reason,
        next_step=payload.next_step,
    )
    db.add(attempt)
    db.commit()
    return get_attempt(db, attempt.id) or attempt


def update_attempt(db: Session, attempt: Attempt, payload: AttemptUpdate) -> Attempt:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(attempt, key, value)
    db.commit()
    return get_attempt(db, attempt.id) or attempt


def delete_attempt(db: Session, attempt: Attempt) -> None:
    db.execute(delete(AttemptFragmentLink).where(AttemptFragmentLink.attempt_id == attempt.id))
    db.delete(attempt)
    db.commit()


def list_attempt_fragment_links(db: Session, attempt_id: str) -> list[AttemptFragmentLink]:
    return list(
        db.execute(
            select(AttemptFragmentLink)
            .where(AttemptFragmentLink.attempt_id == attempt_id)
            .options(selectinload(AttemptFragmentLink.fragment))
            .order_by(AttemptFragmentLink.created_at)
        ).scalars()
    )


def add_attempt_fragment_link(
    db: Session,
    attempt: Attempt,
    payload: AttemptFragmentLinkCreate,
) -> AttemptFragmentLink:
    if db.get(Fragment, payload.fragment_id) is None:
        raise ValueError(f"Unknown fragment: {payload.fragment_id}")
    existing = db.execute(
        select(AttemptFragmentLink)
        .where(AttemptFragmentLink.attempt_id == attempt.id)
        .where(AttemptFragmentLink.fragment_id == payload.fragment_id)
    ).scalar_one_or_none()
    if existing is not None:
        raise ValueError("Fragment is already linked to this attempt")
    link = AttemptFragmentLink(
        id=unique_model_id(db, AttemptFragmentLink, f"af_{attempt.id}_{payload.fragment_id}"),
        attempt_id=attempt.id,
        fragment_id=payload.fragment_id,
        role=payload.role,
        note=payload.note,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


def update_attempt_fragment_link(
    db: Session,
    link: AttemptFragmentLink,
    payload: AttemptFragmentLinkUpdate,
) -> AttemptFragmentLink:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(link, key, value)
    db.commit()
    db.refresh(link)
    return link


def remove_attempt_fragment_link(db: Session, link: AttemptFragmentLink) -> None:
    db.delete(link)
    db.commit()


def get_attempt_workspace(db: Session, attempt: Attempt) -> AttemptWorkspaceRead:
    loaded = get_attempt(db, attempt.id) or attempt
    problem = get_problem(db, loaded.problem_id)
    if problem is None:
        raise ValueError("Attempt problem not found")
    fragment_links = list_attempt_fragment_links(db, loaded.id)
    fragment_ids = {link.fragment_id for link in fragment_links}
    relations: list[Relation] = []
    if fragment_ids:
        relations = list(
            db.execute(
                select(Relation)
                .where(Relation.source_fragment_id.in_(fragment_ids))
                .where(Relation.target_fragment_id.in_(fragment_ids))
                .order_by(Relation.created_at.desc())
            ).scalars()
        )
    return AttemptWorkspaceRead(
        attempt=loaded,
        problem=problem,
        fragment_links=fragment_links,
        relations=relations,
    )
