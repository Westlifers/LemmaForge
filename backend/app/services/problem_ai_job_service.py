from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime

from app.db import get_session_factory
from app.models.fragment import utc_now
from app.schemas.problem import ProblemSummaryJobRead, ProblemSummaryRequest, ProblemSummaryResult
from app.services.codex_import_service import CodexImportError, CodexImportUnavailable
from app.services.ids import short_uuid
from app.services.problem_ai_service import _problem_context, suggest_problem_summary_with_codex


@dataclass
class _ProblemSummaryJob:
    job_id: str
    payload: ProblemSummaryRequest
    status: str = "queued"
    logs: list[str] = field(default_factory=list)
    result: ProblemSummaryResult | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)


_jobs: dict[str, _ProblemSummaryJob] = {}
_jobs_lock = threading.Lock()


def start_problem_summary_job(payload: ProblemSummaryRequest) -> ProblemSummaryJobRead:
    job = _ProblemSummaryJob(job_id=f"ai_prob_{short_uuid()}", payload=payload)
    with _jobs_lock:
        _jobs[job.job_id] = job
    thread = threading.Thread(target=_run_job, args=(job.job_id,), daemon=True)
    thread.start()
    return read_problem_summary_job(job.job_id)


def read_problem_summary_job(job_id: str) -> ProblemSummaryJobRead:
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is None:
            raise ValueError("Problem summary job not found")
        return _job_read(job)


def _run_job(job_id: str) -> None:
    _set_status(job_id, "running")
    payload = _job_payload(job_id)
    db = get_session_factory()()
    try:
        topics, fragments, relations = _problem_context(db, payload)
        proposal = suggest_problem_summary_with_codex(
            payload,
            topics,
            fragments,
            relations,
            on_log=lambda line: _append_log(job_id, line),
        )
        _set_result(
            job_id,
            ProblemSummaryResult(available=True, proposal=proposal, logs=_job_logs(job_id)),
        )
    except CodexImportUnavailable as exc:
        _set_result(
            job_id,
            ProblemSummaryResult(available=False, error=str(exc), logs=_job_logs(job_id)),
        )
    except CodexImportError as exc:
        for line in exc.logs:
            _append_log(job_id, line)
        _set_error(job_id, str(exc))
    except Exception as exc:
        _append_log(job_id, f"[error] {exc}")
        _set_error(job_id, str(exc))
    finally:
        db.close()


def _job_payload(job_id: str) -> ProblemSummaryRequest:
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


def _set_result(job_id: str, result: ProblemSummaryResult) -> None:
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
        job.result = ProblemSummaryResult(available=True, error=error, logs=list(job.logs))
        job.updated_at = utc_now()


def _job_read(job: _ProblemSummaryJob) -> ProblemSummaryJobRead:
    return ProblemSummaryJobRead(
        job_id=job.job_id,
        status=job.status,  # type: ignore[arg-type]
        logs=list(job.logs),
        result=job.result,
        error=job.error,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )
