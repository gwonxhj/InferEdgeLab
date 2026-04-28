from __future__ import annotations

from typing import Any


JOB_STATUSES = {"queued", "running", "completed", "failed", "cancelled"}
ACTIVE_JOB_STATUSES = {"queued", "running"}


class ApiJobContractError(ValueError):
    """Raised when a SaaS job response does not satisfy the contract."""


def build_api_job_response(
    *,
    job_id: str,
    status: str,
    created_at: str,
    updated_at: str,
    input_summary: dict[str, Any],
    result: dict[str, Any] | None = None,
    error: dict[str, Any] | None = None,
    links: dict[str, Any] | None = None,
    next_actions: list[str] | None = None,
) -> dict[str, Any]:
    """Build and validate a SaaS async job response.

    This contract helper only describes the response shape. It does not create
    jobs, persist state, enqueue work, or run background workers.
    """

    response = {
        "job_id": job_id,
        "status": status,
        "created_at": created_at,
        "updated_at": updated_at,
        "input_summary": input_summary,
        "result": result,
        "error": error,
        "links": links or {},
        "next_actions": next_actions or [],
    }
    return validate_api_job_response(response)


def validate_api_job_response(response: Any) -> dict[str, Any]:
    if not isinstance(response, dict):
        raise ApiJobContractError("job response must be a JSON object")

    _require_string(response, "job_id")
    status = _require_string(response, "status")
    if status not in JOB_STATUSES:
        raise ApiJobContractError(
            "status must be one of: cancelled, completed, failed, queued, running"
        )

    _require_string(response, "created_at")
    _require_string(response, "updated_at")
    _require_dict(response, "input_summary")

    if "result" not in response:
        raise ApiJobContractError("result field must be present")
    if "error" not in response:
        raise ApiJobContractError("error field must be present")

    result = response.get("result")
    error = response.get("error")

    if status == "completed":
        if not isinstance(result, dict):
            raise ApiJobContractError("completed job must include a result object")
        deployment_decision = result.get("deployment_decision")
        if not isinstance(deployment_decision, dict):
            raise ApiJobContractError(
                "completed job result must include deployment_decision"
            )
        if not deployment_decision.get("decision"):
            raise ApiJobContractError(
                "completed job deployment_decision must include decision"
            )
        if error is not None:
            raise ApiJobContractError("completed job error must be null")
    elif status == "failed":
        if result is not None:
            raise ApiJobContractError("failed job result must be null")
        if not isinstance(error, dict):
            raise ApiJobContractError("failed job must include an error object")
        _require_string(error, "code")
        _require_string(error, "message")
    else:
        if result is not None:
            raise ApiJobContractError(f"{status} job result must be null")
        if error is not None and not isinstance(error, dict):
            raise ApiJobContractError("error must be null or an object")

    _require_dict(response, "links")
    next_actions = response.get("next_actions")
    if not isinstance(next_actions, list):
        raise ApiJobContractError("next_actions must be a list")
    if any(not isinstance(action, str) for action in next_actions):
        raise ApiJobContractError("next_actions entries must be strings")

    return response


def _require_string(data: dict[str, Any], field: str) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value:
        raise ApiJobContractError(f"{field} must be a non-empty string")
    return value


def _require_dict(data: dict[str, Any], field: str) -> dict[str, Any]:
    value = data.get(field)
    if not isinstance(value, dict):
        raise ApiJobContractError(f"{field} must be an object")
    return value
