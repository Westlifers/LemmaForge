from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.config import get_settings

LOCAL_API_TIMEOUT_SECONDS = 3.0


@dataclass
class ZoteroStatus:
    configured: bool
    running: bool
    local_api_available: bool
    base_url: str
    library_id: int | None
    library_name: str | None
    error: str | None
    references_bib: str
    references_exists: bool


def status() -> ZoteroStatus:
    settings = get_settings()
    error: str | None = None
    running = False
    local_api_available = False
    library_id: int | None = None
    library_name: str | None = None
    try:
        ping_text = _get_text("/connector/ping")
        running = "Zotero is running" in ping_text
        items = list_local_items(limit=1)
        local_api_available = True
        if items:
            library = items[0].get("library") or {}
            library_id = library.get("id")
            library_name = library.get("name")
    except ZoteroLocalApiError as caught:
        error = str(caught)
    return ZoteroStatus(
        configured=running or settings.references_bib.exists(),
        running=running,
        local_api_available=local_api_available,
        base_url=settings.zotero_local_api_url,
        library_id=library_id,
        library_name=library_name,
        error=error,
        references_bib=str(settings.references_bib),
        references_exists=settings.references_bib.exists(),
    )


def search_local_items(query: str, *, limit: int = 20) -> list[dict[str, Any]]:
    params: dict[str, str | int] = {"limit": _bounded_limit(limit)}
    if query.strip():
        params["q"] = query.strip()
        params["qmode"] = "everything"
    return list_local_items(**params)


def list_local_items(*, limit: int = 20, q: str | None = None, qmode: str | None = None) -> list[dict[str, Any]]:
    params: dict[str, str | int] = {"limit": _bounded_limit(limit)}
    if q:
        params["q"] = q
    if qmode:
        params["qmode"] = qmode
    items = _get_json(f"/api/users/0/items/top?{urlencode(params)}")
    if not isinstance(items, list):
        return []
    return [item for item in items if _is_top_level_source_item(item)]


def get_local_item(item_key: str) -> dict[str, Any]:
    item = _get_json(f"/api/users/0/items/{item_key}")
    if not isinstance(item, dict):
        raise ZoteroLocalApiError(f"Zotero item {item_key} did not return an object.")
    attachments = []
    try:
        children = _get_json(f"/api/users/0/items/{item_key}/children?limit=50")
        if isinstance(children, list):
            attachments = [_attachment_summary(child) for child in children if _is_attachment(child)]
    except ZoteroLocalApiError:
        attachments = []
    item["attachments"] = attachments
    return item


def get_local_items_by_keys(item_keys: list[str]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item_key in item_keys:
        item = get_local_item(item_key)
        if _is_top_level_source_item(item):
            items.append(item)
    return items


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


class ZoteroLocalApiError(RuntimeError):
    pass


def _get_json(path: str) -> Any:
    text = _get_text(path)
    try:
        return json.loads(text)
    except json.JSONDecodeError as caught:
        raise ZoteroLocalApiError(f"Zotero returned invalid JSON for {path}.") from caught


def _get_text(path: str) -> str:
    settings = get_settings()
    url = f"{settings.zotero_local_api_url}{path}"
    request = Request(url, headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=LOCAL_API_TIMEOUT_SECONDS) as response:
            return response.read().decode("utf-8", errors="replace")
    except HTTPError as caught:
        raise ZoteroLocalApiError(f"Zotero Local API returned HTTP {caught.code} for {path}.") from caught
    except URLError as caught:
        reason = getattr(caught, "reason", caught)
        raise ZoteroLocalApiError(f"Zotero Local API is unavailable: {reason}.") from caught
    except TimeoutError as caught:
        raise ZoteroLocalApiError("Zotero Local API timed out.") from caught


def _is_top_level_source_item(item: dict[str, Any]) -> bool:
    data = item.get("data") or {}
    return data.get("itemType") != "attachment" and not data.get("parentItem")


def _is_attachment(item: dict[str, Any]) -> bool:
    return (item.get("data") or {}).get("itemType") == "attachment"


def _attachment_summary(item: dict[str, Any]) -> dict[str, Any]:
    data = item.get("data") or {}
    enclosure = (item.get("links") or {}).get("enclosure") or {}
    return {
        "key": data.get("key") or item.get("key"),
        "title": data.get("title") or data.get("filename") or enclosure.get("title"),
        "content_type": data.get("contentType") or enclosure.get("type"),
        "filename": data.get("filename"),
        "url": data.get("url") or enclosure.get("href"),
    }


def _bounded_limit(limit: int) -> int:
    return max(1, min(limit, 100))


def _clean_bib_value(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()
