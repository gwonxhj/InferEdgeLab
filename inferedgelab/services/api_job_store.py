from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from inferedgelab.services.api_job_contract import build_api_job_response
from inferedgelab.services.worker_contract import WorkerContractError
from inferedgelab.services.worker_contract import apply_worker_response_to_job


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
        options = payload.get("options")
        if options is not None and not isinstance(options, dict):
            raise ValueError("options must be a JSON object when provided")

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
        if options is not None:
            input_summary["options"] = dict(options)
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

    def complete_job_dev(self, job_id: str, result: dict[str, Any]) -> dict[str, Any]:
        """Complete an in-memory analyze job with a mock API response result.

        This is a development-only helper. It validates the external response
        contract shape but does not execute Forge, Runtime, queues, or workers.
        """

        job = self.get_job(job_id)
        if job is None:
            raise KeyError(job_id)
        if job["status"] in {"completed", "failed", "cancelled"}:
            raise RuntimeError(f"{job['status']} job cannot be completed")

        _validate_api_response_result(result)
        updated_at = _utc_now_iso()
        completed = build_api_job_response(
            job_id=job_id,
            status="completed",
            created_at=job["created_at"],
            updated_at=updated_at,
            input_summary=job["input_summary"],
            result=result,
            error=None,
            links={
                "self": f"/api/jobs/{job_id}",
                "result": f"/api/jobs/{job_id}",
            },
            next_actions=["review_deployment_decision"],
        )
        self._jobs[job_id] = completed
        return completed

    def apply_worker_response(self, job_id: str, worker_response: dict[str, Any]) -> dict[str, Any]:
        job = self.get_job(job_id)
        if job is None:
            raise KeyError(job_id)
        try:
            updated = apply_worker_response_to_job(job, worker_response)
        except WorkerContractError:
            raise
        self._jobs[job_id] = updated
        return updated


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


def _validate_api_response_result(result: Any) -> None:
    if not isinstance(result, dict):
        raise ValueError("result must be a JSON object")

    required_objects = {
        "summary",
        "comparison",
        "deployment_decision",
        "provenance",
        "metadata",
        "timestamps",
        "execution_info",
    }
    missing = sorted(field for field in required_objects if field not in result)
    if missing:
        raise ValueError(f"result missing required field(s): {', '.join(missing)}")

    for field in sorted(required_objects):
        if not isinstance(result[field], dict):
            raise ValueError(f"result.{field} must be an object")

    decision = result["deployment_decision"].get("decision")
    if not isinstance(decision, str) or not decision:
        raise ValueError("result.deployment_decision.decision must be a non-empty string")

    if result["summary"].get("deployment_decision") != decision:
        raise ValueError(
            "result.summary.deployment_decision must match "
            "result.deployment_decision.decision"
        )
