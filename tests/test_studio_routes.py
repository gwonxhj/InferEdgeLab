from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from fastapi.responses import FileResponse
from fastapi.responses import RedirectResponse

import inferedgelab.api as api


def _get_route(app, path: str):
    for route in app.routes:
        if getattr(route, "path", None) == path:
            return route
    raise AssertionError(f"route not found: {path}")


def _runtime_result(
    *,
    engine: str = "onnxruntime",
    device: str = "cpu",
    mean_ms: float = 45.0,
    p99_ms: float = 50.0,
    backend_key: str | None = "onnxruntime__cpu",
) -> dict:
    result = {
        "runtime_role": "runtime-result",
        "model": "yolov8n",
        "engine": engine,
        "device": device,
        "precision": "fp32",
        "batch": 1,
        "height": 640,
        "width": 640,
        "mean_ms": mean_ms,
        "p99_ms": p99_ms,
        "timestamp": "2026-04-29T12:00:00Z",
        "compare_key": "yolov8n__b1__h640w640__fp32",
    }
    if backend_key is not None:
        result["backend_key"] = backend_key
    return result


def test_studio_route_returns_local_studio_html():
    app = api.create_app()
    route = _get_route(app, "/studio")

    response = route.endpoint()
    html = Path(response.path).read_text(encoding="utf-8")

    assert isinstance(response, FileResponse)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert "InferEdge Local Studio" in html
    assert "SaaS-ready (local mode)" in html
    assert "Pipeline Flow" in html
    assert "Run" in html
    assert "Import" in html
    assert "Jetson Helper" in html
    assert 'data-critical="studio-dark"' in html
    assert 'href="/studio/static/style.css?v=15"' in html
    assert 'href="style.css?v=15"' in html
    assert 'src="/studio/static/app.js?v=15"' in html
    assert 'src="app.js?v=15"' in html
    assert "file-protocol-warning" in html
    assert 'placeholder="results/latest.json"' in html
    assert 'value="results/latest.json"' not in html
    assert 'id="import-json-payload"' in html
    assert 'autocomplete="off"' in html
    assert 'id="run-backend"' in html
    assert 'id="run-device"' in html
    assert 'id="import-backend-preset"' in html
    assert "TensorRT / Jetson" in html
    assert "Lab's local gate" in html
    assert "Load Demo Evidence" in html
    assert 'id="demo-state"' in html


def test_studio_static_assets_are_served():
    app = api.create_app()
    route = _get_route(app, "/studio/static/{asset_name}")

    app_response = route.endpoint(asset_name="app.js")
    style_response = route.endpoint(asset_name="style.css")

    assert isinstance(app_response, FileResponse)
    assert isinstance(style_response, FileResponse)
    assert app_response.status_code == 200
    assert style_response.status_code == 200
    assert app_response.headers["cache-control"] == "no-store"
    assert style_response.headers["cache-control"] == "no-store"
    assert "renderPipeline" in Path(app_response.path).read_text(encoding="utf-8")
    assert "pipeline-flow" in Path(style_response.path).read_text(encoding="utf-8")


def test_studio_static_assets_include_redesigned_ui_contracts():
    app = api.create_app()
    route = _get_route(app, "/studio/static/{asset_name}")

    app_response = route.endpoint(asset_name="app.js")
    style_response = route.endpoint(asset_name="style.css")
    app_text = Path(app_response.path).read_text(encoding="utf-8")
    style_text = Path(style_response.path).read_text(encoding="utf-8")

    assert app_response.status_code == 200
    assert style_response.status_code == 200
    assert "initLocalStudio" in app_text
    assert "DOMContentLoaded" in app_text
    assert "Open Studio from http://127.0.0.1:8000/studio" in app_text
    assert "responseErrorMessage" in app_text
    assert "markFileMode" in app_text
    assert "parseJsonResponse" in app_text
    assert "renderImportEvidence" in app_text
    assert "AIGuard diagnosis evidence was not loaded" in app_text
    assert "compareTone" in app_text
    assert "runtimeModelName" in app_text
    assert "Same backend" in app_text
    assert "hasImportedEvidence" in app_text
    assert "importedResultsByJobId" in app_text
    assert "rememberImportedResultForSelectedJob" in app_text
    assert "runOptions" in app_text
    assert "resetTransientInputs" in app_text
    assert "No guard run is required" in app_text
    assert "decisionNotes" in app_text
    assert "request record only" in app_text
    assert "loadDemoEvidence" in app_text
    assert "/studio/api/demo-evidence" in app_text
    assert "jobDisplayName" in app_text
    assert "jobCaption" in app_text
    assert "compareStatList" in app_text
    assert 'aiguard: hasGuardEvidence ? "completed" : "optional"' in app_text
    assert "#0b0f14" in style_text
    assert "grid-template-columns" in style_text
    assert ".form-stack button" in style_text
    assert ".tool-card" in style_text
    assert ".state-pill.optional" in style_text
    assert ".file-protocol-warning" in style_text
    assert ".evidence-summary" in style_text
    assert ".compare-card.improvement" in style_text
    assert ".demo-card" in style_text
    assert ".compare-stat-list" in style_text
    assert "justify-content: flex-start" in style_text


def test_studio_app_preserves_selected_job_detail_contract():
    app = api.create_app()
    route = _get_route(app, "/studio/static/{asset_name}")

    app_response = route.endpoint(asset_name="app.js")
    style_response = route.endpoint(asset_name="style.css")
    app_text = Path(app_response.path).read_text(encoding="utf-8")
    style_text = Path(style_response.path).read_text(encoding="utf-8")

    assert "selectedJobId" in app_text
    assert "loadJobs(payload.job_id)" in app_text
    assert "Queued job" in app_text
    assert "Runtime metrics are not attached" in app_text
    assert ".detail-note" in style_text
    assert ".inline-fields" in style_text
    assert ".future-heading" in style_text
    assert "min-width: 62px" in style_text


def test_studio_jobs_api_returns_json_structure():
    app = api.create_app()
    route = _get_route(app, "/studio/api/jobs")
    request = SimpleNamespace(app=app)

    response = route.endpoint(request=request)

    assert route.status_code is None
    assert response["source"] == "/api/jobs"
    assert response["count"] == 0
    assert response["jobs"] == []


def test_studio_malformed_path_redirects_to_studio():
    app = api.create_app()
    route = _get_route(app, "/studio로")

    response = route.endpoint()

    assert isinstance(response, RedirectResponse)
    assert response.status_code == 307
    assert response.headers["location"] == "/studio"


def test_studio_compare_latest_api_returns_json_structure():
    app = api.create_app()
    route = _get_route(app, "/studio/api/compare/latest")
    request = SimpleNamespace(app=app)

    response = route.endpoint(request=request)

    assert route.status_code is None
    assert response["status"] == "empty"
    assert "deployment_decision" in response
    assert "data" in response
    assert response.get("source") in {None, "/api/compare-latest"}
    assert response["deployment_decision"]["decision"] == "unknown"


def test_studio_run_api_creates_analyze_job():
    app = api.create_app()
    route = _get_route(app, "/studio/api/run")
    request = SimpleNamespace(app=app)

    response = route.endpoint(
        request=request,
        payload={
            "model_path": "models/yolov8n.onnx",
            "options": {"backend": "tensorrt", "device": "jetson"},
        },
    )

    assert response["status"] == "created"
    assert response["source"] == "/api/analyze"
    assert response["job_id"].startswith("job_")
    assert response["job"]["display_name"] == "Analyze yolov8n.onnx (tensorrt/jetson)"
    assert response["job"]["input_summary"]["model_path"] == "models/yolov8n.onnx"
    assert response["job"]["input_summary"]["options"] == {
        "backend": "tensorrt",
        "device": "jetson",
    }


def test_studio_run_job_can_be_listed_and_selected():
    app = api.create_app()
    request = SimpleNamespace(app=app)
    run_route = _get_route(app, "/studio/api/run")
    jobs_route = _get_route(app, "/studio/api/jobs")
    detail_route = _get_route(app, "/studio/api/job/{job_id}")

    created = run_route.endpoint(request=request, payload={"model_path": "models/yolov8n.onnx"})
    jobs = jobs_route.endpoint(request=request)
    detail = detail_route.endpoint(request=request, job_id=created["job_id"])

    assert jobs["count"] == 1
    assert jobs["jobs"][0]["job_id"] == created["job_id"]
    assert jobs["jobs"][0]["display_name"] == "Analyze yolov8n.onnx"
    assert detail["job_id"] == created["job_id"]
    assert detail["status"] == "queued"
    assert detail["result"] is None
    assert detail["next_actions"] == ["poll_self"]


def test_studio_import_api_accepts_runtime_result_json():
    app = api.create_app()
    route = _get_route(app, "/studio/api/import")
    request = SimpleNamespace(app=app)
    result = _runtime_result()

    response = route.endpoint(request=request, payload={"result": result})

    assert response["status"] == "imported"
    assert response["count"] == 1
    assert response["result"]["backend_key"] == "onnxruntime__cpu"
    assert response["compare_ready"] is False


def test_studio_import_api_applies_backend_override():
    app = api.create_app()
    route = _get_route(app, "/studio/api/import")
    request = SimpleNamespace(app=app)
    result = _runtime_result(engine="onnxruntime", device="cpu", mean_ms=9.9)

    response = route.endpoint(
        request=request,
        payload={"result": result, "backend_override": "tensorrt__jetson"},
    )

    assert response["status"] == "imported"
    assert response["result"]["engine"] == "tensorrt"
    assert response["result"]["engine_backend"] == "tensorrt"
    assert response["result"]["device"] == "jetson"
    assert response["result"]["backend_key"] == "tensorrt__jetson"


def test_studio_import_api_generates_missing_compare_keys():
    app = api.create_app()
    route = _get_route(app, "/studio/api/import")
    request = SimpleNamespace(app=app)
    result = _runtime_result(backend_key=None)
    result.pop("compare_key")

    response = route.endpoint(request=request, payload={"result": result})

    assert response["status"] == "imported"
    assert response["result"]["backend_key"] == "onnxruntime__cpu"
    assert response["result"]["compare_key"] == "yolov8n__b1__h640w640__fp32"


def test_studio_import_api_accepts_existing_result_path():
    app = api.create_app()
    route = _get_route(app, "/studio/api/import")
    request = SimpleNamespace(app=app)

    response = route.endpoint(request=request, payload={"path": "results/latest.json"})

    assert response["status"] == "imported"
    assert response["result"]["compare_key"]
    assert response["result"]["backend_key"]
    assert response["compare_ready"] is False
    assert isinstance(response["result"]["model"], dict)
    assert response["result"]["model"]["name"] == "yolov8n.onnx"


def test_studio_jetson_command_api_returns_command():
    app = api.create_app()
    route = _get_route(app, "/studio/api/jetson-command")

    response = route.endpoint()

    assert "--engine tensorrt" in response["command"]
    assert "--device jetson" in response["command"]
    assert "--output results/jetson/" in response["command"]


def test_studio_demo_evidence_loads_compare_ready_pair():
    app = api.create_app()
    route = _get_route(app, "/studio/api/demo-evidence")
    compare_route = _get_route(app, "/studio/api/compare/latest")
    request = SimpleNamespace(app=app)

    response = route.endpoint(request=request)
    compare = compare_route.endpoint(request=request)

    assert response["status"] == "loaded"
    assert response["source"] == "examples/studio_demo"
    assert response["job_id"] == "demo_yolov8n_trt_vs_onnx"
    assert response["job"]["display_name"] == "Demo: TensorRT vs ONNX Runtime"
    assert response["job"]["status"] == "completed"
    assert response["count"] == 2
    assert response["compare_ready"] is True
    assert response["results"][0]["backend_key"] == "onnxruntime__cpu"
    assert response["results"][1]["backend_key"] == "tensorrt__jetson"
    assert response["results"][0]["mean_ms"] == 45.4299
    assert response["results"][1]["mean_ms"] == 9.9375
    assert response["compare"]["status"] == "ok"
    assert response["compare"]["judgement"]["overall"] == "improvement"
    assert response["deployment_decision"]["decision"] == "unknown"
    assert compare["status"] == "ok"
    assert compare["base"]["backend_key"] == "onnxruntime__cpu"
    assert compare["new"]["backend_key"] == "tensorrt__jetson"


def test_studio_demo_evidence_is_listed_and_selectable_as_job():
    app = api.create_app()
    request = SimpleNamespace(app=app)
    demo_route = _get_route(app, "/studio/api/demo-evidence")
    jobs_route = _get_route(app, "/studio/api/jobs")
    detail_route = _get_route(app, "/studio/api/job/{job_id}")

    demo = demo_route.endpoint(request=request)
    jobs = jobs_route.endpoint(request=request)
    detail = detail_route.endpoint(request=request, job_id=demo["job_id"])

    assert jobs["count"] == 1
    assert jobs["jobs"][0]["job_id"] == "demo_yolov8n_trt_vs_onnx"
    assert jobs["jobs"][0]["display_name"] == "Demo: TensorRT vs ONNX Runtime"
    assert detail["job_id"] == "demo_yolov8n_trt_vs_onnx"
    assert detail["status"] == "completed"
    assert detail["result"]["runtime_result"]["backend_key"] == "tensorrt__jetson"
    assert detail["result"]["comparison"]["base"]["backend_key"] == "onnxruntime__cpu"
    assert detail["result"]["comparison"]["new"]["backend_key"] == "tensorrt__jetson"


def test_studio_importing_two_compatible_results_returns_compare_data():
    app = api.create_app()
    request = SimpleNamespace(app=app)
    import_route = _get_route(app, "/studio/api/import")
    compare_route = _get_route(app, "/studio/api/compare/latest")

    first = import_route.endpoint(
        request=request,
        payload={"result": _runtime_result(engine="onnxruntime", device="cpu", mean_ms=45.0, p99_ms=50.0)},
    )
    second = import_route.endpoint(
        request=request,
        payload={
            "result": _runtime_result(
                engine="tensorrt",
                device="jetson",
                mean_ms=9.9,
                p99_ms=12.0,
                backend_key="tensorrt__jetson",
            )
        },
    )
    compare = compare_route.endpoint(request=request)

    assert first["compare_ready"] is False
    assert second["compare_ready"] is True
    assert compare["status"] == "ok"
    assert compare["base"]["backend_key"] == "onnxruntime__cpu"
    assert compare["new"]["backend_key"] == "tensorrt__jetson"
    assert compare["result"]["metrics"]["mean_ms"]["new"] == 9.9
    assert compare["judgement"]["overall"] == "improvement"
    assert compare["deployment_decision"]["decision"] == "unknown"
