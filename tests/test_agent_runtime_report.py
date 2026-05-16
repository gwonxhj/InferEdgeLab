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
        "policy_decision_log": [
            {
                "agent_id": "vision_agent",
                "decision": "load_shedding",
                "reason": "queue_backlog_threshold_exceeded",
                "protected_agent_id": "safety_monitor_agent",
            }
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


def test_compute_agent_runtime_metrics_from_orchestrator_summary():
    metrics = compute_agent_runtime_metrics(orchestration_summary())

    assert metrics["deadline_miss_rate"] == pytest.approx(0.1)
    assert metrics["drop_rate"] == pytest.approx(14 / 24)
    assert metrics["fallback_rate"] == pytest.approx(14 / 24)
    assert metrics["queue_backlog_policy_decision_count"] == 1


def test_agent_runtime_report_blocks_when_guard_blocks():
    report = build_agent_runtime_reliability_report(
        orchestration_summary=orchestration_summary(),
        guard_analysis=guard_analysis(),
    )

    decision = report["agent_deployment_decision"]
    assert report["schema_version"] == AGENT_RUNTIME_REPORT_SCHEMA_VERSION
    assert report["contracts"]["orchestration_summary"] == (
        "inferedge-orchestration-summary-v1"
    )
    assert report["contracts"]["aiguard_guard_analysis"] == (
        "inferedge-aiguard-diagnosis-v1"
    )
    assert decision["policy_version"] == AGENT_RUNTIME_POLICY_VERSION
    assert decision["decision"] == "blocked"
    assert "guard_blocked_runtime_block" in decision["triggered_rules"]
    assert "drop_rate_block" in decision["triggered_rules"]
    assert report["guard_summary"]["guard_verdict"] == "blocked"


def test_agent_runtime_report_markdown_contains_sections():
    report = build_agent_runtime_reliability_report(
        orchestration_summary=orchestration_summary(),
        guard_analysis=guard_analysis(),
    )
    markdown = build_agent_runtime_reliability_markdown(report)

    assert "# InferEdge Agent Runtime Reliability Report" in markdown
    assert "Agent Runtime Summary" in markdown
    assert "Runtime Reliability Metrics" in markdown
    assert "AIGuard Runtime Reliability Evidence" in markdown
    assert "Lab Agent Deployment Decision" in markdown
    assert "guard_blocked_runtime_block" in markdown
    assert "not a production cloud orchestration dashboard" in markdown


def test_agent_runtime_report_loads_committed_fixtures():
    report = load_agent_runtime_reliability_bundle(
        orchestration_summary_path="examples/agent_runtime/agent_3_orchestration_summary.json",
        guard_analysis_path="examples/agent_runtime/aiguard_runtime_guard_analysis.json",
    )

    assert report["agent_deployment_decision"]["decision"] == "blocked"
    assert report["agent_runtime_summary"]["metrics"]["drop_rate"] == pytest.approx(14 / 24)
    assert len(report["agent_runtime_summary"]["agents"]) == 3


def test_agent_runtime_report_command_outputs_json(capsys):
    agent_runtime_report_cmd(
        orchestration_summary="examples/agent_runtime/agent_3_orchestration_summary.json",
        guard_analysis="examples/agent_runtime/aiguard_runtime_guard_analysis.json",
        format="json",
        output="",
    )
    out = capsys.readouterr().out
    report = json.loads(out)

    assert report["schema_version"] == AGENT_RUNTIME_REPORT_SCHEMA_VERSION
    assert report["agent_deployment_decision"]["decision"] == "blocked"
