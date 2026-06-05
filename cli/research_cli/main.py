from __future__ import annotations

import json
import shutil
import sqlite3
import subprocess
from pathlib import Path
from typing import Optional

import typer
from pydantic import ValidationError

from app.config import ensure_local_directories, get_settings, project_root
from app.db import get_session_factory, init_db
from app.models.context_pack import ContextPack
from app.schemas.research_patch import ResearchPatch
from app.services.context_builder import export_context_pack
from app.services.git_service import status_short
from app.services.import_batch_service import (
    get_import_batch,
    list_import_batches,
    read_import_batch,
    reject_import_batch,
)
from app.services.import_service import commit_patch
from app.services.source_service import sync_references_to_sources
from app.services.zotero_service import search_references, status as zotero_status

app = typer.Typer(help="Local LemmaForge research operations.")
db_app = typer.Typer(help="Database commands.")
import_app = typer.Typer(help="ResearchPatch import commands.")
zotero_app = typer.Typer(help="Zotero reference commands.")
context_app = typer.Typer(help="Context pack commands.")

app.add_typer(db_app, name="db")
app.add_typer(import_app, name="import")
app.add_typer(zotero_app, name="zotero")
app.add_typer(context_app, name="context")


@app.command()
def status() -> None:
    settings = get_settings()
    typer.echo(f"Database: {settings.database_url}")
    typer.echo(f"Vault: {settings.vault_dir}")
    typer.echo(f"References: {settings.references_bib}")
    typer.echo(f"Git: {status_short() or 'clean'}")


@db_app.command("init")
def db_init() -> None:
    ensure_local_directories()
    init_db()
    typer.echo("Database initialized.")


@db_app.command("migrate")
def db_migrate() -> None:
    settings = get_settings()
    sqlite_path = _sqlite_path_from_url(settings.database_url)
    if sqlite_path is not None and sqlite_path.exists() and _sqlite_table_exists(sqlite_path, "fragments"):
        init_db()
        if not _sqlite_table_exists(sqlite_path, "alembic_version"):
            completed = subprocess.run(
                ["alembic", "-c", "alembic.ini", "stamp", "head"],
                cwd=project_root() / "backend",
                check=False,
                text=True,
            )
            if completed.returncode != 0:
                raise typer.Exit(code=completed.returncode)
            typer.echo("Database schema ensured and stamped at Alembic head.")
            return
    completed = subprocess.run(
        ["alembic", "-c", "alembic.ini", "upgrade", "head"],
        cwd=project_root() / "backend",
        check=False,
        text=True,
    )
    if completed.returncode != 0:
        raise typer.Exit(code=completed.returncode)
    typer.echo("Database migrated.")


@db_app.command("backup")
def db_backup(destination: Path) -> None:
    settings = get_settings()
    source = _sqlite_path_from_url(settings.database_url)
    if source is None or not source.exists():
        typer.echo("SQLite database file not found.")
        raise typer.Exit(code=1)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    typer.echo(f"Backed up database to {destination}")


@import_app.command("validate")
def import_validate(path: Path) -> None:
    try:
        patch = _load_patch(path)
    except ValidationError as exc:
        typer.echo(exc.json(indent=2))
        raise typer.Exit(code=1) from exc
    typer.echo(
        json.dumps(
            {
                "valid": True,
                "fragments": len(patch.fragments),
                "relations": len(patch.relations),
                "source_pointers": len(patch.source_pointers),
                "warnings": patch.warnings,
            },
            indent=2,
        )
    )


@import_app.command("commit")
def import_commit(path: Path) -> None:
    patch = _load_patch(path)
    init_db()
    db = get_session_factory()()
    try:
        result = commit_patch(db, patch)
    finally:
        db.close()
    typer.echo(result.model_dump_json(indent=2))


@import_app.command("list")
def import_list() -> None:
    init_db()
    db = get_session_factory()()
    try:
        rows = [
            {
                "id": batch.id,
                "status": batch.status,
                "topic_hint": batch.topic_hint,
                "citekey": batch.citekey,
                "updated_at": batch.updated_at.isoformat(),
            }
            for batch in list_import_batches(db)
        ]
    finally:
        db.close()
    typer.echo(json.dumps(rows, indent=2))


@import_app.command("show")
def import_show(import_batch_id: str) -> None:
    init_db()
    db = get_session_factory()()
    try:
        batch = get_import_batch(db, import_batch_id)
        if batch is None:
            typer.echo(f"Import batch not found: {import_batch_id}")
            raise typer.Exit(code=1)
        read = read_import_batch(batch)
    finally:
        db.close()
    typer.echo(read.model_dump_json(indent=2))


@import_app.command("reject")
def import_reject(import_batch_id: str, note: Optional[str] = None) -> None:
    init_db()
    db = get_session_factory()()
    try:
        batch = get_import_batch(db, import_batch_id)
        if batch is None:
            typer.echo(f"Import batch not found: {import_batch_id}")
            raise typer.Exit(code=1)
        result = reject_import_batch(db, batch, note)
    finally:
        db.close()
    typer.echo(result.model_dump_json(indent=2))


@zotero_app.command("status")
def zotero_status_command() -> None:
    typer.echo(json.dumps(zotero_status().__dict__, indent=2))


@zotero_app.command("search")
def zotero_search(query: str) -> None:
    typer.echo(json.dumps(search_references(query), indent=2))


@zotero_app.command("sync")
def zotero_sync() -> None:
    settings = get_settings()
    if not settings.references_bib.exists():
        typer.echo("references.bib not found.")
        raise typer.Exit(code=1)
    init_db()
    db = get_session_factory()()
    try:
        sources = sync_references_to_sources(
            db,
            settings.references_bib.read_text(encoding="utf-8", errors="ignore"),
        )
    finally:
        db.close()
    typer.echo(json.dumps({"synced": len(sources)}, indent=2))


@context_app.command("export")
def context_export(context_pack_id: str) -> None:
    init_db()
    db = get_session_factory()()
    try:
        context_pack = db.get(ContextPack, context_pack_id)
        if context_pack is None:
            typer.echo(f"Context pack not found: {context_pack_id}")
            raise typer.Exit(code=1)
        result = export_context_pack(db, context_pack)
    finally:
        db.close()
    typer.echo(result.model_dump_json(indent=2))


vault_app = typer.Typer(help="Markdown vault commands.")
app.add_typer(vault_app, name="vault")


@vault_app.command("check")
def vault_check() -> None:
    init_db()
    db = get_session_factory()()
    settings = get_settings()
    from app.models.fragment import Fragment
    from app.services.markdown_vault import fragment_markdown_path

    try:
        fragments = db.query(Fragment).all()
        missing = [
            fragment.id
            for fragment in fragments
            if not fragment_markdown_path(fragment).exists()
        ]
    finally:
        db.close()
    typer.echo(
        json.dumps(
            {
                "vault": str(settings.vault_dir),
                "fragment_count": len(fragments),
                "missing_fragment_markdown": missing,
                "ok": not missing,
            },
            indent=2,
        )
    )


def _load_patch(path: Path) -> ResearchPatch:
    return ResearchPatch.model_validate_json(path.read_text(encoding="utf-8"))


def _sqlite_path_from_url(database_url: str) -> Path | None:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return None
    return Path(database_url.removeprefix(prefix))


def _sqlite_table_exists(path: Path, table_name: str) -> bool:
    if not path.exists():
        return False
    with sqlite3.connect(path) as connection:
        row = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        ).fetchone()
    return row is not None


if __name__ == "__main__":
    app()
