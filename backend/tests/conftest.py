from __future__ import annotations

import pytest

from app.config import reset_settings_cache
from app.db import get_session_factory, init_db, reset_engine_for_tests


@pytest.fixture()
def db_session(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_DB_URL", f"sqlite:///{(tmp_path / 'research.db').as_posix()}")
    monkeypatch.setenv("RESEARCH_VAULT_DIR", str(tmp_path / "vault"))
    monkeypatch.setenv("RESEARCH_REFERENCES_BIB", str(tmp_path / "references.bib"))
    reset_settings_cache()
    reset_engine_for_tests()
    init_db()
    db = get_session_factory()()
    try:
        yield db, tmp_path
    finally:
        db.close()
        reset_engine_for_tests()
        reset_settings_cache()

