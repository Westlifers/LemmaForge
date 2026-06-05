from __future__ import annotations

from typer.testing import CliRunner

from app.config import reset_settings_cache
from app.db import reset_engine_for_tests
from research_cli.main import app


def test_import_list_show_reject_cli(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_DB_URL", f"sqlite:///{(tmp_path / 'research.db').as_posix()}")
    monkeypatch.setenv("RESEARCH_VAULT_DIR", str(tmp_path / "vault"))
    monkeypatch.setenv("RESEARCH_REFERENCES_BIB", str(tmp_path / "references.bib"))
    reset_settings_cache()
    reset_engine_for_tests()
    runner = CliRunner()

    list_result = runner.invoke(app, ["import", "list"])

    assert list_result.exit_code == 0
    assert list_result.stdout.strip() == "[]"

    # Exercise command registration and not-found behavior without touching fragments.
    show_result = runner.invoke(app, ["import", "show", "missing"])
    reject_result = runner.invoke(app, ["import", "reject", "missing"])

    assert show_result.exit_code == 1
    assert reject_result.exit_code == 1

    reset_engine_for_tests()
    reset_settings_cache()

