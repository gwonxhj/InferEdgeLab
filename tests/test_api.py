from __future__ import annotations

from fastapi import HTTPException

import edgebench
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
    assert any(path == "/api/compare-latest" and "GET" in methods for path, methods in routes)


def test_health_endpoint_returns_expected_payload():
    app = api.create_app()
    endpoint = _get_route_endpoint(app, "/health")

    assert endpoint() == {"status": "ok", "service": "edgebench-api", "version": edgebench.__version__}


def test_list_results_endpoint_returns_service_bundle_and_passes_args(monkeypatch):
    app = api.create_app()
    endpoint = _get_route_endpoint(app, "/api/list-results")
    captured = {}
    expected = {
        "meta": {"count": 1, "limit": 5, "filters": {"model": "resnet18"}},
        "data": {"items": [{"model": "resnet18"}]},
    }

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
    expected = {
        "meta": {"mode": "both", "sort": "time"},
        "data": {"rows": [], "latest_rows": [], "history_rows": []},
        "rendered": {"markdown": "## Latest"},
    }

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


def test_history_report_endpoint_returns_bundle(monkeypatch):
    app = api.create_app()
    endpoint = _get_route_endpoint(app, "/api/history-report")
    expected = {
        "meta": {"pattern": "results/*.json", "count": 1, "filters": {"model": "toy224.onnx"}},
        "data": {"history": [{"timestamp": "2026-04-14T09:00:00Z"}]},
        "rendered": {"html": "<html></html>", "markdown": None},
    }

    def fake_build_history_report_outputs(**kwargs):
        return expected

    monkeypatch.setattr(api, "build_history_report_outputs", fake_build_history_report_outputs)

    result = endpoint(model="toy224.onnx")

    assert result == expected
    assert set(result.keys()) == {"meta", "data", "rendered"}


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


def test_compare_endpoint_returns_bundle(monkeypatch):
    app = api.create_app()
    endpoint = _get_route_endpoint(app, "/api/compare")
    expected = {
        "meta": {
            "base_path": "base.json",
            "new_path": "new.json",
            "legacy_warning": False,
        },
        "data": {
            "base": {"model": "resnet18"},
            "new": {"model": "resnet18"},
            "result": {"precision": {"comparison_mode": "same_precision"}},
            "judgement": {"overall": "improvement"},
        },
        "rendered": {
            "markdown": "# report",
            "html": "<html></html>",
        },
    }

    def fake_build_compare_bundle(**kwargs):
        return expected

    monkeypatch.setattr(api, "build_compare_bundle", fake_build_compare_bundle)

    result = endpoint(base_path="base.json", new_path="new.json")

    assert result == expected
    assert set(result.keys()) == {"meta", "data", "rendered"}


def test_compare_latest_endpoint_returns_bundle_and_passes_args(monkeypatch):
    app = api.create_app()
    endpoint = _get_route_endpoint(app, "/api/compare-latest")
    captured = {}
    expected = {
        "meta": {
            "selection_mode": "cross_precision",
            "base_path": "base.json",
            "new_path": "new.json",
            "run_config_mismatch_fields": [],
            "legacy_warning": False,
        },
        "data": {
            "pair": {"selection_mode": "cross_precision"},
            "base": {"model": "resnet18"},
            "new": {"model": "resnet18"},
            "result": {"precision": {"comparison_mode": "cross_precision"}},
            "judgement": {"overall": "tradeoff_faster"},
        },
        "rendered": {"markdown": "# report", "html": "<html></html>"},
    }

    def fake_build_compare_latest_bundle(**kwargs):
        captured.update(kwargs)
        return expected

    monkeypatch.setattr(api, "build_compare_latest_bundle", fake_build_compare_latest_bundle)

    result = endpoint(
        pattern="results/*.json",
        model="resnet18",
        engine="onnxruntime",
        device="cpu",
        precision="",
        selection_mode="cross_precision",
        latency_improve_threshold=-5.0,
        latency_regress_threshold=5.0,
        accuracy_improve_threshold=0.3,
        accuracy_regress_threshold=-0.3,
        tradeoff_caution_threshold=-0.4,
        tradeoff_risky_threshold=-1.2,
        tradeoff_severe_threshold=-2.5,
        pyproject_path="pyproject.toml",
    )

    assert result == expected
    assert captured == {
        "pattern": "results/*.json",
        "model": "resnet18",
        "engine": "onnxruntime",
        "device": "cpu",
        "precision": "",
        "selection_mode": "cross_precision",
        "latency_improve_threshold": -5.0,
        "latency_regress_threshold": 5.0,
        "accuracy_improve_threshold": 0.3,
        "accuracy_regress_threshold": -0.3,
        "tradeoff_caution_threshold": -0.4,
        "tradeoff_risky_threshold": -1.2,
        "tradeoff_severe_threshold": -2.5,
        "pyproject_path": "pyproject.toml",
    }


def test_compare_latest_endpoint_converts_value_error_to_http_400(monkeypatch):
    app = api.create_app()
    endpoint = _get_route_endpoint(app, "/api/compare-latest")

    def fake_build_compare_latest_bundle(**kwargs):
        raise ValueError("bad compare latest request")

    monkeypatch.setattr(api, "build_compare_latest_bundle", fake_build_compare_latest_bundle)

    try:
        endpoint()
    except HTTPException as exc:
        assert exc.status_code == 400
        assert exc.detail == "bad compare latest request"
    else:
        raise AssertionError("HTTPException was not raised")
