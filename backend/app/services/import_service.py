from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.fragment import Fragment
from app.schemas.fragment import FragmentCreate
from app.schemas.relation import RelationCreate
from app.schemas.research_patch import ImportCommitResult, ImportPreview, ResearchPatch
from app.schemas.source import SourceCreate, SourcePointerCreate
from app.services.fragment_service import create_fragment
from app.services.git_service import commit_paths
from app.services.markdown_vault import write_fragment_markdown
from app.services.relation_service import create_relation
from app.services.source_service import (
    create_source,
    create_source_pointer,
    get_or_create_source_from_citekey,
    get_source_by_citekey,
)


def preview_patch(patch: ResearchPatch) -> ImportPreview:
    warnings = list(patch.warnings)
    if not patch.fragments:
        warnings.append("Patch contains no fragments.")
    return ImportPreview(
        valid=True,
        fragment_count=len(patch.fragments),
        relation_count=len(patch.relations),
        source_pointer_count=len(patch.source_pointers),
        warnings=warnings,
        patch=patch,
    )


def commit_patch(db: Session, patch: ResearchPatch, *, git_commit: bool = False) -> ImportCommitResult:
    created_fragments: list[Fragment] = []
    local_to_fragment_id: dict[str, str] = {}
    relation_ids: list[str] = []
    pointer_ids: list[str] = []
    warnings = list(patch.warnings)

    try:
        for patch_fragment in patch.fragments:
            fragment = create_fragment(
                db,
                FragmentCreate(
                    type=patch_fragment.type,
                    title=patch_fragment.title,
                    status=patch_fragment.status,
                    body=patch_fragment.body,
                    origin_classification=patch_fragment.origin_classification,
                    exactness=patch_fragment.exactness,
                ),
                id_hint=patch_fragment.local_id,
                commit=False,
                write_markdown=False,
            )
            created_fragments.append(fragment)
            local_to_fragment_id[patch_fragment.local_id] = fragment.id

        for patch_relation in patch.relations:
            source_id = local_to_fragment_id.get(patch_relation.source, patch_relation.source)
            target_id = local_to_fragment_id.get(patch_relation.target, patch_relation.target)
            if db.get(Fragment, source_id) is None:
                raise ValueError(
                    f"Relation source '{patch_relation.source}' is neither in the patch nor existing"
                )
            if db.get(Fragment, target_id) is None:
                raise ValueError(
                    f"Relation target '{patch_relation.target}' is neither in the patch nor existing"
                )
            relation = create_relation(
                db,
                RelationCreate(
                    source_fragment_id=source_id,
                    relation_kind=patch_relation.kind,
                    target_fragment_id=target_id,
                    confidence=patch_relation.confidence,
                ),
                commit=False,
            )
            relation_ids.append(relation.id)

        for patch_pointer in patch.source_pointers:
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
                raise ValueError("Source pointer requires citekey or source metadata")

            pointer = create_source_pointer(
                db,
                SourcePointerCreate(
                    fragment_id=local_to_fragment_id[patch_pointer.fragment_local_id],
                    source_id=source.id,
                    locator=patch_pointer.locator,
                    exactness=patch_pointer.exactness,
                    quote_text=patch_pointer.quote_text,
                    note=patch_pointer.note,
                ),
                commit=False,
            )
            pointer_ids.append(pointer.id)

        db.commit()
        markdown_paths = []
        for fragment in created_fragments:
            db.refresh(fragment)
            markdown_paths.append(write_fragment_markdown(fragment))
        if git_commit and markdown_paths:
            commit_paths(markdown_paths, "Import research patch")
    except Exception:
        db.rollback()
        raise

    return ImportCommitResult(
        fragment_ids=[fragment.id for fragment in created_fragments],
        relation_ids=relation_ids,
        source_pointer_ids=pointer_ids,
        warnings=warnings,
    )
