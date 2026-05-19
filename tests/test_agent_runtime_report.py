from __future__ import annotations

import json

import pytest

from inferedgelab.commands.agent_runtime_report import agent_runtime_report_cmd
from inferedgelab.services.agent_runtime_report import (
    AGENT_RUNTIME_POLICY_VERSION,
    AGENT_RUNTIME_REPORT_SCHEMA_VERSION,
    build_agent_runtime_reliability_markdown,
    build_agent_runtime_reliability_report,
    compute_agent_runtime_metrics,
    load_agent_runtime_reliability_bundle,
)


def orchestration_summary() -> dict:
    return {
        "schema_version": "inferedge-orchestration-summary-v1",
        "run": {
            "name": "agent_3_workload_sustained_high_load",
            "scenario_mode": "sustained_high_load",
            "frame_interval_ms": 5.0,
        },
        "agent_runtime_summary": {
            "schema_version": "inferedge-orchestration-summary-v1",
            "source_contracts": {
                "forge_agent_manifest": "inferedge-agent-manifest-v1",
                "runtime_agent_result": "inferedge-runtime-agent-task-v1",
            },
            "agents": {
                "safety_monitor_agent": {
                    "agent_id": "safety_monitor_agent",
                    "agent_type": "safety",
                    "priority": 100,
                    "latency_budget_ms": 20.0,
                    "fallback_policy": "protect",
                },
                "vision_agent": {
                    "agent_id": "vision_agent",
                    "agent_type": "vision",
                    "priority": 90,
                    "latency_budget_ms": 33.0,
                    "fallback_policy": "drop_stale",
                },
            },
            "totals": {
                "executed_count": 10,
                "dropped_count": 14,
                "deadline_missed_count": 1,
                "fallback_count": 14,
                "policy_decision_count": 14,
                "overload_event_count": 14,
            },
        },
        "sustained_runtime_summary": {
            "schema_version": "inferedge-orchestrator-sustained-summary-v1",
            "scenario_mode": "sustained_high_load",
            "queue_depth_sample_count": 1,
            "latency_sample_count": 1,
            "max_total_queue_depth": 6,
        },
        "queue_depth_timeline": [
            {
                "cycle": 1,
                "stage": "before_policy",
                "queue_depth": {
                    "vision_agent": 4,
                    "voice_command_agent": 2,
                    "safety_monitor_agent": 0,
                },
                "total_queue_depth": 6,
            }
        ],
        "latency_timeline": [
            {
                "agent_id": "vision_agent",
                "task_id": "task_vision_agent",
                "latency_ms": 41.0,
                "latency_budget_ms": 33.0,
                "deadline_missed": True,
            }
        ],
        "policy_decision_log": [
            {
                "agent_id": "vision_agent",
                "decision": "load_shedding",
                "reason": "queue_backlog_threshold_exceeded",
                "decision_reason": "queue_backlog_threshold_exceeded",
                "total_backlog_before": 6,
                "backlog_threshold": 3,
                "queue_depth_snapshot": {
                    "vision_agent": 4,
                    "voice_command_agent": 2,
                    "safety_monitor_agent": 0,
                },
                "protected_agent_id": "safety_monitor_agent",
            }
        ],
        "queue_state_summary": {
            "schema_version": "inferedge-orchestrator-queue-state-v1",
            "sample_count": 1,
            "overload_backlog_threshold": 3,
            "max_total_queue_depth": 6,
            "average_total_queue_depth": 6.0,
            "final_queue_depth": {
                "vision_agent": 4,
                "voice_command_agent": 2,
                "safety_monitor_agent": 0,
            },
            "max_queue_depth_by_task": {
                "vision_agent": 4,
                "voice_command_agent": 2,
                "safety_monitor_agent": 0,
            },
            "queue_pressure_state": "overloaded",
        },
        "worker_health_snapshot": {
            "schema_version": "inferedge-orchestrator-worker-health-v1",
            "workers": {
                "safety_monitor_agent": {
                    "task": "safety_monitor_agent",
                    "agent_id": "safety_monitor_agent",
                    "task_id": "task_safety_monitor_agent",
                    "agent_type": "safety",
                    "worker": "dummy",
                    "health_state": "healthy",
                    "executed_count": 2,
                    "dropped_count": 0,
                    "deadline_missed_count": 0,
                    "fallback_count": 0,
                    "mean_latency_ms": 6.0,
                },
                "vision_agent": {
                    "task": "vision_agent",
                    "agent_id": "vision_agent",
                    "task_id": "task_vision_agent",
                    "agent_type": "vision",
                    "worker": "dummy",
                    "health_state": "degraded",
                    "executed_count": 8,
                    "dropped_count": 14,
                    "deadline_missed_count": 1,
                    "fallback_count": 14,
                    "mean_latency_ms": 41.0,
                },
            },
        },
        "runtime_event_summary": {
            "schema_version": "inferedge-orchestrator-runtime-event-summary-v1",
            "event_count": 4,
            "event_type_counts": {
                "queue_snapshot": 1,
                "policy_decision": 1,
                "drop": 1,
                "execution": 1,
            },
        },
        "runtime_event_timeline": [
            {
                "event_index": 0,
                "event_type": "queue_snapshot",
                "reason": "queue_depth_sampled",
            },
            {
                "event_index": 1,
                "event_type": "policy_decision",
                "agent_id": "vision_agent",
                "task_id": "task_vision_agent",
                "reason": "queue_backlog_threshold_exceeded",
            },
            {
                "event_index": 2,
                "event_type": "drop",
                "agent_id": "vision_agent",
                "task_id": "task_vision_agent",
                "reason": "load_shedding_backlog_threshold_exceeded",
            },
            {
                "event_index": 3,
                "event_type": "execution",
                "agent_id": "vision_agent",
                "task_id": "task_vision_agent",
                "reason": "deadline_missed",
            },
        ],
    }


def guard_analysis() -> dict:
    return {
        "schema_version": "inferedge-aiguard-diagnosis-v1",
        "guard_verdict": "blocked",
        "severity": "high",
        "confidence": 0.88,
        "primary_reason": "drop_rate indicates runtime reliability risk.",
        "evidence": [
            {
                "type": "excessive_drop_rate",
                "metric_name": "drop_rate",
                "observed_value": 14 / 24,
                "baseline_value": None,
                "threshold": 0.2,
                "delta": None,
                "delta_pct": None,
                "increase_factor": None,
                "severity": "high",
                "status": "failed",
                "explanation": "Drop rate crossed threshold.",
                "why_it_matters": "Dropped work may become stale.",
                "suspected_causes": ["queue_backlog"],
                "recommendation": "Tune scheduling policy.",
                "raw_context": {},
            }
        ],
        "created_at": "2026-05-17T00:00:00Z",
    }


def runtime_result_with_operation_evidence() -> dict:
    return {
        "schema_version": "inferedge-runtime-result-v1",
        "compare_key": "yolov8n__b1__h224w224__fp32",
        "backend_key": "onnxruntime__cpu",
        "status": "skipped",
        "success": False,
        "runtime_health_snapshot": {
            "schema_version": "inferedge-runtime-health-v1",
            "status": "degraded",
            "engine_backend": "onnxruntime",
            "device": "cpu",
            "input_mode": "dummy",
            "input_preprocess": "synthetic",
            "warmup": 1,
            "runs": 1,
            "run_once": False,
            "success": False,
            "latency_mean_ms": 0.0,
            "latency_p95_ms": 0.0,
            "latency_p99_ms": 0.0,
            "fps": 0.0,
            "power_mode": "unknown",
            "jetson_clocks": "unknown",
            "timeout_policy": "not_configured",
            "timeout_observed": False,
        },
        "runtime_error_classification": {
            "schema_version": "inferedge-runtime-error-v1",
            "status": "classified",
            "category": "runtime_execution_skipped",
            "message": "backend is not available in this build",
            "timeout_observed": False,
            "retryable": False,
        },
        "runtime_events": [
            {
                "type": "runtime_configured",
                "status": "ok",
                "engine_backend": "onnxruntime",
                "device": "cpu",
                "input_mode": "dummy",
            },
            {
                "type": "benchmark_completed",
                "status": "skipped",
                "success": False,
                "warmup": 1,
                "runs": 1,
                "mean_ms": 0.0,
            },
            {
                "type": "runtime_error_classified",
                "status": "classified",
                "category": "runtime_execution_skipped",
            },
        ],
    }


def sustained_guard_analysis() -> dict:
    data = guard_analysis()
    data["evidence"].append(
        {
            "type": "sustained_overload_risk",
            "metric_name": "max_total_queue_depth",
            "observed_value": 6,
            "baseline_value": None,
            "threshold": 3,
            "delta": None,
            "delta_pct": None,
            "increase_factor": None,
            "severity": "medium",
            "status": "failed",
            "explanation": "Queue depth grew under sustained high-load mode.",
            "why_it_matters": "Queue growth indicates multi-agent runtime pressure.",
            "suspected_causes": ["sustained_multi_agent_overload"],
            "recommendation": "Lower producer rate or tighten stale-frame drop policy.",
            "raw_context": {
                "scenario_mode": "sustained_high_load",
                "queue_depth_sample_count": 1,
                "latency_sample_count": 1,
            },
        }
    )
    data["suspected_causes"] = [
        "queue_backlog",
        "sustained_multi_agent_overload",
    ]
    data["recommendations"] = [
        "Tune scheduling policy.",
        "Lower producer rate or tighten stale-frame drop policy.",
    ]
    return data


def test_compute_agent_runtime_metrics_from_orchestrator_summary():
    metrics = compute_agent_runtime_metrics(orchestration_summary())

    assert metrics["deadline_miss_rate"] == pytest.approx(0.1)
    assert metrics["drop_rate"] == pytest.approx(14 / 24)
    assert metrics["fallback_rate"] == pytest.approx(14 / 24)
    assert metrics["queue_backlog_policy_decision_count"] == 1
    assert metrics["scenario_mode"] == "sustained_high_load"
    assert metrics["max_total_queue_depth"] == 6
    assert metrics["queue_depth_sample_count"] == 1
    assert metrics["latency_sample_count"] == 1
    assert metrics["top_policy_decision_reason"] == "queue_backlog_threshold_exceeded"
    assert metrics["policy_decision_reasons"] == {
        "queue_backlog_threshold_exceeded": 1
    }
    assert metrics["queue_pressure_state"] == "overloaded"
    assert metrics["runtime_event_count"] == 4
    assert metrics["runtime_event_type_counts"] == {
        "queue_snapshot": 1,
        "policy_decision": 1,
        "drop": 1,
        "execution": 1,
    }
    assert metrics["degraded_worker_count"] == 1
    assert metrics["healthy_worker_count"] == 1


def test_agent_runtime_report_blocks_when_guard_blocks():
    report = build_agent_runtime_reliability_report(
        orchestration_summary=orchestration_summary(),
        guard_analysis=sustained_guard_analysis(),
        runtime_result=runtime_result_with_operation_evidence(),
    )

    decision = report["agent_deployment_decision"]
    assert report["schema_version"] == AGENT_RUNTIME_REPORT_SCHEMA_VERSION
    assert report["contracts"]["orchestration_summary"] == (
        "inferedge-orchestration-summary-v1"
    )
    assert report["contracts"]["aiguard_guard_analysis"] == (
        "inferedge-aiguard-diagnosis-v1"
    )
    assert report["contracts"]["runtime_result"] == "inferedge-runtime-result-v1"
    assert decision["policy_version"] == AGENT_RUNTIME_POLICY_VERSION
    assert decision["decision"] == "blocked"
    assert "guard_blocked_runtime_block" in decision["triggered_rules"]
    assert "drop_rate_block" in decision["triggered_rules"]
    assert "sustained_overload_review" in decision["triggered_rules"]
    assert report["guard_summary"]["guard_verdict"] == "blocked"
    assert "sustained_overload_risk" in report["guard_summary"]["evidence_types"]
    assert report["agent_runtime_summary"]["timeline_summary"] == {
        "scenario_mode": "sustained_high_load",
        "queue_depth_sample_count": 1,
        "latency_sample_count": 1,
        "max_total_queue_depth": 6,
        "top_policy_decision_reason": "queue_backlog_threshold_exceeded",
        "policy_decision_reasons": {"queue_backlog_threshold_exceeded": 1},
        "has_queue_depth_timeline": True,
        "has_latency_timeline": True,
    }
    assert {
        item["type"] for item in report["runtime_reliability_evidence"]
    } == {"excessive_drop_rate", "sustained_overload_risk"}
    operation_context = report["agent_runtime_summary"]["operation_context"]
    assert operation_context["queue_state_summary"]["queue_pressure_state"] == "overloaded"
    assert operation_context["worker_health_counts"] == {
        "healthy": 1,
        "degraded": 1,
    }
    assert operation_context["runtime_event_summary"]["event_type_counts"]["drop"] == 1
    assert operation_context["runtime_event_timeline_count"] == 4
    assert operation_context["runtime_event_timeline_sample"][1]["event_type"] == (
        "policy_decision"
    )
    runtime_context = report["agent_runtime_summary"]["runtime_result_context"]
    assert runtime_context["source_schema_version"] == "inferedge-runtime-result-v1"
    assert runtime_context["runtime_health_snapshot"]["status"] == "degraded"
    assert runtime_context["runtime_error_classification"]["category"] == (
        "runtime_execution_skipped"
    )
    assert runtime_context["runtime_event_summary"]["event_count"] == 3
    assert runtime_context["runtime_event_summary"]["event_type_counts"] == {
        "runtime_configured": 1,
        "benchmark_completed": 1,
        "runtime_error_classified": 1,
    }


def test_agent_runtime_report_keeps_legacy_orchestrator_summary_compatible():
    legacy_summary = orchestration_summary()
    legacy_summary.pop("queue_state_summary")
    legacy_summary.pop("worker_health_snapshot")
    legacy_summary.pop("runtime_event_summary")
    legacy_summary.pop("runtime_event_timeline")

    report = build_agent_runtime_reliability_report(
        orchestration_summary=legacy_summary,
        guard_analysis=sustained_guard_analysis(),
    )

    operation_context = report["agent_runtime_summary"]["operation_context"]
    assert operation_context["queue_state_summary"]["schema_version"] is None
    assert operation_context["queue_state_summary"]["max_total_queue_depth"] == 6
    assert operation_context["worker_health_snapshot"]["workers"] == {}
    assert operation_context["runtime_event_summary"]["event_count"] == 0
    assert report["agent_deployment_decision"]["decision"] == "blocked"


def test_agent_runtime_report_markdown_contains_sections():
    report = build_agent_runtime_reliability_report(
        orchestration_summary=orchestration_summary(),
        guard_analysis=sustained_guard_analysis(),
        runtime_result=runtime_result_with_operation_evidence(),
    )
    markdown = build_agent_runtime_reliability_markdown(report)

    assert "# InferEdge Agent Runtime Reliability Report" in markdown
    assert "Agent Runtime Summary" in markdown
    assert "Runtime Reliability Metrics" in markdown
    assert "Orchestrator Operation Context" in markdown
    assert "Queue State" in markdown
    assert "Worker Health" in markdown
    assert "Runtime Event Summary" in markdown
    assert "Runtime Result Operation Evidence" in markdown
    assert "runtime_execution_skipped" in markdown
    assert "queue_pressure_state" in markdown
    assert "policy_decision" in markdown
    assert "AIGuard Runtime Reliability Evidence" in markdown
    assert "Lab Agent Deployment Decision" in markdown
    assert "guard_blocked_runtime_block" in markdown
    assert "sustained_overload_risk" in markdown
    assert "max_total_queue_depth" in markdown
    assert "not a production cloud orchestration dashboard" in markdown


def test_agent_runtime_report_loads_committed_fixtures():
    report = load_agent_runtime_reliability_bundle(
        orchestration_summary_path="examples/agent_runtime/agent_3_orchestration_summary.json",
        guard_analysis_path="examples/agent_runtime/aiguard_runtime_guard_analysis.json",
    )

    assert report["agent_deployment_decision"]["decision"] == "blocked"
    assert report["agent_runtime_summary"]["metrics"]["drop_rate"] == pytest.approx(14 / 24)
    assert len(report["agent_runtime_summary"]["agents"]) == 3


def test_agent_runtime_report_command_outputs_json(tmp_path, capsys):
    runtime_result_path = tmp_path / "runtime_operation_result.json"
    with runtime_result_path.open("w", encoding="utf-8") as file:
        json.dump(runtime_result_with_operation_evidence(), file)

    agent_runtime_report_cmd(
        orchestration_summary="examples/agent_runtime/agent_3_orchestration_summary.json",
        guard_analysis="examples/agent_runtime/aiguard_runtime_guard_analysis.json",
        runtime_result=str(runtime_result_path),
        format="json",
        output="",
    )
    out = capsys.readouterr().out
    report = json.loads(out)

    assert report["schema_version"] == AGENT_RUNTIME_REPORT_SCHEMA_VERSION
    assert report["agent_deployment_decision"]["decision"] == "blocked"
    runtime_context = report["agent_runtime_summary"]["runtime_result_context"]
    assert runtime_context["runtime_health_snapshot"]["status"] == "degraded"
