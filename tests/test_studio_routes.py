from __future__ import annotations

from pathlib import Path

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
