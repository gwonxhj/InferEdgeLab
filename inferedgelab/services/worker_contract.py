from __future__ import annotations

from typing import Any


WORKER_RESPONSE_STATUSES = {"completed", "failed"}


class WorkerContractError(ValueError):
    """Raised when a Forge/Runtime worker boundary payload is invalid."""


def validate_worker_request(request: Any) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise WorkerContractError("worker request must be a JSON object")

    _require_string(request, "job_id")
    input_summary = _require_dict(request, "input_summary")
    _require_string(request, "requested_at")
    _require_dict(request, "options")

    model_path = _optional_string(request, "model_path")
    artifact_path = _optional_string(request, "artifact_path")
    if not model_path and not artifact_path:
        raise WorkerContractError("worker request requires model_path or artifact_path")

    for field in ("metadata_path", "manifest_path"):
        _optional_string(request, field)

    if input_summary.get("workflow") != "analyze":
        raise WorkerContractError("input_summary.workflow must be analyze")

    return request


def validate_worker_response(response: Any) -> dict[str, Any]:
    if not isinstance(response, dict):
        raise WorkerContractError("worker response must be a JSON object")

    _require_string(response, "job_id")
    status = _require_string(response, "status")
    if status not in WORKER_RESPONSE_STATUSES:
        raise WorkerContractError("status must be completed or failed")

    if status == "completed":
        _require_dict(response, "forge_metadata")
        runtime_result = _require_dict(response, "runtime_result")
        _require_string(response, "completed_at")
        if "error" in response and response["error"] is not None:
            raise WorkerContractError("completed worker response error must be null")
        if response.get("guard_analysis") is not None:
            _require_dict(response, "guard_analysis")
        _validate_runtime_result(runtime_result)
    else:
        _require_dict(response, "error")
        _require_string(response, "failed_at")
        if response.get("runtime_result") is not None:
            raise WorkerContractError("failed worker response runtime_result must be null")

    return response


def _validate_runtime_result(runtime_result: dict[str, Any]) -> None:
    required = {
        "model",
        "engine",
        "device",
        "precision",
        "batch",
        "height",
        "width",
        "mean_ms",
        "p95_ms",
        "p99_ms",
        "timestamp",
    }
    missing = sorted(field for field in required if field not in runtime_result)
    if missing:
        raise WorkerContractError(
            f"runtime_result missing required field(s): {', '.join(missing)}"
        )


def _require_string(data: dict[str, Any], field: str) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value:
        raise WorkerContractError(f"{field} must be a non-empty string")
    return value


def _optional_string(data: dict[str, Any], field: str) -> str | None:
    value = data.get(field)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise WorkerContractError(f"{field} must be a non-empty string when provided")
    return value


def _require_dict(data: dict[str, Any], field: str) -> dict[str, Any]:
    value = data.get(field)
    if not isinstance(value, dict):
        raise WorkerContractError(f"{field} must be an object")
    return value
