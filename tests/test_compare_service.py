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
EDGEENV_REGRESSION_FIXTURES = FIXTURES / "edgeenv_regression"


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


def load_edgeenv_regression_fixture(name: str) -> dict:
    return json.loads(
        (EDGEENV_REGRESSION_FIXTURES / name).read_text(encoding="utf-8")
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
                        "history_execution_sequence_id": 1,
                        "telemetry_source": "synthetic_local_fixture",
                    },
                    "candidate": {
                        "run_id": "candidate",
                        "result_telemetry_present": True,
                        "history_entry_present": True,
                        "execution_sequence_id": 2,
                        "history_execution_sequence_id": 2,
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


def write_edgeenv_regression_with_orchestrator_context(tmp_path) -> str:
    path = Path(write_edgeenv_regression(tmp_path))
    payload = json.loads(path.read_text(encoding="utf-8"))
    context = payload["runtime_telemetry_context"]
    context["history"]["summary"]["orchestrator_feed_runs"] = 1
    context["candidate"]["orchestrator_context_present"] = True
    context["candidate"]["orchestrator_operation_context"] = {
        "schema_version": "inferedge-orchestrator-edgeenv-runtime-telemetry-feed-v1",
        "role": "orchestrator_operation_context_for_edgeenv",
        "source": "orchestration_summary",
        "run_id": "candidate",
        "not_a_regression_judgement": True,
        "not_a_comparability_gate": True,
        "decision_owner": "lab",
        "regression_owner": "edgeenv",
        "candidate_context": {
            "run_id": "candidate",
            "queue_depth": 7,
            "operation": {
                "queue_depth": 7,
                "max_total_queue_depth": 7,
                "deadline_missed_count": 2,
                "fallback_count": 1,
                "runtime_task_event_summary": {
                    "vision_agent": {
                        "scheduler_delay_event_count": 1,
                        "deadline_missed_count": 1,
                        "fallback_decision_count": 0,
                        "max_scheduler_delay_cycles": 3,
                        "max_queue_wait_ms": 15.0,
                        "policy_decision_reason_counts": {},
                        "drop_reason_counts": {},
                    },
                    "voice_command_agent": {
                        "scheduler_delay_event_count": 0,
                        "deadline_missed_count": 0,
                        "fallback_decision_count": 1,
                        "max_scheduler_delay_cycles": 0,
                        "max_queue_wait_ms": 0.0,
                        "policy_decision_reason_counts": {
                            "queue_backlog_threshold_exceeded": 1,
                        },
                        "drop_reason_counts": {
                            "load_shedding_backlog_threshold_exceeded": 1,
                        },
                    },
                },
                "tasks_with_deadline_miss": ["vision_agent"],
                "tasks_with_fallback": ["voice_command_agent"],
                "tasks_with_scheduler_delay": ["vision_agent"],
            },
            "resource": {
                "source": "tegrastats_timeline",
                "gpu_temperature": 78.5,
                "throttling_detected": True,
            },
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def write_edgeenv_candidate_telemetry_gap(tmp_path) -> str:
    path = tmp_path / "edgeenv_candidate_telemetry_gap.json"
    path.write_text(
        json.dumps(
            {
                "regression_detected": False,
                "regression_type": "none",
                "severity": "none",
                "comparable": True,
                "mode": "same-condition",
                "recommendation": "telemetry_replay_review",
                "comparability": {
                    "comparable": True,
                    "reasons": ["All strict regression keys match."],
                },
                "evidence": {},
                "runtime_telemetry_context": {
                    "role": "supplemental_runtime_telemetry_context",
                    "source": "result_artifacts+runtime_telemetry_history",
                    "baseline": {
                        "run_id": "baseline",
                        "result_telemetry_present": True,
                        "history_entry_present": True,
                        "execution_sequence_id": 1,
                        "history_execution_sequence_id": 1,
                        "telemetry_source": "synthetic_local_fixture",
                    },
                    "candidate": {
                        "run_id": "candidate",
                        "result_telemetry_present": False,
                        "history_entry_present": False,
                        "history_missing_recorded": True,
                        "history_missing_reason": "runtime_telemetry_missing",
                        "execution_sequence_id": 2,
                        "history_execution_sequence_id": None,
                        "telemetry_source": "synthetic_local_fixture",
                    },
                    "history": {
                        "schema_version": "edgeenv.runtime-telemetry-history.v1",
                        "summary": {
                            "registered_runs": 3,
                            "telemetry_runs": 2,
                            "missing_telemetry_runs": 1,
                        },
                    },
                    "evidence_gaps": [
                        {
                            "run_id": "candidate",
                            "reason": "runtime_telemetry_missing_in_result",
                        },
                        {
                            "run_id": "candidate",
                            "reason": "runtime_telemetry_missing",
                        },
                    ],
                },
            }
        ),
        encoding="utf-8",
    )
    return str(path)


def write_edgeenv_sequence_inversion(tmp_path) -> str:
    path = tmp_path / "edgeenv_sequence_inversion.json"
    path.write_text(
        json.dumps(
            {
                "regression_detected": False,
                "regression_type": "none",
                "severity": "none",
                "comparable": True,
                "mode": "same-condition",
                "recommendation": "telemetry_replay_review",
                "comparability": {
                    "comparable": True,
                    "reasons": ["All strict regression keys match."],
                },
                "evidence": {},
                "runtime_telemetry_context": {
                    "role": "supplemental_runtime_telemetry_context",
                    "source": "result_artifacts+runtime_telemetry_history",
                    "baseline": {
                        "run_id": "baseline",
                        "result_telemetry_present": True,
                        "history_entry_present": True,
                        "execution_sequence_id": 5,
                        "history_execution_sequence_id": 5,
                        "telemetry_source": "synthetic_local_fixture",
                    },
                    "candidate": {
                        "run_id": "candidate",
                        "result_telemetry_present": True,
                        "history_entry_present": True,
                        "execution_sequence_id": 2,
                        "history_execution_sequence_id": 2,
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
            {
                "type": "runtime_telemetry_replay_context",
                "metric_name": "runtime_telemetry_history_missing_run_count",
                "observed_value": 1.0,
                "baseline_value": 0,
                "threshold": 1.0,
                "delta": None,
                "delta_pct": None,
                "increase_factor": None,
                "severity": "medium",
                "status": "warning",
                "explanation": (
                    "runtime_telemetry_history_missing_run_count observed value is 1.0. "
                    "Baseline value is 0. Threshold is 1.0. This "
                    "runtime_telemetry_replay_context evidence should be reviewed "
                    "before deployment."
                ),
                "why_it_matters": (
                    "EdgeEnv telemetry history is the replay artifact behind runtime "
                    "regression context."
                ),
                "suspected_causes": ["telemetry_history_replay_gap"],
                "recommendation": (
                    "Inspect the EdgeEnv telemetry history artifact before relying on "
                    "trend diagnosis."
                ),
                "raw_context": {
                    "edgeenv_regression": {"history_missing_telemetry_runs": 1.0}
                },
            },
        ],
        "suspected_causes": [
            "runtime_latency_drift",
            "tail_latency_spike",
            "telemetry_history_replay_gap",
        ],
        "recommendations": [
            "Review EdgeEnv comparability judgement and telemetry before deployment."
        ],
        "thresholds": {"edgeenv_p99_delta_pct_review": 25.0},
        "baseline_summary": {},
        "candidate_summary": {
            "edgeenv_regression": {
                "candidate_run_id": "edgeenv-smoke-candidate",
                "history_missing_telemetry_runs": 1.0,
            }
        },
        "created_at": "2026-05-22T00:00:00Z",
    }


def make_edgeenv_replay_warning_guard_analysis(
    *,
    suspected_cause: str,
    observed_value: float,
    coverage_gap_count: float | None = None,
) -> dict:
    coverage_observed_value = (
        coverage_gap_count
        if coverage_gap_count is not None
        else 3.0 if observed_value else 0.0
    )
    return {
        "schema_version": "inferedge-aiguard-diagnosis-v1",
        "source": {
            "edgeenv_runtime_regression_report": True,
            "edgeenv_mode": "same-condition",
            "edgeenv_comparable": True,
        },
        "guard_verdict": "suspicious",
        "severity": "medium",
        "confidence": 0.82,
        "primary_reason": "Runtime telemetry replay context should be reviewed.",
        "evidence": [
            {
                "type": "runtime_telemetry_context_coverage",
                "metric_name": "runtime_telemetry_evidence_gap_count",
                "observed_value": coverage_observed_value,
                "baseline_value": 0,
                "threshold": 1,
                "severity": "medium" if coverage_observed_value else "low",
                "status": "warning" if coverage_observed_value else "passed",
                "explanation": "Runtime telemetry context coverage was evaluated.",
                "why_it_matters": (
                    "Missing baseline or candidate telemetry is an evidence gap, "
                    "not a failed benchmark by itself."
                ),
                "suspected_causes": (
                    ["runtime_telemetry_gap"] if coverage_observed_value else []
                ),
                "recommendation": (
                    "Preserve runtime telemetry artifacts before relying on trend diagnosis."
                ),
            },
            {
                "type": "runtime_telemetry_replay_context",
                "metric_name": "runtime_telemetry_history_missing_run_count",
                "observed_value": observed_value,
                "baseline_value": 0,
                "threshold": 1,
                "severity": "medium",
                "status": "warning",
                "explanation": "Runtime telemetry replay context should be reviewed.",
                "why_it_matters": (
                    "EdgeEnv telemetry history is the replay artifact behind runtime "
                    "regression context."
                ),
                "suspected_causes": [suspected_cause],
                "recommendation": (
                    "Inspect the EdgeEnv telemetry history artifact before relying on "
                    "trend diagnosis."
                ),
            },
        ],
        "suspected_causes": [suspected_cause],
        "recommendations": [
            "Review EdgeEnv telemetry replay context before deployment."
        ],
        "created_at": "2026-05-22T00:00:00Z",
    }


def make_edgeenv_orchestrator_context_guard_analysis() -> dict:
    return {
        "schema_version": "inferedge-aiguard-diagnosis-v1",
        "source": {
            "edgeenv_runtime_regression_report": True,
            "edgeenv_mode": "same-condition",
            "edgeenv_comparable": True,
        },
        "guard_verdict": "suspicious",
        "severity": "medium",
        "confidence": 0.74,
        "primary_reason": "Orchestrator operation context should be reviewed.",
        "evidence": [
            {
                "type": "runtime_thermal_instability",
                "metric_name": "candidate_max_temperature_c",
                "observed_value": 78.5,
                "baseline_value": None,
                "threshold": 70.0,
                "severity": "medium",
                "status": "warning",
                "why_it_matters": "Thermal pressure can explain runtime drift.",
                "suspected_causes": ["thermal_pressure", "thermal_throttling"],
                "recommendation": "Review cooling and sustained runtime context.",
            },
            {
                "type": "runtime_queue_overload",
                "metric_name": "candidate_queue_depth",
                "observed_value": 7.0,
                "baseline_value": None,
                "threshold": 3.0,
                "severity": "medium",
                "status": "warning",
                "why_it_matters": "Queue backlog can inflate runtime latency.",
                "suspected_causes": ["queue_overload", "scheduler_contention"],
                "recommendation": "Review Orchestrator queue policy.",
                "raw_context": {
                    "edgeenv_regression": {
                        "orchestrator_candidate_operation_max_total_queue_depth": 7.0,
                    },
                },
            },
        ],
        "suspected_causes": ["thermal_pressure", "queue_overload"],
        "recommendations": ["Review Orchestrator context before deployment."],
        "candidate_summary": {
            "edgeenv_regression": {
                "history_orchestrator_feed_runs": 1.0,
                "candidate_orchestrator_context_present": True,
                "candidate_queue_depth": 7.0,
                "orchestrator_candidate_operation_max_total_queue_depth": 7.0,
                "candidate_max_temperature_c": 78.5,
                "candidate_throttling_detected": True,
            }
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
    assert "runtime_telemetry_replay_context" in bundle["markdown"]
    assert "telemetry_history_replay_gap" in bundle["markdown"]
    assert "Runtime Regression Evidence" in bundle["markdown"]
    assert "Runtime Telemetry Context" in bundle["markdown"]
    assert "runtime_telemetry_context_coverage" in bundle["html"]
    assert "runtime_telemetry_history_missing_run_count" in bundle["html"]


def test_build_compare_bundle_summarizes_orchestrator_context_runtime_anomalies(
    tmp_path, monkeypatch
):
    guard_analysis = make_edgeenv_orchestrator_context_guard_analysis()

    def fake_analyze_edgeenv_regression_report(report):
        context = report["runtime_telemetry_context"]
        assert context["history"]["summary"]["orchestrator_feed_runs"] == 1
        assert context["candidate"]["orchestrator_context_present"] is True
        assert context["candidate"]["orchestrator_operation_context"][
            "not_a_regression_judgement"
        ] is True
        return guard_analysis

    monkeypatch.setattr(
        compare_service,
        "analyze_edgeenv_regression_report",
        fake_analyze_edgeenv_regression_report,
    )
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
    )

    bundle = build_compare_bundle(
        base_path=base_path,
        new_path=new_path,
        with_guard=True,
        edgeenv_regression_path=write_edgeenv_regression_with_orchestrator_context(
            tmp_path
        ),
    )

    assert bundle["guard_analysis"] == guard_analysis
    assert bundle["deployment_decision"]["decision"] == "review_required"
    assert bundle["deployment_decision"]["guard_status"] == "warning"
    assert "guard_warning_review" in bundle["deployment_decision"]["triggered_rules"]
    assert "| Orchestrator operation feed context | 1 |" in bundle["markdown"]
    assert "| Orchestrator context attached runs | candidate |" in bundle["markdown"]
    assert (
        "| Orchestrator queue/deadline/fallback markers | candidate: "
        "max_total_queue_depth=7, deadline_missed_count=2, fallback_count=1 |"
    ) in bundle["markdown"]
    assert (
        "| AIGuard max queue raw-context traceability | candidate: "
        "report=max_total_queue_depth=7, "
        "raw_context=orchestrator_candidate_operation_max_total_queue_depth=7, "
        "match=True |"
    ) in bundle["markdown"]
    assert "| Orchestrator task event rollup | candidate: " in bundle["markdown"]
    assert "vision_agent(delay=1,miss=1,max_delay_cycles=3,max_wait_ms=15)" in bundle[
        "markdown"
    ]
    assert (
        "voice_command_agent(fallback=1,policy=queue_backlog_threshold_exceeded:1,"
        "drop=load_shedding_backlog_threshold_exceeded:1)"
    ) in bundle["markdown"]
    assert "runtime_queue_overload, runtime_thermal_instability" in bundle["markdown"]
    assert "| AIGuard Orchestrator context handoff | feeds=1.0, candidate |" in bundle[
        "markdown"
    ]
    assert "AIGuard does not own the final decision" in bundle["markdown"]
    assert "AIGuard Orchestrator context handoff" in bundle["html"]
    assert "AIGuard max queue raw-context traceability" in bundle["html"]
    assert "supplemental operation evidence" in bundle["html"]


def test_build_compare_bundle_preserves_edgeenv_candidate_gap_guard_report(
    tmp_path, monkeypatch
):
    guard_analysis = make_edgeenv_replay_warning_guard_analysis(
        suspected_cause="telemetry_history_replay_gap",
        observed_value=1.0,
    )

    def fake_analyze_edgeenv_regression_report(report):
        context = report["runtime_telemetry_context"]
        assert context["candidate"]["result_telemetry_present"] is False
        assert context["candidate"]["history_entry_present"] is False
        assert context["candidate"]["history_missing_recorded"] is True
        assert (
            context["candidate"]["history_missing_reason"]
            == "runtime_telemetry_missing"
        )
        assert context["history"]["summary"]["missing_telemetry_runs"] == 1
        return guard_analysis

    monkeypatch.setattr(
        compare_service,
        "analyze_edgeenv_regression_report",
        fake_analyze_edgeenv_regression_report,
    )
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
    )

    bundle = build_compare_bundle(
        base_path=base_path,
        new_path=new_path,
        with_guard=True,
        edgeenv_regression_path=write_edgeenv_candidate_telemetry_gap(tmp_path),
    )

    assert bundle["guard_analysis"] == guard_analysis
    assert bundle["data"]["guard_analysis"] == guard_analysis
    assert bundle["deployment_decision"]["decision"] == "review_required"
    assert bundle["deployment_decision"]["guard_status"] == "warning"
    assert bundle["deployment_decision"]["guard_verdict"] == "suspicious"
    assert "guard_warning_review" in bundle["deployment_decision"]["triggered_rules"]
    assert (
        "edgeenv_runtime_regression_review"
        not in bundle["deployment_decision"]["triggered_rules"]
    )
    assert "runtime_telemetry_replay_context" in bundle["markdown"]
    assert "runtime_telemetry_context_coverage" in bundle["markdown"]
    assert "runtime_telemetry_gap" in bundle["markdown"]
    assert "telemetry_history_replay_gap" in bundle["markdown"]
    assert (
        "| candidate `candidate` | False | False | 2 | - | synthetic_local_fixture |"
        in bundle["markdown"]
    )
    assert "runtime_telemetry_missing_in_result" in bundle["html"]
    assert "runtime_telemetry_history_missing_run_count" in bundle["html"]


def test_build_compare_bundle_preserves_edgeenv_sequence_inversion_guard_report(
    tmp_path, monkeypatch
):
    guard_analysis = make_edgeenv_replay_warning_guard_analysis(
        suspected_cause="telemetry_sequence_order_mismatch",
        observed_value=0.0,
    )

    def fake_analyze_edgeenv_regression_report(report):
        context = report["runtime_telemetry_context"]
        assert context["baseline"]["execution_sequence_id"] == 5
        assert context["baseline"]["history_execution_sequence_id"] == 5
        assert context["candidate"]["execution_sequence_id"] == 2
        assert context["candidate"]["history_execution_sequence_id"] == 2
        return guard_analysis

    monkeypatch.setattr(
        compare_service,
        "analyze_edgeenv_regression_report",
        fake_analyze_edgeenv_regression_report,
    )
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
    )

    bundle = build_compare_bundle(
        base_path=base_path,
        new_path=new_path,
        with_guard=True,
        edgeenv_regression_path=write_edgeenv_sequence_inversion(tmp_path),
    )

    assert bundle["guard_analysis"] == guard_analysis
    assert bundle["deployment_decision"]["decision"] == "review_required"
    assert bundle["deployment_decision"]["guard_status"] == "warning"
    assert bundle["deployment_decision"]["guard_verdict"] == "suspicious"
    assert "runtime_telemetry_replay_context" in bundle["markdown"]
    assert "telemetry_sequence_order_mismatch" in bundle["markdown"]
    assert "| baseline `baseline` | True | True | 5 | 5 |" in bundle["markdown"]
    assert "| candidate `candidate` | True | True | 2 | 2 |" in bundle["markdown"]
    assert "telemetry_sequence_order_mismatch" in bundle["html"]
    assert "history_execution_sequence_id" in bundle["html"]


def test_build_compare_bundle_consumes_edgeenv_candidate_gap_fixture(
    tmp_path, monkeypatch
):
    fixture_name = "edgeenv_candidate_telemetry_gap.json"
    fixture_path = EDGEENV_REGRESSION_FIXTURES / fixture_name
    guard_analysis = make_edgeenv_replay_warning_guard_analysis(
        suspected_cause="telemetry_history_replay_gap",
        observed_value=1.0,
        coverage_gap_count=4.0,
    )

    def fake_analyze_edgeenv_regression_report(report):
        assert "guard_analysis" not in report
        assert report == load_edgeenv_regression_fixture(fixture_name)
        context = report["runtime_telemetry_context"]
        assert context["candidate"]["result_telemetry_present"] is False
        assert context["candidate"]["history_entry_present"] is False
        assert context["candidate"]["history_missing_recorded"] is True
        assert context["candidate"]["history_missing_reason"] == (
            "runtime_telemetry_missing"
        )
        assert context["history"]["summary"]["missing_telemetry_runs"] == 1
        return guard_analysis

    monkeypatch.setattr(
        compare_service,
        "analyze_edgeenv_regression_report",
        fake_analyze_edgeenv_regression_report,
    )
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
    )

    bundle = build_compare_bundle(
        base_path=base_path,
        new_path=new_path,
        with_guard=True,
        edgeenv_regression_path=str(fixture_path),
    )

    assert bundle["edgeenv_runtime_regression"] == load_edgeenv_regression_fixture(
        fixture_name
    )
    assert bundle["guard_analysis"] == guard_analysis
    assert bundle["deployment_decision"]["decision"] == "review_required"
    assert bundle["deployment_decision"]["guard_status"] == "warning"
    assert bundle["deployment_decision"]["guard_verdict"] == "suspicious"
    assert "guard_warning_review" in bundle["deployment_decision"]["triggered_rules"]
    assert (
        "edgeenv_runtime_regression_review"
        not in bundle["deployment_decision"]["triggered_rules"]
    )
    assert "runtime_telemetry_context_coverage" in bundle["markdown"]
    assert "runtime_telemetry_replay_context" in bundle["markdown"]
    assert "telemetry_history_replay_gap" in bundle["markdown"]
    assert "runtime_telemetry_missing_in_result" in bundle["markdown"]
    assert "| candidate `candidate` | False | False | - | - | - |" in bundle["markdown"]
    assert "## Runtime Intelligence Risk Summary" in bundle["markdown"]
    assert "| Telemetry evidence gaps | 2 |" in bundle["markdown"]
    assert "| Telemetry history replay gaps | 1 |" in bundle["markdown"]
    assert "| AIGuard evidence items needing review | 2 |" in bundle["markdown"]
    assert "Lab remains the final deployment decision owner" in bundle["markdown"]
    assert "Runtime Intelligence Risk Summary" in bundle["html"]
    assert "AIGuard explains runtime/anomaly evidence" in bundle["html"]
    assert "runtime_telemetry_history_missing_run_count" in bundle["html"]
    assert "Missing telemetry is an evidence gap" in bundle["html"]


def test_build_compare_bundle_consumes_edgeenv_sequence_inversion_fixture(
    tmp_path, monkeypatch
):
    fixture_name = "edgeenv_sequence_inversion.json"
    fixture_path = EDGEENV_REGRESSION_FIXTURES / fixture_name
    guard_analysis = make_edgeenv_replay_warning_guard_analysis(
        suspected_cause="telemetry_sequence_order_mismatch",
        observed_value=0.0,
    )

    def fake_analyze_edgeenv_regression_report(report):
        assert "guard_analysis" not in report
        assert report == load_edgeenv_regression_fixture(fixture_name)
        context = report["runtime_telemetry_context"]
        assert context["baseline"]["execution_sequence_id"] == 5
        assert context["baseline"]["history_execution_sequence_id"] == 5
        assert context["candidate"]["execution_sequence_id"] == 2
        assert context["candidate"]["history_execution_sequence_id"] == 2
        assert context["evidence_gaps"] == []
        return guard_analysis

    monkeypatch.setattr(
        compare_service,
        "analyze_edgeenv_regression_report",
        fake_analyze_edgeenv_regression_report,
    )
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
    )

    bundle = build_compare_bundle(
        base_path=base_path,
        new_path=new_path,
        with_guard=True,
        edgeenv_regression_path=str(fixture_path),
    )

    assert bundle["edgeenv_runtime_regression"] == load_edgeenv_regression_fixture(
        fixture_name
    )
    assert bundle["guard_analysis"] == guard_analysis
    assert bundle["deployment_decision"]["decision"] == "review_required"
    assert bundle["deployment_decision"]["guard_status"] == "warning"
    assert bundle["deployment_decision"]["guard_verdict"] == "suspicious"
    assert "runtime_telemetry_replay_context" in bundle["markdown"]
    assert "telemetry_sequence_order_mismatch" in bundle["markdown"]
    assert "| baseline `baseline` | True | True | 5 | 5 |" in bundle["markdown"]
    assert "| candidate `candidate` | True | True | 2 | 2 |" in bundle["markdown"]
    assert "## Runtime Intelligence Risk Summary" in bundle["markdown"]
    assert "| Telemetry evidence gaps | 0 |" in bundle["markdown"]
    assert "| Telemetry history replay gaps | 0 |" in bundle["markdown"]
    assert "| AIGuard evidence items needing review | 1 |" in bundle["markdown"]
    assert "telemetry_sequence_order_mismatch" in bundle["html"]
    assert "not a comparability gate" in bundle["html"]


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
