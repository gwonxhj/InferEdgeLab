from __future__ import annotations

import json
from pathlib import Path

from inferedgelab.services.api_job_contract import build_api_job_response
from inferedgelab.services.api_job_contract import validate_api_job_response
from inferedgelab.services.worker_contract import apply_worker_response_to_job
from inferedgelab.services.worker_contract import validate_worker_response


FIXTURES = Path(__file__).resolve().parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_runtime_completed_worker_response_fixture_satisfies_lab_contract():
    response = validate_worker_response(
        load_fixture("runtime_worker_completed_response.json")
    )

    assert response["status"] == "completed"
    assert response["runtime_result"]["engine_backend"] == "tensorrt"
    assert response["runtime_result"]["device_name"] == "jetson"
    assert response["runtime_result"]["extra"]["worker_response_mode"] == "dry_run"


def test_runtime_failed_worker_response_fixture_satisfies_lab_contract():
    response = validate_worker_response(load_fixture("runtime_worker_failed_response.json"))

    assert response["status"] == "failed"
    assert response["error"]["code"] == "runtime_worker_dry_run_failed"
    assert "runtime_result" not in response


def test_runtime_completed_worker_response_maps_to_completed_lab_job():
    job = _make_runtime_queued_job()
    worker_response = load_fixture("runtime_worker_completed_response.json")

    completed = validate_api_job_response(
        apply_worker_response_to_job(job, worker_response)
    )

    assert completed["status"] == "completed"
    assert completed["error"] is None
    assert completed["updated_at"] == worker_response["completed_at"]
    assert completed["result"]["deployment_decision"]["decision"] == "unknown"
    assert completed["result"]["comparison"]["result"]["runtime_result"] == worker_response["runtime_result"]
    assert completed["result"]["guard_analysis"] == worker_response["guard_analysis"]
    assert completed["result"]["provenance"]["runtime"]["runtime_artifact_sha256"]
    assert completed["result"]["provenance"]["runtime"]["source_model_sha256"]
    assert completed["result"]["execution_info"]["engine"] == "tensorrt"
    assert completed["result"]["execution_info"]["device"] == "jetson"


def test_runtime_failed_worker_response_maps_to_failed_lab_job():
    job = _make_runtime_queued_job()
    worker_response = load_fixture("runtime_worker_failed_response.json")

    failed = validate_api_job_response(apply_worker_response_to_job(job, worker_response))

    assert failed["status"] == "failed"
    assert failed["result"] is None
    assert failed["error"] == worker_response["error"]
    assert failed["updated_at"] == worker_response["failed_at"]


def _make_runtime_queued_job() -> dict:
    return build_api_job_response(
        job_id="job_runtime_worker_smoke",
        status="queued",
        created_at="2026-04-28T06:34:00Z",
        updated_at="2026-04-28T06:34:10Z",
        input_summary={
            "workflow": "analyze",
            "model_path": "models/yolov8n.onnx",
            "artifact_path": "builds/yolov8n__jetson__tensorrt__jetson_fp16/model.engine",
            "metadata_path": "artifacts/metadata.json",
            "manifest_path": "artifacts/manifest.json",
            "notes": "runtime worker response compatibility smoke",
        },
        result=None,
        error=None,
        links={"self": "/api/jobs/job_runtime_worker_smoke"},
        next_actions=["poll_self"],
    )
