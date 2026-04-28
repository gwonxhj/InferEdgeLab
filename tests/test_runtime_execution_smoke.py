from __future__ import annotations

import json
from pathlib import Path

import inferedgelab.api as api
from inferedgelab.services import runtime_executor
from inferedgelab.services.api_job_contract import validate_api_job_response


def _get_route_endpoint(app, path: str, method: str = "GET"):
    for route in app.routes:
        if getattr(route, "path", None) == path and method in getattr(route, "methods", set()):
            return route.endpoint
    raise AssertionError(f"route not found: {method} {path}")


def test_runtime_executor_invokes_cli_and_returns_completed_worker_response(monkeypatch):
    captured: dict[str, object] = {}

    def fake_run(command, check, capture_output, text):
        captured["command"] = command
        output_path = Path(command[command.index("--output") + 1])
        output_path.write_text(
            json.dumps(
                {
                    "model": "models/resnet18.onnx",
                    "engine": "onnxruntime",
                    "device": "cpu",
                    "precision": "fp32",
                    "batch": 1,
                    "height": 224,
                    "width": 224,
                    "mean_ms": 10.0,
                    "p50_ms": 9.8,
                    "p95_ms": 11.2,
                    "p99_ms": 12.0,
                    "timestamp": "2026-04-28T10:00:00Z",
                    "extra": {"runtime_artifact_path": "models/resnet18.onnx"},
                }
            ),
            encoding="utf-8",
        )
        return _CompletedProcess(returncode=0)

    monkeypatch.setattr(runtime_executor.subprocess, "run", fake_run)
    worker_response = runtime_executor.run_runtime_inference(
        {
            "job_id": "job_runtime_smoke",
            "input_summary": {"workflow": "analyze", "model_path": "models/resnet18.onnx"},
            "model_path": "models/resnet18.onnx",
            "options": {
                "runtime_cli_path": "./build/inferedge-runtime",
                "backend": "onnxruntime",
                "target": "cpu",
                "precision": "fp32",
            },
        }
    )

    assert worker_response["job_id"] == "job_runtime_smoke"
    assert worker_response["status"] == "completed"
    assert worker_response["runtime_result"]["mean_ms"] == 10.0
    assert worker_response["runtime_result"]["p50_ms"] == 9.8
    assert worker_response["completed_at"]
    assert captured["command"][:3] == [
        "./build/inferedge-runtime",
        "--model",
        "models/resnet18.onnx",
    ]
    assert "--output" in captured["command"]


def test_analyze_preserves_runtime_execution_options():
    app = api.create_app()
    analyze_endpoint = _get_route_endpoint(app, "/api/analyze", method="POST")

    queued = analyze_endpoint(
        payload={
            "model_path": "models/resnet18.onnx",
            "options": {
                "runtime_cli_path": "/opt/inferedge-runtime/bin/inferedge-runtime",
                "runs": 5,
                "warmup": 1,
            },
        }
    )

    assert queued["input_summary"]["options"] == {
        "runtime_cli_path": "/opt/inferedge-runtime/bin/inferedge-runtime",
        "runs": 5,
        "warmup": 1,
    }


def test_run_runtime_dev_passes_analyze_options_to_runtime_executor(monkeypatch):
    app = api.create_app()
    analyze_endpoint = _get_route_endpoint(app, "/api/analyze", method="POST")
    run_runtime_endpoint = _get_route_endpoint(
        app,
        "/api/jobs/{job_id}/run-runtime-dev",
        method="POST",
    )
    captured: dict[str, object] = {}

    def fake_run_runtime_inference(worker_request):
        captured["worker_request"] = worker_request
        return _make_completed_worker_response(worker_request["job_id"])

    monkeypatch.setattr(api, "run_runtime_inference", fake_run_runtime_inference)

    queued = analyze_endpoint(
        payload={
            "model_path": "models/resnet18.onnx",
            "options": {
                "runtime_cli_path": "/opt/inferedge-runtime/bin/inferedge-runtime",
                "runs": 7,
                "warmup": 2,
            },
        }
    )
    completed = run_runtime_endpoint(job_id=queued["job_id"])

    worker_request = captured["worker_request"]
    assert completed["status"] == "completed"
    assert worker_request["options"]["runtime_cli_path"] == "/opt/inferedge-runtime/bin/inferedge-runtime"
    assert worker_request["options"]["runs"] == 7
    assert worker_request["options"]["warmup"] == 2


def test_runtime_executor_returns_failed_worker_response_on_cli_failure(monkeypatch):
    def fake_run(command, check, capture_output, text):
        return _CompletedProcess(returncode=2, stderr="runtime failed")

    monkeypatch.setattr(runtime_executor.subprocess, "run", fake_run)

    worker_response = runtime_executor.run_runtime_inference(
        {
            "job_id": "job_runtime_failure",
            "input_summary": {"workflow": "analyze", "model_path": "models/resnet18.onnx"},
            "model_path": "models/resnet18.onnx",
            "options": {"runtime_cli_path": "./build/inferedge-runtime"},
        }
    )

    assert worker_response["status"] == "failed"
    assert worker_response["error"]["code"] == "runtime_cli_failed"
    assert worker_response["error"]["stage"] == "runtime"
    assert "runtime failed" in worker_response["error"]["message"]


def test_runtime_executor_returns_unavailable_for_bad_runtime_cli_path():
    worker_response = runtime_executor.run_runtime_inference(
        {
            "job_id": "job_runtime_missing_cli",
            "input_summary": {"workflow": "analyze", "model_path": "models/resnet18.onnx"},
            "model_path": "models/resnet18.onnx",
            "options": {"runtime_cli_path": "/definitely/missing/inferedge-runtime"},
        }
    )

    assert worker_response["status"] == "failed"
    assert worker_response["error"]["code"] == "runtime_cli_unavailable"
    assert "/definitely/missing/inferedge-runtime" in worker_response["error"]["message"]


def test_run_runtime_dev_endpoint_maps_worker_response_to_completed_job(monkeypatch):
    app = api.create_app()
    analyze_endpoint = _get_route_endpoint(app, "/api/analyze", method="POST")
    run_runtime_endpoint = _get_route_endpoint(
        app,
        "/api/jobs/{job_id}/run-runtime-dev",
        method="POST",
    )
    jobs_endpoint = _get_route_endpoint(app, "/api/jobs/{job_id}")

    def fake_run_runtime_inference(worker_request):
        return _make_completed_worker_response(worker_request["job_id"])

    monkeypatch.setattr(api, "run_runtime_inference", fake_run_runtime_inference)

    queued = analyze_endpoint(payload={"model_path": "models/resnet18.onnx"})
    completed = run_runtime_endpoint(job_id=queued["job_id"])
    fetched = jobs_endpoint(job_id=queued["job_id"])

    job = validate_api_job_response(completed)
    assert job["status"] == "completed"
    assert job["result"] is not None
    assert job["result"]["deployment_decision"]["decision"] == "unknown"
    assert fetched == completed


def test_run_runtime_dev_endpoint_maps_runtime_failure_to_failed_job(monkeypatch):
    app = api.create_app()
    analyze_endpoint = _get_route_endpoint(app, "/api/analyze", method="POST")
    run_runtime_endpoint = _get_route_endpoint(
        app,
        "/api/jobs/{job_id}/run-runtime-dev",
        method="POST",
    )

    def fake_run_runtime_inference(worker_request):
        return {
            "job_id": worker_request["job_id"],
            "status": "failed",
            "error": {
                "code": "runtime_cli_failed",
                "message": "runtime failed",
                "stage": "runtime",
            },
            "failed_at": "2026-04-28T10:00:30Z",
        }

    monkeypatch.setattr(api, "run_runtime_inference", fake_run_runtime_inference)

    queued = analyze_endpoint(payload={"model_path": "models/resnet18.onnx"})
    failed = run_runtime_endpoint(job_id=queued["job_id"])
    job = validate_api_job_response(failed)

    assert job["status"] == "failed"
    assert job["result"] is None
    assert job["error"]["code"] == "runtime_cli_failed"


def _make_completed_worker_response(job_id: str) -> dict:
    return {
        "job_id": job_id,
        "status": "completed",
        "forge_metadata": {
            "backend": "onnxruntime",
            "target": "cpu",
            "precision": "fp32",
        },
        "runtime_result": {
            "model": "resnet18",
            "engine": "onnxruntime",
            "device": "cpu",
            "precision": "fp32",
            "batch": 1,
            "height": 224,
            "width": 224,
            "mean_ms": 10.0,
            "p50_ms": 9.8,
            "p95_ms": 11.2,
            "p99_ms": 12.0,
            "timestamp": "2026-04-28T10:00:00Z",
            "extra": {"runtime_artifact_path": "models/resnet18.onnx"},
        },
        "completed_at": "2026-04-28T10:00:30Z",
    }


class _CompletedProcess:
    def __init__(self, *, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
