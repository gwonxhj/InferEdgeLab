from __future__ import annotations

import json

import pytest

import inferedgelab.services.compare_service as compare_service
from inferedgelab.services.compare_service import (
    build_compare_bundle,
    build_compare_latest_bundle,
    select_latest_compare_pair,
)


def write_result(
    tmp_path,
    name: str,
    *,
    timestamp: str,
    precision: str,
    mean_ms: float = 10.0,
    p99_ms: float = 12.0,
    model: str = "resnet18",
    engine: str = "onnxruntime",
    device: str = "cpu",
    batch: int = 1,
    height: int = 224,
    width: int = 224,
    run_config: dict | None = None,
    system: dict | None = None,
    accuracy: dict | None = None,
    extra: dict | None = None,
) -> str:
    path = tmp_path / name
    path.write_text(
        json.dumps(
            {
                "model": model,
                "engine": engine,
                "device": device,
                "precision": precision,
                "batch": batch,
                "height": height,
                "width": width,
                "mean_ms": mean_ms,
                "p99_ms": p99_ms,
                "timestamp": timestamp,
                "run_config": run_config or {},
                "system": system or {"os": "Linux", "python": "3.11.0", "machine": "x86_64", "cpu_count_logical": 8},
                "accuracy": accuracy
                or {
                    "task": "classification",
                    "sample_count": 100,
                    "metrics": {"top1_accuracy": 0.9},
                },
                "extra": extra or {},
            }
        ),
        encoding="utf-8",
    )
    return str(path)


def test_build_compare_bundle_returns_compare_artifacts_for_same_precision_pair(tmp_path):
    base_path = write_result(
        tmp_path,
        "base.json",
        timestamp="2026-04-13T09:00:00Z",
        precision="fp32",
        mean_ms=10.0,
        p99_ms=12.0,
    )
    new_path = write_result(
        tmp_path,
        "new.json",
        timestamp="2026-04-13T10:00:00Z",
        precision="fp32",
        mean_ms=9.0,
        p99_ms=11.0,
        accuracy={
            "task": "classification",
            "sample_count": 100,
            "metrics": {"top1_accuracy": 0.92},
        },
    )

    bundle = build_compare_bundle(base_path=base_path, new_path=new_path)

    assert set(bundle.keys()) >= {
        "meta",
        "data",
        "rendered",
        "base",
        "new",
        "base_path",
        "new_path",
        "result",
        "judgement",
        "markdown",
        "html",
        "legacy_warning",
        "deployment_decision",
    }
    assert bundle["meta"]["base_path"] == base_path
    assert bundle["meta"]["new_path"] == new_path
    assert bundle["meta"]["legacy_warning"] is False
    assert bundle["data"]["base"] == bundle["base"]
    assert bundle["data"]["new"] == bundle["new"]
    assert bundle["data"]["result"] == bundle["result"]
    assert bundle["data"]["judgement"] == bundle["judgement"]
    assert bundle["data"]["deployment_decision"] == bundle["deployment_decision"]
    assert bundle["rendered"]["markdown"] == bundle["markdown"]
    assert bundle["rendered"]["html"] == bundle["html"]
    assert bundle["base_path"] == base_path
    assert bundle["new_path"] == new_path
    assert bundle["result"]["precision"]["comparison_mode"] == "same_precision"
    assert bundle["judgement"]["comparison_mode"] == "same_precision"
    assert isinstance(bundle["markdown"], str) and bundle["markdown"]
    assert isinstance(bundle["html"], str) and bundle["html"]
    assert bundle["legacy_warning"] is False
    assert bundle["deployment_decision"]["decision"] == "unknown"
    assert "guard_analysis" not in bundle
    assert "guard_analysis" not in bundle["data"]


def test_build_compare_bundle_with_guard_false_preserves_existing_keys(tmp_path):
    base_path = write_result(
        tmp_path,
        "base.json",
        timestamp="2026-04-13T09:00:00Z",
        precision="fp32",
    )
    new_path = write_result(
        tmp_path,
        "new.json",
        timestamp="2026-04-13T10:00:00Z",
        precision="fp32",
    )

    bundle = build_compare_bundle(base_path=base_path, new_path=new_path, with_guard=False)

    assert bundle["data"]["result"] == bundle["result"]
    assert bundle["data"]["judgement"] == bundle["judgement"]
    assert bundle["rendered"]["markdown"] == bundle["markdown"]
    assert bundle["rendered"]["html"] == bundle["html"]
    assert bundle["data"]["deployment_decision"] == bundle["deployment_decision"]
    assert bundle["deployment_decision"]["decision"] == "unknown"
    assert "guard_analysis" not in bundle
    assert "guard_analysis" not in bundle["data"]


def test_build_compare_bundle_with_guard_runs_optional_reasoning(tmp_path, monkeypatch):
    def fake_analyze_compare_result(guard_input):
        assert guard_input["comparison_mode"] == "same_precision"
        assert guard_input["precision_pair"] == "fp32_vs_fp32"
        assert guard_input["latency_delta_pct"] == pytest.approx(-10.0)
        assert guard_input["base_precision"] == "fp32"
        assert guard_input["candidate_precision"] == "fp32"
        assert guard_input["accuracy_delta"] == pytest.approx(0.02)
        assert guard_input["accuracy_delta_pp"] == pytest.approx(2.0)
        assert "runtime_provenance" in guard_input
        assert "run_config_diff" in guard_input
        assert "shape_context" in guard_input
        return {
            "status": "ok",
            "confidence": 0.9,
            "anomalies": [],
            "suspected_causes": [],
            "recommendations": ["Keep tracking same-precision runs."],
        }

    monkeypatch.setattr(compare_service, "analyze_compare_result", fake_analyze_compare_result)
    base_path = write_result(
        tmp_path,
        "base.json",
        timestamp="2026-04-13T09:00:00Z",
        precision="fp32",
        mean_ms=10.0,
        accuracy={
            "task": "classification",
            "sample_count": 100,
            "metrics": {"top1_accuracy": 0.90},
        },
    )
    new_path = write_result(
        tmp_path,
        "new.json",
        timestamp="2026-04-13T10:00:00Z",
        precision="fp32",
        mean_ms=9.0,
        accuracy={
            "task": "classification",
            "sample_count": 100,
            "metrics": {"top1_accuracy": 0.92},
        },
    )

    bundle = build_compare_bundle(base_path=base_path, new_path=new_path, with_guard=True)

    assert bundle["guard_analysis"]["status"] == "ok"
    assert "anomalies" in bundle["guard_analysis"]
    assert "recommendations" in bundle["guard_analysis"]
    assert bundle["data"]["guard_analysis"] == bundle["guard_analysis"]
    assert bundle["data"]["deployment_decision"] == bundle["deployment_decision"]
    assert bundle["deployment_decision"]["decision"] == "deployable"


def test_build_compare_bundle_with_guard_skips_when_aiguard_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(compare_service, "analyze_compare_result", None)
    base_path = write_result(tmp_path, "base.json", timestamp="2026-04-13T09:00:00Z", precision="fp32")
    new_path = write_result(tmp_path, "new.json", timestamp="2026-04-13T10:00:00Z", precision="fp32")

    bundle = build_compare_bundle(base_path=base_path, new_path=new_path, with_guard=True)

    assert bundle["guard_analysis"] == {
        "status": "skipped",
        "reason": "inferedge_aiguard is not installed",
    }
    assert bundle["data"]["guard_analysis"] == bundle["guard_analysis"]
    assert bundle["data"]["deployment_decision"] == bundle["deployment_decision"]
    assert bundle["deployment_decision"]["decision"] == "unknown"
    assert "Guard Analysis" in bundle["markdown"]
    assert "Deployment Decision" in bundle["markdown"]


def test_build_compare_bundle_with_guard_cross_precision_low_speedup(tmp_path, monkeypatch):
    def fake_analyze_compare_result(guard_input):
        assert guard_input["comparison_mode"] == "cross_precision"
        assert guard_input["precision_pair"] == "fp32_vs_fp16"
        assert abs(guard_input["latency_delta_pct"]) < 3.0
        return {
            "status": "warning",
            "confidence": 0.7,
            "anomalies": ["insufficient_precision_speedup"],
            "suspected_causes": ["precision_speedup_not_observed"],
            "recommendations": ["Inspect runtime provenance and run config before promoting the candidate."],
        }

    monkeypatch.setattr(compare_service, "analyze_compare_result", fake_analyze_compare_result)
    base_path = write_result(
        tmp_path,
        "base-fp32.json",
        timestamp="2026-04-13T09:00:00Z",
        precision="fp32",
        mean_ms=10.0,
        p99_ms=12.0,
    )
    new_path = write_result(
        tmp_path,
        "new-fp16.json",
        timestamp="2026-04-13T10:00:00Z",
        precision="fp16",
        mean_ms=9.9,
        p99_ms=11.9,
    )

    bundle = build_compare_bundle(base_path=base_path, new_path=new_path, with_guard=True)

    assert "insufficient_precision_speedup" in bundle["guard_analysis"]["anomalies"]
    assert bundle["deployment_decision"]["decision"] == "review_required"
    assert "Guard Analysis" in bundle["markdown"]


def test_select_latest_compare_pair_selects_latest_same_precision_pair(tmp_path):
    older = write_result(tmp_path, "older.json", timestamp="2026-04-13T09:00:00Z", precision="fp32")
    write_result(tmp_path, "other.json", timestamp="2026-04-13T09:30:00Z", precision="fp16")
    newer = write_result(
        tmp_path,
        "newer.json",
        timestamp="2026-04-13T10:00:00Z",
        precision="fp32",
        run_config={"runs": 50},
    )

    pair = select_latest_compare_pair(
        pattern=str(tmp_path / "*.json"),
        selection_mode="same_precision",
    )

    assert pair["selection_mode"] == "same_precision"
    assert pair["base_path"] == older
    assert pair["new_path"] == newer
    assert pair["run_config_mismatch_fields"] == ["runs"]


def test_select_latest_compare_pair_cross_precision_with_precision_filter_raises(tmp_path):
    write_result(tmp_path, "base.json", timestamp="2026-04-13T09:00:00Z", precision="fp32")
    write_result(tmp_path, "new.json", timestamp="2026-04-13T10:00:00Z", precision="fp16")

    with pytest.raises(ValueError, match="cross_precision"):
        select_latest_compare_pair(
            pattern=str(tmp_path / "*.json"),
            selection_mode="cross_precision",
            precision="fp16",
        )


def test_build_compare_latest_bundle_same_precision_includes_bundle_and_compat_keys(tmp_path):
    older = write_result(tmp_path, "older.json", timestamp="2026-04-13T09:00:00Z", precision="fp32")
    newer = write_result(
        tmp_path,
        "newer.json",
        timestamp="2026-04-13T10:00:00Z",
        precision="fp32",
        run_config={"runs": 50},
    )

    bundle = build_compare_latest_bundle(pattern=str(tmp_path / "*.json"), selection_mode="same_precision")

    assert set(bundle.keys()) >= {
        "meta",
        "data",
        "rendered",
        "pair",
        "base",
        "new",
        "base_path",
        "new_path",
        "result",
        "judgement",
        "markdown",
        "html",
        "legacy_warning",
        "run_config_mismatch_fields",
        "selection_mode",
        "deployment_decision",
    }
    assert bundle["selection_mode"] == "same_precision"
    assert bundle["base_path"] == older
    assert bundle["new_path"] == newer
    assert bundle["run_config_mismatch_fields"] == ["runs"]
    assert bundle["meta"]["selection_mode"] == "same_precision"
    assert bundle["meta"]["base_path"] == older
    assert bundle["meta"]["new_path"] == newer
    assert bundle["meta"]["run_config_mismatch_fields"] == ["runs"]
    assert bundle["data"]["pair"] == bundle["pair"]
    assert bundle["data"]["base"] == bundle["base"]
    assert bundle["data"]["new"] == bundle["new"]
    assert bundle["data"]["result"] == bundle["result"]
    assert bundle["data"]["judgement"] == bundle["judgement"]
    assert bundle["data"]["deployment_decision"] == bundle["deployment_decision"]
    assert bundle["rendered"]["markdown"] == bundle["markdown"]
    assert bundle["rendered"]["html"] == bundle["html"]
    assert bundle["deployment_decision"]["decision"] == "unknown"


def test_build_compare_latest_bundle_cross_precision_selects_expected_pair(tmp_path):
    older_fp32 = write_result(tmp_path, "older-fp32.json", timestamp="2026-04-13T09:00:00Z", precision="fp32")
    write_result(tmp_path, "older-fp16.json", timestamp="2026-04-13T09:10:00Z", precision="fp16")
    newer_fp16 = write_result(tmp_path, "newer-fp16.json", timestamp="2026-04-13T10:00:00Z", precision="fp16")

    bundle = build_compare_latest_bundle(pattern=str(tmp_path / "*.json"), selection_mode="cross_precision")

    assert bundle["selection_mode"] == "cross_precision"
    assert bundle["base_path"] == older_fp32
    assert bundle["new_path"] == newer_fp16
    assert bundle["meta"]["selection_mode"] == "cross_precision"
    assert bundle["pair"]["base_path"] == older_fp32
    assert bundle["pair"]["new_path"] == newer_fp16
    assert bundle["data"]["deployment_decision"] == bundle["deployment_decision"]
