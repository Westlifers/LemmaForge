from __future__ import annotations

import json

from sqlalchemy import select

from app.config import get_settings, project_root, reset_settings_cache
from app.models.source import Source
from app.services import zotero_service
from app.services.source_service import sync_zotero_items_to_sources


def _zotero_item(
    key: str,
    *,
    title: str,
    citation_key: str | None,
    item_type: str = "journalArticle",
    parent: str | None = None,
) -> dict:
    data = {
        "key": key,
        "itemType": item_type,
        "title": title,
        "citationKey": citation_key,
        "date": "2026-05-26",
        "url": f"https://example.test/{key}",
        "creators": [{"firstName": "Ada", "lastName": "Lovelace", "creatorType": "author"}],
    }
    if parent:
        data["parentItem"] = parent
    return {
        "key": key,
        "version": 1,
        "library": {"id": 123, "name": "Test Library"},
        "meta": {"creatorSummary": "Lovelace", "numChildren": 1},
        "data": data,
    }


def test_zotero_status_reports_unavailable(monkeypatch, tmp_path):
    monkeypatch.setenv("RESEARCH_REFERENCES_BIB", str(tmp_path / "references.bib"))
    reset_settings_cache()


def test_saved_zotero_local_api_url_is_loaded(monkeypatch, tmp_path):
    settings_path = project_root() / "data" / "zotero_settings.json"
    original = settings_path.read_text(encoding="utf-8") if settings_path.exists() else None
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        json.dumps({"zotero_local_api_url": "http://127.0.0.1:24000"}),
        encoding="utf-8",
    )
    monkeypatch.delenv("RESEARCH_ZOTERO_LOCAL_API_URL", raising=False)
    reset_settings_cache()
    try:
        assert get_settings().zotero_local_api_url == "http://127.0.0.1:24000"
    finally:
        if original is None:
            settings_path.unlink(missing_ok=True)
        else:
            settings_path.write_text(original, encoding="utf-8")
        reset_settings_cache()

    def fail(_path: str) -> str:
        raise zotero_service.ZoteroLocalApiError("Zotero Local API is unavailable.")

    monkeypatch.setattr(zotero_service, "_get_text", fail)

    result = zotero_service.status()

    assert result.running is False
    assert result.local_api_available is False
    assert result.error == "Zotero Local API is unavailable."
    reset_settings_cache()


def test_zotero_search_filters_out_attachments(monkeypatch):
    top_item = _zotero_item("AAA111", title="Top paper", citation_key="topPaper2026")
    attachment = _zotero_item(
        "PDF111",
        title="Full Text PDF",
        citation_key=None,
        item_type="attachment",
        parent="AAA111",
    )

    def fake_get_text(path: str) -> str:
        assert path.startswith("/api/users/0/items/top?")
        return json.dumps([attachment, top_item])

    monkeypatch.setattr(zotero_service, "_get_text", fake_get_text)

    results = zotero_service.search_local_items("paper")

    assert [item["key"] for item in results] == ["AAA111"]


def test_zotero_sync_creates_source_and_uses_zotero_key_without_citekey(db_session):
    db, _tmp_path = db_session
    items = [
        _zotero_item("AAA111", title="Paper with citekey", citation_key="paperWithCitekey2026"),
        _zotero_item("BBB222", title="Paper without citekey", citation_key=None),
    ]

    synced = sync_zotero_items_to_sources(db, items)

    assert len(synced) == 2
    sources = db.execute(select(Source).order_by(Source.title)).scalars().all()
    assert {source.zotero_item_key for source in sources} == {"AAA111", "BBB222"}
    assert any(source.citekey is None and source.zotero_item_key == "BBB222" for source in sources)


def test_zotero_sync_updates_existing_source_by_zotero_key(db_session):
    db, _tmp_path = db_session
    sync_zotero_items_to_sources(
        db,
        [_zotero_item("AAA111", title="Old title", citation_key="oldKey2026")],
    )

    sync_zotero_items_to_sources(
        db,
        [_zotero_item("AAA111", title="New title", citation_key="newKey2026")],
    )

    sources = db.execute(select(Source)).scalars().all()
    assert len(sources) == 1
    assert sources[0].title == "New title"
    assert sources[0].citekey == "newKey2026"


def test_zotero_sync_updates_existing_source_by_citekey(db_session):
    db, _tmp_path = db_session
    sync_zotero_items_to_sources(
        db,
        [_zotero_item("AAA111", title="Original", citation_key="sameKey2026")],
    )

    sync_zotero_items_to_sources(
        db,
        [_zotero_item("CCC333", title="Moved Zotero item", citation_key="sameKey2026")],
    )

    sources = db.execute(select(Source)).scalars().all()
    assert len(sources) == 1
    assert sources[0].title == "Moved Zotero item"
    assert sources[0].zotero_item_key == "CCC333"
