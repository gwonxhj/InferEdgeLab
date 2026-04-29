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
    assert "InferEdge Local Studio" in html


def test_studio_static_assets_are_served():
    app = api.create_app()
    route = _get_route(app, "/studio/static/{asset_name}")

    app_response = route.endpoint(asset_name="app.js")
    style_response = route.endpoint(asset_name="style.css")

    assert isinstance(app_response, FileResponse)
    assert isinstance(style_response, FileResponse)
    assert app_response.status_code == 200
    assert style_response.status_code == 200
    assert "renderPipeline" in Path(app_response.path).read_text(encoding="utf-8")
    assert "pipeline-flow" in Path(style_response.path).read_text(encoding="utf-8")


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
