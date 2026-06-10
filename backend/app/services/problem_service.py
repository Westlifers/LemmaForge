from __future__ import annotations

from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.fragment import Fragment, Topic
from app.models.problem import (
    Attempt,
    AttemptFragmentLink,
    ProblemFragmentLink,
    ProblemGraphNodePosition,
    ProblemTopicLink,
    ResearchProblem,
)
from app.models.relation import Relation
from app.schemas.problem import (
    ProblemFragmentLinkCreate,
    ProblemFragmentLinkUpdate,
    ProblemGraphLayoutUpdate,
    ProblemGraphNodePositionRead,
    ProblemWorkspaceRead,
    ProblemTopicLinkCreate,
    ResearchProblemCreate,
    ResearchProblemUpdate,
)
from app.services.ids import slugify, unique_model_id


def list_problems(
    db: Session,
    *,
    search: str | None = None,
    status: str | None = None,
) -> list[ResearchProblem]:
    query = select(ResearchProblem).order_by(ResearchProblem.updated_at.desc())
    if search:
        needle = f"%{search}%"
        query = query.where(
            or_(
                ResearchProblem.title.ilike(needle),
                ResearchProblem.objective.ilike(needle),
                ResearchProblem.current_formulation.ilike(needle),
            )
        )
    if status:
        query = query.where(ResearchProblem.status == status)
    return list(db.execute(query).scalars())


def get_problem(db: Session, problem_id: str) -> ResearchProblem | None:
    return db.execute(
        select(ResearchProblem)
        .where(ResearchProblem.id == problem_id)
        .options(
            selectinload(ResearchProblem.topic_links).selectinload(ProblemTopicLink.topic),
            selectinload(ResearchProblem.fragment_links).selectinload(ProblemFragmentLink.fragment),
            selectinload(ResearchProblem.attempts).selectinload(Attempt.fragment_links).selectinload(AttemptFragmentLink.fragment),
        )
        .execution_options(populate_existing=True)
    ).scalar_one_or_none()


def create_problem(db: Session, payload: ResearchProblemCreate) -> ResearchProblem:
    problem = ResearchProblem(
        id=unique_model_id(db, ResearchProblem, f"prob_{slugify(payload.title)}"),
        title=payload.title,
        status=payload.status,
        objective=payload.objective,
        current_formulation=payload.current_formulation,
        motivation=payload.motivation,
        why_it_matters=payload.why_it_matters,
    )
    db.add(problem)
    db.commit()
    return get_problem(db, problem.id) or problem


def update_problem(
    db: Session,
    problem: ResearchProblem,
    payload: ResearchProblemUpdate,
) -> ResearchProblem:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(problem, key, value)
    db.commit()
    return get_problem(db, problem.id) or problem


def delete_problem(db: Session, problem: ResearchProblem) -> None:
    attempt_ids = list(db.execute(select(Attempt.id).where(Attempt.problem_id == problem.id)).scalars())
    if attempt_ids:
        db.execute(delete(AttemptFragmentLink).where(AttemptFragmentLink.attempt_id.in_(attempt_ids)))
    db.execute(delete(Attempt).where(Attempt.problem_id == problem.id))
    db.execute(delete(ProblemGraphNodePosition).where(ProblemGraphNodePosition.problem_id == problem.id))
    db.execute(delete(ProblemFragmentLink).where(ProblemFragmentLink.problem_id == problem.id))
    db.execute(delete(ProblemTopicLink).where(ProblemTopicLink.problem_id == problem.id))
    db.delete(problem)
    db.commit()


def list_problem_topic_links(db: Session, problem_id: str) -> list[ProblemTopicLink]:
    return list(
        db.execute(
            select(ProblemTopicLink)
            .where(ProblemTopicLink.problem_id == problem_id)
            .options(selectinload(ProblemTopicLink.topic))
            .order_by(ProblemTopicLink.created_at)
        ).scalars()
    )


def add_problem_topic_link(
    db: Session,
    problem: ResearchProblem,
    payload: ProblemTopicLinkCreate,
) -> ProblemTopicLink:
    if db.get(Topic, payload.topic_id) is None:
        raise ValueError(f"Unknown topic: {payload.topic_id}")
    existing = db.execute(
        select(ProblemTopicLink)
        .where(ProblemTopicLink.problem_id == problem.id)
        .where(ProblemTopicLink.topic_id == payload.topic_id)
    ).scalar_one_or_none()
    if existing is not None:
        raise ValueError("Topic is already linked to this problem")
    link = ProblemTopicLink(
        id=unique_model_id(db, ProblemTopicLink, f"pt_{problem.id}_{payload.topic_id}"),
        problem_id=problem.id,
        topic_id=payload.topic_id,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


def remove_problem_topic_link(db: Session, problem_id: str, topic_id: str) -> bool:
    link = db.execute(
        select(ProblemTopicLink)
        .where(ProblemTopicLink.problem_id == problem_id)
        .where(ProblemTopicLink.topic_id == topic_id)
    ).scalar_one_or_none()
    if link is None:
        return False
    db.delete(link)
    db.commit()
    return True


def list_problem_fragment_links(db: Session, problem_id: str) -> list[ProblemFragmentLink]:
    return list(
        db.execute(
            select(ProblemFragmentLink)
            .where(ProblemFragmentLink.problem_id == problem_id)
            .options(selectinload(ProblemFragmentLink.fragment))
            .order_by(ProblemFragmentLink.created_at)
        ).scalars()
    )


def add_problem_fragment_link(
    db: Session,
    problem: ResearchProblem,
    payload: ProblemFragmentLinkCreate,
) -> ProblemFragmentLink:
    if db.get(Fragment, payload.fragment_id) is None:
        raise ValueError(f"Unknown fragment: {payload.fragment_id}")
    existing = db.execute(
        select(ProblemFragmentLink)
        .where(ProblemFragmentLink.problem_id == problem.id)
        .where(ProblemFragmentLink.fragment_id == payload.fragment_id)
    ).scalar_one_or_none()
    if existing is not None:
        raise ValueError("Fragment is already linked to this problem")
    link = ProblemFragmentLink(
        id=unique_model_id(db, ProblemFragmentLink, f"pf_{problem.id}_{payload.fragment_id}"),
        problem_id=problem.id,
        fragment_id=payload.fragment_id,
        role=payload.role,
        note=payload.note,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


def update_problem_fragment_link(
    db: Session,
    link: ProblemFragmentLink,
    payload: ProblemFragmentLinkUpdate,
) -> ProblemFragmentLink:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(link, key, value)
    db.commit()
    db.refresh(link)
    return link


def remove_problem_fragment_link(db: Session, link: ProblemFragmentLink) -> None:
    db.delete(link)
    db.commit()


def get_problem_workspace(db: Session, problem: ResearchProblem) -> ProblemWorkspaceRead:
    loaded = get_problem(db, problem.id) or problem
    fragment_links = list_problem_fragment_links(db, problem.id)
    topic_links = list_problem_topic_links(db, problem.id)
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
    positions = {
        position.node_key: ProblemGraphNodePositionRead(
            node_key=position.node_key,
            x=position.x,
            y=position.y,
        )
        for position in db.execute(
            select(ProblemGraphNodePosition).where(ProblemGraphNodePosition.problem_id == problem.id)
        ).scalars()
    }
    return ProblemWorkspaceRead(
        problem=loaded,
        topic_links=topic_links,
        fragment_links=fragment_links,
        relations=relations,
        attempts=list(loaded.attempts),
        positions=positions,
    )


def update_problem_graph_layout(
    db: Session,
    problem: ResearchProblem,
    payload: ProblemGraphLayoutUpdate,
) -> ProblemWorkspaceRead:
    allowed_node_keys = {f"problem:{problem.id}"}
    allowed_node_keys.update(
        f"fragment_link:{link.id}" for link in list_problem_fragment_links(db, problem.id)
    )
    unknown_keys = sorted(set(payload.positions) - allowed_node_keys)
    if unknown_keys:
        raise ValueError(f"Unknown problem graph nodes: {', '.join(unknown_keys)}")
    for node_key, position in payload.positions.items():
        existing = db.get(ProblemGraphNodePosition, (problem.id, node_key))
        if existing is None:
            db.add(
                ProblemGraphNodePosition(
                    problem_id=problem.id,
                    node_key=node_key,
                    x=position.x,
                    y=position.y,
                )
            )
        else:
            existing.x = position.x
            existing.y = position.y
    db.commit()
    return get_problem_workspace(db, problem)
