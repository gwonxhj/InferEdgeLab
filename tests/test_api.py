from __future__ import annotations

from fastapi import HTTPException

import edgebench.api as api


def _get_route_endpoint(app, path: str, method: str = "GET"):
    for route in app.routes:
        if getattr(route, "path", None) == path and method in getattr(route, "methods", set()):
            return route.endpoint
    raise AssertionError(f"route not found: {method} {path}")


def test_create_app_registers_expected_routes():
    app = api.create_app()
    routes = {(route.path, tuple(sorted(route.methods))) for route in app.routes if hasattr(route, "path")}

    assert any(path == "/health" and "GET" in methods for path, methods in routes)
    assert any(path == "/api/list-results" and "GET" in methods for path, methods in routes)
    assert any(path == "/api/summarize" and "GET" in methods for path, methods in routes)
    assert any(path == "/api/history-report" and "GET" in methods for path, methods in routes)
    assert any(path == "/api/compare" and "GET" in methods for path, methods in routes)


def test_health_endpoint_returns_expected_payload():
    app = api.create_app()
    endpoint = _get_route_endpoint(app, "/health")

    assert endpoint() == {"status": "ok", "service": "edgebench-api"}


def test_list_results_endpoint_returns_service_bundle_and_passes_args(monkeypatch):
    app = api.create_app()
    endpoint = _get_route_endpoint(app, "/api/list-results")
    captured = {}
    expected = {"meta": {"count": 1}, "data": {"items": [{"model": "resnet18"}]}}

    def fake_build_list_results_bundle(**kwargs):
        captured.update(kwargs)
        return expected

    monkeypatch.setattr(api, "build_list_results_bundle", fake_build_list_results_bundle)

    result = endpoint(
        pattern="tmp/*.json",
        limit=5,
        model="resnet18",
        engine="onnxruntime",
        device="cpu",
        precision="fp32",
        batch=1,
        height=224,
        width=224,
        legacy_only=True,
    )

    assert result == expected
    assert captured == {
        "pattern": "tmp/*.json",
        "limit": 5,
        "model": "resnet18",
        "engine": "onnxruntime",
        "device": "cpu",
        "precision": "fp32",
        "batch": 1,
        "height": 224,
        "width": 224,
        "legacy_only": True,
    }


def test_summarize_endpoint_returns_service_bundle_and_passes_args(monkeypatch):
    app = api.create_app()
    endpoint = _get_route_endpoint(app, "/api/summarize")
    captured = {}
    expected = {"meta": {"mode": "latest"}, "data": {"rows": []}, "rendered": {"markdown": "## Latest"}}

    def fake_build_summary_bundle(**kwargs):
        captured.update(kwargs)
        return expected

    monkeypatch.setattr(api, "build_summary_bundle", fake_build_summary_bundle)

    result = endpoint(
        pattern="reports/*.json",
        format="md",
        mode="both",
        sort="time",
        recent=3,
        top=2,
    )

    assert result == expected
    assert captured == {
        "pattern": "reports/*.json",
        "format": "md",
        "mode": "both",
        "sort": "time",
        "recent": 3,
        "top": 2,
    }


def test_history_report_endpoint_converts_value_error_to_http_400(monkeypatch):
    app = api.create_app()
    endpoint = _get_route_endpoint(app, "/api/history-report")

    def fake_build_history_report_outputs(**kwargs):
        raise ValueError("bad history request")

    monkeypatch.setattr(api, "build_history_report_outputs", fake_build_history_report_outputs)

    try:
        endpoint(pattern="results/*.json")
    except HTTPException as exc:
        assert exc.status_code == 400
        assert exc.detail == "bad history request"
    else:
        raise AssertionError("HTTPException was not raised")


def test_compare_endpoint_converts_value_error_to_http_400(monkeypatch):
    app = api.create_app()
    endpoint = _get_route_endpoint(app, "/api/compare")

    def fake_build_compare_bundle(**kwargs):
        raise ValueError("bad compare request")

    monkeypatch.setattr(api, "build_compare_bundle", fake_build_compare_bundle)

    try:
        endpoint(base_path="base.json", new_path="new.json")
    except HTTPException as exc:
        assert exc.status_code == 400
        assert exc.detail == "bad compare request"
    else:
        raise AssertionError("HTTPException was not raised")
