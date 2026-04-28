from __future__ import annotations

from typing import Any

from inferedgelab.services.api_job_contract import ApiJobContractError
from inferedgelab.services.api_job_contract import build_api_job_response
from inferedgelab.services.api_job_contract import validate_api_job_response


WORKER_RESPONSE_STATUSES = {"completed", "failed"}


class WorkerContractError(ValueError):
    """Raised when a Forge/Runtime worker boundary payload is invalid."""


def forge_summary_to_input_summary(summary: dict[str, Any]) -> dict[str, Any]:
    """Normalize a Forge worker/runtime summary into a Lab analyze input summary."""

    if not isinstance(summary, dict):
        raise WorkerContractError("Forge worker/runtime summary must be a JSON object")

    source_model_path = _require_string(summary, "source_model_path")
    artifact_path = _require_string(summary, "artifact_path")
    metadata_path = _optional_string(summary, "metadata_path")
    manifest_path = _optional_string(summary, "manifest_path")
    provenance = {
        "source_model_sha256": _require_string(summary, "source_model_sha256"),
        "artifact_sha256": _require_string(summary, "artifact_sha256"),
        "artifact_type": _require_string(summary, "artifact_type"),
        "preset_name": _require_string(summary, "preset_name"),
        "build_id": _require_string(summary, "build_id"),
    }
    options = {
        "backend": _require_string(summary, "backend"),
        "target": _require_string(summary, "target"),
        "precision": _require_string(summary, "precision"),
        "batch": _require_positive_int(summary, "batch"),
        "height": _require_positive_int(summary, "height"),
        "width": _require_positive_int(summary, "width"),
        "provenance": provenance,
    }
    return {
        "workflow": "analyze",
        "model_path": source_model_path,
        "artifact_path": artifact_path,
        "metadata_path": metadata_path,
        "manifest_path": manifest_path,
        "provenance": provenance,
        "options": options,
    }


normalize_forge_summary_for_worker_request = forge_summary_to_input_summary


def build_worker_request_from_job(
    job: dict[str, Any],
    *,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Project a queued analyze job response into the worker request contract."""

    try:
        validated_job = validate_api_job_response(job)
    except ApiJobContractError as exc:
        raise WorkerContractError(str(exc)) from exc

    status = validated_job["status"]
    if status != "queued":
        raise WorkerContractError("only queued jobs can be converted to worker requests")

    input_summary = validated_job["input_summary"]
    if input_summary.get("workflow") != "analyze":
        raise WorkerContractError("only analyze jobs can be converted to worker requests")

    request_options = _build_worker_options(input_summary, options)
    request = {
        "job_id": validated_job["job_id"],
        "input_summary": input_summary,
        "requested_at": validated_job.get("updated_at") or validated_job["created_at"],
        "model_path": input_summary.get("model_path"),
        "artifact_path": input_summary.get("artifact_path"),
        "metadata_path": input_summary.get("metadata_path"),
        "manifest_path": input_summary.get("manifest_path"),
        "options": request_options,
    }
    return validate_worker_request(request)


def apply_worker_response_to_job(
    job: dict[str, Any],
    worker_response: dict[str, Any],
) -> dict[str, Any]:
    """Project a terminal worker response back into a Lab job response."""

    try:
        validated_job = validate_api_job_response(job)
    except ApiJobContractError as exc:
        raise WorkerContractError(str(exc)) from exc

    job_status = validated_job["status"]
    if job_status in {"completed", "failed", "cancelled"}:
        raise WorkerContractError(f"{job_status} job cannot accept worker response")

    validated_response = validate_worker_response(worker_response)
    if validated_response["job_id"] != validated_job["job_id"]:
        raise WorkerContractError("worker response job_id must match job_id")

    if validated_response["status"] == "completed":
        result = _build_completed_job_result(validated_response)
        return build_api_job_response(
            job_id=validated_job["job_id"],
            status="completed",
            created_at=validated_job["created_at"],
            updated_at=validated_response["completed_at"],
            input_summary=validated_job["input_summary"],
            result=result,
            error=None,
            links={
                "self": f"/api/jobs/{validated_job['job_id']}",
                "result": f"/api/jobs/{validated_job['job_id']}",
            },
            next_actions=["review_deployment_decision"],
        )

    return build_api_job_response(
        job_id=validated_job["job_id"],
        status="failed",
        created_at=validated_job["created_at"],
        updated_at=validated_response["failed_at"],
        input_summary=validated_job["input_summary"],
        result=None,
        error=validated_response["error"],
        links={"self": f"/api/jobs/{validated_job['job_id']}"},
        next_actions=["inspect_error", "create_new_job"],
    )


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


def _build_completed_job_result(worker_response: dict[str, Any]) -> dict[str, Any]:
    provided_result = worker_response.get("result")
    if provided_result is not None:
        if not isinstance(provided_result, dict):
            raise WorkerContractError("completed worker response result must be an object")
        _validate_completed_job_result(provided_result)
        return provided_result

    runtime_result = worker_response["runtime_result"]
    guard_analysis = worker_response.get("guard_analysis")
    deployment_decision = {
        "decision": "unknown",
        "reason": "Worker response has not been compared by Lab yet.",
        "lab_overall": None,
        "guard_status": (guard_analysis or {}).get("status"),
        "recommended_action": "Run Lab compare/report before deployment decision.",
    }
    result = {
        "summary": {
            "response_type": "analyze_worker_result",
            "overall": None,
            "comparison_mode": None,
            "precision_pair": None,
            "deployment_decision": deployment_decision["decision"],
            "guard_status": deployment_decision["guard_status"],
        },
        "comparison": {
            "result": {"runtime_result": runtime_result},
            "judgement": {},
            "rendered": {"markdown": None, "html": None},
        },
        "deployment_decision": deployment_decision,
        "provenance": {
            "runtime": runtime_result.get("extra"),
            "forge_metadata": worker_response.get("forge_metadata"),
            "source_bundle": "worker_response",
        },
        "metadata": {
            "worker_status": worker_response["status"],
            "completed_at": worker_response["completed_at"],
        },
        "timestamps": {
            "runtime": runtime_result.get("timestamp"),
            "completed_at": worker_response["completed_at"],
        },
        "execution_info": {
            "engine": _first_present(runtime_result, ("engine", "engine_backend", "backend")),
            "device": _first_present(runtime_result, ("device", "device_name", "target")),
            "precision": runtime_result.get("precision"),
            "batch": runtime_result.get("batch"),
            "height": runtime_result.get("height"),
            "width": runtime_result.get("width"),
        },
    }
    if guard_analysis is not None:
        result["guard_analysis"] = guard_analysis
    _validate_completed_job_result(result)
    return result


def _validate_completed_job_result(result: dict[str, Any]) -> None:
    deployment_decision = result.get("deployment_decision")
    if not isinstance(deployment_decision, dict):
        raise WorkerContractError("completed job result must include deployment_decision")
    decision = deployment_decision.get("decision")
    if not isinstance(decision, str) or not decision:
        raise WorkerContractError(
            "completed job deployment_decision must include decision"
        )


def _build_worker_options(
    input_summary: dict[str, Any],
    options: dict[str, Any] | None,
) -> dict[str, Any]:
    summary_options = input_summary.get("options")
    if summary_options is None:
        request_options: dict[str, Any] = {}
    elif isinstance(summary_options, dict):
        request_options = dict(summary_options)
    else:
        raise WorkerContractError("input_summary.options must be an object when provided")

    if options is not None:
        if not isinstance(options, dict):
            raise WorkerContractError("options must be an object when provided")
        request_options.update(options)

    notes = input_summary.get("notes")
    if notes is not None:
        if not isinstance(notes, str):
            raise WorkerContractError("input_summary.notes must be a string when provided")
        request_options.setdefault("notes", notes)

    return request_options


def _validate_runtime_result(runtime_result: dict[str, Any]) -> None:
    required = {
        "precision",
        "batch",
        "height",
        "width",
        "mean_ms",
        "p50_ms",
        "p95_ms",
        "p99_ms",
        "timestamp",
    }
    missing = sorted(field for field in required if field not in runtime_result)
    for aliases in (
        ("model", "model_path"),
        ("engine", "engine_backend", "backend"),
        ("device", "device_name", "target"),
    ):
        if _first_present(runtime_result, aliases) is None:
            missing.append("/".join(aliases))
    if missing:
        raise WorkerContractError(
            f"runtime_result missing required field(s): {', '.join(missing)}"
        )


def _first_present(data: dict[str, Any], fields: tuple[str, ...]) -> Any:
    for field in fields:
        value = data.get(field)
        if value is not None:
            return value
    return None


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


def _require_positive_int(data: dict[str, Any], field: str) -> int:
    value = data.get(field)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise WorkerContractError(f"{field} must be a positive integer")
    return value


def _require_dict(data: dict[str, Any], field: str) -> dict[str, Any]:
    value = data.get(field)
    if not isinstance(value, dict):
        raise WorkerContractError(f"{field} must be an object")
    return value
