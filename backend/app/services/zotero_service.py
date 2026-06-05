from __future__ import annotations

import re
from dataclasses import dataclass

from app.config import get_settings


@dataclass
class ZoteroStatus:
    configured: bool
    zotero_data_dir: str | None
    references_bib: str
    references_exists: bool


def status() -> ZoteroStatus:
    settings = get_settings()
    return ZoteroStatus(
        configured=settings.zotero_data_dir is not None or settings.references_bib.exists(),
        zotero_data_dir=str(settings.zotero_data_dir) if settings.zotero_data_dir else None,
        references_bib=str(settings.references_bib),
        references_exists=settings.references_bib.exists(),
    )


def search_references(query: str) -> list[dict[str, str | None]]:
    settings = get_settings()
    if not settings.references_bib.exists():
        return []
    text = settings.references_bib.read_text(encoding="utf-8", errors="ignore")
    entries = re.split(r"\n@", "\n" + text)
    normalized_query = query.lower()
    results: list[dict[str, str | None]] = []
    for entry in entries:
        if not entry.strip() or normalized_query not in entry.lower():
            continue
        citekey_match = re.search(r"@\w+\{([^,\s]+)", entry)
        title_match = re.search(r"title\s*=\s*[{\"'](.+?)[}\"']", entry, re.IGNORECASE | re.DOTALL)
        author_match = re.search(r"author\s*=\s*[{\"'](.+?)[}\"']", entry, re.IGNORECASE | re.DOTALL)
        year_match = re.search(r"year\s*=\s*[{\"']?(\d{4})", entry, re.IGNORECASE)
        results.append(
            {
                "citekey": citekey_match.group(1) if citekey_match else None,
                "title": _clean_bib_value(title_match.group(1)) if title_match else None,
                "authors": _clean_bib_value(author_match.group(1)) if author_match else None,
                "year": year_match.group(1) if year_match else None,
            }
        )
    return results[:20]


def _clean_bib_value(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()

