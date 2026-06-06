from __future__ import annotations

import json
from datetime import timezone
from difflib import SequenceMatcher

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.fragment import Fragment, utc_now
from app.models.import_batch import ImportBatch
from app.schemas.fragment import FragmentCreate
from app.schemas.import_batch import (
    AIApplyRelationsRequest,
    AIApplyRelationsResult,
    AICreateDraftsRequest,
    AIDraftCreationResult,
    AIRelationProposal,
    DuplicateSuggestion,
    ImportBatchCreate,
    ImportBatchRead,
    ImportBatchSuggestionRead,
    ImportBatchUpdate,
)
from app.schemas.relation import RelationCreate
from app.schemas.research_patch import ImportCommitResult, ResearchPatch
from app.schemas.source import SourceCreate, SourcePointerCreate
from app.services.fragment_service import create_fragment
from app.services.ids import slugify, unique_model_id
from app.services.import_service import commit_patch, preview_patch
from app.services.markdown_vault import write_fragment_markdown
from app.services.relation_service import create_relation
from app.services.source_service import (
    create_source,
    create_source_pointer,
    get_or_create_source_from_citekey,
    get_source_by_citekey,
)


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


def create_ai_drafts_from_patch(
    db: Session,
    payload: AICreateDraftsRequest,
) -> AIDraftCreationResult:
    batch = get_import_batch(db, payload.batch_id) if payload.batch_id else None
    if payload.batch_id and batch is None:
        raise ValueError("Import batch not found")

    if batch is None:
        assert payload.patch is not None
        batch_read = create_import_batch(
            db,
            ImportBatchCreate(
                raw_excerpt=payload.raw_excerpt,
                topic_hint=payload.topic_hint,
                citekey=payload.citekey,
                locator=payload.locator,
                patch=payload.patch,
            ),
        )
        batch = get_import_batch(db, batch_read.id)
        if batch is None:
            raise ValueError("Created import batch could not be loaded")

    existing_result = _safe_ai_draft_result(batch.ai_draft_result_json)
    if existing_result is not None:
        return existing_result

    patch = _selected_patch(_batch_patch(batch), payload.selected_local_ids)
    preview = preview_patch(patch)
    local_to_fragment_id: dict[str, str] = {}
    fragment_ids: list[str] = []
    source_pointer_ids: list[str] = []
    warnings = list(preview.warnings)
    created_fragments: list[Fragment] = []

    try:
        for patch_fragment in patch.fragments:
            fragment = create_fragment(
                db,
                FragmentCreate(
                    type=patch_fragment.type,
                    title=patch_fragment.title,
                    status="draft",
                    body=patch_fragment.body,
                    origin_classification=_ai_origin(patch_fragment.origin_classification),
                    exactness=patch_fragment.exactness,
                ),
                id_hint=patch_fragment.local_id,
                commit=False,
                write_markdown=False,
            )
            created_fragments.append(fragment)
            local_to_fragment_id[patch_fragment.local_id] = fragment.id
            fragment_ids.append(fragment.id)

        for patch_pointer in patch.source_pointers:
            fragment_id = local_to_fragment_id.get(patch_pointer.fragment_local_id)
            if fragment_id is None:
                warnings.append(
                    f"Skipped source pointer for unknown fragment {patch_pointer.fragment_local_id}."
                )
                continue
            if patch_pointer.source:
                source_payload = patch_pointer.source
                citekey = source_payload.citekey or patch_pointer.citekey
                source = get_source_by_citekey(db, citekey) if citekey else None
                if source is None:
                    source = create_source(
                        db,
                        SourceCreate(
                            source_type=source_payload.source_type,
                            title=source_payload.title or citekey or "Unknown source",
                            authors=source_payload.authors,
                            year=source_payload.year,
                            citekey=citekey,
                            zotero_item_key=source_payload.zotero_item_key,
                            url=source_payload.url,
                        ),
                        commit=False,
                    )
            elif patch_pointer.citekey:
                source = get_or_create_source_from_citekey(db, patch_pointer.citekey)
            else:
                warnings.append(
                    f"Skipped source pointer for {patch_pointer.fragment_local_id}; no source."
                )
                continue

            pointer = create_source_pointer(
                db,
                SourcePointerCreate(
                    fragment_id=fragment_id,
                    source_id=source.id,
                    locator=patch_pointer.locator,
                    exactness=patch_pointer.exactness,
                    quote_text=patch_pointer.quote_text,
                    note=patch_pointer.note,
                ),
                commit=False,
            )
            source_pointer_ids.append(pointer.id)

        proposals = _relation_proposals_from_patch(db, batch, patch, local_to_fragment_id)
        result = AIDraftCreationResult(
            batch_id=batch.id,
            fragment_ids=fragment_ids,
            local_to_fragment_id=local_to_fragment_id,
            source_pointer_ids=source_pointer_ids,
            relation_proposals=proposals,
            warnings=warnings,
        )
        batch.ai_draft_result_json = result.model_dump_json()
        batch.relation_proposals_json = _relation_proposals_to_json(proposals)
        batch.commit_result_json = ImportCommitResult(
            fragment_ids=fragment_ids,
            relation_ids=[],
            source_pointer_ids=source_pointer_ids,
            warnings=warnings,
        ).model_dump_json()
        batch.warnings_json = json.dumps(warnings)
        batch.status = "committed"
        batch.reviewed_at = utc_now()
        db.commit()
        for fragment in created_fragments:
            db.refresh(fragment)
            write_fragment_markdown(fragment)
    except Exception:
        db.rollback()
        raise

    return result


def apply_ai_relation_proposals(
    db: Session,
    batch: ImportBatch,
    payload: AIApplyRelationsRequest,
) -> AIApplyRelationsResult:
    proposals = _safe_relation_proposals(batch.relation_proposals_json)
    if not proposals:
        raise ValueError("Import batch has no AI relation proposals")
    selected = set(payload.proposal_ids)
    if not selected:
        raise ValueError("Select at least one relation proposal")

    relation_ids: list[str] = []
    warnings: list[str] = []
    try:
        for proposal in proposals:
            if proposal.proposal_id not in selected or proposal.applied_relation_id:
                continue
            source_id = proposal.source_fragment_id or proposal.source
            target_id = proposal.target_fragment_id or proposal.target
            if db.get(Fragment, source_id) is None:
                warnings.append(f"Skipped {proposal.proposal_id}; source fragment is missing.")
                continue
            if db.get(Fragment, target_id) is None:
                warnings.append(f"Skipped {proposal.proposal_id}; target fragment is missing.")
                continue
            relation = create_relation(
                db,
                RelationCreate(
                    source_fragment_id=source_id,
                    relation_kind=proposal.kind,  # type: ignore[arg-type]
                    target_fragment_id=target_id,
                    confidence=proposal.confidence,
                ),
                commit=False,
            )
            proposal.applied_relation_id = relation.id
            relation_ids.append(relation.id)
        batch.relation_proposals_json = _relation_proposals_to_json(proposals)
        _merge_relation_ids_into_commit_result(batch, relation_ids, warnings)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return AIApplyRelationsResult(
        batch_id=batch.id,
        relation_ids=relation_ids,
        relation_proposals=proposals,
        warnings=warnings,
    )


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
        ai_draft_result=_safe_ai_draft_result(batch.ai_draft_result_json),
        relation_proposals=_safe_relation_proposals(batch.relation_proposals_json),
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


def _safe_ai_draft_result(value: str | None) -> AIDraftCreationResult | None:
    if not value:
        return None
    return AIDraftCreationResult.model_validate_json(value)


def _safe_relation_proposals(value: str | None) -> list[AIRelationProposal]:
    if not value:
        return []
    loaded = json.loads(value)
    if not isinstance(loaded, list):
        return []
    return [AIRelationProposal.model_validate(item) for item in loaded]


def _json_list(value: str | None) -> list[str]:
    if not value:
        return []
    loaded = json.loads(value)
    return [str(item) for item in loaded] if isinstance(loaded, list) else []


def _patch_to_json(patch: ResearchPatch) -> str:
    return patch.model_dump_json()


def _selected_patch(patch: ResearchPatch, selected_local_ids: list[str] | None) -> ResearchPatch:
    if selected_local_ids is None:
        return patch
    selected = set(selected_local_ids)
    local_ids = {fragment.local_id for fragment in patch.fragments}
    unknown = sorted(selected - local_ids)
    if unknown:
        raise ValueError(f"Unknown selected fragment local_id values: {', '.join(unknown)}")
    if not selected:
        raise ValueError("Select at least one fragment to create drafts")

    selected_fragments = [fragment for fragment in patch.fragments if fragment.local_id in selected]
    selected_pointers = [
        pointer for pointer in patch.source_pointers if pointer.fragment_local_id in selected
    ]
    selected_relations = []
    for relation in patch.relations:
        source_is_patch_local = relation.source in local_ids
        target_is_patch_local = relation.target in local_ids
        if source_is_patch_local and relation.source not in selected:
            continue
        if target_is_patch_local and relation.target not in selected:
            continue
        selected_relations.append(relation)

    return ResearchPatch.model_validate(
        {
            **patch.model_dump(),
            "fragments": [fragment.model_dump() for fragment in selected_fragments],
            "relations": [relation.model_dump() for relation in selected_relations],
            "source_pointers": [pointer.model_dump() for pointer in selected_pointers],
        }
    )


def _relation_proposals_to_json(proposals: list[AIRelationProposal]) -> str:
    return json.dumps([proposal.model_dump() for proposal in proposals])


def _relation_proposals_from_patch(
    db: Session,
    batch: ImportBatch,
    patch: ResearchPatch,
    local_to_fragment_id: dict[str, str],
) -> list[AIRelationProposal]:
    proposals: list[AIRelationProposal] = []
    for index, relation in enumerate(patch.relations, start=1):
        source_fragment_id = local_to_fragment_id.get(relation.source)
        target_fragment_id = local_to_fragment_id.get(relation.target)
        if source_fragment_id is None and db.get(Fragment, relation.source) is not None:
            source_fragment_id = relation.source
        if target_fragment_id is None and db.get(Fragment, relation.target) is not None:
            target_fragment_id = relation.target
        proposals.append(
            AIRelationProposal(
                proposal_id=f"{batch.id}_rel_{index}",
                source=relation.source,
                kind=relation.kind,
                target=relation.target,
                confidence=relation.confidence,
                source_fragment_id=source_fragment_id,
                target_fragment_id=target_fragment_id,
            )
        )
    return proposals


def _merge_relation_ids_into_commit_result(
    batch: ImportBatch,
    relation_ids: list[str],
    warnings: list[str],
) -> None:
    result = _safe_commit_result(batch.commit_result_json) or ImportCommitResult(
        fragment_ids=[],
        relation_ids=[],
        source_pointer_ids=[],
        warnings=[],
    )
    result.relation_ids.extend(relation_ids)
    result.warnings.extend(warnings)
    batch.commit_result_json = result.model_dump_json()


def _ai_origin(origin: str) -> str:
    if origin == "assistant_generated":
        return "assistant_generated"
    if origin in {"user_original", "external_source", "mixed"}:
        return "mixed"
    return "assistant_generated"


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
