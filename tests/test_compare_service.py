from __future__ import annotations

import json
from pathlib import Path

import pytest

import inferedgelab.services.compare_service as compare_service
from inferedgelab.services.compare_service import (
    build_compare_bundle,
    build_compare_latest_bundle,
    select_latest_compare_pair,
)


FIXTURES = Path(__file__).resolve().parent / "fixtures"


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


def load_aiguard_mismatch_fixture(name: str) -> dict:
    fixtures = json.loads(
        (FIXTURES / "aiguard_artifact_mismatch_guard_analysis.json").read_text(
            encoding="utf-8"
        )
    )
    return fixtures[name]


def load_worker_provenance_guard_fixture() -> dict:
    return json.loads(
        (
            FIXTURES
            / "aiguard_worker_provenance_mismatch_guard_analysis.json"
        ).read_text(encoding="utf-8")
    )


def write_edgeenv_regression(tmp_path) -> str:
    path = tmp_path / "edgeenv_regression.json"
    path.write_text(
        json.dumps(
            {
                "regression_detected": True,
                "regression_type": "latency",
                "severity": "high",
                "comparable": True,
                "mode": "same-condition",
                "recommendation": "review_required",
                "comparability": {
                    "comparable": True,
                    "reasons": ["All strict regression keys match."],
                },
                "evidence": {
                    "mean_delta_pct": 18.4,
                    "p99_delta_pct": 32.1,
                    "triggered_thresholds": [
                        {
                            "name": "p99_latency_high",
                            "metric": "p99_delta_pct",
                            "observed": 32.1,
                            "threshold": 25.0,
                            "severity": "high",
                        }
                    ],
                },
                "runtime_telemetry_context": {
                    "role": "supplemental_runtime_telemetry_context",
                    "source": "result_artifacts+runtime_telemetry_history",
                    "baseline": {
                        "run_id": "baseline",
                        "result_telemetry_present": True,
                        "history_entry_present": True,
                        "execution_sequence_id": 1,
                        "telemetry_source": "synthetic_local_fixture",
                    },
                    "candidate": {
                        "run_id": "candidate",
                        "result_telemetry_present": True,
                        "history_entry_present": True,
                        "execution_sequence_id": 2,
                        "telemetry_source": "synthetic_local_fixture",
                    },
                    "history": {
                        "schema_version": "edgeenv.runtime-telemetry-history.v1",
                        "summary": {
                            "registered_runs": 2,
                            "telemetry_runs": 2,
                            "missing_telemetry_runs": 0,
                        },
                    },
                    "evidence_gaps": [],
                    "notes": [
                        "Runtime telemetry context is supplemental evidence, not a comparability gate.",
                    ],
                },
            }
        ),
        encoding="utf-8",
    )
    return str(path)


def make_edgeenv_runtime_regression_guard_analysis() -> dict:
    return {
        "schema_version": "inferedge-aiguard-diagnosis-v1",
        "source": {
            "edgeenv_runtime_regression_report": True,
            "edgeenv_mode": "same-condition",
            "edgeenv_comparable": True,
        },
        "guard_verdict": "blocked",
        "severity": "high",
        "confidence": 0.88,
        "primary_reason": (
            "EdgeEnv same-condition runtime regression evidence requires "
            "deterministic AIGuard review."
        ),
        "evidence": [
            {
                "type": "runtime_latency_regression",
                "metric_name": "p99_delta_pct",
                "observed_value": 32.0,
                "baseline_value": 0,
                "threshold": 25.0,
                "delta": None,
                "delta_pct": 32.0,
                "increase_factor": None,
                "severity": "high",
                "status": "failed",
                "explanation": (
                    "p99_delta_pct observed value is 32.0. Baseline value is 0. "
                    "Threshold is 25.0. This runtime_latency_regression evidence "
                    "should be reviewed before deployment."
                ),
                "why_it_matters": (
                    "Same-condition tail latency regression is deployment risk evidence."
                ),
                "suspected_causes": ["runtime_latency_drift", "tail_latency_spike"],
                "recommendation": (
                    "Review EdgeEnv comparability judgement and telemetry before deployment."
                ),
                "raw_context": {"edgeenv_regression": {"mode": "same-condition"}},
            },
            {
                "type": "runtime_telemetry_context_coverage",
                "metric_name": "runtime_telemetry_evidence_gap_count",
                "observed_value": 0,
                "baseline_value": 0,
                "threshold": 1,
                "delta": None,
                "delta_pct": None,
                "increase_factor": None,
                "severity": "low",
                "status": "passed",
                "explanation": "Runtime telemetry context is present for both compared runs.",
                "why_it_matters": (
                    "Runtime telemetry context makes regression evidence more explainable."
                ),
                "suspected_causes": [],
                "recommendation": (
                    "Telemetry coverage is present for the EdgeEnv regression report."
                ),
                "raw_context": {},
            },
        ],
        "suspected_causes": ["runtime_latency_drift", "tail_latency_spike"],
        "recommendations": [
            "Review EdgeEnv comparability judgement and telemetry before deployment."
        ],
        "thresholds": {"edgeenv_p99_delta_pct_review": 25.0},
        "baseline_summary": {},
        "candidate_summary": {
            "edgeenv_regression": {"candidate_run_id": "edgeenv-smoke-candidate"}
        },
        "created_at": "2026-05-22T00:00:00Z",
    }


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
    assert "edgeenv_runtime_regression" not in bundle
    assert "edgeenv_runtime_regression" not in bundle["data"]


def test_build_compare_bundle_accepts_edgeenv_regression_evidence(tmp_path):
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
        mean_ms=8.0,
        p99_ms=10.0,
        accuracy={
            "task": "classification",
            "sample_count": 100,
            "metrics": {"top1_accuracy": 0.92},
        },
    )
    edgeenv_regression_path = write_edgeenv_regression(tmp_path)

    bundle = build_compare_bundle(
        base_path=base_path,
        new_path=new_path,
        edgeenv_regression_path=edgeenv_regression_path,
    )

    assert bundle["edgeenv_runtime_regression"]["mode"] == "same-condition"
    assert (
        bundle["edgeenv_runtime_regression"]["runtime_telemetry_context"]["candidate"][
            "execution_sequence_id"
        ]
        == 2
    )
    assert bundle["data"]["edgeenv_runtime_regression"] == bundle["edgeenv_runtime_regression"]
    assert bundle["deployment_decision"]["decision"] == "review_required"
    assert "edgeenv_runtime_regression_review" in bundle["deployment_decision"]["triggered_rules"]
    assert "## Runtime Regression Evidence" in bundle["markdown"]
    assert "### Runtime Telemetry Context" in bundle["markdown"]
    assert "p99_latency_high" in bundle["html"]
    assert "Runtime Telemetry Context" in bundle["html"]


def test_build_compare_bundle_routes_edgeenv_regression_to_aiguard_when_available(
    tmp_path, monkeypatch
):
    guard_analysis = make_edgeenv_runtime_regression_guard_analysis()

    def fake_analyze_edgeenv_regression_report(report):
        assert report["mode"] == "same-condition"
        assert (
            report["runtime_telemetry_context"]["candidate"]["execution_sequence_id"]
            == 2
        )
        return guard_analysis

    def fail_compare_reasoning(_guard_input):
        raise AssertionError(
            "EdgeEnv regression diagnosis should use the EdgeEnv AIGuard analyzer"
        )

    monkeypatch.setattr(
        compare_service,
        "analyze_edgeenv_regression_report",
        fake_analyze_edgeenv_regression_report,
    )
    monkeypatch.setattr(compare_service, "analyze_compare_result", fail_compare_reasoning)
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
        mean_ms=8.0,
        p99_ms=10.0,
        accuracy={
            "task": "classification",
            "sample_count": 100,
            "metrics": {"top1_accuracy": 0.92},
        },
    )

    bundle = build_compare_bundle(
        base_path=base_path,
        new_path=new_path,
        with_guard=True,
        edgeenv_regression_path=write_edgeenv_regression(tmp_path),
    )

    assert bundle["guard_analysis"] == guard_analysis
    assert bundle["data"]["guard_analysis"] == guard_analysis
    assert bundle["edgeenv_runtime_regression"]["mode"] == "same-condition"
    assert bundle["deployment_decision"]["decision"] == "blocked"
    assert bundle["deployment_decision"]["guard_status"] == "error"
    assert bundle["deployment_decision"]["guard_verdict"] == "blocked"
    assert bundle["data"]["deployment_decision"] == bundle["deployment_decision"]
    assert "runtime_latency_regression" in bundle["markdown"]
    assert (
        "Same-condition tail latency regression is deployment risk evidence."
        in bundle["markdown"]
    )
    assert "tail_latency_spike" in bundle["markdown"]
    assert "Runtime Regression Evidence" in bundle["markdown"]
    assert "Runtime Telemetry Context" in bundle["markdown"]
    assert "runtime_telemetry_context_coverage" in bundle["html"]


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
        assert guard_input["source"]["baseline_profile_path"]
        assert guard_input["source"]["candidate_result_path"]
        assert guard_input["source"]["runtime_result_path"] == guard_input["source"]["candidate_result_path"]
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


def test_build_compare_bundle_accepts_diagnosis_guard_contract(tmp_path, monkeypatch):
    def fake_analyze_compare_result(guard_input):
        return {
            "schema_version": "inferedge-aiguard-diagnosis-v1",
            "source": guard_input["source"],
            "guard_verdict": "review_required",
            "severity": "medium",
            "confidence": 0.88,
            "primary_reason": "Temporal consistency should be reviewed before deployment.",
            "evidence": [
                {
                    "type": "temporal_consistency",
                    "metric_name": "frame_to_frame_detection_count_cv",
                    "observed_value": 1.25,
                    "baseline_value": None,
                    "threshold": 1.0,
                    "severity": "medium",
                    "status": "warning",
                    "explanation": "Detection count variance exceeds review threshold.",
                    "recommendation": "Review frame sequence output before deployment.",
                }
            ],
            "suspected_causes": ["Temporal instability"],
            "recommendations": ["Review adjacent-frame output."],
        }

    monkeypatch.setattr(compare_service, "analyze_compare_result", fake_analyze_compare_result)
    base_path = write_result(tmp_path, "base.json", timestamp="2026-04-13T09:00:00Z", precision="fp32")
    new_path = write_result(tmp_path, "new.json", timestamp="2026-04-13T10:00:00Z", precision="fp32")

    bundle = build_compare_bundle(base_path=base_path, new_path=new_path, with_guard=True)

    assert bundle["guard_analysis"]["guard_verdict"] == "review_required"
    assert bundle["guard_analysis"]["source"]["runtime_result_path"] == new_path
    assert bundle["deployment_decision"]["decision"] == "review_required"
    assert bundle["deployment_decision"]["guard_status"] == "warning"
    assert bundle["deployment_decision"]["guard_verdict"] == "review_required"
    assert "frame_to_frame_detection_count_cv" in bundle["markdown"]
    assert "Temporal consistency should be reviewed before deployment." in bundle["html"]


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


@pytest.mark.parametrize(
    ("fixture_name", "expected_decision", "expected_anomaly"),
    [
        ("artifact_hash_mismatch", "blocked", "artifact_sha256_mismatch"),
        ("source_model_hash_mismatch", "blocked", "source_model_sha256_mismatch"),
        ("precision_or_shape_mismatch", "review_required", "shape_mismatch"),
        ("insufficient_provenance", "review_required", "insufficient_provenance"),
    ],
)
def test_build_compare_bundle_preserves_aiguard_artifact_mismatch_evidence(
    tmp_path,
    monkeypatch,
    fixture_name,
    expected_decision,
    expected_anomaly,
):
    guard_analysis = load_aiguard_mismatch_fixture(fixture_name)
    monkeypatch.setattr(
        compare_service,
        "analyze_compare_result",
        lambda guard_input: guard_analysis,
    )
    base_path = write_result(
        tmp_path,
        "base.json",
        timestamp="2026-04-13T09:00:00Z",
        precision="fp16",
        mean_ms=10.0,
    )
    new_path = write_result(
        tmp_path,
        "new.json",
        timestamp="2026-04-13T10:00:00Z",
        precision="fp16",
        mean_ms=9.0,
    )

    bundle = build_compare_bundle(base_path=base_path, new_path=new_path, with_guard=True)

    assert bundle["guard_analysis"] == guard_analysis
    assert bundle["data"]["guard_analysis"] == guard_analysis
    assert bundle["deployment_decision"]["decision"] == expected_decision
    assert bundle["deployment_decision"]["guard_status"] == guard_analysis["status"]
    assert bundle["data"]["deployment_decision"] == bundle["deployment_decision"]
    assert "Deployment Decision" in bundle["markdown"]
    assert "Guard Analysis" in bundle["markdown"]
    assert expected_anomaly in bundle["markdown"]
    assert "Deployment Decision" in bundle["html"]
    assert "Guard Analysis" in bundle["html"]
    assert expected_anomaly in bundle["html"]


def test_build_compare_latest_bundle_preserves_aiguard_mismatch_evidence(
    tmp_path,
    monkeypatch,
):
    guard_analysis = load_aiguard_mismatch_fixture("artifact_hash_mismatch")
    monkeypatch.setattr(
        compare_service,
        "analyze_compare_result",
        lambda guard_input: guard_analysis,
    )
    write_result(
        tmp_path,
        "older.json",
        timestamp="2026-04-13T09:00:00Z",
        precision="fp32",
        mean_ms=10.0,
    )
    write_result(
        tmp_path,
        "newer.json",
        timestamp="2026-04-13T10:00:00Z",
        precision="fp32",
        mean_ms=9.0,
    )

    bundle = build_compare_latest_bundle(
        pattern=str(tmp_path / "*.json"),
        selection_mode="same_precision",
        with_guard=True,
    )

    assert bundle["guard_analysis"] == guard_analysis
    assert bundle["data"]["guard_analysis"] == guard_analysis
    assert bundle["deployment_decision"]["decision"] == "blocked"
    assert bundle["data"]["deployment_decision"] == bundle["deployment_decision"]
    assert "artifact_sha256_mismatch" in bundle["markdown"]


@pytest.mark.parametrize(
    ("guard_status", "expected_decision"),
    [
        ("error", "blocked"),
        ("warning", "review_required"),
    ],
)
def test_build_compare_bundle_preserves_worker_provenance_guard_evidence(
    tmp_path,
    monkeypatch,
    guard_status,
    expected_decision,
):
    guard_analysis = load_worker_provenance_guard_fixture()
    guard_analysis["status"] = guard_status
    if guard_status == "warning":
        guard_analysis["anomalies"][0]["severity"] = "medium"

    monkeypatch.setattr(
        compare_service,
        "analyze_compare_result",
        lambda guard_input: guard_analysis,
    )
    base_path = write_result(
        tmp_path,
        "base.json",
        timestamp="2026-04-13T09:00:00Z",
        precision="fp16",
        mean_ms=10.0,
    )
    new_path = write_result(
        tmp_path,
        "new.json",
        timestamp="2026-04-13T10:00:00Z",
        precision="fp16",
        mean_ms=9.0,
    )

    bundle = build_compare_bundle(base_path=base_path, new_path=new_path, with_guard=True)

    assert bundle["guard_analysis"] == guard_analysis
    assert bundle["data"]["guard_analysis"] == guard_analysis
    assert bundle["deployment_decision"]["decision"] == expected_decision
    assert bundle["deployment_decision"]["guard_status"] == guard_status
    assert bundle["data"]["deployment_decision"] == bundle["deployment_decision"]
    evidence = guard_analysis["anomalies"][0]["evidence"]
    assert evidence["expected_source"] == "forge_worker_runtime_summary"
    assert evidence["observed_source"] == "runtime_worker_response"
    assert "Guard Analysis" in bundle["markdown"]
    assert "worker_provenance_mismatch" in bundle["markdown"]
    assert "forge_worker_runtime_summary" in bundle["markdown"]
    assert "runtime_worker_response" in bundle["markdown"]
    assert "Deployment Decision" in bundle["html"]
    assert "Guard Analysis" in bundle["html"]
    assert "worker_provenance_mismatch" in bundle["html"]


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
