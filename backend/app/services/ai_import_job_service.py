from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime

from app.db import get_session_factory
from app.models.fragment import utc_now
from app.schemas.import_batch import AIExtractJobRead, AIExtractRequest, AIExtractResult, ImportBatchCreate
from app.services.codex_import_service import (
    CodexImportError,
    CodexImportUnavailable,
    extract_research_patch_with_codex,
)
from app.services.ids import short_uuid
from app.services.import_batch_service import create_import_batch, get_import_batch, validate_import_batch
from app.services.import_service import preview_patch


@dataclass
class _AIExtractJob:
    job_id: str
    payload: AIExtractRequest
    status: str = "queued"
    logs: list[str] = field(default_factory=list)
    result: AIExtractResult | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)


_jobs: dict[str, _AIExtractJob] = {}
_jobs_lock = threading.Lock()


def start_ai_extract_job(payload: AIExtractRequest) -> AIExtractJobRead:
    job = _AIExtractJob(job_id=f"ai_imp_{short_uuid()}", payload=payload)
    with _jobs_lock:
        _jobs[job.job_id] = job
    thread = threading.Thread(target=_run_job, args=(job.job_id,), daemon=True)
    thread.start()
    return read_ai_extract_job(job.job_id)


def read_ai_extract_job(job_id: str) -> AIExtractJobRead:
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is None:
            raise ValueError("AI extraction job not found")
        return _job_read(job)


def _run_job(job_id: str) -> None:
    _set_status(job_id, "running")
    payload = _job_payload(job_id)
    try:
        patch = extract_research_patch_with_codex(payload, on_log=lambda line: _append_log(job_id, line))
        preview = preview_patch(patch)
        db = get_session_factory()()
        try:
            batch = create_import_batch(
                db,
                ImportBatchCreate(
                    raw_excerpt=payload.raw_excerpt,
                    topic_hint=payload.topic_hint,
                    citekey=payload.citekey,
                    locator=payload.locator,
                    patch=patch,
                ),
            )
            stored = get_import_batch(db, batch.id)
            if stored is None:
                raise ValueError("Created import batch could not be loaded")
            validated = validate_import_batch(db, stored)
        finally:
            db.close()
        _set_result(
            job_id,
            AIExtractResult(available=True, preview=preview, batch=validated, logs=_job_logs(job_id)),
        )
    except CodexImportUnavailable as exc:
        _set_result(job_id, AIExtractResult(available=False, error=str(exc), logs=_job_logs(job_id)))
    except CodexImportError as exc:
        for line in exc.logs:
            _append_log(job_id, line)
        _set_error(job_id, str(exc))
    except Exception as exc:
        _append_log(job_id, f"[error] {exc}")
        _set_error(job_id, str(exc))


def _job_payload(job_id: str) -> AIExtractRequest:
    with _jobs_lock:
        return _jobs[job_id].payload


def _job_logs(job_id: str) -> list[str]:
    with _jobs_lock:
        return list(_jobs[job_id].logs)


def _append_log(job_id: str, line: str) -> None:
    with _jobs_lock:
        job = _jobs[job_id]
        if line not in job.logs[-3:]:
            job.logs.append(line)
        job.logs = job.logs[-400:]
        job.updated_at = utc_now()


def _set_status(job_id: str, status: str) -> None:
    with _jobs_lock:
        job = _jobs[job_id]
        job.status = status
        job.updated_at = utc_now()


def _set_result(job_id: str, result: AIExtractResult) -> None:
    with _jobs_lock:
        job = _jobs[job_id]
        job.status = "succeeded" if result.available else "failed"
        job.result = result
        job.error = result.error
        job.updated_at = utc_now()


def _set_error(job_id: str, error: str) -> None:
    with _jobs_lock:
        job = _jobs[job_id]
        job.status = "failed"
        job.error = error
        job.result = AIExtractResult(available=True, error=error, logs=list(job.logs))
        job.updated_at = utc_now()


def _job_read(job: _AIExtractJob) -> AIExtractJobRead:
    return AIExtractJobRead(
        job_id=job.job_id,
        status=job.status,  # type: ignore[arg-type]
        logs=list(job.logs),
        result=job.result,
        error=job.error,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )
