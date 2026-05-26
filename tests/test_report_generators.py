from __future__ import annotations

from inferedgelab.report.markdown_generator import generate_compare_markdown
from inferedgelab.report.html_generator import generate_compare_html


def make_compare_result(
    *,
    comparison_mode: str = "same_precision",
    base_precision: str = "fp32",
    new_precision: str = "fp32",
    accuracy_task: str = "classification",
    primary_metric_name: str = "top1_accuracy",
    accuracy_metrics: dict | None = None,
) -> dict:
    if accuracy_metrics is None:
        accuracy_metrics = {
            "top1_accuracy": {
                "base": 0.90,
                "new": 0.92,
                "delta": 0.02,
                "delta_pct": 2.2222,
                "delta_pp": 2.0,
            }
        }

    return {
        "base_id": {
            "model": "base_model.onnx",
            "engine": "onnxruntime",
            "device": "cpu",
            "timestamp": "2026-04-14T00:00:00Z",
            "precision": base_precision,
        },
        "new_id": {
            "model": "new_model.onnx",
            "engine": "onnxruntime",
            "device": "cpu",
            "timestamp": "2026-04-14T01:00:00Z",
            "precision": new_precision,
        },
        "precision": {
            "base": base_precision,
            "new": new_precision,
            "match": comparison_mode == "same_precision",
            "comparison_mode": comparison_mode,
            "pair": f"{base_precision}_vs_{new_precision}",
        },
        "metrics": {
            "mean_ms": {
                "base": 10.0,
                "new": 8.0,
                "delta": -2.0,
                "delta_pct": -20.0,
            },
            "p99_ms": {
                "base": 12.0,
                "new": 10.0,
                "delta": -2.0,
                "delta_pct": -16.6667,
            },
        },
        "accuracy": {
            "present": True,
            "task": accuracy_task,
            "metric_name": primary_metric_name,
            "sample_count": {
                "base": 100,
                "new": 100,
            },
            "metrics": accuracy_metrics,
        },
        "shape": {
            "base": {"batch": 1, "height": 224, "width": 224},
            "new": {"batch": 1, "height": 224, "width": 224},
        },
        "shape_context": {
            "base": {
                "requested_batch": 1,
                "requested_height": 224,
                "requested_width": 224,
                "effective_batch": 1,
                "effective_height": 224,
                "effective_width": 224,
                "primary_input_name": "input",
                "resolved_input_shapes": {"input": [1, 3, 224, 224]},
            },
            "new": {
                "requested_batch": 1,
                "requested_height": 224,
                "requested_width": 224,
                "effective_batch": 1,
                "effective_height": 224,
                "effective_width": 224,
                "primary_input_name": "input",
                "resolved_input_shapes": {"input": [1, 3, 224, 224]},
            },
        },
        "runtime_provenance": {
            "base": {
                "runtime_artifact_path": "/tmp/base.engine",
                "primary_input_name": "input",
                "requested_shape_summary": "b1 / h224 / w224",
                "effective_shape_summary": "b1 / h224 / w224",
            },
            "new": {
                "runtime_artifact_path": "/tmp/new.engine",
                "primary_input_name": "input",
                "requested_shape_summary": "b1 / h224 / w224",
                "effective_shape_summary": "b1 / h224 / w224",
            },
        },
        "system_diff": {
            "os": {"base": "Linux", "new": "Linux"},
            "python": {"base": "3.11.0", "new": "3.11.0"},
            "machine": {"base": "x86_64", "new": "x86_64"},
            "cpu_count_logical": {"base": 8, "new": 8},
        },
        "run_config_diff": {
            "warmup": {"base": 10, "new": 10},
            "runs": {"base": 100, "new": 100},
            "intra_threads": {"base": 1, "new": 1},
            "inter_threads": {"base": 1, "new": 1},
            "mode": {"base": "profile", "new": "profile"},
            "task": {"base": accuracy_task, "new": accuracy_task},
        },
    }


def make_judgement(
    *,
    comparison_mode: str = "same_precision",
    precision_match: bool = True,
    overall: str = "improvement",
    accuracy: str = "improvement",
    tradeoff_risk: str = "not_applicable",
) -> dict:
    return {
        "overall": overall,
        "shape_match": True,
        "system_match": True,
        "precision_match": precision_match,
        "comparison_mode": comparison_mode,
        "precision_pair": "fp32_vs_fp32" if precision_match else "fp16_vs_int8",
        "mean_ms": "improvement",
        "p99_ms": "improvement",
        "accuracy": accuracy,
        "accuracy_present": True,
        "tradeoff_risk": tradeoff_risk,
        "thresholds": {
            "latency_improve_threshold": -3.0,
            "latency_regress_threshold": 3.0,
            "accuracy_improve_threshold": 0.2,
            "accuracy_regress_threshold": -0.2,
            "tradeoff_caution_threshold": -0.3,
            "tradeoff_risky_threshold": -1.0,
            "tradeoff_severe_threshold": -2.0,
        },
        "summary": "Synthetic summary for report generator testing.",
        "notes": [
            "Synthetic note 1",
            "Synthetic note 2",
        ],
    }


def make_edgeenv_regression() -> dict:
    return {
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
            "p95_delta_pct": 21.2,
            "p99_delta_pct": 32.1,
            "fps_delta_pct": -20.5,
            "memory_peak_delta_pct": 5.0,
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
                "telemetry_coverage": {
                    "schema_version": "inferedge-runtime-telemetry-coverage-v1",
                    "expected_fields": [
                        "gpu_temperature",
                        "queue_depth",
                        "telemetry_timestamp",
                    ],
                    "observed_fields": [
                        "gpu_temperature",
                        "queue_depth",
                        "telemetry_timestamp",
                    ],
                    "missing_fields": [],
                    "expected_field_count": 3,
                    "observed_field_count": 3,
                    "missing_field_count": 0,
                    "coverage_ratio": 1.0,
                    "comparability_owner": "edgeenv",
                    "missing_telemetry_is_failure": False,
                },
            },
            "candidate": {
                "run_id": "candidate",
                "result_telemetry_present": True,
                "history_entry_present": True,
                "execution_sequence_id": 2,
                "history_execution_sequence_id": 2,
                "telemetry_source": "synthetic_local_fixture",
                "telemetry_coverage": {
                    "schema_version": "inferedge-runtime-telemetry-coverage-v1",
                    "expected_fields": [
                        "gpu_temperature",
                        "queue_depth",
                        "telemetry_timestamp",
                    ],
                    "observed_fields": [
                        "gpu_temperature",
                        "telemetry_timestamp",
                    ],
                    "missing_fields": ["queue_depth"],
                    "expected_field_count": 3,
                    "observed_field_count": 2,
                    "missing_field_count": 1,
                    "coverage_ratio": 0.666667,
                    "comparability_owner": "edgeenv",
                    "missing_telemetry_is_failure": False,
                },
            },
            "history": {
                "schema_version": "edgeenv.runtime-telemetry-history.v1",
                "summary": {
                    "registered_runs": 2,
                    "telemetry_runs": 2,
                    "missing_telemetry_runs": 0,
                },
                "telemetry_coverage": {
                    "runs_with_coverage": 2,
                    "runs_without_coverage": 0,
                    "expected_fields": [
                        "gpu_temperature",
                        "queue_depth",
                        "telemetry_timestamp",
                    ],
                    "observed_fields": [
                        "gpu_temperature",
                        "queue_depth",
                        "telemetry_timestamp",
                    ],
                    "missing_fields": ["queue_depth"],
                    "coverage_ratio_min": 0.666667,
                    "coverage_ratio_max": 1.0,
                    "missing_telemetry_is_failure_values": [False],
                    "any_missing_telemetry_is_failure": False,
                    "missing_field_run_count": 1,
                    "missing_field_runs": [
                        {
                            "run_id": "candidate",
                            "missing_fields": ["queue_depth"],
                            "missing_field_count": 1,
                            "missing_telemetry_is_failure": False,
                        }
                    ],
                    "run_summaries": [
                        {
                            "run_id": "baseline",
                            "coverage_present": True,
                            "expected_fields": [
                                "gpu_temperature",
                                "queue_depth",
                                "telemetry_timestamp",
                            ],
                            "observed_fields": [
                                "gpu_temperature",
                                "queue_depth",
                                "telemetry_timestamp",
                            ],
                            "missing_fields": [],
                            "expected_field_count": 3,
                            "observed_field_count": 3,
                            "missing_field_count": 0,
                            "coverage_ratio": 1.0,
                            "missing_telemetry_is_failure": False,
                        },
                        {
                            "run_id": "candidate",
                            "coverage_present": True,
                            "expected_fields": [
                                "gpu_temperature",
                                "queue_depth",
                                "telemetry_timestamp",
                            ],
                            "observed_fields": [
                                "gpu_temperature",
                                "telemetry_timestamp",
                            ],
                            "missing_fields": ["queue_depth"],
                            "expected_field_count": 3,
                            "observed_field_count": 2,
                            "missing_field_count": 1,
                            "coverage_ratio": 0.666667,
                            "missing_telemetry_is_failure": False,
                        },
                    ],
                },
            },
            "evidence_gaps": [],
            "notes": [
                "Runtime telemetry context is supplemental evidence, not a comparability gate.",
            ],
        },
    }


def make_edgeenv_regression_with_orchestrator_context() -> dict:
    regression = make_edgeenv_regression()
    context = regression["runtime_telemetry_context"]
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
                "deadline_missed_count": 2,
                "fallback_count": 1,
            },
            "resource": {
                "source": "tegrastats_timeline",
                "gpu_temperature": 78.5,
                "throttling_detected": True,
            },
        },
    }
    return regression


def make_runtime_operation_guard_analysis() -> dict:
    return {
        "schema_version": "inferedge-aiguard-diagnosis-v1",
        "guard_verdict": "suspicious",
        "severity": "medium",
        "confidence": 0.74,
        "primary_reason": (
            "Runtime operation context indicates thermal and queue review risk."
        ),
        "evidence": [
            {
                "type": "runtime_thermal_instability",
                "metric_name": "candidate_max_temperature_c",
                "observed_value": 78.5,
                "baseline_value": None,
                "threshold": 70.0,
                "status": "warning",
                "severity": "medium",
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
                "status": "warning",
                "severity": "medium",
                "why_it_matters": "Queue backlog can inflate runtime latency.",
                "suspected_causes": ["queue_overload", "scheduler_contention"],
                "recommendation": "Review Orchestrator queue policy.",
            },
        ],
        "candidate_summary": {
            "edgeenv_regression": {
                "history_orchestrator_feed_runs": 1.0,
                "candidate_orchestrator_context_present": True,
                "baseline_runtime_telemetry_history_seed_run_config": {
                    "batch": 1,
                    "height": 640,
                    "width": 640,
                    "warmup": 1,
                    "runs": 10,
                    "input_mode": "dummy",
                    "input_preprocess": "none",
                    "power_mode": "unknown",
                    "jetson_clocks": "unknown",
                },
                "candidate_runtime_telemetry_history_seed_run_config": {
                    "batch": 1,
                    "height": 640,
                    "width": 640,
                    "warmup": 1,
                    "runs": 10,
                    "input_mode": "dummy",
                    "input_preprocess": "none",
                    "power_mode": "unknown",
                    "jetson_clocks": "unknown",
                },
                "candidate_queue_depth": 7.0,
                "candidate_max_temperature_c": 78.5,
                "candidate_throttling_detected": True,
            }
        },
    }


def test_generate_compare_markdown_includes_classification_primary_metric_and_summary():
    compare_result = make_compare_result()
    judgement = make_judgement()

    text = generate_compare_markdown(compare_result, judgement)

    assert "# EdgeBench Compare Report" in text
    assert "## Judgement" in text
    assert "- Primary accuracy metric: **`top1_accuracy`**" in text
    assert "- Summary: Synthetic summary for report generator testing." in text
    assert "| top1_accuracy (primary) |" in text
    assert "| runtime_artifact_path | /tmp/base.engine | /tmp/new.engine |" in text


def test_generate_compare_markdown_includes_cross_precision_warning_for_detection():
    compare_result = make_compare_result(
        comparison_mode="cross_precision",
        base_precision="fp16",
        new_precision="int8",
        accuracy_task="detection",
        primary_metric_name="map50",
        accuracy_metrics={
            "map50": {
                "base": 0.7791,
                "new": 0.7977,
                "delta": 0.0186,
                "delta_pct": 2.3874,
                "delta_pp": 1.86,
            },
            "f1_score": {
                "base": 0.8000,
                "new": 0.8129,
                "delta": 0.0129,
                "delta_pct": 1.6125,
                "delta_pp": 1.29,
            },
        },
    )
    judgement = make_judgement(
        comparison_mode="cross_precision",
        precision_match=False,
        overall="tradeoff_faster",
        accuracy="improvement",
        tradeoff_risk="acceptable_tradeoff",
    )

    text = generate_compare_markdown(compare_result, judgement)

    assert "> [!WARNING]" in text
    assert "This is a cross-precision comparison." in text
    assert "- Overall semantics: **trade-off status, not same-condition regression status**" in text
    assert "- Task: **`detection`**" in text
    assert "- Primary metric: **`map50`**" in text
    assert "| map50 (primary) |" in text
    assert "| f1_score |" in text


def test_generate_compare_markdown_orders_primary_accuracy_metric_first():
    compare_result = make_compare_result(
        accuracy_task="detection",
        primary_metric_name="map50",
        accuracy_metrics={
            "f1_score": {
                "base": 0.81,
                "new": 0.82,
                "delta": 0.01,
                "delta_pct": 1.2345,
                "delta_pp": 1.0,
            },
            "map50": {
                "base": 0.77,
                "new": 0.79,
                "delta": 0.02,
                "delta_pct": 2.5974,
                "delta_pp": 2.0,
            },
        },
    )
    judgement = make_judgement()

    text = generate_compare_markdown(compare_result, judgement)

    map50_idx = text.index("| map50 (primary) |")
    f1_idx = text.index("| f1_score |")
    assert map50_idx < f1_idx


def test_generate_compare_markdown_includes_guard_analysis_section():
    compare_result = make_compare_result()
    judgement = make_judgement()
    guard_analysis = {
        "status": "warning",
        "confidence": 0.7,
        "anomalies": ["insufficient_precision_speedup"],
        "suspected_causes": ["precision_speedup_not_observed"],
        "recommendations": ["Review runtime provenance."],
    }

    text = generate_compare_markdown(compare_result, judgement, guard_analysis=guard_analysis)

    assert "## Guard Analysis" in text
    assert "- status: warning" in text
    assert "insufficient_precision_speedup" in text
    assert "Review runtime provenance." in text


def test_generate_compare_markdown_includes_skipped_guard_analysis():
    compare_result = make_compare_result()
    judgement = make_judgement()
    guard_analysis = {
        "status": "skipped",
        "reason": "inferedge_aiguard is not installed",
    }

    text = generate_compare_markdown(compare_result, judgement, guard_analysis=guard_analysis)

    assert "## Guard Analysis" in text
    assert "- status: skipped" in text
    assert "- reason: inferedge_aiguard is not installed" in text


def test_generate_compare_markdown_includes_deployment_decision_section():
    compare_result = make_compare_result()
    judgement = make_judgement()
    deployment_decision = {
        "policy_version": "inferedge-lab-decision-policy-v1",
        "decision": "deployable",
        "reason": "Lab judgement is favorable and Guard analysis passed.",
        "lab_overall": "improvement",
        "guard_status": "ok",
        "recommended_action": "Deployment can proceed with normal rollout monitoring.",
        "triggered_rules": ["guard_ok_lab_favorable_deployable"],
        "policy_summary": [
            {
                "rule": "guard_ok_lab_favorable_deployable",
                "effect": "deployable",
                "description": "Lab comparison is favorable and AIGuard passed.",
            }
        ],
    }

    text = generate_compare_markdown(compare_result, judgement, deployment_decision=deployment_decision)

    assert "## Deployment Decision" in text
    assert "- policy_version: inferedge-lab-decision-policy-v1" in text
    assert "- decision: deployable" in text
    assert "- guard_status: ok" in text
    assert "guard_ok_lab_favorable_deployable" in text
    assert "### Decision Policy Summary" in text
    assert "| guard_ok_lab_favorable_deployable | deployable | Lab comparison is favorable and AIGuard passed. |" in text


def test_generate_compare_markdown_includes_edgeenv_regression_evidence():
    compare_result = make_compare_result()
    judgement = make_judgement()

    text = generate_compare_markdown(
        compare_result,
        judgement,
        edgeenv_regression=make_edgeenv_regression(),
    )

    assert "## Runtime Regression Evidence" in text
    assert "- source: EdgeEnv Runtime Regression Monitor" in text
    assert "- mode: same-condition" in text
    assert "| mean_delta_pct | +18.40% |" in text
    assert "p99_latency_high" in text
    assert "### Runtime Telemetry Context" in text
    assert "edgeenv.runtime-telemetry-history.v1" in text
    assert "history_telemetry_coverage" in text
    assert "missing_field_runs: candidate=queue_depth" in text
    assert "history_execution_sequence_id" in text
    assert "coverage_missing_fields" in text
    assert "| candidate `candidate` | True | True | 2 | 2 | synthetic_local_fixture | 0.6667 | queue_depth | False |" in text
    assert "| Runtime telemetry coverage gaps | baseline=none; candidate=queue_depth |" in text
    assert "candidate `candidate`" in text
    assert "Runtime telemetry evidence gaps: none" in text
    assert "not cloud monitoring, ranking, or production observability" in text


def test_generate_compare_markdown_summarizes_orchestrator_context_risk():
    compare_result = make_compare_result()
    judgement = make_judgement()

    text = generate_compare_markdown(
        compare_result,
        judgement,
        guard_analysis=make_runtime_operation_guard_analysis(),
        edgeenv_regression=make_edgeenv_regression_with_orchestrator_context(),
    )

    assert "## Runtime Intelligence Risk Summary" in text
    assert "| Orchestrator operation feed context | 1 |" in text
    assert "| Orchestrator context attached runs | candidate |" in text
    assert (
        "| AIGuard runtime operation anomalies | runtime_queue_overload, "
        "runtime_thermal_instability |"
    ) in text
    assert "| AIGuard Orchestrator context handoff | feeds=1.0, candidate |" in text
    assert (
        "| AIGuard history seed run_config markers | "
        "baseline/candidate=shape=1x640x640, input_mode=dummy, "
        "input_preprocess=none, power_mode=unknown, jetson_clocks=unknown, "
        "warmup=1, runs=10 |"
    ) in text
    assert "AIGuard does not own the final decision" in text


def test_generate_compare_markdown_includes_diagnosis_guard_evidence():
    compare_result = make_compare_result()
    judgement = make_judgement()
    guard_analysis = {
        "schema_version": "inferedge-aiguard-diagnosis-v1",
        "source": {
            "runtime_result_path": "results/candidate.json",
            "model_contract_path": "model_contract.json",
        },
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
                "why_it_matters": (
                    "Temporal evidence explains whether the runtime output is stable "
                    "enough to review."
                ),
                "suspected_causes": ["frame_jitter", "scheduler_contention"],
                "recommendation": "Review frame sequence output before deployment.",
            }
        ],
        "suspected_causes": ["Temporal instability"],
        "recommendations": ["Review adjacent-frame output."],
    }

    text = generate_compare_markdown(compare_result, judgement, guard_analysis=guard_analysis)

    assert "- status: warning" in text
    assert "- guard_verdict: review_required" in text
    assert "- primary_reason: Temporal consistency should be reviewed before deployment." in text
    assert "runtime_result_path: `results/candidate.json`" in text
    assert "### Guard Evidence" in text
    assert "frame_to_frame_detection_count_cv" in text
    assert "Detection count variance exceeds review threshold." in text
    assert (
        "why_it_matters: Temporal evidence explains whether the runtime output is "
        "stable enough to review."
    ) in text
    assert "suspected_causes: frame_jitter, scheduler_contention" in text


def test_generate_compare_html_includes_primary_metric_summary_and_thresholds():
    compare_result = make_compare_result()
    judgement = make_judgement()

    html = generate_compare_html(compare_result, judgement)

    assert "<title>EdgeBench Compare Report</title>" in html
    assert "Primary metric" in html
    assert "top1_accuracy" in html
    assert "Synthetic summary for report generator testing." in html
    assert "latency_improve_threshold" in html
    assert "/tmp/base.engine" in html
    assert "/tmp/new.engine" in html


def test_generate_compare_html_includes_cross_precision_warning_and_detection_metric():
    compare_result = make_compare_result(
        comparison_mode="cross_precision",
        base_precision="fp16",
        new_precision="int8",
        accuracy_task="detection",
        primary_metric_name="map50",
        accuracy_metrics={
            "map50": {
                "base": 0.7791,
                "new": 0.7977,
                "delta": 0.0186,
                "delta_pct": 2.3874,
                "delta_pp": 1.86,
            },
            "f1_score": {
                "base": 0.8000,
                "new": 0.8129,
                "delta": 0.0129,
                "delta_pct": 1.6125,
                "delta_pp": 1.29,
            },
        },
    )
    judgement = make_judgement(
        comparison_mode="cross_precision",
        precision_match=False,
        overall="tradeoff_faster",
        accuracy="improvement",
        tradeoff_risk="acceptable_tradeoff",
    )

    html = generate_compare_html(compare_result, judgement)

    assert "Cross-precision comparison detected." in html
    assert "fp16_vs_int8" in html
    assert "map50" in html
    assert "f1_score" in html
    assert "acceptable_tradeoff" in html


def test_generate_compare_html_includes_notes_list_items():
    compare_result = make_compare_result()
    judgement = make_judgement()

    html = generate_compare_html(compare_result, judgement)

    assert "<li>Synthetic note 1</li>" in html
    assert "<li>Synthetic note 2</li>" in html


def test_generate_compare_html_includes_guard_analysis_section():
    compare_result = make_compare_result()
    judgement = make_judgement()
    guard_analysis = {
        "status": "warning",
        "confidence": 0.7,
        "anomalies": ["insufficient_precision_speedup"],
        "suspected_causes": ["precision_speedup_not_observed"],
        "recommendations": ["Review runtime provenance."],
    }

    html = generate_compare_html(compare_result, judgement, guard_analysis=guard_analysis)

    assert "Guard Analysis" in html
    assert "insufficient_precision_speedup" in html
    assert "Review runtime provenance." in html


def test_generate_compare_html_includes_deployment_decision_section():
    compare_result = make_compare_result()
    judgement = make_judgement()
    deployment_decision = {
        "policy_version": "inferedge-lab-decision-policy-v1",
        "decision": "deployable",
        "reason": "Lab judgement is favorable and Guard analysis passed.",
        "lab_overall": "improvement",
        "guard_status": "ok",
        "recommended_action": "Deployment can proceed with normal rollout monitoring.",
        "triggered_rules": ["guard_ok_lab_favorable_deployable"],
        "policy_summary": [
            {
                "rule": "guard_ok_lab_favorable_deployable",
                "effect": "deployable",
                "description": "Lab comparison is favorable and AIGuard passed.",
            }
        ],
    }

    html = generate_compare_html(compare_result, judgement, deployment_decision=deployment_decision)

    assert "Deployment Decision" in html
    assert "inferedge-lab-decision-policy-v1" in html
    assert "deployable" in html
    assert "Deployment can proceed with normal rollout monitoring." in html
    assert "guard_ok_lab_favorable_deployable" in html
    assert "Decision Policy Summary" in html
    assert "Lab comparison is favorable and AIGuard passed." in html


def test_generate_compare_html_includes_edgeenv_regression_evidence():
    compare_result = make_compare_result()
    judgement = make_judgement()

    html = generate_compare_html(
        compare_result,
        judgement,
        edgeenv_regression=make_edgeenv_regression(),
    )

    assert "Runtime Regression Evidence" in html
    assert "EdgeEnv Runtime Regression Monitor" in html
    assert "same-condition" in html
    assert "mean_delta_pct" in html
    assert "+18.40%" in html
    assert "p99_latency_high" in html
    assert "Runtime Telemetry Context" in html
    assert "edgeenv.runtime-telemetry-history.v1" in html
    assert "history_telemetry_coverage" in html
    assert "candidate=queue_depth" in html
    assert "history_execution_sequence_id" in html
    assert "synthetic_local_fixture" in html
    assert "coverage_missing_fields" in html
    assert "0.6667" in html
    assert "queue_depth" in html
    assert "Runtime telemetry coverage gaps" in html
    assert "Runtime telemetry evidence gaps" in html
    assert "not cloud monitoring, ranking, or production observability" in html


def test_generate_compare_html_summarizes_orchestrator_context_risk():
    compare_result = make_compare_result()
    judgement = make_judgement()

    html = generate_compare_html(
        compare_result,
        judgement,
        guard_analysis=make_runtime_operation_guard_analysis(),
        edgeenv_regression=make_edgeenv_regression_with_orchestrator_context(),
    )

    assert "Runtime Intelligence Risk Summary" in html
    assert "Orchestrator operation feed context" in html
    assert "Orchestrator context attached runs" in html
    assert "runtime_queue_overload, runtime_thermal_instability" in html
    assert "AIGuard Orchestrator context handoff" in html
    assert "AIGuard history seed run_config markers" in html
    assert (
        "baseline/candidate=shape=1x640x640, input_mode=dummy, "
        "input_preprocess=none, power_mode=unknown, jetson_clocks=unknown, "
        "warmup=1, runs=10"
    ) in html
    assert "supplemental operation evidence" in html


def test_generate_compare_html_includes_diagnosis_guard_evidence():
    compare_result = make_compare_result()
    judgement = make_judgement()
    guard_analysis = {
        "schema_version": "inferedge-aiguard-diagnosis-v1",
        "source": {
            "runtime_result_path": "results/candidate.json",
            "model_contract_path": "model_contract.json",
        },
        "guard_verdict": "blocked",
        "severity": "high",
        "confidence": 0.91,
        "primary_reason": "Zero-detection frames exceed threshold.",
        "evidence": [
            {
                "type": "temporal_consistency",
                "metric_name": "zero_detection_frame_ratio",
                "observed_value": 0.5,
                "baseline_value": None,
                "threshold": 0.3,
                "severity": "high",
                "status": "failed",
                "explanation": "Zero-detection frame ratio exceeds blocked threshold.",
                "why_it_matters": (
                    "Detection disappearance can make an otherwise fast deployment unsafe."
                ),
                "suspected_causes": ["preprocess_mismatch", "runtime_output_instability"],
                "recommendation": "Do not deploy until disappearance is explained.",
            }
        ],
        "suspected_causes": ["Detection disappearance"],
        "recommendations": ["Review frame sequence."],
    }

    html = generate_compare_html(compare_result, judgement, guard_analysis=guard_analysis)

    assert "guard_verdict" in html
    assert "blocked" in html
    assert "runtime_result_path" in html
    assert "Guard Evidence" in html
    assert "zero_detection_frame_ratio" in html
    assert "Zero-detection frame ratio exceeds blocked threshold." in html
    assert "why_it_matters" in html
    assert "Detection disappearance can make an otherwise fast deployment unsafe." in html
    assert "preprocess_mismatch, runtime_output_instability" in html
