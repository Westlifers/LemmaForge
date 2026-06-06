from __future__ import annotations

import json
import shutil
import tempfile
from collections.abc import Callable
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.fragment import Fragment, Topic
from app.models.relation import Relation
from app.schemas.context_pack import (
    ContextPackSuggestRequest,
    ContextPackSuggestResult,
    ContextPackSuggestion,
)
from app.services.codex_import_service import (
    CodexImportError,
    CodexImportUnavailable,
    _extract_json_object,
    _repo_root,
    _run_codex_command,
)


def suggest_topic_context_pack(
    db: Session,
    payload: ContextPackSuggestRequest,
) -> ContextPackSuggestResult:
    topic = db.get(Topic, payload.topic_id)
    if topic is None:
        raise ValueError("Topic not found")

    fragments = list(
        db.execute(
            select(Fragment)
            .where(Fragment.topic_id == topic.id)
            .where(Fragment.status != "rejected")
            .order_by(Fragment.updated_at.desc())
        ).scalars()
    )
    fragment_ids = {fragment.id for fragment in fragments}
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
    try:
        suggestion = suggest_context_pack_with_codex(payload, topic, fragments, relations)
        return ContextPackSuggestResult(available=True, suggestion=suggestion)
    except CodexImportUnavailable as exc:
        return ContextPackSuggestResult(available=False, error=str(exc))
    except CodexImportError as exc:
        return ContextPackSuggestResult(available=True, error=str(exc), logs=exc.logs)


def suggest_context_pack_with_codex(
    payload: ContextPackSuggestRequest,
    topic: Topic,
    fragments: list[Fragment],
    relations: list[Relation],
    *,
    on_log: Callable[[str], None] | None = None,
) -> ContextPackSuggestion:
    codex_path = shutil.which("codex")
    if codex_path is None:
        raise CodexImportUnavailable("Codex CLI is not available on PATH.")

    repo_root = _repo_root()
    schema_path = repo_root / "schemas" / "context_pack_suggestion.schema.json"
    if not schema_path.exists():
        raise CodexImportError(f"Context pack suggestion schema not found: {schema_path}")

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
    prompt = _build_prompt(payload, topic, fragments, relations)
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
        suggestion = ContextPackSuggestion.model_validate_json(candidate)
    except ValidationError as exc:
        raise CodexImportError(exc.json(), logs=logs) from exc
    except ValueError as exc:
        try:
            suggestion = ContextPackSuggestion.model_validate(_extract_json_object(candidate))
        except (ValidationError, ValueError, json.JSONDecodeError) as fallback_exc:
            raise CodexImportError(
                f"Codex output was not valid context pack suggestion JSON: {exc}",
                logs=logs,
            ) from fallback_exc
    return _validate_suggestion(topic.id, fragments, suggestion)


def _build_prompt(
    payload: ContextPackSuggestRequest,
    topic: Topic,
    fragments: list[Fragment],
    relations: list[Relation],
) -> str:
    fragment_payload = [
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
    ]
    relation_payload = [
        {
            "source_fragment_id": relation.source_fragment_id,
            "relation_kind": relation.relation_kind,
            "target_fragment_id": relation.target_fragment_id,
            "confidence": relation.confidence,
        }
        for relation in relations
    ]
    context = {
        "topic": {
            "id": topic.id,
            "title": topic.title,
            "description": topic.description,
        },
        "objective": payload.objective,
        "task_prompt": payload.task_prompt,
        "fragments": fragment_payload,
        "relations": relation_payload,
    }
    return (
        "You are helping build a LemmaForge context pack for a future AI reasoning task.\n"
        "Return JSON only. Do not use Markdown or commentary.\n"
        "You are advisory only: select and order existing fragments, but do not rewrite any "
        "fragment body and do not invent fragment IDs.\n\n"
        "Output one object with these fields:\n"
        "- topic_id: the provided topic id\n"
        "- objective: the user's objective, possibly lightly clarified\n"
        "- task_prompt: the user-facing AI task wording, possibly lightly clarified\n"
        "- items: selected fragments in dependency-aware order, each with fragment_id, "
        "order_index, and a short reason\n"
        "- warnings: risks about status, provenance, uncertainty, or missing hypotheses\n"
        "- missing_context_questions: concise questions about context that seems absent\n\n"
        "Selection policy:\n"
        "- Use only fragment IDs from the provided fragments list.\n"
        "- Prefer fragments directly useful for the objective/task.\n"
        "- Put definitions and notation before claims, constructions, proof sketches, and questions.\n"
        "- Include draft/raw/candidate/superseded only when useful, and warn about them.\n"
        "- Never select rejected fragments; they are not provided.\n\n"
        f"LemmaForge topic context:\n{json.dumps(context, ensure_ascii=False, indent=2)}\n"
    )


def _validate_suggestion(
    topic_id: str,
    fragments: list[Fragment],
    suggestion: ContextPackSuggestion,
) -> ContextPackSuggestion:
    if suggestion.topic_id != topic_id:
        raise CodexImportError("Codex returned a suggestion for the wrong topic.")
    allowed_ids = {fragment.id for fragment in fragments if fragment.status != "rejected"}
    selected_ids = [item.fragment_id for item in suggestion.items]
    unknown = sorted(set(selected_ids) - allowed_ids)
    if unknown:
        raise CodexImportError(f"Codex suggested unknown fragments: {', '.join(unknown)}")
    seen: set[str] = set()
    deduped = []
    for item in sorted(suggestion.items, key=lambda value: value.order_index):
        if item.fragment_id in seen:
            continue
        seen.add(item.fragment_id)
        item.order_index = len(deduped)
        deduped.append(item)
    suggestion.items = deduped
    return suggestion
