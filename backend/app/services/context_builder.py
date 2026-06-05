from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.context_pack import ContextPack
from app.models.fragment import Fragment
from app.schemas.context_pack import ContextPackExport
from app.services.git_service import commit_paths
from app.services.markdown_vault import write_context_pack_markdown


def build_context_markdown(db: Session, context_pack: ContextPack) -> str:
    fragments = [item.fragment for item in context_pack.items]
    sections = [
        ("Original Ideas", _filter_fragments(fragments, origin="user_original")),
        (
            "External Definitions And Results",
            [
                fragment
                for fragment in fragments
                if fragment.type in {"ExternalDefinition", "ExternalTheorem", "LiteratureClaim"}
                or fragment.origin_classification == "external_source"
            ],
        ),
        (
            "Notation Dependencies",
            [fragment for fragment in fragments if fragment.type == "ExternalNotation"],
        ),
        (
            "Proof Sketches",
            [fragment for fragment in fragments if fragment.type in {"Proof", "ProofSketch"}],
        ),
        (
            "Open Questions",
            [fragment for fragment in fragments if fragment.type in {"Question", "Conjecture", "TODO"}],
        ),
    ]
    lines = [
        f"# {context_pack.title}",
        "",
        "## Current Objective",
        "",
        context_pack.objective.strip(),
        "",
    ]
    for heading, grouped_fragments in sections:
        lines.extend([f"## {heading}", ""])
        if not grouped_fragments:
            lines.extend(["_None selected._", ""])
            continue
        for fragment in grouped_fragments:
            lines.extend(
                [
                    f"### {fragment.title}",
                    "",
                    f"- ID: `{fragment.id}`",
                    f"- Type: {fragment.type}",
                    f"- Status: {fragment.status}",
                    f"- Origin: {fragment.origin_classification}",
                    f"- Exactness: {fragment.exactness}",
                    "",
                    fragment.body.strip(),
                    "",
                ]
            )
    lines.extend(["## Warnings And Provenance Notes", ""])
    for fragment in fragments:
        if fragment.status in {"raw", "candidate", "working"}:
            lines.append(f"- `{fragment.id}` is `{fragment.status}` and needs review before reuse.")
    if lines[-1] == "":
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


def _filter_fragments(fragments: list[Fragment], *, origin: str) -> list[Fragment]:
    return [fragment for fragment in fragments if fragment.origin_classification == origin]
