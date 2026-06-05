from __future__ import annotations

import json
from pathlib import Path

from app.config import get_settings
from app.models.context_pack import ContextPack
from app.models.fragment import Fragment
from app.services.ids import slugify


def _scalar(value: object) -> str:
    if value is None:
        return "null"
    return json.dumps(str(value), ensure_ascii=False)


def _iso(value: object) -> str:
    return str(value.isoformat()) if hasattr(value, "isoformat") else str(value)


def fragment_markdown_path(fragment: Fragment) -> Path:
    return get_settings().vault_dir / "fragments" / f"{slugify(fragment.id)}.md"


def write_fragment_markdown(fragment: Fragment, topic_title: str | None = None) -> Path:
    path = fragment_markdown_path(fragment)
    path.parent.mkdir(parents=True, exist_ok=True)
    frontmatter = {
        "id": fragment.id,
        "type": fragment.type,
        "status": fragment.status,
        "origin_classification": fragment.origin_classification,
        "exactness": fragment.exactness,
        "topic": topic_title or fragment.topic_id,
        "created_at": _iso(fragment.created_at),
        "updated_at": _iso(fragment.updated_at),
    }
    metadata = "\n".join(f"{key}: {_scalar(value)}" for key, value in frontmatter.items())
    content = (
        f"---\n{metadata}\n---\n\n"
        f"# {fragment.title}\n\n"
        f"{fragment.body.strip()}\n\n"
        "## Provenance\n\n"
        f"- Origin: {fragment.origin_classification}\n"
        f"- Exactness: {fragment.exactness}\n"
        f"- Status: {fragment.status}\n"
    )
    path.write_text(content, encoding="utf-8")
    return path


def delete_fragment_markdown(fragment: Fragment) -> None:
    path = fragment_markdown_path(fragment)
    if path.exists():
        path.unlink()


def context_pack_markdown_path(context_pack: ContextPack) -> Path:
    filename = f"{slugify(context_pack.id or context_pack.title)}.md"
    return get_settings().vault_dir / "context_packs" / filename


def write_context_pack_markdown(context_pack: ContextPack, markdown: str) -> Path:
    path = context_pack_markdown_path(context_pack)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")
    return path
