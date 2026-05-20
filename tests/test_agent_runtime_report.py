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


def runtime_operation_guard_analysis() -> dict:
    data = guard_analysis()
    data["primary_reason"] = (
        "runtime_error_severity indicates runtime reliability risk."
    )
    data["evidence"].extend(
        [
            {
                "type": "runtime_backend_unavailable",
                "metric_name": "engine_available",
                "observed_value": 0,
                "baseline_value": None,
                "threshold": 1,
                "delta": None,
                "delta_pct": None,
                "increase_factor": None,
                "severity": "high",
                "status": "failed",
                "explanation": "Runtime could not confirm backend availability.",
                "why_it_matters": (
                    "Runtime backend availability is required before using the "
                    "result as deployment evidence."
                ),
                "suspected_causes": ["backend_runtime_unavailable"],
                "recommendation": "Check backend installation and engine load logs.",
                "raw_context": {
                    "runtime_operation": {
                        "engine_available": False,
                        "retry_hint": "check_backend_availability",
                    }
                },
            },
            {
                "type": "runtime_latency_budget_overrun",
                "metric_name": "latency_budget_exceeded",
                "observed_value": 1,
                "baseline_value": None,
                "threshold": 50.0,
                "delta": 22.5,
                "delta_pct": 0.45,
                "increase_factor": None,
                "severity": "high",
                "status": "failed",
                "explanation": "Runtime latency exceeded the configured budget.",
                "why_it_matters": (
                    "Latency budget overrun means the runtime result did not "
                    "satisfy the expected timing contract."
                ),
                "suspected_causes": ["runtime_latency_spike"],
                "recommendation": "Review runtime event log and fallback policy.",
                "raw_context": {
                    "runtime_operation": {
                        "latency_budget_ms": 50.0,
                        "observed_mean_ms": 72.5,
                    }
                },
            },
        ]
    )
    data["suspected_causes"] = [
        "queue_backlog",
        "backend_runtime_unavailable",
        "runtime_latency_spike",
    ]
    data["recommendations"] = [
        "Tune scheduling policy.",
        "Check backend installation and engine load logs.",
        "Review runtime event log and fallback policy.",
    ]
    return data


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


def remote_dispatch_result() -> dict:
    return {
        "schema_version": "inferedge-remote-dispatch-result-v1",
        "dispatch_status": "accepted",
        "selected_worker_id": "jetson-nano-01",
        "decision_reason": (
            "selected online worker matching backend/device requirements"
        ),
        "remote_execution": {
            "mode": "file_contract_starter",
            "production_remote_execution": False,
            "registry_path": "examples/remote_worker_registry.json",
            "request_path": "examples/remote_task_request.json",
        },
        "remote_execution_plan": {
            "schema_version": "inferedge-remote-execution-plan-v1",
            "mode": "plan_only",
            "network_execution_performed": False,
            "transport": "file_contract",
            "endpoint_type": "file_contract",
            "selected_worker_id": "jetson-nano-01",
            "task_id": "task_vision_001",
            "agent_id": "vision_agent",
        },
        "worker_selection": {
            "schema_version": "inferedge-remote-worker-selection-v1",
            "selected_worker_id": "jetson-nano-01",
            "candidate_worker_ids": ["jetson-nano-01"],
            "fallback_worker_ids": [],
            "evaluations": [
                {
                    "worker_id": "jetson-nano-01",
                    "eligible": True,
                    "status": "online",
                    "health_state": "healthy",
                    "endpoint_type": "file_contract",
                    "decision_reason": "eligible",
                }
            ],
        },
        "retry_fallback_plan": {
            "schema_version": "inferedge-remote-retry-fallback-plan-v1",
            "max_attempts": 1,
            "fallback_on": ["timeout", "worker_unhealthy", "runtime_error"],
            "primary_worker_id": "jetson-nano-01",
            "fallback_worker_ids": [],
            "execution_performed": False,
        },
        "runtime_events": [
            {
                "event": "remote_dispatch_selected",
                "task_id": "task_vision_001",
                "agent_id": "vision_agent",
                "selected_worker_id": "jetson-nano-01",
                "reason": (
                    "selected online worker matching backend/device requirements"
                ),
            }
        ],
    }


def remote_dispatch_failed_execution_result() -> dict:
    data = remote_dispatch_result()
    data["remote_execution_plan"] = {
        **data["remote_execution_plan"],
        "mode": "execute_plan",
        "network_execution_performed": True,
        "transport": "http",
        "endpoint_type": "http",
    }
    data["remote_execution_result"] = {
        "status": "failed",
        "transport": "http",
        "execution_requested": True,
        "execution_performed": True,
        "fallback_execution_performed": False,
        "error_category": "connection_error",
        "error_message": "worker endpoint refused connection",
        "http_status": None,
        "exit_code": None,
        "elapsed_ms": 42.5,
        "note": "starter evidence only; not production remote execution",
    }
    data["runtime_events"].append(
        {
            "event": "remote_execution_failed",
            "task_id": "task_vision_001",
            "agent_id": "vision_agent",
            "selected_worker_id": "jetson-nano-01",
            "error_category": "connection_error",
        }
    )
    return data


def remote_dispatch_fallback_recovered_result() -> dict:
    data = remote_dispatch_failed_execution_result()
    data["retry_fallback_plan"].update(
        {
            "fallback_execution_performed": True,
            "fallback_attempted_worker_ids": ["jetson-fallback"],
            "fallback_final_status": "succeeded",
            "last_execution_status": "succeeded",
        }
    )
    data["fallback_execution_result"] = {
        "schema_version": "inferedge-remote-fallback-execution-v1",
        "fallback_requested": True,
        "fallback_reason": "connection_error",
        "primary_worker_id": "jetson-nano-01",
        "attempted_worker_ids": ["jetson-fallback"],
        "final_status": "succeeded",
        "attempts": [
            {
                "schema_version": "inferedge-remote-execution-result-v1",
                "execution_requested": True,
                "execution_performed": True,
                "production_remote_execution": False,
                "status": "succeeded",
                "transport": "http",
                "selected_worker_id": "jetson-fallback",
                "task_id": "task_vision_001",
                "agent_id": "vision_agent",
                "http_status": 200,
                "fallback_attempt": 1,
                "fallback_for_worker_id": "jetson-nano-01",
                "response_json": {"status": "ok"},
            }
        ],
        "production_remote_execution": False,
    }
    data["runtime_events"].append(
        {
            "event": "remote_fallback_execution_completed",
            "task_id": "task_vision_001",
            "agent_id": "vision_agent",
            "selected_worker_id": "jetson-fallback",
            "status": "succeeded",
        }
    )
    return data


def remote_execution_guard_analysis() -> dict:
    data = passing_guard_analysis()
    data.update(
        {
            "guard_verdict": "review_required",
            "severity": "medium",
            "confidence": 0.86,
            "primary_reason": (
                "Remote execution starter reported connection_error."
            ),
        }
    )
    data["evidence"] = [
        {
            "type": "remote_execution_failed",
            "metric_name": "remote_execution_failed",
            "observed_value": 1,
            "baseline_value": None,
            "threshold": 0,
            "delta": None,
            "delta_pct": None,
            "increase_factor": None,
            "severity": "medium",
            "status": "failed",
            "explanation": "Remote execution starter failed before task completion.",
            "why_it_matters": (
                "A selected worker that cannot execute the task is deployment "
                "review evidence."
            ),
            "suspected_causes": ["remote_worker_unreachable"],
            "recommendation": "Check worker endpoint, tunnel, or SSH access.",
            "raw_context": {
                "remote_execution": {
                    "status": "failed",
                    "transport": "http",
                    "error_category": "connection_error",
                }
            },
        }
    ]
    return data


def remote_fallback_recovered_guard_analysis() -> dict:
    data = remote_execution_guard_analysis()
    data["primary_reason"] = (
        "Remote execution starter failed on the primary worker and recovered via fallback."
    )
    data["evidence"].append(
        {
            "type": "remote_execution_recovered_by_fallback",
            "metric_name": "fallback_final_status",
            "observed_value": "succeeded",
            "baseline_value": "primary_execution_succeeded_without_fallback",
            "threshold": "succeeded",
            "delta": None,
            "delta_pct": None,
            "increase_factor": None,
            "severity": "medium",
            "status": "warning",
            "explanation": (
                "Fallback recovered explicit starter execution after the primary "
                "remote worker failed."
            ),
            "why_it_matters": (
                "Fallback recovery proves a resilience path exists, but the primary "
                "worker path is not clean operation evidence."
            ),
            "suspected_causes": [
                "primary_worker_unstable",
                "connection_error",
                "remote_worker_endpoint_unreachable",
            ],
            "recommendation": (
                "Keep fallback enabled and inspect the primary worker before relying "
                "on this path for deployment."
            ),
            "raw_context": {
                "remote_dispatch": {
                    "fallback_final_status": "succeeded",
                    "fallback_attempted_worker_ids": ["jetson-fallback"],
                }
            },
        }
    )
    return data


def runtime_result_with_timeout_observed() -> dict:
    data = runtime_result_with_operation_evidence()
    data["status"] = "completed"
    data["success"] = True
    data["runtime_health_snapshot"].update(
        {
            "status": "degraded",
            "success": True,
            "latency_mean_ms": 12.5,
            "latency_p95_ms": 15.0,
            "latency_p99_ms": 18.0,
            "fps": 80.0,
            "timeout_policy": "latency_threshold",
            "timeout_budget_ms": 10,
            "timeout_observed": True,
        }
    )
    data["runtime_error_classification"].update(
        {
            "category": "runtime_timeout_observed",
            "message": "mean latency exceeded configured timeout observation threshold",
            "timeout_observed": True,
            "retryable": True,
        }
    )
    data["runtime_events"][-1].update(
        {
            "category": "runtime_timeout_observed",
            "timeout_policy": "latency_threshold",
            "timeout_observed": True,
        }
    )
    return data


def quiet_orchestration_summary() -> dict:
    data = orchestration_summary()
    data["agent_runtime_summary"]["totals"] = {
        "executed_count": 10,
        "dropped_count": 0,
        "deadline_missed_count": 0,
        "fallback_count": 0,
        "policy_decision_count": 0,
        "overload_event_count": 0,
    }
    data["sustained_runtime_summary"].update(
        {
            "scenario_mode": "normal",
            "queue_depth_sample_count": 1,
            "latency_sample_count": 1,
            "max_total_queue_depth": 0,
        }
    )
    data["queue_depth_timeline"] = [
        {
            "cycle": 1,
            "stage": "before_policy",
            "queue_depth": {
                "vision_agent": 0,
                "voice_command_agent": 0,
                "safety_monitor_agent": 0,
            },
            "total_queue_depth": 0,
        }
    ]
    data["latency_timeline"] = []
    data["policy_decision_log"] = []
    data["queue_state_summary"].update(
        {
            "max_total_queue_depth": 0,
            "average_total_queue_depth": 0.0,
            "final_queue_depth": {
                "vision_agent": 0,
                "voice_command_agent": 0,
                "safety_monitor_agent": 0,
            },
            "max_queue_depth_by_task": {
                "vision_agent": 0,
                "voice_command_agent": 0,
                "safety_monitor_agent": 0,
            },
            "queue_pressure_state": "normal",
        }
    )
    data["runtime_event_summary"] = {
        "schema_version": "inferedge-orchestrator-runtime-event-summary-v1",
        "event_count": 0,
        "event_type_counts": {},
    }
    data["runtime_event_timeline"] = []
    return data


def passing_guard_analysis() -> dict:
    return {
        "schema_version": "inferedge-aiguard-diagnosis-v1",
        "status": "pass",
        "guard_verdict": "pass",
        "severity": "low",
        "confidence": 0.96,
        "primary_reason": "Runtime reliability guard evidence stayed within thresholds.",
        "evidence": [],
        "created_at": "2026-05-17T00:00:00Z",
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
        guard_analysis=runtime_operation_guard_analysis(),
        runtime_result=runtime_result_with_operation_evidence(),
        remote_dispatch=remote_dispatch_result(),
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
    assert report["contracts"]["remote_dispatch"] == (
        "inferedge-remote-dispatch-result-v1"
    )
    assert decision["policy_version"] == AGENT_RUNTIME_POLICY_VERSION
    assert decision["decision"] == "blocked"
    assert "guard_blocked_runtime_block" in decision["triggered_rules"]
    assert "drop_rate_block" in decision["triggered_rules"]
    assert "sustained_overload_review" in decision["triggered_rules"]
    assert "runtime_operation_guard_block" in decision["triggered_rules"]
    assert report["guard_summary"]["guard_verdict"] == "blocked"
    assert "runtime_backend_unavailable" in report["guard_summary"]["evidence_types"]
    runtime_guard = report["runtime_operation_guard_summary"]
    assert runtime_guard["evidence_count"] == 2
    assert runtime_guard["failed_count"] == 2
    assert runtime_guard["retry_hints"] == ["check_backend_availability"]
    assert {
        item["type"] for item in runtime_guard["evidence"]
    } == {
        "runtime_backend_unavailable",
        "runtime_latency_budget_overrun",
    }
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
    } == {
        "excessive_drop_rate",
        "runtime_backend_unavailable",
        "runtime_latency_budget_overrun",
    }
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
    remote_context = report["agent_runtime_summary"]["remote_dispatch_context"]
    assert remote_context["dispatch_status"] == "accepted"
    assert remote_context["selected_worker_id"] == "jetson-nano-01"
    assert remote_context["remote_execution"]["production_remote_execution"] is False
    assert remote_context["remote_execution_plan"]["mode"] == "plan_only"
    assert remote_context["remote_execution_plan"]["network_execution_performed"] is False
    assert remote_context["remote_execution_result"]["execution_performed"] is False
    assert remote_context["worker_selection"]["schema_version"] == (
        "inferedge-remote-worker-selection-v1"
    )
    assert remote_context["worker_evaluations"][0]["worker_id"] == "jetson-nano-01"


def test_agent_runtime_report_marks_runtime_timeout_as_review():
    report = build_agent_runtime_reliability_report(
        orchestration_summary=quiet_orchestration_summary(),
        guard_analysis=passing_guard_analysis(),
        runtime_result=runtime_result_with_timeout_observed(),
    )

    decision = report["agent_deployment_decision"]
    assert decision["decision"] == "review_required"
    assert "runtime_timeout_observed_review" in decision["triggered_rules"]
    assert "guard_blocked_runtime_block" not in decision["triggered_rules"]
    runtime_context = report["agent_runtime_summary"]["runtime_result_context"]
    assert runtime_context["runtime_timeout_observed"] is True
    assert runtime_context["runtime_health_snapshot"]["timeout_policy"] == (
        "latency_threshold"
    )

    markdown = build_agent_runtime_reliability_markdown(report)
    assert "runtime_timeout_observed" in markdown
    assert "latency_threshold" in markdown
    assert "runtime_timeout_observed_review" in markdown


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
        guard_analysis=runtime_operation_guard_analysis(),
        runtime_result=runtime_result_with_operation_evidence(),
        remote_dispatch=remote_dispatch_result(),
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
    assert "AIGuard Runtime Operation Evidence" in markdown
    assert "runtime_backend_unavailable" in markdown
    assert "runtime_latency_budget_overrun" in markdown
    assert "check_backend_availability" in markdown
    assert "Remote Dispatch Context" in markdown
    assert "Remote execution starter evidence" in markdown
    assert "jetson-nano-01" in markdown
    assert "plan_only" in markdown
    assert "network_execution_performed" in markdown
    assert "starter evidence only; not production remote execution" in markdown
    assert "retry_max_attempts" in markdown
    assert "runtime_execution_skipped" in markdown
    assert "queue_pressure_state" in markdown
    assert "policy_decision" in markdown
    assert "AIGuard Runtime Reliability Evidence" in markdown
    assert "Lab Agent Deployment Decision" in markdown
    assert "guard_blocked_runtime_block" in markdown
    assert "runtime_operation_guard_block" in markdown
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


def test_agent_runtime_report_surfaces_remote_execution_failure():
    report = build_agent_runtime_reliability_report(
        orchestration_summary=quiet_orchestration_summary(),
        guard_analysis=remote_execution_guard_analysis(),
        remote_dispatch=remote_dispatch_failed_execution_result(),
    )

    remote_context = report["agent_runtime_summary"]["remote_dispatch_context"]
    remote_result = remote_context["remote_execution_result"]
    decision = report["agent_deployment_decision"]

    assert remote_result["status"] == "failed"
    assert remote_result["transport"] == "http"
    assert remote_result["execution_requested"] is True
    assert remote_result["execution_performed"] is True
    assert remote_result["error_category"] == "connection_error"
    assert decision["decision"] == "review_required"
    assert "guard_warning_runtime_review" in decision["triggered_rules"]
    assert {
        item["type"] for item in report["runtime_reliability_evidence"]
    } == {"remote_execution_failed"}

    markdown = build_agent_runtime_reliability_markdown(report)
    assert "Remote execution starter evidence" in markdown
    assert "connection_error" in markdown
    assert "remote_execution_failed" in markdown
    assert "starter evidence only; not production remote execution" in markdown


def test_agent_runtime_report_surfaces_remote_fallback_recovery():
    report = build_agent_runtime_reliability_report(
        orchestration_summary=quiet_orchestration_summary(),
        guard_analysis=remote_fallback_recovered_guard_analysis(),
        remote_dispatch=remote_dispatch_fallback_recovered_result(),
    )

    remote_context = report["agent_runtime_summary"]["remote_dispatch_context"]
    fallback_context = remote_context["fallback_execution_result"]
    decision = report["agent_deployment_decision"]

    assert fallback_context["schema_version"] == (
        "inferedge-remote-fallback-execution-v1"
    )
    assert fallback_context["fallback_requested"] is True
    assert fallback_context["primary_worker_id"] == "jetson-nano-01"
    assert fallback_context["attempted_worker_ids"] == ["jetson-fallback"]
    assert fallback_context["final_status"] == "succeeded"
    assert len(fallback_context["attempts"]) == 1
    assert decision["decision"] == "review_required"
    assert "guard_warning_runtime_review" in decision["triggered_rules"]
    assert {
        item["type"] for item in report["runtime_reliability_evidence"]
    } == {
        "remote_execution_failed",
        "remote_execution_recovered_by_fallback",
    }

    markdown = build_agent_runtime_reliability_markdown(report)
    assert "Remote fallback starter evidence" in markdown
    assert "remote_execution_recovered_by_fallback" in markdown
    assert "jetson-fallback" in markdown
    recovery_evidence = next(
        item
        for item in report["runtime_reliability_evidence"]
        if item["type"] == "remote_execution_recovered_by_fallback"
    )
    assert "primary worker" in recovery_evidence["recommendation"]
    assert "production remote execution" in markdown


def test_agent_runtime_report_command_outputs_json(tmp_path, capsys):
    runtime_result_path = tmp_path / "runtime_operation_result.json"
    with runtime_result_path.open("w", encoding="utf-8") as file:
        json.dump(runtime_result_with_operation_evidence(), file)
    remote_dispatch_path = tmp_path / "remote_dispatch_result.json"
    with remote_dispatch_path.open("w", encoding="utf-8") as file:
        json.dump(remote_dispatch_result(), file)

    agent_runtime_report_cmd(
        orchestration_summary="examples/agent_runtime/agent_3_orchestration_summary.json",
        guard_analysis="examples/agent_runtime/aiguard_runtime_guard_analysis.json",
        runtime_result=str(runtime_result_path),
        remote_dispatch=str(remote_dispatch_path),
        format="json",
        output="",
    )
    out = capsys.readouterr().out
    report = json.loads(out)

    assert report["schema_version"] == AGENT_RUNTIME_REPORT_SCHEMA_VERSION
    assert report["agent_deployment_decision"]["decision"] == "blocked"
    runtime_context = report["agent_runtime_summary"]["runtime_result_context"]
    assert runtime_context["runtime_health_snapshot"]["status"] == "degraded"
    remote_context = report["agent_runtime_summary"]["remote_dispatch_context"]
    assert remote_context["selected_worker_id"] == "jetson-nano-01"
    assert remote_context["worker_selection"]["candidate_worker_ids"] == [
        "jetson-nano-01"
    ]
