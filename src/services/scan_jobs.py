"""In-memory async receipt OCR jobs (avoids HTTP timeouts on slow Tesseract runs)."""

from __future__ import annotations

import logging
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from src.services.receipts import preview_receipt_bytes

logger = logging.getLogger(__name__)

_JOB_TTL = timedelta(minutes=30)


@dataclass
class ScanJob:
    status: str  # processing | complete | failed
    created_at: datetime
    filename: str | None = None
    receipt: dict[str, Any] | None = None
    error: str | None = None


_jobs: dict[str, ScanJob] = {}
_lock = threading.Lock()


def _prune_old_jobs() -> None:
    cutoff = datetime.utcnow() - _JOB_TTL
    stale = [jid for jid, job in _jobs.items() if job.created_at < cutoff]
    for jid in stale:
        _jobs.pop(jid, None)


def start_scan_job(image_bytes: bytes, filename: str | None = None) -> str:
    """Queue OCR work and return a job id immediately."""
    job_id = str(uuid.uuid4())
    with _lock:
        _prune_old_jobs()
        _jobs[job_id] = ScanJob(
            status="processing",
            created_at=datetime.utcnow(),
            filename=filename,
        )

    thread = threading.Thread(
        target=_run_scan_job,
        args=(job_id, image_bytes, filename),
        daemon=True,
        name=f"scan-{job_id[:8]}",
    )
    thread.start()
    return job_id


def _run_scan_job(job_id: str, image_bytes: bytes, filename: str | None) -> None:
    try:
        preview = preview_receipt_bytes(image_bytes, filename=filename)
        with _lock:
            job = _jobs.get(job_id)
            if not job:
                return
            job.status = "complete"
            job.receipt = preview
        logger.info("OCR job %s complete", job_id[:8])
    except Exception as exc:  # noqa: BLE001
        logger.exception("OCR job %s failed", job_id[:8])
        with _lock:
            job = _jobs.get(job_id)
            if not job:
                return
            job.status = "failed"
            job.error = str(exc)


def get_scan_job(job_id: str) -> dict[str, Any] | None:
    with _lock:
        job = _jobs.get(job_id)
        if not job:
            return None

        if job.status == "processing":
            return {"job_id": job_id, "status": "processing"}

        if job.status == "failed":
            return {
                "job_id": job_id,
                "status": "failed",
                "detail": job.error or "OCR failed",
            }

        return {
            "job_id": job_id,
            "status": "complete",
            "receipt": job.receipt,
            "dashboard": None,
        }
