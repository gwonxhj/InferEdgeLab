from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from inferedgelab.services.api_job_contract import build_api_job_response


class InMemoryApiJobStore:
    """Minimal in-memory job store for the SaaS API stub.

    This store is intentionally process-local and non-persistent. It prepares
    the API contract without introducing a database, queue, Redis, or worker.
    """

    def __init__(self) -> None:
        self._jobs: dict[str, dict[str, Any]] = {}

    def create_analyze_job(self, payload: dict[str, Any]) -> dict[str, Any]:
        model_path = _optional_string(payload, "model_path")
        artifact_path = _optional_string(payload, "artifact_path")
        if not model_path and not artifact_path:
            raise ValueError("model_path or artifact_path must be provided")

        metadata_path = _optional_string(payload, "metadata_path")
        manifest_path = _optional_string(payload, "manifest_path")
        notes = payload.get("notes")
        if notes is not None and not isinstance(notes, str):
            raise ValueError("notes must be a string when provided")

        created_at = _utc_now_iso()
        job_id = f"job_{uuid4().hex[:12]}"
        input_summary = {
            "workflow": "analyze",
            "model_path": model_path,
            "artifact_path": artifact_path,
            "metadata_path": metadata_path,
            "manifest_path": manifest_path,
            "notes": notes,
        }
        job = build_api_job_response(
            job_id=job_id,
            status="queued",
            created_at=created_at,
            updated_at=created_at,
            input_summary=input_summary,
            result=None,
            error=None,
            links={
                "self": f"/api/jobs/{job_id}",
                "cancel": f"/api/jobs/{job_id}/cancel",
            },
            next_actions=["poll_self"],
        )
        self._jobs[job_id] = job
        return job

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        return self._jobs.get(job_id)


def _optional_string(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string when provided")
    return value


def _utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
