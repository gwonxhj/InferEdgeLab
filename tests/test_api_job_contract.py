from __future__ import annotations

import json
from pathlib import Path

import pytest

from inferedgelab.services.api_job_contract import (
    ApiJobContractError,
    JOB_STATUSES,
    build_api_job_response,
    validate_api_job_response,
)


FIXTURES = Path(__file__).resolve().parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "fixture_name",
    [
        "api_job_queued.json",
        "api_job_completed.json",
        "api_job_failed.json",
    ],
)
def test_api_job_fixtures_satisfy_contract(fixture_name):
    response = validate_api_job_response(load_fixture(fixture_name))

    assert set(response) >= {
        "job_id",
        "status",
        "created_at",
        "updated_at",
        "input_summary",
        "result",
        "error",
        "links",
        "next_actions",
    }
    assert response["status"] in JOB_STATUSES
    assert isinstance(response["input_summary"], dict)
    assert isinstance(response["links"], dict)
    assert isinstance(response["next_actions"], list)


def test_completed_job_requires_result_with_deployment_decision():
    completed = validate_api_job_response(load_fixture("api_job_completed.json"))

    assert completed["status"] == "completed"
    assert completed["error"] is None
    assert completed["result"]["deployment_decision"]["decision"] == "deployable"


def test_failed_job_requires_error_and_null_result():
    failed = validate_api_job_response(load_fixture("api_job_failed.json"))

    assert failed["status"] == "failed"
    assert failed["result"] is None
    assert failed["error"]["code"] == "result_not_found"


@pytest.mark.parametrize("status", ["queued", "running", "cancelled"])
def test_non_terminal_success_states_do_not_require_result(status):
    response = build_api_job_response(
        job_id=f"job_{status}",
        status=status,
        created_at="2026-04-28T04:30:00Z",
        updated_at="2026-04-28T04:30:30Z",
        input_summary={"workflow": "compare"},
        result=None,
        error=None,
        links={"self": f"/api/jobs/job_{status}"},
        next_actions=["poll_self"] if status != "cancelled" else ["create_new_job"],
    )

    assert response["status"] == status
    assert response["result"] is None


def test_completed_job_rejects_missing_deployment_decision():
    completed = load_fixture("api_job_completed.json")
    completed["result"].pop("deployment_decision")

    with pytest.raises(ApiJobContractError, match="deployment_decision"):
        validate_api_job_response(completed)


def test_failed_job_rejects_result_payload():
    failed = load_fixture("api_job_failed.json")
    failed["result"] = {"deployment_decision": {"decision": "unknown"}}

    with pytest.raises(ApiJobContractError, match="failed job result"):
        validate_api_job_response(failed)
