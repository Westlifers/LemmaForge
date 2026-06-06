from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.context_pack import ContextPack
from app.models.fragment import Fragment
from app.models.relation import Relation
from app.schemas.context_pack import ContextPackExport
from app.services.git_service import commit_paths
from app.services.markdown_vault import write_context_pack_markdown


def build_context_markdown(db: Session, context_pack: ContextPack) -> str:
    items = list(context_pack.items)
    fragments = [item.fragment for item in items]
    reasons = {item.fragment_id: item.reason for item in items}
    relations = _selected_relations(db, fragments)
    lines = [
        f"# {context_pack.title}",
        "",
        "## Task For AI",
        "",
        (context_pack.task_prompt or "Use this context to help with the objective.").strip(),
        "",
        "## Current Objective",
        "",
        context_pack.objective.strip(),
        "",
        "## Topic",
        "",
        context_pack.topic_id or "_No topic linked._",
        "",
        "## Selected Context In Dependency Order",
        "",
    ]
    if not fragments:
        lines.extend(["_No fragments selected._", ""])
    for index, fragment in enumerate(fragments, start=1):
        reason = reasons.get(fragment.id)
        lines.extend(
            [
                f"### {index}. {fragment.title}",
                "",
                f"- ID: `{fragment.id}`",
                f"- Type: {fragment.type}",
                f"- Status: {fragment.status}",
                f"- Origin: {fragment.origin_classification}",
                f"- Exactness: {fragment.exactness}",
                f"- Selection reason: {reason or 'Selected for the current task.'}",
                "",
                fragment.body.strip(),
                "",
            ]
        )

    sections = [
        (
            "Definitions And Notation",
            [
                fragment
                for fragment in fragments
                if fragment.type in {"Definition", "ExternalDefinition", "ExternalNotation"}
            ],
        ),
        (
            "Known Context",
            [
                fragment
                for fragment in fragments
                if fragment.type in {"ContextNote", "Remark", "PaperNote", "ReadingNote", "LiteratureClaim"}
            ],
        ),
        (
            "Claims / Constructions / Proof Sketches",
            [
                fragment
                for fragment in fragments
                if fragment.type
                in {
                    "Proposition",
                    "Lemma",
                    "Theorem",
                    "Corollary",
                    "ExternalTheorem",
                    "Construction",
                    "Proof",
                    "ProofSketch",
                }
            ],
        ),
        (
            "Examples And Counterexamples",
            [fragment for fragment in fragments if fragment.type in {"Example", "Counterexample"}],
        ),
        (
            "Questions / Conjectures / TODOs",
            [fragment for fragment in fragments if fragment.type in {"Question", "Conjecture", "TODO"}],
        ),
    ]
    for heading, grouped_fragments in sections:
        lines.extend([f"## {heading}", ""])
        if not grouped_fragments:
            lines.extend(["_None selected._", ""])
            continue
        for fragment in grouped_fragments:
            reason = reasons.get(fragment.id)
            lines.extend(
                [
                    f"- `{fragment.id}` - {fragment.title}",
                    f"  - Status: {fragment.status}",
                    f"  - Reason: {reason or 'Selected for the current task.'}",
                ]
            )
        lines.append("")
    lines.extend(["## Relations Among Selected Fragments", ""])
    if relations:
        for relation in relations:
            source = _fragment_title(fragments, relation.source_fragment_id)
            target = _fragment_title(fragments, relation.target_fragment_id)
            confidence = (
                f" confidence={relation.confidence:.2f}" if relation.confidence is not None else ""
            )
            lines.append(
                f"- `{relation.source_fragment_id}` ({source}) "
                f"{relation.relation_kind} `{relation.target_fragment_id}` ({target}).{confidence}"
            )
        lines.append("")
    else:
        lines.extend(["_No selected internal relations._", ""])

    lines.extend(["## Provenance And Warnings", ""])
    warning_lines: list[str] = []
    for fragment in fragments:
        if fragment.status in {"draft", "raw", "candidate", "superseded"}:
            warning_lines.append(
                f"- `{fragment.id}` is `{fragment.status}`; verify before relying on it."
            )
        if fragment.origin_classification in {"assistant_generated", "mixed", "external_source"}:
            warning_lines.append(
                f"- `{fragment.id}` origin is `{fragment.origin_classification}` "
                f"with exactness `{fragment.exactness}`."
            )
        for pointer in fragment.source_pointers:
            source = pointer.source
            source_label = source.citekey or source.title if source else pointer.source_id
            detail = f", locator {pointer.locator}" if pointer.locator else ""
            warning_lines.append(
                f"- `{fragment.id}` source: {source_label}{detail}; exactness `{pointer.exactness}`."
            )
    if warning_lines:
        lines.extend(warning_lines)
    else:
        lines.append("_No warnings generated._")
    lines.append("")
    return "\n".join(lines)


def export_context_pack(
    db: Session,
    context_pack: ContextPack,
    *,
    git_commit: bool = False,
) -> ContextPackExport:
    markdown = build_context_markdown(db, context_pack)
    context_pack.body = markdown
    db.commit()
    db.refresh(context_pack)
    path = write_context_pack_markdown(context_pack, markdown)
    if git_commit:
        commit_paths([path], f"Export context pack {context_pack.id}")
    return ContextPackExport(context_pack_id=context_pack.id, markdown=markdown, path=str(path))


def list_context_packs_for_topic(db: Session, topic_id: str) -> list[ContextPack]:
    return list(
        db.execute(
            select(ContextPack)
            .where(ContextPack.topic_id == topic_id)
            .order_by(ContextPack.updated_at.desc())
        ).scalars()
    )


def _selected_relations(db: Session, fragments: list[Fragment]) -> list[Relation]:
    fragment_ids = {fragment.id for fragment in fragments}
    if not fragment_ids:
        return []
    return list(
        db.execute(
            select(Relation)
            .where(Relation.source_fragment_id.in_(fragment_ids))
            .where(Relation.target_fragment_id.in_(fragment_ids))
            .order_by(Relation.created_at)
        ).scalars()
    )


def _fragment_title(fragments: list[Fragment], fragment_id: str) -> str:
    for fragment in fragments:
        if fragment.id == fragment_id:
            return fragment.title
    return fragment_id
