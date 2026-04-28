from __future__ import annotations

import json
from pathlib import Path

import pytest

from inferedgelab.services.api_job_contract import build_api_job_response
from inferedgelab.services.worker_contract import (
    WorkerContractError,
    apply_worker_response_to_job,
    build_worker_request_from_job,
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


def test_queued_analyze_job_maps_to_valid_worker_request():
    job = _make_queued_analyze_job()

    request = build_worker_request_from_job(job)

    assert validate_worker_request(request) == request
    assert request["job_id"] == job["job_id"]
    assert request["input_summary"] == job["input_summary"]
    assert request["requested_at"] == job["updated_at"]
    assert request["model_path"] == "models/resnet18.onnx"
    assert request["artifact_path"] is None


def test_worker_request_mapping_preserves_optional_paths_notes_and_options():
    job = _make_queued_analyze_job(
        input_summary={
            "workflow": "analyze",
            "model_path": "models/resnet18.onnx",
            "artifact_path": None,
            "metadata_path": "artifacts/metadata.json",
            "manifest_path": "artifacts/manifest.json",
            "notes": "run worker smoke",
            "options": {
                "backend": "onnxruntime",
                "target": "cpu",
                "precision": "fp32",
            },
        }
    )

    request = build_worker_request_from_job(
        job,
        options={"with_guard": True, "runs": 50},
    )

    assert validate_worker_request(request) == request
    assert request["metadata_path"] == "artifacts/metadata.json"
    assert request["manifest_path"] == "artifacts/manifest.json"
    assert request["options"] == {
        "backend": "onnxruntime",
        "target": "cpu",
        "precision": "fp32",
        "with_guard": True,
        "runs": 50,
        "notes": "run worker smoke",
    }


def test_completed_job_cannot_map_to_worker_request():
    job = build_api_job_response(
        job_id="job_completed",
        status="completed",
        created_at="2026-04-28T05:30:00Z",
        updated_at="2026-04-28T05:31:00Z",
        input_summary={
            "workflow": "analyze",
            "model_path": "models/resnet18.onnx",
            "artifact_path": None,
        },
        result={"deployment_decision": {"decision": "deployable"}},
        error=None,
        links={"self": "/api/jobs/job_completed"},
        next_actions=["review_deployment_decision"],
    )

    with pytest.raises(WorkerContractError, match="only queued jobs"):
        build_worker_request_from_job(job)


def test_worker_request_mapping_rejects_missing_model_or_artifact_path():
    job = _make_queued_analyze_job(
        input_summary={
            "workflow": "analyze",
            "model_path": None,
            "artifact_path": None,
        }
    )

    with pytest.raises(WorkerContractError, match="model_path or artifact_path"):
        build_worker_request_from_job(job)


def test_worker_request_mapping_rejects_non_analyze_job():
    job = _make_queued_analyze_job(
        input_summary={
            "workflow": "compare",
            "model_path": "models/resnet18.onnx",
            "artifact_path": None,
        }
    )

    with pytest.raises(WorkerContractError, match="only analyze jobs"):
        build_worker_request_from_job(job)


def test_worker_completed_response_fixture_satisfies_contract():
    response = validate_worker_response(load_fixture("worker_completed_response.json"))

    assert response["status"] == "completed"
    assert response["runtime_result"]["engine"] == "onnxruntime"
    assert response["forge_metadata"]["precision"] == "fp32"
    assert response["guard_analysis"]["status"] == "ok"


def test_completed_worker_response_maps_to_completed_job():
    job = _make_queued_analyze_job(job_id="job_worker_smoke")
    worker_response = load_fixture("worker_completed_response.json")

    completed = apply_worker_response_to_job(job, worker_response)

    assert completed["job_id"] == job["job_id"]
    assert completed["status"] == "completed"
    assert completed["updated_at"] == worker_response["completed_at"]
    assert completed["error"] is None
    assert completed["result"]["deployment_decision"]["decision"] == "unknown"
    assert completed["result"]["comparison"]["result"]["runtime_result"] == worker_response["runtime_result"]
    assert completed["result"]["provenance"]["forge_metadata"] == worker_response["forge_metadata"]
    assert completed["next_actions"] == ["review_deployment_decision"]


def test_completed_worker_response_preserves_optional_guard_analysis():
    job = _make_queued_analyze_job(job_id="job_worker_smoke")
    worker_response = load_fixture("worker_completed_response.json")

    completed = apply_worker_response_to_job(job, worker_response)

    assert completed["result"]["guard_analysis"] == worker_response["guard_analysis"]
    assert completed["result"]["summary"]["guard_status"] == "ok"


def test_completed_worker_response_allows_guard_analysis_absent():
    job = _make_queued_analyze_job(job_id="job_worker_smoke")
    worker_response = load_fixture("worker_completed_response.json")
    worker_response.pop("guard_analysis")

    completed = apply_worker_response_to_job(job, worker_response)

    assert "guard_analysis" not in completed["result"]
    assert completed["result"]["summary"]["guard_status"] is None


def test_worker_failed_response_fixture_satisfies_contract():
    response = validate_worker_response(load_fixture("worker_failed_response.json"))

    assert response["status"] == "failed"
    assert response["error"]["code"] == "runtime_result_missing"


def test_failed_worker_response_maps_to_failed_job():
    job = _make_queued_analyze_job(job_id="job_worker_smoke")
    worker_response = load_fixture("worker_failed_response.json")

    failed = apply_worker_response_to_job(job, worker_response)

    assert failed["job_id"] == job["job_id"]
    assert failed["status"] == "failed"
    assert failed["updated_at"] == worker_response["failed_at"]
    assert failed["result"] is None
    assert failed["error"] == worker_response["error"]
    assert failed["next_actions"] == ["inspect_error", "create_new_job"]


def test_worker_response_mapping_rejects_job_id_mismatch():
    job = _make_queued_analyze_job(job_id="job_other")
    worker_response = load_fixture("worker_completed_response.json")

    with pytest.raises(WorkerContractError, match="job_id"):
        apply_worker_response_to_job(job, worker_response)


def test_worker_response_mapping_rejects_already_completed_job():
    job = build_api_job_response(
        job_id="job_worker_smoke",
        status="completed",
        created_at="2026-04-28T05:30:00Z",
        updated_at="2026-04-28T05:31:00Z",
        input_summary={
            "workflow": "analyze",
            "model_path": "models/resnet18.onnx",
            "artifact_path": None,
        },
        result={"deployment_decision": {"decision": "unknown"}},
        error=None,
        links={"self": "/api/jobs/job_worker_smoke"},
        next_actions=["review_deployment_decision"],
    )

    with pytest.raises(WorkerContractError, match="completed job"):
        apply_worker_response_to_job(job, load_fixture("worker_completed_response.json"))


def test_worker_response_mapping_rejects_invalid_worker_response():
    job = _make_queued_analyze_job(job_id="job_worker_smoke")
    worker_response = load_fixture("worker_completed_response.json")
    worker_response.pop("runtime_result")

    with pytest.raises(WorkerContractError, match="runtime_result"):
        apply_worker_response_to_job(job, worker_response)


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


def _make_queued_analyze_job(
    *,
    job_id: str = "job_analyze_queued",
    input_summary: dict | None = None,
) -> dict:
    return build_api_job_response(
        job_id=job_id,
        status="queued",
        created_at="2026-04-28T05:30:00Z",
        updated_at="2026-04-28T05:30:10Z",
        input_summary=input_summary
        or {
            "workflow": "analyze",
            "model_path": "models/resnet18.onnx",
            "artifact_path": None,
            "metadata_path": None,
            "manifest_path": None,
            "notes": None,
        },
        result=None,
        error=None,
        links={"self": f"/api/jobs/{job_id}"},
        next_actions=["poll_self"],
    )
