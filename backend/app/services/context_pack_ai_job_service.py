from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import select

from app.db import get_session_factory
from app.models.fragment import Fragment, Topic, utc_now
from app.models.relation import Relation
from app.schemas.context_pack import (
    ContextPackSuggestJobRead,
    ContextPackSuggestRequest,
    ContextPackSuggestResult,
)
from app.services.codex_import_service import CodexImportError, CodexImportUnavailable
from app.services.context_pack_ai_service import suggest_context_pack_with_codex
from app.services.ids import short_uuid


@dataclass
class _ContextPackSuggestJob:
    job_id: str
    payload: ContextPackSuggestRequest
    status: str = "queued"
    logs: list[str] = field(default_factory=list)
    result: ContextPackSuggestResult | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)


_jobs: dict[str, _ContextPackSuggestJob] = {}
_jobs_lock = threading.Lock()


def start_context_pack_suggest_job(payload: ContextPackSuggestRequest) -> ContextPackSuggestJobRead:
    job = _ContextPackSuggestJob(job_id=f"ai_ctx_{short_uuid()}", payload=payload)
    with _jobs_lock:
        _jobs[job.job_id] = job
    thread = threading.Thread(target=_run_job, args=(job.job_id,), daemon=True)
    thread.start()
    return read_context_pack_suggest_job(job.job_id)


def read_context_pack_suggest_job(job_id: str) -> ContextPackSuggestJobRead:
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is None:
            raise ValueError("Context pack suggestion job not found")
        return _job_read(job)


def _run_job(job_id: str) -> None:
    _set_status(job_id, "running")
    payload = _job_payload(job_id)
    db = get_session_factory()()
    try:
        topic = db.get(Topic, payload.topic_id)
        if topic is None:
            raise ValueError("Topic not found")
        fragments = list(
            db.execute(
                select(Fragment)
                .where(Fragment.topic_id == topic.id)
                .where(Fragment.status != "rejected")
                .order_by(Fragment.updated_at.desc())
            ).scalars()
        )
        fragment_ids = {fragment.id for fragment in fragments}
        relations: list[Relation] = []
        if fragment_ids:
            relations = list(
                db.execute(
                    select(Relation)
                    .where(Relation.source_fragment_id.in_(fragment_ids))
                    .where(Relation.target_fragment_id.in_(fragment_ids))
                    .order_by(Relation.created_at.desc())
                ).scalars()
            )
        suggestion = suggest_context_pack_with_codex(
            payload,
            topic,
            fragments,
            relations,
            on_log=lambda line: _append_log(job_id, line),
        )
        _set_result(
            job_id,
            ContextPackSuggestResult(
                available=True,
                suggestion=suggestion,
                logs=_job_logs(job_id),
            ),
        )
    except CodexImportUnavailable as exc:
        _set_result(
            job_id,
            ContextPackSuggestResult(available=False, error=str(exc), logs=_job_logs(job_id)),
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


def _job_payload(job_id: str) -> ContextPackSuggestRequest:
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


def _set_result(job_id: str, result: ContextPackSuggestResult) -> None:
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
        job.result = ContextPackSuggestResult(available=True, error=error, logs=list(job.logs))
        job.updated_at = utc_now()


def _job_read(job: _ContextPackSuggestJob) -> ContextPackSuggestJobRead:
    return ContextPackSuggestJobRead(
        job_id=job.job_id,
        status=job.status,  # type: ignore[arg-type]
        logs=list(job.logs),
        result=job.result,
        error=job.error,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )
