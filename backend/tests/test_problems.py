from __future__ import annotations

import pytest
import time
from sqlalchemy import select

from app.models.fragment import Fragment, Topic
from app.models.problem import (
    Attempt,
    AttemptFragmentLink,
    AttemptGraphNodePosition,
    ProblemFragmentLink,
    ProblemTopicLink,
    ResearchProblem,
)
from app.schemas.fragment import FragmentCreate, TopicCreate
from app.schemas.problem import (
    AttemptCreate,
    AttemptFragmentLinkCreate,
    AttemptFragmentLinkUpdate,
    AttemptGraphLayoutUpdate,
    AttemptGraphNodePositionRead,
    AttemptUpdate,
    ProblemFragmentLinkCreate,
    ProblemFragmentLinkUpdate,
    ProblemGraphLayoutUpdate,
    ProblemGraphNodePositionRead,
    ProblemSummaryProposal,
    ProblemSummaryRequest,
    ProblemSuggestedFragmentRole,
    ProblemTopicLinkCreate,
    ResearchProblemCreate,
    ResearchProblemUpdate,
)
from app.services.codex_import_service import CodexImportError, CodexImportUnavailable
from app.services.fragment_service import create_fragment
from app.services.problem_ai_service import suggest_problem_summary
from app.services.problem_ai_job_service import read_problem_summary_job, start_problem_summary_job
from app.services import problem_ai_service
from app.services.attempt_service import (
    add_attempt_fragment_link,
    create_attempt,
    delete_attempt,
    get_attempt_workspace,
    list_attempts_for_problem,
    remove_attempt_fragment_link,
    update_attempt_graph_layout,
    update_attempt,
    update_attempt_fragment_link,
)
from app.services.problem_service import (
    add_problem_fragment_link,
    add_problem_topic_link,
    create_problem,
    delete_problem,
    get_problem,
    get_problem_workspace,
    list_problem_fragment_links,
    list_problem_topic_links,
    list_problems,
    remove_problem_fragment_link,
    remove_problem_topic_link,
    update_problem,
    update_problem_graph_layout,
    update_problem_fragment_link,
)
from app.schemas.relation import RelationCreate
from app.services.relation_service import create_relation
from app.services.topic_service import create_topic


def _topic(db, title="Canonical extension"):
    return create_topic(db, TopicCreate(title=title))


def _fragment(db, topic_id: str | None = None, title="Candidate definition", type_="Definition"):
    return create_fragment(
        db,
        FragmentCreate(
            type=type_,
            title=title,
            status="candidate",
            body=f"{title} body.",
            topic_id=topic_id,
            origin_classification="user_original",
            exactness="original",
        ),
    )


def _problem(db, title="Find compactness condition"):
    return create_problem(
        db,
        ResearchProblemCreate(
            title=title,
            status="active",
            objective="Find the correct enriched compactness condition.",
            current_formulation="Start with the canonical extension construction.",
        ),
    )


def test_problem_create_list_read_update_delete_keeps_topics_and_fragments(db_session):
    db, _tmp_path = db_session
    topic = _topic(db)
    fragment = _fragment(db, topic.id)
    problem = _problem(db)
    add_problem_topic_link(db, problem, ProblemTopicLinkCreate(topic_id=topic.id))
    add_problem_fragment_link(
        db,
        problem,
        ProblemFragmentLinkCreate(fragment_id=fragment.id, role="candidate_definition"),
    )

    assert list_problems(db, status="active")[0].id == problem.id
    loaded = get_problem(db, problem.id)
    assert loaded is not None
    assert loaded.topic_links[0].topic_id == topic.id
    assert loaded.fragment_links[0].fragment_id == fragment.id

    updated = update_problem(
        db,
        problem,
        ResearchProblemUpdate(status="blocked", motivation="The current definition is too strong."),
    )
    assert updated.status == "blocked"
    assert updated.motivation == "The current definition is too strong."

    delete_problem(db, updated)

    assert db.get(ResearchProblem, problem.id) is None
    assert db.get(Topic, topic.id) is not None
    assert db.get(Fragment, fragment.id) is not None
    assert db.execute(select(ProblemTopicLink)).scalars().all() == []
    assert db.execute(select(ProblemFragmentLink)).scalars().all() == []


def test_problem_topic_links_reject_duplicates_and_unknown_topics(db_session):
    db, _tmp_path = db_session
    topic = _topic(db)
    problem = _problem(db)

    link = add_problem_topic_link(db, problem, ProblemTopicLinkCreate(topic_id=topic.id))

    assert list_problem_topic_links(db, problem.id)[0].id == link.id
    with pytest.raises(ValueError, match="already linked"):
        add_problem_topic_link(db, problem, ProblemTopicLinkCreate(topic_id=topic.id))
    with pytest.raises(ValueError, match="Unknown topic"):
        add_problem_topic_link(db, problem, ProblemTopicLinkCreate(topic_id="missing_topic"))

    assert remove_problem_topic_link(db, problem.id, topic.id) is True
    assert remove_problem_topic_link(db, problem.id, topic.id) is False


def test_problem_fragment_links_update_and_reject_duplicates(db_session):
    db, _tmp_path = db_session
    problem = _problem(db)
    fragment = _fragment(db)

    link = add_problem_fragment_link(
        db,
        problem,
        ProblemFragmentLinkCreate(fragment_id=fragment.id, role="main_question", note="Start here."),
    )
    updated = update_problem_fragment_link(
        db,
        link,
        ProblemFragmentLinkUpdate(role="gap", note="The proof is missing."),
    )

    assert updated.role == "gap"
    assert updated.note == "The proof is missing."
    assert list_problem_fragment_links(db, problem.id)[0].fragment_id == fragment.id
    with pytest.raises(ValueError, match="already linked"):
        add_problem_fragment_link(
            db,
            problem,
            ProblemFragmentLinkCreate(fragment_id=fragment.id, role="claim"),
        )
    with pytest.raises(ValueError, match="Unknown fragment"):
        add_problem_fragment_link(
            db,
            problem,
            ProblemFragmentLinkCreate(fragment_id="missing_fragment", role="claim"),
        )

    remove_problem_fragment_link(db, updated)
    assert list_problem_fragment_links(db, problem.id) == []
    assert db.get(Fragment, fragment.id) is not None


def test_problem_workspace_returns_internal_relations_and_layout(db_session):
    db, _tmp_path = db_session
    problem = _problem(db)
    definition = _fragment(db, title="Workspace definition", type_="Definition")
    claim = _fragment(db, title="Workspace claim", type_="Theorem")
    add_problem_fragment_link(
        db,
        problem,
        ProblemFragmentLinkCreate(fragment_id=definition.id, role="active_definition"),
    )
    claim_link = add_problem_fragment_link(
        db,
        problem,
        ProblemFragmentLinkCreate(fragment_id=claim.id, role="claim"),
    )
    create_relation(
        db,
        RelationCreate(
            source_fragment_id=claim.id,
            relation_kind="depends_on",
            target_fragment_id=definition.id,
        ),
    )

    workspace = get_problem_workspace(db, problem)

    assert workspace.problem.id == problem.id
    assert {link.fragment_id for link in workspace.fragment_links} == {definition.id, claim.id}
    assert len(workspace.relations) == 1

    updated = update_problem_graph_layout(
        db,
        problem,
        ProblemGraphLayoutUpdate(
            positions={
                f"problem:{problem.id}": ProblemGraphNodePositionRead(
                    node_key=f"problem:{problem.id}",
                    x=100,
                    y=120,
                ),
                f"fragment_link:{claim_link.id}": ProblemGraphNodePositionRead(
                    node_key=f"fragment_link:{claim_link.id}",
                    x=400,
                    y=120,
                ),
            }
        ),
    )

    assert updated.positions[f"problem:{problem.id}"].x == 100
    assert updated.positions[f"fragment_link:{claim_link.id}"].y == 120
    with pytest.raises(ValueError, match="Unknown problem graph nodes"):
        update_problem_graph_layout(
            db,
            problem,
            ProblemGraphLayoutUpdate(
                positions={
                    "fragment_link:missing": ProblemGraphNodePositionRead(
                        node_key="fragment_link:missing",
                        x=0,
                        y=0,
                    )
                }
            ),
        )


def test_attempt_create_update_link_workspace_and_delete_keeps_fragments(db_session):
    db, _tmp_path = db_session
    problem = _problem(db)
    fragment = _fragment(db, title="Attempt input")
    produced = _fragment(db, title="Attempt produced", type_="Question")
    attempt = create_attempt(
        db,
        problem,
        AttemptCreate(
            title="Try Phi compactness",
            status="in_progress",
            strategy="Restrict compactness to a chosen class of weights.",
            expected_outcome="A weaker condition still supports the construction.",
            next_step="Test one-object quantale case.",
        ),
    )

    assert list_attempts_for_problem(db, problem.id)[0].id == attempt.id
    updated_attempt = update_attempt(
        db,
        attempt,
        AttemptUpdate(status="blocked", failure_reason="Need exactness assumptions."),
    )
    assert updated_attempt.status == "blocked"
    assert updated_attempt.failure_reason == "Need exactness assumptions."

    link = add_attempt_fragment_link(
        db,
        attempt,
        AttemptFragmentLinkCreate(fragment_id=fragment.id, role="input", note="Use as seed."),
    )
    add_attempt_fragment_link(
        db,
        attempt,
        AttemptFragmentLinkCreate(fragment_id=produced.id, role="produced"),
    )
    with pytest.raises(ValueError, match="already linked"):
        add_attempt_fragment_link(
            db,
            attempt,
            AttemptFragmentLinkCreate(fragment_id=fragment.id, role="assumption"),
        )
    updated_link = update_attempt_fragment_link(
        db,
        link,
        AttemptFragmentLinkUpdate(role="blocked_by", note="Missing verification."),
    )
    assert updated_link.role == "blocked_by"

    workspace = get_attempt_workspace(db, attempt)
    assert workspace.attempt.id == attempt.id
    assert workspace.problem.id == problem.id
    assert {item.fragment_id for item in workspace.fragment_links} == {fragment.id, produced.id}

    saved_layout = update_attempt_graph_layout(
        db,
        attempt,
        AttemptGraphLayoutUpdate(
            positions={
                f"attempt:{attempt.id}": AttemptGraphNodePositionRead(
                    node_key=f"attempt:{attempt.id}",
                    x=160,
                    y=180,
                ),
                f"attempt_link:{link.id}": AttemptGraphNodePositionRead(
                    node_key=f"attempt_link:{link.id}",
                    x=420,
                    y=180,
                ),
            }
        ),
    )
    assert saved_layout.positions[f"attempt:{attempt.id}"].x == 160
    assert saved_layout.positions[f"attempt_link:{link.id}"].y == 180
    reloaded_workspace = get_attempt_workspace(db, attempt)
    assert reloaded_workspace.positions[f"attempt:{attempt.id}"].x == 160

    with pytest.raises(ValueError, match="Unknown attempt graph nodes"):
        update_attempt_graph_layout(
            db,
            attempt,
            AttemptGraphLayoutUpdate(
                positions={
                    "attempt_link:missing": AttemptGraphNodePositionRead(
                        node_key="attempt_link:missing",
                        x=0,
                        y=0,
                    )
                }
            ),
        )

    remove_attempt_fragment_link(db, updated_link)
    assert db.get(Fragment, fragment.id) is not None
    delete_attempt(db, attempt)
    assert db.get(Attempt, attempt.id) is None
    assert db.get(Fragment, produced.id) is not None
    assert db.execute(select(AttemptFragmentLink)).scalars().all() == []
    assert db.execute(select(AttemptGraphNodePosition)).scalars().all() == []


def test_deleting_problem_deletes_attempts_but_keeps_fragments(db_session):
    db, _tmp_path = db_session
    problem = _problem(db)
    fragment = _fragment(db)
    attempt = create_attempt(
        db,
        problem,
        AttemptCreate(title="Temporary attempt", strategy="Try a temporary strategy."),
    )
    add_attempt_fragment_link(
        db,
        attempt,
        AttemptFragmentLinkCreate(fragment_id=fragment.id, role="input"),
    )
    update_attempt_graph_layout(
        db,
        attempt,
        AttemptGraphLayoutUpdate(
            positions={
                f"attempt:{attempt.id}": AttemptGraphNodePositionRead(
                    node_key=f"attempt:{attempt.id}",
                    x=10,
                    y=20,
                )
            }
        ),
    )

    delete_problem(db, problem)

    assert db.get(ResearchProblem, problem.id) is None
    assert db.get(Attempt, attempt.id) is None
    assert db.get(Fragment, fragment.id) is not None
    assert db.execute(select(AttemptFragmentLink)).scalars().all() == []
    assert db.execute(select(AttemptGraphNodePosition)).scalars().all() == []


def test_problem_summary_suggestion_is_advisory_and_validated(db_session, monkeypatch):
    db, _tmp_path = db_session
    topic = _topic(db)
    definition = _fragment(db, topic.id, title="Phi compactness", type_="Definition")
    claim = _fragment(db, topic.id, title="Canonical extension claim", type_="Theorem")
    rejected = create_fragment(
        db,
        FragmentCreate(
            type="Remark",
            title="Rejected note",
            status="rejected",
            body="Do not use this.",
            topic_id=topic.id,
            origin_classification="user_original",
            exactness="original",
        ),
    )

    def fake_suggest(payload, topics, fragments, relations):
        assert [item.id for item in topics] == [topic.id]
        assert {fragment.id for fragment in fragments} == {definition.id, claim.id}
        assert rejected.id not in {fragment.id for fragment in fragments}
        return ProblemSummaryProposal(
            title="Find Phi compactness",
            objective=payload.objective_hint or "Find the right compactness condition.",
            current_formulation="Use Phi-weighted compactness.",
            motivation="The unrestricted condition appears too strong.",
            why_it_matters="It controls the canonical extension construction.",
            suggested_fragment_roles=[
                ProblemSuggestedFragmentRole(
                    fragment_id=definition.id,
                    role="candidate_definition",
                    note="Main candidate definition.",
                ),
                ProblemSuggestedFragmentRole(
                    fragment_id=claim.id,
                    role="claim",
                    note="Target claim.",
                ),
            ],
            open_gaps=["Need examples."],
            warnings=["Claim is only candidate-level."],
        )

    monkeypatch.setattr(problem_ai_service, "suggest_problem_summary_with_codex", fake_suggest)

    result = suggest_problem_summary(
        db,
        ProblemSummaryRequest(
            topic_ids=[topic.id],
            objective_hint="Find the right compactness condition.",
        ),
    )

    assert result.available is True
    assert result.proposal is not None
    assert result.proposal.title == "Find Phi compactness"
    assert [item.fragment_id for item in result.proposal.suggested_fragment_roles] == [
        definition.id,
        claim.id,
    ]
    assert db.execute(select(ResearchProblem)).scalars().all() == []
    assert db.execute(select(ProblemFragmentLink)).scalars().all() == []


def test_problem_summary_reports_codex_failures(db_session, monkeypatch):
    db, _tmp_path = db_session
    fragment = _fragment(db)
    request = ProblemSummaryRequest(fragment_ids=[fragment.id])

    def unavailable(*args, **kwargs):
        raise CodexImportUnavailable("Codex CLI is not available on PATH.")

    monkeypatch.setattr(problem_ai_service, "suggest_problem_summary_with_codex", unavailable)
    unavailable_result = suggest_problem_summary(db, request)
    assert unavailable_result.available is False

    def invalid(*args, **kwargs):
        raise CodexImportError("Invalid JSON", logs=["bad output"])

    monkeypatch.setattr(problem_ai_service, "suggest_problem_summary_with_codex", invalid)
    invalid_result = suggest_problem_summary(db, request)
    assert invalid_result.available is True
    assert invalid_result.error == "Invalid JSON"
    assert invalid_result.logs == ["bad output"]


def test_problem_summary_job_reports_logs_and_does_not_mutate(db_session, monkeypatch):
    db, _tmp_path = db_session
    topic = _topic(db)
    fragment = _fragment(db, topic.id)

    def fake_suggest(payload, topics, fragments, relations, on_log=None):
        if on_log:
            on_log("Summarizing problem context.")
        return ProblemSummaryProposal(
            title="Job problem proposal",
            objective="Understand the target problem.",
            current_formulation="Use the selected fragment.",
            motivation=None,
            why_it_matters=None,
            suggested_fragment_roles=[
                ProblemSuggestedFragmentRole(
                    fragment_id=fragments[0].id,
                    role="main_question",
                    note="Useful seed.",
                )
            ],
            open_gaps=[],
            warnings=[],
        )

    monkeypatch.setattr(
        "app.services.problem_ai_job_service.suggest_problem_summary_with_codex",
        fake_suggest,
    )

    started = start_problem_summary_job(ProblemSummaryRequest(topic_ids=[topic.id]))

    for _ in range(30):
        read = read_problem_summary_job(started.job_id)
        if read.status == "succeeded":
            break
        time.sleep(0.05)
    else:
        pytest.fail("Problem summary job did not finish")

    assert read.result is not None
    assert read.result.proposal is not None
    assert read.result.proposal.suggested_fragment_roles[0].fragment_id == fragment.id
    assert read.logs == ["Summarizing problem context."]
    assert db.execute(select(ResearchProblem)).scalars().all() == []


def test_problem_summary_rejects_unknown_context(db_session):
    db, _tmp_path = db_session

    with pytest.raises(ValueError, match="Unknown topics"):
        suggest_problem_summary(db, ProblemSummaryRequest(topic_ids=["missing_topic"]))

    with pytest.raises(ValueError, match="Unknown or rejected fragments"):
        suggest_problem_summary(db, ProblemSummaryRequest(fragment_ids=["missing_fragment"]))
