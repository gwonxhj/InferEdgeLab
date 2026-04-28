from __future__ import annotations

import json
from pathlib import Path

import pytest

from inferedgelab.services.worker_contract import (
    WorkerContractError,
    validate_worker_request,
    validate_worker_response,
)


FIXTURES = Path(__file__).resolve().parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_worker_request_fixture_satisfies_contract():
    request = validate_worker_request(load_fixture("worker_request.json"))

    assert request["job_id"] == "job_worker_smoke"
    assert request["input_summary"]["workflow"] == "analyze"
    assert request["model_path"] == "models/resnet18.onnx"
    assert request["options"]["backend"] == "onnxruntime"


def test_worker_completed_response_fixture_satisfies_contract():
    response = validate_worker_response(load_fixture("worker_completed_response.json"))

    assert response["status"] == "completed"
    assert response["runtime_result"]["engine"] == "onnxruntime"
    assert response["forge_metadata"]["precision"] == "fp32"
    assert response["guard_analysis"]["status"] == "ok"


def test_worker_failed_response_fixture_satisfies_contract():
    response = validate_worker_response(load_fixture("worker_failed_response.json"))

    assert response["status"] == "failed"
    assert response["error"]["code"] == "runtime_result_missing"


def test_worker_completed_response_requires_runtime_result():
    response = load_fixture("worker_completed_response.json")
    response.pop("runtime_result")

    with pytest.raises(WorkerContractError, match="runtime_result"):
        validate_worker_response(response)


def test_worker_failed_response_requires_error():
    response = load_fixture("worker_failed_response.json")
    response.pop("error")

    with pytest.raises(WorkerContractError, match="error"):
        validate_worker_response(response)


def test_worker_guard_analysis_is_optional():
    response = load_fixture("worker_completed_response.json")
    response.pop("guard_analysis")

    validated = validate_worker_response(response)

    assert "guard_analysis" not in validated
    assert validated["status"] == "completed"


def test_worker_response_rejects_invalid_status():
    response = load_fixture("worker_completed_response.json")
    response["status"] = "running"

    with pytest.raises(WorkerContractError, match="status"):
        validate_worker_response(response)


def test_worker_request_rejects_missing_model_or_artifact_path():
    request = load_fixture("worker_request.json")
    request.pop("model_path")
    request.pop("artifact_path", None)

    with pytest.raises(WorkerContractError, match="model_path or artifact_path"):
        validate_worker_request(request)
