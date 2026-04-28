from __future__ import annotations

import copy
import json
from pathlib import Path

import inferedgelab.api as api
from inferedgelab.services.api_job_contract import validate_api_job_response
from inferedgelab.services.worker_contract import (
    apply_worker_response_to_job,
    build_worker_request_from_job,
    validate_worker_request,
)


FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _get_route_endpoint(app, path: str, method: str = "GET"):
    for route in app.routes:
        if getattr(route, "path", None) == path and method in getattr(route, "methods", set()):
            return route.endpoint
    raise AssertionError(f"route not found: {method} {path}")


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_analyze_worker_completed_workflow_smoke():
    app = api.create_app()
    analyze_endpoint = _get_route_endpoint(app, "/api/analyze", method="POST")
    complete_dev_endpoint = _get_route_endpoint(
        app,
        "/api/jobs/{job_id}/complete-dev",
        method="POST",
    )
    jobs_endpoint = _get_route_endpoint(app, "/api/jobs/{job_id}")

    queued = analyze_endpoint(
        payload={
            "model_path": "models/resnet18.onnx",
            "metadata_path": "artifacts/metadata.json",
            "manifest_path": "artifacts/manifest.json",
            "notes": "worker workflow smoke",
        }
    )
    queued_job = validate_api_job_response(queued)
    assert queued_job["status"] == "queued"

    worker_request = build_worker_request_from_job(
        queued_job,
        options={"backend": "onnxruntime", "target": "cpu", "precision": "fp32"},
    )
    assert validate_worker_request(worker_request) == worker_request
    assert worker_request["job_id"] == queued_job["job_id"]
    assert worker_request["metadata_path"] == "artifacts/metadata.json"
    assert worker_request["manifest_path"] == "artifacts/manifest.json"

    worker_response = _make_completed_worker_response(worker_request["job_id"])
    mapped_completed = apply_worker_response_to_job(queued_job, worker_response)
    assert mapped_completed["status"] == "completed"
    assert mapped_completed["result"]["deployment_decision"]["decision"] == "unknown"
    assert mapped_completed["result"]["guard_analysis"] == worker_response["guard_analysis"]

    stored_completed = complete_dev_endpoint(
        job_id=queued_job["job_id"],
        payload={"result": mapped_completed["result"]},
    )
    fetched = jobs_endpoint(job_id=queued_job["job_id"])

    assert validate_api_job_response(stored_completed)["status"] == "completed"
    assert fetched == stored_completed
    assert fetched["status"] == "completed"
    assert fetched["result"]["deployment_decision"]["decision"] == "unknown"
    assert fetched["result"]["guard_analysis"] == worker_response["guard_analysis"]


def test_analyze_worker_failed_workflow_smoke():
    app = api.create_app()
    analyze_endpoint = _get_route_endpoint(app, "/api/analyze", method="POST")

    queued = analyze_endpoint(payload={"artifact_path": "artifacts/resnet18.engine"})
    queued_job = validate_api_job_response(queued)
    worker_request = build_worker_request_from_job(queued_job)
    worker_response = _make_failed_worker_response(worker_request["job_id"])

    mapped_failed = apply_worker_response_to_job(queued_job, worker_response)

    failed_job = validate_api_job_response(mapped_failed)
    assert failed_job["status"] == "failed"
    assert failed_job["result"] is None
    assert failed_job["error"] == worker_response["error"]


def _make_completed_worker_response(job_id: str) -> dict:
    response = copy.deepcopy(load_fixture("worker_completed_response.json"))
    response["job_id"] = job_id
    return response


def _make_failed_worker_response(job_id: str) -> dict:
    response = copy.deepcopy(load_fixture("worker_failed_response.json"))
    response["job_id"] = job_id
    return response
