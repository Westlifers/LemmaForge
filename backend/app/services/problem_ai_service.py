from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from collections.abc import Callable

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.fragment import Fragment, Topic
from app.models.relation import Relation
from app.schemas.problem import (
    ProblemSummaryProposal,
    ProblemSummaryRequest,
    ProblemSummaryResult,
)
from app.services.codex_import_service import (
    CodexImportError,
    CodexImportUnavailable,
    _extract_json_object,
    _repo_root,
    _run_codex_command,
)


def suggest_problem_summary(db: Session, payload: ProblemSummaryRequest) -> ProblemSummaryResult:
    topics, fragments, relations = _problem_context(db, payload)
    try:
        proposal = suggest_problem_summary_with_codex(payload, topics, fragments, relations)
        return ProblemSummaryResult(available=True, proposal=proposal)
    except CodexImportUnavailable as exc:
        return ProblemSummaryResult(available=False, error=str(exc))
    except CodexImportError as exc:
        return ProblemSummaryResult(available=True, error=str(exc), logs=exc.logs)


def suggest_problem_summary_with_codex(
    payload: ProblemSummaryRequest,
    topics: list[Topic],
    fragments: list[Fragment],
    relations: list[Relation],
    *,
    on_log: Callable[[str], None] | None = None,
) -> ProblemSummaryProposal:
    codex_path = shutil.which("codex")
    if codex_path is None:
        raise CodexImportUnavailable("Codex CLI is not available on PATH.")

    repo_root = _repo_root()
    schema_path = repo_root / "schemas" / "problem_summary.schema.json"
    if not schema_path.exists():
        raise CodexImportError(f"Problem summary schema not found: {schema_path}")

    with tempfile.NamedTemporaryFile(
        mode="w+", suffix=".json", delete=False, encoding="utf-8"
    ) as output_file:
        output_path = Path(output_file.name)

    command = [
        codex_path,
        "exec",
        "--ephemeral",
        "--sandbox",
        "read-only",
        "--output-schema",
        str(schema_path),
        "--output-last-message",
        str(output_path),
        "-",
    ]
    prompt = _build_prompt(payload, topics, fragments, relations)
    try:
        completed = _run_codex_command(
            command,
            prompt,
            repo_root,
            payload.timeout_seconds,
            on_log=on_log,
        )
        raw_output = output_path.read_text(encoding="utf-8").strip() if output_path.exists() else ""
    finally:
        try:
            output_path.unlink(missing_ok=True)
        except OSError:
            pass

    logs = completed.logs
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "Codex CLI failed."
        raise CodexImportError(detail, logs=logs)

    candidate = raw_output or completed.stdout.strip()
    if not candidate:
        raise CodexImportError("Codex CLI returned no output.", logs=logs)

    try:
        proposal = ProblemSummaryProposal.model_validate_json(candidate)
    except ValidationError as exc:
        raise CodexImportError(exc.json(), logs=logs) from exc
    except ValueError as exc:
        try:
            proposal = ProblemSummaryProposal.model_validate(_extract_json_object(candidate))
        except (ValidationError, ValueError, json.JSONDecodeError) as fallback_exc:
            raise CodexImportError(
                f"Codex output was not valid problem summary JSON: {exc}",
                logs=logs,
            ) from fallback_exc
    return _validate_proposal(fragments, proposal)


def _problem_context(
    db: Session,
    payload: ProblemSummaryRequest,
) -> tuple[list[Topic], list[Fragment], list[Relation]]:
    topics = []
    if payload.topic_ids:
        topics = list(db.execute(select(Topic).where(Topic.id.in_(payload.topic_ids))).scalars())
        missing_topics = sorted(set(payload.topic_ids) - {topic.id for topic in topics})
        if missing_topics:
            raise ValueError(f"Unknown topics: {', '.join(missing_topics)}")

    fragment_query = select(Fragment).where(Fragment.status != "rejected")
    if payload.topic_ids and payload.fragment_ids:
        fragment_query = fragment_query.where(
            (Fragment.topic_id.in_(payload.topic_ids)) | (Fragment.id.in_(payload.fragment_ids))
        )
    elif payload.topic_ids:
        fragment_query = fragment_query.where(Fragment.topic_id.in_(payload.topic_ids))
    else:
        fragment_query = fragment_query.where(Fragment.id.in_(payload.fragment_ids))
    fragments = list(db.execute(fragment_query.order_by(Fragment.updated_at.desc())).scalars())

    found_fragment_ids = {fragment.id for fragment in fragments}
    missing_fragments = sorted(set(payload.fragment_ids) - found_fragment_ids)
    if missing_fragments:
        raise ValueError(f"Unknown or rejected fragments: {', '.join(missing_fragments)}")

    relations: list[Relation] = []
    if found_fragment_ids:
        relations = list(
            db.execute(
                select(Relation)
                .where(Relation.source_fragment_id.in_(found_fragment_ids))
                .where(Relation.target_fragment_id.in_(found_fragment_ids))
                .order_by(Relation.created_at.desc())
            ).scalars()
        )
    return topics, fragments, relations


def _build_prompt(
    payload: ProblemSummaryRequest,
    topics: list[Topic],
    fragments: list[Fragment],
    relations: list[Relation],
) -> str:
    context = {
        "title_hint": payload.title_hint,
        "objective_hint": payload.objective_hint,
        "topics": [
            {"id": topic.id, "title": topic.title, "description": topic.description}
            for topic in topics
        ],
        "fragments": [
            {
                "id": fragment.id,
                "title": fragment.title,
                "type": fragment.type,
                "status": fragment.status,
                "origin_classification": fragment.origin_classification,
                "exactness": fragment.exactness,
                "body_excerpt": fragment.body[:1200],
            }
            for fragment in fragments
        ],
        "relations": [
            {
                "source_fragment_id": relation.source_fragment_id,
                "relation_kind": relation.relation_kind,
                "target_fragment_id": relation.target_fragment_id,
                "confidence": relation.confidence,
            }
            for relation in relations
        ],
    }
    return (
        "You are helping define a LemmaForge ResearchProblem from selected "
        "mathematical fragments and topics.\n"
        "Return JSON only. Do not use Markdown or commentary.\n"
        "You are advisory only: propose a problem summary and suggested fragment "
        "roles, but do not claim that uncertain mathematics is proved.\n\n"
        "Output one object with these fields:\n"
        "- title\n"
        "- objective\n"
        "- current_formulation\n"
        "- motivation\n"
        "- why_it_matters\n"
        "- suggested_fragment_roles: only use fragment IDs from the provided list\n"
        "- open_gaps\n"
        "- warnings\n\n"
        "Role policy:\n"
        "- Main question or Question fragments may be main_question.\n"
        "- Definition-like fragments may be active_definition or candidate_definition.\n"
        "- Theorem/Proposition/Lemma/Conjecture fragments may be claim.\n"
        "- Proof/ProofSketch fragments may be proof.\n"
        "- Examples and counterexamples should use their dedicated roles.\n"
        "- External notes and reading notes should usually be source_note or background.\n"
        "- If a fragment is draft/raw/candidate/superseded, warn about relying on it.\n\n"
        f"LemmaForge context:\n{json.dumps(context, ensure_ascii=False, indent=2)}\n"
    )


def _validate_proposal(
    fragments: list[Fragment],
    proposal: ProblemSummaryProposal,
) -> ProblemSummaryProposal:
    allowed_ids = {fragment.id for fragment in fragments}
    selected_ids = [item.fragment_id for item in proposal.suggested_fragment_roles]
    unknown = sorted(set(selected_ids) - allowed_ids)
    if unknown:
        raise CodexImportError(f"Codex suggested unknown fragments: {', '.join(unknown)}")
    seen: set[str] = set()
    deduped = []
    for item in proposal.suggested_fragment_roles:
        if item.fragment_id in seen:
            continue
        seen.add(item.fragment_id)
        deduped.append(item)
    proposal.suggested_fragment_roles = deduped
    return proposal
