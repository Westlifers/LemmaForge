from __future__ import annotations

import json
import shutil
import tempfile
import subprocess
import threading
import time
from pathlib import Path
from collections.abc import Callable

from pydantic import ValidationError

from app.schemas.import_batch import AIExtractRequest
from app.schemas.research_patch import ResearchPatch


class CodexImportUnavailable(RuntimeError):
    pass


class CodexImportError(RuntimeError):
    def __init__(self, message: str, *, logs: list[str] | None = None) -> None:
        super().__init__(message)
        self.logs = logs or []


def extract_research_patch_with_codex(
    payload: AIExtractRequest,
    *,
    on_log: Callable[[str], None] | None = None,
) -> ResearchPatch:
    codex_path = shutil.which("codex")
    if codex_path is None:
        raise CodexImportUnavailable("Codex CLI is not available on PATH.")

    repo_root = _repo_root()
    schema_path = repo_root / "schemas" / "research_patch.schema.json"
    skill_path = repo_root / ".codex" / "skills" / "research-import" / "SKILL.md"
    if not schema_path.exists():
        raise CodexImportError(f"ResearchPatch schema not found: {schema_path}")
    if not skill_path.exists():
        raise CodexImportError(f"Research import skill not found: {skill_path}")

    with tempfile.NamedTemporaryFile(
        mode="w+", suffix=".json", delete=False, encoding="utf-8"
    ) as output_file:
        output_path = Path(output_file.name)

    command = [
        codex_path,
        "exec",
        "--ephemeral",
        "--sandbox",
        "read-only",
        "--output-schema",
        str(schema_path),
        "--output-last-message",
        str(output_path),
        "-",
    ]
    prompt = _build_prompt(payload, skill_path.read_text(encoding="utf-8-sig"))
    try:
        completed = _run_codex_command(
            command,
            prompt,
            repo_root,
            payload.timeout_seconds,
            on_log=on_log,
        )
        raw_output = output_path.read_text(encoding="utf-8").strip() if output_path.exists() else ""
    finally:
        try:
            output_path.unlink(missing_ok=True)
        except OSError:
            pass

    logs = completed.logs
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "Codex CLI failed."
        raise CodexImportError(detail, logs=logs)

    candidate = raw_output or completed.stdout.strip()
    if not candidate:
        raise CodexImportError("Codex CLI returned no output.", logs=logs)

    try:
        return ResearchPatch.model_validate_json(candidate)
    except ValidationError as exc:
        raise CodexImportError(exc.json(), logs=logs) from exc
    except ValueError as exc:
        try:
            return ResearchPatch.model_validate(_extract_json_object(candidate))
        except (ValidationError, ValueError, json.JSONDecodeError) as fallback_exc:
            raise CodexImportError(
                f"Codex output was not valid ResearchPatch JSON: {exc}",
                logs=logs,
            ) from fallback_exc


class _CodexProcessResult:
    def __init__(self, returncode: int, stdout: str, stderr: str, logs: list[str]) -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.logs = logs


def _run_codex_command(
    command: list[str],
    prompt: str,
    cwd: Path,
    timeout_seconds: int,
    *,
    on_log: Callable[[str], None] | None,
) -> _CodexProcessResult:
    logs: list[str] = []
    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []

    def log(line: str) -> None:
        cleaned = line.rstrip()
        if not cleaned:
            return
        logs.append(cleaned)
        if on_log:
            on_log(cleaned)

    log("Starting Codex CLI extraction.")
    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    assert process.stdin is not None
    process.stdin.write(prompt)
    process.stdin.close()

    def reader(stream, chunks: list[str], label: str) -> None:
        if stream is None:
            return
        for line in iter(stream.readline, ""):
            chunks.append(line)
            log(f"[{label}] {line}")
        stream.close()

    stdout_thread = threading.Thread(
        target=reader,
        args=(process.stdout, stdout_chunks, "stdout"),
        daemon=True,
    )
    stderr_thread = threading.Thread(
        target=reader,
        args=(process.stderr, stderr_chunks, "stderr"),
        daemon=True,
    )
    stdout_thread.start()
    stderr_thread.start()

    deadline = time.monotonic() + timeout_seconds
    while process.poll() is None:
        if time.monotonic() >= deadline:
            log(f"Codex extraction timed out after {timeout_seconds} seconds. Terminating process.")
            process.kill()
            stdout_thread.join(timeout=2)
            stderr_thread.join(timeout=2)
            raise CodexImportError("Codex extraction timed out.", logs=logs)
        time.sleep(0.1)

    stdout_thread.join(timeout=2)
    stderr_thread.join(timeout=2)
    log(f"Codex CLI exited with code {process.returncode}.")
    return _CodexProcessResult(
        process.returncode or 0,
        "".join(stdout_chunks),
        "".join(stderr_chunks),
        logs,
    )


def _build_prompt(payload: AIExtractRequest, skill_text: str) -> str:
    metadata = {
        "source_kind": payload.source_kind,
        "topic_hint": payload.topic_hint,
        "citekey": payload.citekey,
        "locator": payload.locator,
    }
    return (
        "You are extracting mathematical research fragments for LemmaForge.\n"
        "Follow this skill exactly.\n\n"
        f"{skill_text}\n\n"
        "Current LemmaForge import flow notes:\n"
        "- Output only a ResearchPatch JSON object.\n"
        "- Fragment statuses in the patch must be raw or candidate only.\n"
        "- The app will later create database draft fragments from this patch.\n"
        "- Use metadata.topic_hint; do not invent a topic_id.\n"
        "- Use relation source/target local_id values for newly extracted fragments.\n"
        "- If material is external, include citekey or source metadata for source pointers.\n\n"
        f"Import metadata:\n{json.dumps(metadata, ensure_ascii=False, indent=2)}\n\n"
        "Excerpt to extract:\n"
        f"{payload.raw_excerpt}\n"
    )


def _extract_json_object(value: str) -> dict:
    start = value.find("{")
    end = value.rfind("}")
    if start < 0 or end < start:
        raise ValueError("No JSON object found")
    loaded = json.loads(value[start : end + 1])
    if not isinstance(loaded, dict):
        raise ValueError("JSON output is not an object")
    return loaded


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]
