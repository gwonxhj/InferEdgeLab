from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from fastapi.responses import FileResponse

import inferedgelab.api as api


def _get_route(app, path: str):
    for route in app.routes:
        if getattr(route, "path", None) == path:
            return route
    raise AssertionError(f"route not found: {path}")


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
    assert 'href="/studio/static/style.css?v=' in html
    assert 'src="/studio/static/app.js?v=' in html


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
    assert "#0b0f14" in style_text
    assert "grid-template-columns" in style_text
    assert ".form-stack button" in style_text
    assert ".tool-card" in style_text


def test_studio_jobs_api_returns_json_structure():
    app = api.create_app()
    route = _get_route(app, "/studio/api/jobs")
    request = SimpleNamespace(app=app)

    response = route.endpoint(request=request)

    assert route.status_code is None
    assert response["source"] == "/api/jobs"
    assert response["count"] == 0
    assert response["jobs"] == []


def test_studio_compare_latest_api_returns_json_structure():
    app = api.create_app()
    route = _get_route(app, "/studio/api/compare/latest")
    request = SimpleNamespace(app=app)

    response = route.endpoint(request=request)

    assert route.status_code is None
    assert "deployment_decision" in response
    assert "data" in response
    assert response.get("source") in {None, "/api/compare-latest"}


def test_studio_run_api_creates_analyze_job():
    app = api.create_app()
    route = _get_route(app, "/studio/api/run")
    request = SimpleNamespace(app=app)

    response = route.endpoint(request=request, payload={"model_path": "models/yolov8n.onnx"})

    assert response["status"] == "created"
    assert response["source"] == "/api/analyze"
    assert response["job_id"].startswith("job_")
    assert response["job"]["input_summary"]["model_path"] == "models/yolov8n.onnx"


def test_studio_import_api_accepts_runtime_result_json():
    app = api.create_app()
    route = _get_route(app, "/studio/api/import")
    request = SimpleNamespace(app=app)
    result = {
        "runtime_role": "runtime-result",
        "model": "yolov8n",
        "engine": "onnxruntime",
        "device": "cpu",
        "precision": "fp32",
        "batch": 1,
        "height": 640,
        "width": 640,
        "mean_ms": 45.0,
        "p99_ms": 50.0,
        "timestamp": "2026-04-29T12:00:00Z",
        "compare_key": "yolov8n__b1__h640w640__fp32",
        "backend_key": "onnxruntime__cpu",
    }

    response = route.endpoint(request=request, payload={"result": result})

    assert response["status"] == "imported"
    assert response["count"] == 1
    assert response["result"]["backend_key"] == "onnxruntime__cpu"
    assert response["compare_ready"] is False


def test_studio_jetson_command_api_returns_command():
    app = api.create_app()
    route = _get_route(app, "/studio/api/jetson-command")

    response = route.endpoint()

    assert "--engine tensorrt" in response["command"]
    assert "--device jetson" in response["command"]
    assert "--output results/jetson/" in response["command"]
