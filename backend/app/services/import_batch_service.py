from __future__ import annotations

import json
from datetime import timezone
from difflib import SequenceMatcher

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.fragment import Fragment, utc_now
from app.models.import_batch import ImportBatch
from app.schemas.import_batch import (
    DuplicateSuggestion,
    ImportBatchCreate,
    ImportBatchRead,
    ImportBatchSuggestionRead,
    ImportBatchUpdate,
)
from app.schemas.research_patch import ImportCommitResult, ResearchPatch
from app.services.ids import slugify, unique_model_id
from app.services.import_service import commit_patch, preview_patch


def list_import_batches(db: Session) -> list[ImportBatchRead]:
    batches = db.execute(select(ImportBatch).order_by(ImportBatch.updated_at.desc())).scalars()
    return [_read_batch(batch) for batch in batches]


def get_import_batch(db: Session, batch_id: str) -> ImportBatch | None:
    return db.get(ImportBatch, batch_id)


def read_import_batch(batch: ImportBatch) -> ImportBatchRead:
    return _read_batch(batch)


def create_import_batch(db: Session, payload: ImportBatchCreate) -> ImportBatchRead:
    patch = payload.patch or _manual_patch_from_payload(payload)
    batch = ImportBatch(
        id=unique_model_id(db, ImportBatch, f"imp_{slugify(_batch_title(payload, patch))}"),
        status="draft",
        raw_excerpt=payload.raw_excerpt,
        topic_hint=payload.topic_hint or patch.metadata.topic_hint,
        citekey=payload.citekey,
        locator=payload.locator,
        patch_json=_patch_to_json(patch),
        warnings_json=json.dumps(patch.warnings),
        review_note=payload.review_note,
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return _read_batch(batch)


def update_import_batch(
    db: Session,
    batch: ImportBatch,
    payload: ImportBatchUpdate,
) -> ImportBatchRead:
    changes = payload.model_dump(exclude_unset=True)
    patch_changed = False
    if "patch" in changes:
        patch = changes.pop("patch")
        if patch is not None:
            batch.patch_json = _patch_to_json(patch)
            batch.warnings_json = json.dumps(patch.warnings)
            patch_changed = True
    for key, value in changes.items():
        setattr(batch, key, value)
    if batch.patch_json is None and batch.raw_excerpt.strip():
        patch = _manual_patch_from_payload(
            ImportBatchCreate(
                raw_excerpt=batch.raw_excerpt,
                topic_hint=batch.topic_hint,
                citekey=batch.citekey,
                locator=batch.locator,
                review_note=batch.review_note,
            )
        )
        batch.patch_json = _patch_to_json(patch)
        batch.warnings_json = json.dumps(patch.warnings)
        patch_changed = True
    if patch_changed and batch.status not in {"committed", "rejected"}:
        batch.status = "draft"
        batch.commit_result_json = None
        batch.reviewed_at = None
    db.commit()
    db.refresh(batch)
    return _read_batch(batch)


def validate_import_batch(db: Session, batch: ImportBatch) -> ImportBatchRead:
    if batch.patch_json is None and batch.raw_excerpt.strip():
        patch = _manual_patch_from_payload(
            ImportBatchCreate(
                raw_excerpt=batch.raw_excerpt,
                topic_hint=batch.topic_hint,
                citekey=batch.citekey,
                locator=batch.locator,
                review_note=batch.review_note,
            )
        )
        batch.patch_json = _patch_to_json(patch)
        batch.warnings_json = json.dumps(patch.warnings)
        db.flush()
    patch = _batch_patch(batch)
    preview = preview_patch(patch)
    batch.warnings_json = json.dumps(preview.warnings)
    batch.status = "validated"
    batch.commit_result_json = None
    batch.reviewed_at = None
    db.commit()
    db.refresh(batch)
    return _read_batch(batch)


def commit_import_batch(
    db: Session,
    batch: ImportBatch,
    *,
    git_commit: bool = False,
) -> ImportBatchRead:
    if batch.status != "validated":
        raise ValueError("Import batch must be validated before commit")
    patch = _batch_patch(batch)
    result = commit_patch(db, patch, git_commit=git_commit)
    batch.status = "committed"
    batch.commit_result_json = result.model_dump_json()
    batch.reviewed_at = utc_now()
    batch.warnings_json = json.dumps(result.warnings)
    db.commit()
    db.refresh(batch)
    return _read_batch(batch)


def reject_import_batch(db: Session, batch: ImportBatch, review_note: str | None = None) -> ImportBatchRead:
    batch.status = "rejected"
    batch.reviewed_at = utc_now()
    if review_note is not None:
        batch.review_note = review_note
    db.commit()
    db.refresh(batch)
    return _read_batch(batch)


def duplicate_suggestions(db: Session, batch: ImportBatch) -> ImportBatchSuggestionRead:
    patch = _batch_patch(batch)
    suggestions: list[DuplicateSuggestion] = []
    existing = list(db.execute(select(Fragment)).scalars())
    for patch_fragment in patch.fragments:
        candidates: list[DuplicateSuggestion] = []
        for fragment in existing:
            title_score = SequenceMatcher(
                None,
                patch_fragment.title.lower(),
                fragment.title.lower(),
            ).ratio()
            type_bonus = 0.15 if patch_fragment.type == fragment.type else 0
            score = min(1.0, title_score + type_bonus)
            if score < 0.45:
                continue
            reason = "similar title"
            if patch_fragment.type == fragment.type:
                reason = "same type and similar title"
            candidates.append(
                DuplicateSuggestion(
                    local_id=patch_fragment.local_id,
                    fragment_id=fragment.id,
                    title=fragment.title,
                    type=fragment.type,
                    status=fragment.status,
                    origin_classification=fragment.origin_classification,
                    exactness=fragment.exactness,
                    score=round(score, 3),
                    reason=reason,
                )
            )
        suggestions.extend(sorted(candidates, key=lambda item: item.score, reverse=True)[:3])
    return ImportBatchSuggestionRead(batch_id=batch.id, suggestions=suggestions)


def _read_batch(batch: ImportBatch) -> ImportBatchRead:
    return ImportBatchRead(
        id=batch.id,
        status=batch.status,
        raw_excerpt=batch.raw_excerpt,
        topic_hint=batch.topic_hint,
        citekey=batch.citekey,
        locator=batch.locator,
        patch=_safe_patch(batch.patch_json),
        warnings=_json_list(batch.warnings_json),
        commit_result=_safe_commit_result(batch.commit_result_json),
        review_note=batch.review_note,
        created_at=batch.created_at,
        updated_at=batch.updated_at,
        reviewed_at=batch.reviewed_at,
    )


def _batch_patch(batch: ImportBatch) -> ResearchPatch:
    if not batch.patch_json:
        raise ValueError("Import batch has no patch JSON")
    try:
        return ResearchPatch.model_validate_json(batch.patch_json)
    except ValidationError as exc:
        raise ValueError(exc.json()) from exc


def _safe_patch(value: str | None) -> ResearchPatch | None:
    if not value:
        return None
    try:
        return ResearchPatch.model_validate_json(value)
    except ValidationError:
        return None


def _safe_commit_result(value: str | None) -> ImportCommitResult | None:
    if not value:
        return None
    return ImportCommitResult.model_validate_json(value)


def _json_list(value: str | None) -> list[str]:
    if not value:
        return []
    loaded = json.loads(value)
    return [str(item) for item in loaded] if isinstance(loaded, list) else []


def _patch_to_json(patch: ResearchPatch) -> str:
    return patch.model_dump_json()


def _manual_patch_from_payload(payload: ImportBatchCreate) -> ResearchPatch:
    body = payload.raw_excerpt.strip()
    title = _first_sentence(body) or "Imported note"
    local_id = slugify(title, fallback="imported_note")
    source_pointers = []
    if payload.citekey:
        source_pointers.append(
            {
                "fragment_local_id": local_id,
                "citekey": payload.citekey,
                "locator": payload.locator,
                "exactness": "interpretation",
                "quote_text": None,
                "note": "Created from durable import inbox.",
            }
        )
    return ResearchPatch.model_validate(
        {
            "patch_type": "ResearchPatch",
            "metadata": {
                "source_kind": "manual_excerpt",
                "topic_hint": payload.topic_hint,
                "created_by": "lemmaforge_import_inbox",
                "requires_user_review": True,
            },
            "fragments": [
                {
                    "local_id": local_id,
                    "type": "ContextNote",
                    "title": title,
                    "status": "candidate",
                    "origin_classification": "unknown",
                    "exactness": "interpretation",
                    "body": body,
                    "assumptions": [],
                    "conclusion": None,
                    "confidence": None,
                    "source_excerpt": body,
                }
            ],
            "relations": [],
            "source_pointers": source_pointers,
            "warnings": [
                "Manual import creates a candidate ContextNote. Review before marking stable."
            ],
        }
    )


def _first_sentence(value: str) -> str:
    cleaned = " ".join(value.split())
    if not cleaned:
        return ""
    for separator in (".", "\n"):
        if separator in cleaned:
            return cleaned.split(separator, 1)[0][:80]
    return cleaned[:80]


def _batch_title(payload: ImportBatchCreate, patch: ResearchPatch) -> str:
    if patch.fragments:
        return patch.fragments[0].title
    return payload.topic_hint or payload.citekey or "import"
