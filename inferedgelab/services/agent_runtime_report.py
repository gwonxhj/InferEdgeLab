from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from inferedgelab.services.guard_analysis import (
    guard_evidence_items,
    guard_primary_reason,
    guard_status,
    guard_verdict,
)


AGENT_RUNTIME_REPORT_SCHEMA_VERSION = "inferedgelab-agent-runtime-reliability-report-v1"
AGENT_RUNTIME_POLICY_VERSION = "inferedge-lab-agent-runtime-policy-v1"
ORCHESTRATION_SCHEMA_VERSION = "inferedge-orchestration-summary-v1"
AIGUARD_DIAGNOSIS_SCHEMA_VERSION = "inferedge-aiguard-diagnosis-v1"
REMOTE_DISPATCH_SCHEMA_VERSION = "inferedge-remote-dispatch-result-v1"

RUNTIME_OPERATION_GUARD_EVIDENCE_TYPES = {
    "runtime_backend_unavailable",
    "runtime_latency_budget_overrun",
    "runtime_error_classification",
    "runtime_thermal_memory_evidence_missing",
    "runtime_operation_health",
}

DEFAULT_AGENT_RUNTIME_THRESHOLDS = {
    "deadline_miss_rate_review": 0.05,
    "deadline_miss_rate_blocked": 0.20,
    "drop_rate_review": 0.20,
    "drop_rate_blocked": 0.50,
    "fallback_rate_review": 0.20,
    "fallback_rate_blocked": 0.50,
    "queue_backlog_policy_decision_count_review": 1,
    "max_total_queue_depth_review": 3,
    "max_total_queue_depth_blocked": 8,
}

AGENT_RUNTIME_POLICY_RULES: dict[str, dict[str, str]] = {
    "guard_blocked_runtime_block": {
        "effect": "blocked",
        "description": "AIGuard runtime reliability evidence reported blocked/error status.",
    },
    "guard_warning_runtime_review": {
        "effect": "review_required",
        "description": "AIGuard runtime reliability evidence requires deployment review.",
    },
    "guard_missing_unknown": {
        "effect": "unknown",
        "description": "AIGuard runtime reliability evidence is missing.",
    },
    "deadline_miss_block": {
        "effect": "blocked",
        "description": "Deadline miss rate crossed the blocking threshold.",
    },
    "deadline_miss_review": {
        "effect": "review_required",
        "description": "Deadline miss rate crossed the review threshold.",
    },
    "drop_rate_block": {
        "effect": "blocked",
        "description": "Drop rate crossed the blocking threshold.",
    },
    "drop_rate_review": {
        "effect": "review_required",
        "description": "Drop rate crossed the review threshold.",
    },
    "fallback_rate_block": {
        "effect": "blocked",
        "description": "Fallback usage crossed the blocking threshold.",
    },
    "fallback_rate_review": {
        "effect": "review_required",
        "description": "Fallback usage crossed the review threshold.",
    },
    "queue_backlog_review": {
        "effect": "review_required",
        "description": "Queue backlog policy intervention was observed.",
    },
    "sustained_overload_block": {
        "effect": "blocked",
        "description": "Sustained queue depth crossed the blocking threshold.",
    },
    "sustained_overload_review": {
        "effect": "review_required",
        "description": "Sustained queue depth crossed the review threshold.",
    },
    "runtime_timeout_observed_review": {
        "effect": "review_required",
        "description": "Runtime result reported a latency timeout observation threshold breach.",
    },
    "runtime_operation_guard_block": {
        "effect": "blocked",
        "description": "AIGuard Runtime operation evidence reported failed backend, latency, or error-classification risk.",
    },
    "runtime_operation_guard_review": {
        "effect": "review_required",
        "description": "AIGuard Runtime operation evidence reported warning-level runtime context risk.",
    },
    "runtime_reliability_pass_note": {
        "effect": "deployable_with_note",
        "description": "Runtime reliability evidence stayed within configured thresholds.",
    },
}


def build_agent_runtime_reliability_report(
    *,
    orchestration_summary: dict[str, Any],
    guard_analysis: dict[str, Any] | None = None,
    runtime_result: dict[str, Any] | None = None,
    remote_dispatch: dict[str, Any] | None = None,
    source: dict[str, Any] | None = None,
    thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Build a Lab-owned report for an agent runtime reliability bundle."""

    policy = {**DEFAULT_AGENT_RUNTIME_THRESHOLDS, **(thresholds or {})}
    metrics = compute_agent_runtime_metrics(orchestration_summary)
    runtime_summary = _agent_runtime_summary(orchestration_summary)
    runtime_result_context = _runtime_result_operation_context(runtime_result)
    remote_dispatch_context = _remote_dispatch_context(remote_dispatch)
    runtime_operation_guard_summary = _runtime_operation_guard_summary(guard_analysis)
    decision = build_agent_runtime_deployment_decision(
        metrics=metrics,
        guard_analysis=guard_analysis,
        runtime_result_context=runtime_result_context,
        runtime_operation_guard_summary=runtime_operation_guard_summary,
        thresholds=policy,
    )

    return {
        "schema_version": AGENT_RUNTIME_REPORT_SCHEMA_VERSION,
        "generated_at": _utc_now_iso(),
        "scope": "local-first agent runtime reliability report",
        "source": dict(source or {}),
        "contracts": {
            "orchestration_summary": (
                orchestration_summary.get("schema_version")
                or runtime_summary.get("schema_version")
            ),
            "aiguard_guard_analysis": (
                guard_analysis.get("schema_version")
                if isinstance(guard_analysis, dict)
                else None
            ),
            "runtime_result": (
                runtime_result.get("schema_version")
                if isinstance(runtime_result, dict)
                else None
            ),
            "remote_dispatch": (
                remote_dispatch.get("schema_version")
                if isinstance(remote_dispatch, dict)
                else None
            ),
            "source_contracts": runtime_summary.get("source_contracts", {}),
        },
        "agent_runtime_summary": {
            "agents": _agent_summaries(runtime_summary),
            "totals": _totals(runtime_summary),
            "metrics": metrics,
            "timeline_summary": _timeline_summary(orchestration_summary, metrics),
            "operation_context": _operation_context(orchestration_summary, metrics),
            "runtime_result_context": runtime_result_context,
            "remote_dispatch_context": remote_dispatch_context,
            "policy_decision_reasons": metrics["policy_decision_reasons"],
            "policy_decision_log_count": len(_policy_log(orchestration_summary)),
        },
        "guard_summary": _guard_summary(guard_analysis),
        "runtime_operation_guard_summary": runtime_operation_guard_summary,
        "runtime_reliability_evidence": _runtime_reliability_evidence(guard_analysis),
        "agent_deployment_decision": decision,
        "notes": [
            "This report is local-first runtime reliability evidence, not a production cloud orchestration dashboard.",
            "InferEdgeLab remains the final deployment decision owner.",
            "AIGuard and Orchestrator provide optional evidence; they do not overwrite Lab policy.",
        ],
    }


def build_agent_runtime_deployment_decision(
    *,
    metrics: dict[str, Any],
    guard_analysis: dict[str, Any] | None,
    runtime_result_context: dict[str, Any] | None = None,
    runtime_operation_guard_summary: dict[str, Any] | None = None,
    thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    policy = {**DEFAULT_AGENT_RUNTIME_THRESHOLDS, **(thresholds or {})}
    triggered_rules: list[str] = []

    normalized_guard_status = guard_status(guard_analysis)
    normalized_guard_verdict = guard_verdict(guard_analysis)

    if normalized_guard_status == "error" or normalized_guard_verdict == "blocked":
        triggered_rules.append("guard_blocked_runtime_block")
    elif normalized_guard_status == "warning" or normalized_guard_verdict in {
        "suspicious",
        "review_required",
    }:
        triggered_rules.append("guard_warning_runtime_review")
    elif normalized_guard_status is None and normalized_guard_verdict is None:
        triggered_rules.append("guard_missing_unknown")

    _append_metric_rules(
        triggered_rules,
        metric_value=metrics["deadline_miss_rate"],
        review=policy["deadline_miss_rate_review"],
        blocked=policy["deadline_miss_rate_blocked"],
        review_rule="deadline_miss_review",
        blocked_rule="deadline_miss_block",
    )
    _append_metric_rules(
        triggered_rules,
        metric_value=metrics["drop_rate"],
        review=policy["drop_rate_review"],
        blocked=policy["drop_rate_blocked"],
        review_rule="drop_rate_review",
        blocked_rule="drop_rate_block",
    )
    _append_metric_rules(
        triggered_rules,
        metric_value=metrics["fallback_rate"],
        review=policy["fallback_rate_review"],
        blocked=policy["fallback_rate_blocked"],
        review_rule="fallback_rate_review",
        blocked_rule="fallback_rate_block",
    )
    if (
        metrics["queue_backlog_policy_decision_count"]
        >= policy["queue_backlog_policy_decision_count_review"]
    ):
        triggered_rules.append("queue_backlog_review")
    _append_metric_rules(
        triggered_rules,
        metric_value=metrics["max_total_queue_depth"],
        review=policy["max_total_queue_depth_review"],
        blocked=policy["max_total_queue_depth_blocked"],
        review_rule="sustained_overload_review",
        blocked_rule="sustained_overload_block",
    )
    if _runtime_timeout_observed(runtime_result_context):
        triggered_rules.append("runtime_timeout_observed_review")
    runtime_guard = runtime_operation_guard_summary
    if runtime_guard is None:
        runtime_guard = _runtime_operation_guard_summary(guard_analysis)
    if _runtime_operation_guard_blocking(runtime_guard):
        triggered_rules.append("runtime_operation_guard_block")
    elif _runtime_operation_guard_review(runtime_guard):
        triggered_rules.append("runtime_operation_guard_review")

    if not triggered_rules:
        triggered_rules.append("runtime_reliability_pass_note")

    if any(_rule_effect(rule) == "blocked" for rule in triggered_rules):
        decision = "blocked"
        reason = "Agent runtime reliability evidence indicates blocked deployment risk."
        recommended_action = (
            "Do not deploy until deadline, drop, fallback, and guard evidence are reviewed."
        )
    elif any(_rule_effect(rule) == "review_required" for rule in triggered_rules):
        decision = "review_required"
        reason = "Agent runtime reliability evidence requires deployment review."
        recommended_action = (
            "Review Orchestrator policy decisions, AIGuard evidence, and agent priority budgets."
        )
    elif "guard_missing_unknown" in triggered_rules:
        decision = "unknown"
        reason = "AIGuard runtime reliability evidence is unavailable."
        recommended_action = (
            "Run AIGuard runtime reliability analysis before using this report for deployment."
        )
    else:
        decision = "deployable_with_note"
        reason = "Agent runtime reliability evidence stayed within configured thresholds."
        recommended_action = (
            "Deployment can proceed with runtime monitoring and the local evidence note retained."
        )

    return {
        "policy_version": AGENT_RUNTIME_POLICY_VERSION,
        "decision": decision,
        "reason": reason,
        "guard_status": normalized_guard_status,
        "guard_verdict": normalized_guard_verdict,
        "recommended_action": recommended_action,
        "triggered_rules": triggered_rules,
        "policy_summary": [
            {
                "rule": rule,
                "effect": _rule_effect(rule),
                "description": AGENT_RUNTIME_POLICY_RULES[rule]["description"],
            }
            for rule in triggered_rules
        ],
    }


def compute_agent_runtime_metrics(orchestration_summary: dict[str, Any]) -> dict[str, Any]:
    runtime_summary = _agent_runtime_summary(orchestration_summary)
    sustained_summary = _sustained_runtime_summary(orchestration_summary)
    totals = _totals(runtime_summary)
    queue_depth_timeline = _dict_list(orchestration_summary.get("queue_depth_timeline"))
    latency_timeline = _dict_list(orchestration_summary.get("latency_timeline"))
    executed_count = _non_negative_number(totals.get("executed_count"))
    dropped_count = _non_negative_number(totals.get("dropped_count"))
    timeline_deadline_missed_count = sum(
        1 for item in latency_timeline if bool(item.get("deadline_missed"))
    )
    deadline_missed_count = max(
        _non_negative_number(totals.get("deadline_missed_count")),
        float(timeline_deadline_missed_count),
    )
    fallback_count = _non_negative_number(totals.get("fallback_count"))
    if executed_count <= 0 and latency_timeline:
        executed_count = float(len(latency_timeline))
    total_task_events = executed_count + dropped_count
    policy_log = _policy_log(orchestration_summary)
    queue_state = _queue_state_summary(orchestration_summary)
    worker_health = _worker_health_snapshot(orchestration_summary)
    worker_health_counts = _worker_health_counts(worker_health)
    runtime_events = _runtime_event_timeline(orchestration_summary)
    runtime_event_summary = _runtime_event_summary(orchestration_summary, runtime_events)
    policy_decision_reasons = _policy_decision_reasons(policy_log)
    queue_backlog_count = sum(
        1
        for item in policy_log
        if "backlog" in str(item.get("reason", "")).lower()
        or "backlog" in str(item.get("decision_reason", "")).lower()
        or "backlog" in str(item.get("decision", "")).lower()
    )
    max_total_queue_depth = max(
        _non_negative_number(sustained_summary.get("max_total_queue_depth")),
        _max_total_queue_depth(queue_depth_timeline),
    )
    return {
        "scenario_label": _scenario_metadata(orchestration_summary, "scenario_label")
        or "unknown",
        "scenario_category": _scenario_metadata(
            orchestration_summary,
            "scenario_category",
        )
        or "unknown",
        "scenario_description": _scenario_metadata(
            orchestration_summary,
            "scenario_description",
        )
        or "unknown",
        "scenario_mode": _scenario_mode(orchestration_summary),
        "executed_count": executed_count,
        "dropped_count": dropped_count,
        "deadline_missed_count": deadline_missed_count,
        "fallback_count": fallback_count,
        "policy_decision_count": _non_negative_number(
            totals.get("policy_decision_count")
        ),
        "overload_event_count": _non_negative_number(totals.get("overload_event_count")),
        "total_task_events": total_task_events,
        "deadline_miss_rate": _ratio(deadline_missed_count, executed_count),
        "drop_rate": _ratio(dropped_count, total_task_events),
        "fallback_rate": _ratio(fallback_count, total_task_events),
        "queue_backlog_policy_decision_count": queue_backlog_count,
        "max_total_queue_depth": max_total_queue_depth,
        "queue_depth_sample_count": len(queue_depth_timeline),
        "latency_sample_count": len(latency_timeline),
        "queue_pressure_state": queue_state.get("queue_pressure_state") or "unknown",
        "queue_state_sample_count": _non_negative_number(queue_state.get("sample_count")),
        "queue_state_max_total_queue_depth": _non_negative_number(
            queue_state.get("max_total_queue_depth")
        ),
        "queue_state_average_total_queue_depth": _non_negative_number(
            queue_state.get("average_total_queue_depth")
        ),
        "worker_health_counts": worker_health_counts,
        "degraded_worker_count": _non_negative_number(worker_health_counts.get("degraded")),
        "constrained_worker_count": _non_negative_number(
            worker_health_counts.get("constrained")
        ),
        "healthy_worker_count": _non_negative_number(worker_health_counts.get("healthy")),
        "runtime_event_count": _non_negative_number(
            runtime_event_summary.get("event_count")
        ),
        "runtime_event_type_counts": dict(
            runtime_event_summary.get("event_type_counts") or {}
        ),
        "policy_decision_reasons": policy_decision_reasons,
        "top_policy_decision_reason": _top_reason(policy_decision_reasons),
    }


def load_agent_runtime_reliability_bundle(
    *,
    orchestration_summary_path: str | Path,
    guard_analysis_path: str | Path | None = None,
    runtime_result_path: str | Path | None = None,
    remote_dispatch_path: str | Path | None = None,
) -> dict[str, Any]:
    orchestration_summary = _load_json_dict(orchestration_summary_path)
    guard_analysis = _load_json_dict(guard_analysis_path) if guard_analysis_path else None
    runtime_result = _load_json_dict(runtime_result_path) if runtime_result_path else None
    remote_dispatch = (
        _load_json_dict(remote_dispatch_path) if remote_dispatch_path else None
    )
    return build_agent_runtime_reliability_report(
        orchestration_summary=orchestration_summary,
        guard_analysis=guard_analysis,
        runtime_result=runtime_result,
        remote_dispatch=remote_dispatch,
        source={
            "orchestration_summary_path": str(orchestration_summary_path),
            "guard_analysis_path": str(guard_analysis_path)
            if guard_analysis_path
            else None,
            "runtime_result_path": str(runtime_result_path)
            if runtime_result_path
            else None,
            "remote_dispatch_path": str(remote_dispatch_path)
            if remote_dispatch_path
            else None,
        },
    )


def build_agent_runtime_reliability_markdown(report: dict[str, Any]) -> str:
    runtime = report["agent_runtime_summary"]
    metrics = runtime["metrics"]
    decision = report["agent_deployment_decision"]
    guard = report["guard_summary"]
    runtime_guard = report.get("runtime_operation_guard_summary") or {}
    runtime_result_context = runtime.get("runtime_result_context") or {}
    remote_dispatch_context = runtime.get("remote_dispatch_context") or {}
    runtime_health = runtime_result_context.get("runtime_health_snapshot") or {}
    runtime_error = runtime_result_context.get("runtime_error_classification") or {}
    runtime_event_summary = runtime_result_context.get("runtime_event_summary") or {}
    remote_execution = remote_dispatch_context.get("remote_execution") or {}
    remote_execution_plan = remote_dispatch_context.get("remote_execution_plan") or {}
    remote_execution_result = (
        remote_dispatch_context.get("remote_execution_result") or {}
    )
    fallback_execution_result = (
        remote_dispatch_context.get("fallback_execution_result") or {}
    )
    retry_fallback_plan = remote_dispatch_context.get("retry_fallback_plan") or {}
    worker_selection = remote_dispatch_context.get("worker_selection") or {}

    lines = [
        "# InferEdge Agent Runtime Reliability Report",
        "",
        "## Scope",
        "",
        f"- schema_version: `{report['schema_version']}`",
        f"- generated_at: `{report['generated_at']}`",
        f"- scope: {report['scope']}",
        "- This is local-first report evidence, not a production cloud orchestration dashboard.",
        "",
        "## Agent Runtime Summary",
        "",
        "| Agent | Type | Priority | Latency Budget ms | Fallback Policy |",
        "|---|---|---:|---:|---|",
    ]
    for agent in runtime["agents"]:
        lines.append(
            "| "
            f"{agent.get('agent_id', '')} | "
            f"{agent.get('agent_type', '')} | "
            f"{_fmt_number(agent.get('priority'))} | "
            f"{_fmt_number(agent.get('latency_budget_ms'))} | "
            f"{agent.get('fallback_policy', '')} |"
        )

    lines.extend(
        [
            "",
            "## Runtime Reliability Metrics",
            "",
            "| Metric | Value |",
            "|---|---:|",
            f"| scenario_label | {metrics.get('scenario_label') or '-'} |",
            f"| scenario_category | {metrics.get('scenario_category') or '-'} |",
            f"| scenario_description | {metrics.get('scenario_description') or '-'} |",
            f"| scenario_mode | {metrics.get('scenario_mode') or '-'} |",
            f"| executed_count | {_fmt_number(metrics['executed_count'])} |",
            f"| dropped_count | {_fmt_number(metrics['dropped_count'])} |",
            f"| deadline_missed_count | {_fmt_number(metrics['deadline_missed_count'])} |",
            f"| fallback_count | {_fmt_number(metrics['fallback_count'])} |",
            f"| deadline_miss_rate | {_fmt_number(metrics['deadline_miss_rate'])} |",
            f"| drop_rate | {_fmt_number(metrics['drop_rate'])} |",
            f"| fallback_rate | {_fmt_number(metrics['fallback_rate'])} |",
            f"| queue_backlog_policy_decision_count | {_fmt_number(metrics['queue_backlog_policy_decision_count'])} |",
            f"| max_total_queue_depth | {_fmt_number(metrics['max_total_queue_depth'])} |",
            f"| queue_depth_sample_count | {_fmt_number(metrics['queue_depth_sample_count'])} |",
            f"| latency_sample_count | {_fmt_number(metrics['latency_sample_count'])} |",
            f"| queue_pressure_state | {metrics.get('queue_pressure_state') or '-'} |",
            f"| runtime_event_count | {_fmt_number(metrics.get('runtime_event_count'))} |",
            f"| degraded_worker_count | {_fmt_number(metrics.get('degraded_worker_count'))} |",
            f"| constrained_worker_count | {_fmt_number(metrics.get('constrained_worker_count'))} |",
            f"| top_policy_decision_reason | {metrics.get('top_policy_decision_reason') or '-'} |",
            "",
            "## Orchestrator Operation Context",
            "",
            "### Queue State",
            "",
            "| Field | Value |",
            "|---|---:|",
            f"| queue_pressure_state | {runtime['operation_context']['queue_state_summary'].get('queue_pressure_state') or '-'} |",
            f"| overload_backlog_threshold | {_fmt_number(runtime['operation_context']['queue_state_summary'].get('overload_backlog_threshold'))} |",
            f"| max_total_queue_depth | {_fmt_number(runtime['operation_context']['queue_state_summary'].get('max_total_queue_depth'))} |",
            f"| average_total_queue_depth | {_fmt_number(runtime['operation_context']['queue_state_summary'].get('average_total_queue_depth'))} |",
            "",
            "### Worker Health",
            "",
            "| Worker | Health | Executed | Dropped | Deadline Missed | Fallback | Mean Latency ms |",
            "|---|---|---:|---:|---:|---:|---:|",
            *[
                "| "
                f"{worker.get('task') or task_name} | "
                f"{worker.get('health_state') or '-'} | "
                f"{_fmt_number(worker.get('executed_count'))} | "
                f"{_fmt_number(worker.get('dropped_count'))} | "
                f"{_fmt_number(worker.get('deadline_missed_count'))} | "
                f"{_fmt_number(worker.get('fallback_count'))} | "
                f"{_fmt_number(worker.get('mean_latency_ms'))} |"
                for task_name, worker in runtime["operation_context"][
                    "worker_health_snapshot"
                ]
                .get("workers", {})
                .items()
                if isinstance(worker, dict)
            ],
            "",
            "### Runtime Event Summary",
            "",
            "| Event Type | Count |",
            "|---|---:|",
            *[
                f"| {event_type} | {_fmt_number(count)} |"
                for event_type, count in sorted(
                    (
                        runtime["operation_context"]["runtime_event_summary"].get(
                            "event_type_counts"
                        )
                        or {}
                    ).items()
                )
            ],
            "",
            "Runtime event timeline sample:",
            "",
            "| # | Type | Agent | Task | Reason |",
            "|---:|---|---|---|---|",
            *[
                "| "
                f"{_fmt_number(event.get('event_index'))} | "
                f"{event.get('event_type') or '-'} | "
                f"{event.get('agent_id') or '-'} | "
                f"{event.get('task_id') or event.get('task') or '-'} | "
                f"{event.get('reason') or event.get('decision_reason') or '-'} |"
                for event in runtime["operation_context"][
                    "runtime_event_timeline_sample"
                ]
            ],
            "",
            "## Runtime Result Operation Evidence",
            "",
            "| Field | Value |",
            "|---|---|",
            f"| runtime_result_schema | {runtime_result_context.get('source_schema_version') or '-'} |",
            f"| compare_key | {runtime_result_context.get('compare_key') or '-'} |",
            f"| backend_key | {runtime_result_context.get('backend_key') or '-'} |",
            f"| runtime_status | {runtime_health.get('status') or runtime_result_context.get('status') or '-'} |",
            f"| runtime_error_category | {runtime_error.get('category') or '-'} |",
            f"| timeout_policy | {runtime_health.get('timeout_policy', runtime_error.get('timeout_policy', '-'))} |",
            f"| timeout_budget_ms | {_fmt_number(runtime_health.get('timeout_budget_ms', runtime_error.get('timeout_budget_ms')))} |",
            f"| runtime_timeout_observed | {runtime_result_context.get('runtime_timeout_observed', False)} |",
            f"| runtime_event_count | {_fmt_number(runtime_event_summary.get('event_count'))} |",
            "",
            "## AIGuard Runtime Operation Evidence",
            "",
            "| Field | Value |",
            "|---|---|",
            f"| evidence_count | {_fmt_number(runtime_guard.get('evidence_count'))} |",
            f"| failed_count | {_fmt_number(runtime_guard.get('failed_count'))} |",
            f"| warning_count | {_fmt_number(runtime_guard.get('warning_count'))} |",
            f"| evidence_types | {', '.join(runtime_guard.get('evidence_types') or []) or '-'} |",
            f"| retry_hints | {', '.join(runtime_guard.get('retry_hints') or []) or '-'} |",
            "",
            "Runtime operation guard evidence:",
            "",
            "| Type | Metric | Observed | Severity | Status | Recommendation |",
            "|---|---|---:|---|---|---|",
            *[
                "| "
                f"{item.get('type') or '-'} | "
                f"{item.get('metric_name') or '-'} | "
                f"{_fmt_number(item.get('observed_value'))} | "
                f"{item.get('severity') or '-'} | "
                f"{item.get('status') or '-'} | "
                f"{item.get('recommendation') or '-'} |"
                for item in runtime_guard.get("evidence", [])
            ],
            "",
            "Runtime result event sample:",
            "",
            "| # | Type | Status | Detail |",
            "|---:|---|---|---|",
            *[
                "| "
                f"{index} | "
                f"{event.get('type') or event.get('event_type') or '-'} | "
                f"{event.get('status') or '-'} | "
                f"{event.get('category') or event.get('reason') or event.get('engine_backend') or '-'} |"
                for index, event in enumerate(
                    runtime_result_context.get("runtime_event_sample") or []
                )
            ],
            "",
            "## Remote Dispatch Context",
            "",
            "| Field | Value |",
            "|---|---|",
            f"| remote_dispatch_schema | {remote_dispatch_context.get('source_schema_version') or '-'} |",
            f"| dispatch_status | {remote_dispatch_context.get('dispatch_status') or '-'} |",
            f"| selected_worker_id | {remote_dispatch_context.get('selected_worker_id') or '-'} |",
            f"| decision_reason | {remote_dispatch_context.get('decision_reason') or '-'} |",
            f"| production_remote_execution | {remote_execution.get('production_remote_execution', '-')} |",
            f"| execution_plan_mode | {remote_execution_plan.get('mode') or '-'} |",
            f"| network_execution_performed | {remote_execution_plan.get('network_execution_performed', '-')} |",
            f"| planned_transport | {remote_execution_plan.get('transport') or '-'} |",
            f"| execution_requested | {remote_execution_result.get('execution_requested', '-')} |",
            f"| execution_performed | {remote_execution_result.get('execution_performed', '-')} |",
            f"| execution_status | {remote_execution_result.get('status') or '-'} |",
            f"| execution_transport | {remote_execution_result.get('transport') or '-'} |",
            f"| execution_error_category | {remote_execution_result.get('error_category') or '-'} |",
            f"| execution_http_status | {_fmt_number(remote_execution_result.get('http_status'))} |",
            f"| execution_exit_code | {_fmt_number(remote_execution_result.get('exit_code'))} |",
            f"| execution_fallback_performed | {remote_execution_result.get('fallback_execution_performed', '-')} |",
            f"| fallback_final_status | {fallback_execution_result.get('final_status') or retry_fallback_plan.get('fallback_final_status') or '-'} |",
            f"| fallback_reason | {fallback_execution_result.get('fallback_reason') or '-'} |",
            f"| fallback_attempted_worker_ids | {', '.join(fallback_execution_result.get('attempted_worker_ids') or retry_fallback_plan.get('fallback_attempted_worker_ids') or []) or '-'} |",
            f"| fallback_worker_ids | {', '.join(worker_selection.get('fallback_worker_ids') or []) or '-'} |",
            f"| retry_max_attempts | {_fmt_number(retry_fallback_plan.get('max_attempts'))} |",
            f"| retry_execution_performed | {retry_fallback_plan.get('execution_performed', '-')} |",
            "",
            "Remote execution starter evidence:",
            "",
            "| Field | Value |",
            "|---|---|",
            f"| status | {remote_execution_result.get('status') or '-'} |",
            f"| transport | {remote_execution_result.get('transport') or '-'} |",
            f"| execution_requested | {remote_execution_result.get('execution_requested', '-')} |",
            f"| execution_performed | {remote_execution_result.get('execution_performed', '-')} |",
            f"| error_category | {remote_execution_result.get('error_category') or '-'} |",
            f"| error_message | {remote_execution_result.get('error_message') or '-'} |",
            f"| elapsed_ms | {_fmt_number(remote_execution_result.get('elapsed_ms'))} |",
            f"| note | {remote_execution_result.get('note') or 'starter evidence only; not production remote execution'} |",
            "",
            "Remote fallback starter evidence:",
            "",
            "| Field | Value |",
            "|---|---|",
            f"| fallback_requested | {fallback_execution_result.get('fallback_requested', '-')} |",
            f"| primary_worker_id | {fallback_execution_result.get('primary_worker_id') or '-'} |",
            f"| fallback_reason | {fallback_execution_result.get('fallback_reason') or '-'} |",
            f"| attempted_worker_ids | {', '.join(fallback_execution_result.get('attempted_worker_ids') or []) or '-'} |",
            f"| final_status | {fallback_execution_result.get('final_status') or '-'} |",
            f"| attempt_count | {_fmt_number(len(fallback_execution_result.get('attempts') or []))} |",
            f"| production_remote_execution | {fallback_execution_result.get('production_remote_execution', '-')} |",
            "",
            "Remote worker selection sample:",
            "",
            "| Worker | Eligible | Status | Health | Endpoint | Reason |",
            "|---|---|---|---|---|---|",
            *[
                "| "
                f"{item.get('worker_id') or '-'} | "
                f"{item.get('eligible')} | "
                f"{item.get('status') or '-'} | "
                f"{item.get('health_state') or '-'} | "
                f"{item.get('endpoint_type') or '-'} | "
                f"{item.get('decision_reason') or '-'} |"
                for item in remote_dispatch_context.get("worker_evaluations", [])
            ],
            "",
            "## AIGuard Runtime Reliability Evidence",
            "",
            f"- guard_status: `{guard.get('status')}`",
            f"- guard_verdict: `{guard.get('guard_verdict')}`",
            f"- severity: `{guard.get('severity')}`",
            f"- primary_reason: {guard.get('primary_reason')}",
            f"- evidence_count: `{guard.get('evidence_count')}`",
            "- evidence_types:",
            *[
                f"  - `{item['type']}`: {item.get('metric_name')}={_fmt_number(item.get('observed_value'))} ({item.get('status')})"
                for item in report.get("runtime_reliability_evidence", [])
            ],
            "",
            "## Lab Agent Deployment Decision",
            "",
            f"- policy_version: `{decision['policy_version']}`",
            f"- decision: `{decision['decision']}`",
            f"- reason: {decision['reason']}",
            f"- recommended_action: {decision['recommended_action']}",
            "- triggered_rules:",
            *[f"  - `{rule}`" for rule in decision["triggered_rules"]],
            "",
            "## Notes",
            "",
        ]
    )
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def agent_runtime_reliability_json(report: dict[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2) + "\n"


def write_agent_runtime_reliability_markdown(
    report: dict[str, Any],
    output: str | Path,
) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_agent_runtime_reliability_markdown(report), encoding="utf-8")
    return path


def _agent_runtime_summary(orchestration_summary: dict[str, Any]) -> dict[str, Any]:
    value = orchestration_summary.get("agent_runtime_summary")
    return value if isinstance(value, dict) else {}


def _sustained_runtime_summary(orchestration_summary: dict[str, Any]) -> dict[str, Any]:
    value = orchestration_summary.get("sustained_runtime_summary")
    return value if isinstance(value, dict) else {}


def _totals(runtime_summary: dict[str, Any]) -> dict[str, Any]:
    value = runtime_summary.get("totals")
    return value if isinstance(value, dict) else {}


def _agent_summaries(runtime_summary: dict[str, Any]) -> list[dict[str, Any]]:
    agents = runtime_summary.get("agents")
    if isinstance(agents, dict):
        values = [value for value in agents.values() if isinstance(value, dict)]
    elif isinstance(agents, list):
        values = [value for value in agents if isinstance(value, dict)]
    else:
        values = []
    return sorted(values, key=lambda item: str(item.get("agent_id", "")))


def _guard_summary(guard_analysis: dict[str, Any] | None) -> dict[str, Any]:
    evidence = guard_evidence_items(guard_analysis)
    return {
        "schema_version": guard_analysis.get("schema_version")
        if isinstance(guard_analysis, dict)
        else None,
        "status": guard_status(guard_analysis),
        "guard_verdict": guard_verdict(guard_analysis),
        "severity": guard_analysis.get("severity") if isinstance(guard_analysis, dict) else None,
        "primary_reason": guard_primary_reason(guard_analysis),
        "evidence_count": len(evidence),
        "evidence_types": [
            item.get("type") for item in evidence if isinstance(item, dict) and item.get("type")
        ],
    }


def _append_metric_rules(
    rules: list[str],
    *,
    metric_value: float,
    review: float,
    blocked: float,
    review_rule: str,
    blocked_rule: str,
) -> None:
    if metric_value >= blocked:
        rules.append(blocked_rule)
    elif metric_value >= review:
        rules.append(review_rule)


def _rule_effect(rule: str) -> str:
    return AGENT_RUNTIME_POLICY_RULES.get(rule, {}).get("effect", "unknown")


def _runtime_timeout_observed(runtime_result_context: dict[str, Any] | None) -> bool:
    if not isinstance(runtime_result_context, dict):
        return False
    if bool(runtime_result_context.get("runtime_timeout_observed")):
        return True
    return _runtime_timeout_observed_from_parts(
        health=runtime_result_context.get("runtime_health_snapshot"),
        error=runtime_result_context.get("runtime_error_classification"),
        runtime_events=_dict_list(runtime_result_context.get("runtime_event_sample")),
    )


def _runtime_timeout_observed_from_parts(
    *,
    health: Any,
    error: Any,
    runtime_events: list[dict[str, Any]],
) -> bool:
    if isinstance(health, dict) and bool(health.get("timeout_observed")):
        return True
    if isinstance(error, dict):
        if bool(error.get("timeout_observed")):
            return True
        if error.get("category") == "runtime_timeout_observed":
            return True
    for event in runtime_events:
        if bool(event.get("timeout_observed")):
            return True
        if event.get("category") == "runtime_timeout_observed":
            return True
    return False


def _policy_log(orchestration_summary: dict[str, Any]) -> list[dict[str, Any]]:
    value = orchestration_summary.get("policy_decision_log")
    if not isinstance(value, list):
        value = orchestration_summary.get("policy_decisions")
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _dict_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _scenario_mode(orchestration_summary: dict[str, Any]) -> str:
    mode = _scenario_metadata(orchestration_summary, "scenario_mode")
    if isinstance(mode, str) and mode:
        return mode
    return "unknown"


def _scenario_metadata(orchestration_summary: dict[str, Any], key: str) -> str | None:
    run = orchestration_summary.get("run")
    if isinstance(run, dict) and isinstance(run.get(key), str) and run.get(key):
        return run[key]
    runtime_summary = _agent_runtime_summary(orchestration_summary)
    if (
        isinstance(runtime_summary.get(key), str)
        and runtime_summary.get(key)
    ):
        return runtime_summary[key]
    sustained_summary = _sustained_runtime_summary(orchestration_summary)
    if isinstance(sustained_summary.get(key), str) and sustained_summary.get(key):
        return sustained_summary[key]
    multi_workload_summary = orchestration_summary.get("multi_workload_sustained_summary")
    if (
        isinstance(multi_workload_summary, dict)
        and isinstance(multi_workload_summary.get(key), str)
        and multi_workload_summary.get(key)
    ):
        return multi_workload_summary[key]
    if isinstance(orchestration_summary.get(key), str) and orchestration_summary.get(key):
        return orchestration_summary[key]
    return None


def _max_total_queue_depth(queue_depth_timeline: list[dict[str, Any]]) -> float:
    max_depth = 0.0
    for item in queue_depth_timeline:
        max_depth = max(max_depth, _non_negative_number(item.get("total_queue_depth")))
        queue_depth = item.get("queue_depth")
        if isinstance(queue_depth, dict):
            max_depth = max(
                max_depth,
                sum(_non_negative_number(value) for value in queue_depth.values()),
            )
    return max_depth


def _policy_decision_reasons(policy_log: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in policy_log:
        reason = item.get("decision_reason") or item.get("reason") or item.get("decision")
        if not isinstance(reason, str) or not reason:
            reason = "unknown"
        counts[reason] = counts.get(reason, 0) + 1
    return counts


def _top_reason(reasons: dict[str, int]) -> str | None:
    if not reasons:
        return None
    return max(reasons.items(), key=lambda item: (item[1], item[0]))[0]


def _runtime_reliability_evidence(
    guard_analysis: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    evidence = guard_evidence_items(guard_analysis)
    return [
        {
            "type": item.get("type"),
            "metric_name": item.get("metric_name"),
            "observed_value": item.get("observed_value"),
            "threshold": item.get("threshold"),
            "severity": item.get("severity"),
            "status": item.get("status"),
            "explanation": item.get("explanation"),
            "recommendation": item.get("recommendation"),
            "why_it_matters": item.get("why_it_matters"),
        }
        for item in evidence
        if isinstance(item, dict)
    ]


def _runtime_operation_guard_summary(
    guard_analysis: dict[str, Any] | None,
) -> dict[str, Any]:
    evidence = [
        item
        for item in guard_evidence_items(guard_analysis)
        if isinstance(item, dict)
        and item.get("type") in RUNTIME_OPERATION_GUARD_EVIDENCE_TYPES
    ]
    failed = [item for item in evidence if item.get("status") == "failed"]
    warnings = [item for item in evidence if item.get("status") == "warning"]
    retry_hints = sorted(
        {
            retry_hint
            for item in evidence
            for retry_hint in [_runtime_operation_retry_hint(item)]
            if isinstance(retry_hint, str) and retry_hint
        }
    )
    return {
        "evidence_count": len(evidence),
        "failed_count": len(failed),
        "warning_count": len(warnings),
        "evidence_types": [
            item.get("type") for item in evidence if isinstance(item.get("type"), str)
        ],
        "metric_names": [
            item.get("metric_name")
            for item in evidence
            if isinstance(item.get("metric_name"), str)
        ],
        "retry_hints": retry_hints,
        "evidence": [
            {
                "type": item.get("type"),
                "metric_name": item.get("metric_name"),
                "observed_value": item.get("observed_value"),
                "threshold": item.get("threshold"),
                "severity": item.get("severity"),
                "status": item.get("status"),
                "explanation": item.get("explanation"),
                "recommendation": item.get("recommendation"),
                "why_it_matters": item.get("why_it_matters"),
                "retry_hint": _runtime_operation_retry_hint(item),
            }
            for item in evidence
        ],
    }


def _runtime_operation_guard_blocking(summary: dict[str, Any]) -> bool:
    for item in _dict_list(summary.get("evidence")):
        if item.get("status") != "failed":
            continue
        if item.get("severity") in {"high", "critical"}:
            return True
        if item.get("type") in {
            "runtime_backend_unavailable",
            "runtime_latency_budget_overrun",
        }:
            return True
    return False


def _runtime_operation_guard_review(summary: dict[str, Any]) -> bool:
    if _runtime_operation_guard_blocking(summary):
        return False
    return bool(summary.get("failed_count") or summary.get("warning_count"))


def _runtime_operation_retry_hint(evidence_item: dict[str, Any]) -> str | None:
    raw_context = evidence_item.get("raw_context")
    if not isinstance(raw_context, dict):
        return None
    runtime_operation = raw_context.get("runtime_operation")
    if not isinstance(runtime_operation, dict):
        return None
    retry_hint = runtime_operation.get("retry_hint")
    return retry_hint if isinstance(retry_hint, str) and retry_hint else None


def _timeline_summary(
    orchestration_summary: dict[str, Any],
    metrics: dict[str, Any],
) -> dict[str, Any]:
    return {
        "scenario_label": metrics.get("scenario_label"),
        "scenario_category": metrics.get("scenario_category"),
        "scenario_description": metrics.get("scenario_description"),
        "scenario_mode": metrics["scenario_mode"],
        "queue_depth_sample_count": metrics["queue_depth_sample_count"],
        "latency_sample_count": metrics["latency_sample_count"],
        "max_total_queue_depth": metrics["max_total_queue_depth"],
        "top_policy_decision_reason": metrics.get("top_policy_decision_reason"),
        "policy_decision_reasons": dict(metrics.get("policy_decision_reasons") or {}),
        "has_queue_depth_timeline": bool(
            _dict_list(orchestration_summary.get("queue_depth_timeline"))
        ),
        "has_latency_timeline": bool(
            _dict_list(orchestration_summary.get("latency_timeline"))
        ),
    }


def _operation_context(
    orchestration_summary: dict[str, Any],
    metrics: dict[str, Any],
) -> dict[str, Any]:
    runtime_events = _runtime_event_timeline(orchestration_summary)
    queue_state = _queue_state_summary(orchestration_summary)
    worker_health = _worker_health_snapshot(orchestration_summary)
    runtime_event_summary = _runtime_event_summary(orchestration_summary, runtime_events)
    return {
        "queue_state_summary": queue_state,
        "worker_health_snapshot": worker_health,
        "worker_health_counts": dict(metrics.get("worker_health_counts") or {}),
        "runtime_event_summary": runtime_event_summary,
        "runtime_event_timeline_count": len(runtime_events),
        "runtime_event_timeline_sample": runtime_events[:8],
    }


def _runtime_result_operation_context(
    runtime_result: dict[str, Any] | None,
) -> dict[str, Any]:
    if not isinstance(runtime_result, dict):
        return {
            "source_schema_version": None,
            "compare_key": None,
            "backend_key": None,
            "status": None,
            "success": None,
            "runtime_timeout_observed": False,
            "runtime_health_snapshot": {},
            "runtime_error_classification": {},
            "runtime_event_summary": {
                "schema_version": None,
                "event_count": 0,
                "event_type_counts": {},
            },
            "runtime_event_sample": [],
        }

    health = runtime_result.get("runtime_health_snapshot")
    error = runtime_result.get("runtime_error_classification")
    runtime_events = _dict_list(runtime_result.get("runtime_events"))
    return {
        "source_schema_version": runtime_result.get("schema_version"),
        "compare_key": runtime_result.get("compare_key"),
        "backend_key": runtime_result.get("backend_key"),
        "status": runtime_result.get("status"),
        "success": runtime_result.get("success"),
        "runtime_timeout_observed": _runtime_timeout_observed_from_parts(
            health=health,
            error=error,
            runtime_events=runtime_events,
        ),
        "runtime_health_snapshot": dict(health) if isinstance(health, dict) else {},
        "runtime_error_classification": dict(error) if isinstance(error, dict) else {},
        "runtime_event_summary": {
            "schema_version": "inferedgelab-runtime-result-event-summary-v1",
            "event_count": len(runtime_events),
            "event_type_counts": _runtime_result_event_type_counts(runtime_events),
        },
        "runtime_event_sample": runtime_events[:8],
    }


def _remote_dispatch_context(
    remote_dispatch: dict[str, Any] | None,
) -> dict[str, Any]:
    if not isinstance(remote_dispatch, dict):
        return {
            "source_schema_version": None,
            "dispatch_status": None,
            "selected_worker_id": None,
            "decision_reason": None,
            "remote_execution": {},
            "remote_execution_plan": {},
            "remote_execution_result": _empty_remote_execution_result(),
            "fallback_execution_result": _empty_fallback_execution_result(),
            "worker_selection": {
                "schema_version": None,
                "selected_worker_id": None,
                "candidate_worker_ids": [],
                "fallback_worker_ids": [],
                "evaluations": [],
            },
            "retry_fallback_plan": {},
            "worker_evaluations": [],
            "runtime_event_sample": [],
        }

    worker_selection = remote_dispatch.get("worker_selection")
    if not isinstance(worker_selection, dict):
        worker_selection = {
            "schema_version": None,
            "selected_worker_id": remote_dispatch.get("selected_worker_id"),
            "candidate_worker_ids": [],
            "fallback_worker_ids": [],
            "evaluations": [],
        }
    retry_fallback_plan = remote_dispatch.get("retry_fallback_plan")
    remote_execution_plan = remote_dispatch.get("remote_execution_plan")
    remote_execution = remote_dispatch.get("remote_execution")
    remote_execution_result = remote_dispatch.get("remote_execution_result")
    fallback_execution_result = remote_dispatch.get("fallback_execution_result")
    runtime_events = _dict_list(remote_dispatch.get("runtime_events"))
    evaluations = _dict_list(worker_selection.get("evaluations"))
    return {
        "source_schema_version": remote_dispatch.get("schema_version"),
        "dispatch_status": remote_dispatch.get("dispatch_status"),
        "selected_worker_id": remote_dispatch.get("selected_worker_id"),
        "decision_reason": remote_dispatch.get("decision_reason"),
        "remote_execution": dict(remote_execution)
        if isinstance(remote_execution, dict)
        else {},
        "remote_execution_plan": dict(remote_execution_plan)
        if isinstance(remote_execution_plan, dict)
        else {},
        "remote_execution_result": _remote_execution_result_context(
            remote_execution_result
        ),
        "fallback_execution_result": _fallback_execution_result_context(
            fallback_execution_result
        ),
        "worker_selection": dict(worker_selection),
        "retry_fallback_plan": dict(retry_fallback_plan)
        if isinstance(retry_fallback_plan, dict)
        else {},
        "worker_evaluations": evaluations[:8],
        "runtime_event_sample": runtime_events[:8],
    }


def _empty_remote_execution_result() -> dict[str, Any]:
    return {
        "status": None,
        "transport": None,
        "execution_requested": False,
        "execution_performed": False,
        "fallback_execution_performed": False,
        "error_category": None,
        "error_message": None,
        "http_status": None,
        "exit_code": None,
        "elapsed_ms": None,
        "note": None,
    }


def _empty_fallback_execution_result() -> dict[str, Any]:
    return {
        "schema_version": None,
        "fallback_requested": False,
        "fallback_reason": None,
        "primary_worker_id": None,
        "attempted_worker_ids": [],
        "final_status": None,
        "attempts": [],
        "production_remote_execution": False,
    }


def _remote_execution_result_context(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return _empty_remote_execution_result()
    context = _empty_remote_execution_result()
    context.update(dict(value))
    return context


def _fallback_execution_result_context(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return _empty_fallback_execution_result()
    context = _empty_fallback_execution_result()
    context.update(dict(value))
    context["attempts"] = _dict_list(context.get("attempts"))
    if not isinstance(context.get("attempted_worker_ids"), list):
        context["attempted_worker_ids"] = []
    context["attempted_worker_ids"] = [
        item for item in context["attempted_worker_ids"] if isinstance(item, str)
    ]
    return context


def _queue_state_summary(orchestration_summary: dict[str, Any]) -> dict[str, Any]:
    value = orchestration_summary.get("queue_state_summary")
    if isinstance(value, dict):
        return dict(value)

    queue_depth_timeline = _dict_list(orchestration_summary.get("queue_depth_timeline"))
    max_total_queue_depth = _max_total_queue_depth(queue_depth_timeline)
    final_queue_depth: dict[str, Any] = {}
    if queue_depth_timeline:
        queue_depth = queue_depth_timeline[-1].get("queue_depth")
        if isinstance(queue_depth, dict):
            final_queue_depth = dict(queue_depth)
    return {
        "schema_version": None,
        "sample_count": len(queue_depth_timeline),
        "overload_backlog_threshold": None,
        "max_total_queue_depth": max_total_queue_depth,
        "average_total_queue_depth": _average_total_queue_depth(queue_depth_timeline),
        "final_queue_depth": final_queue_depth,
        "max_queue_depth_by_task": _max_queue_depth_by_task(queue_depth_timeline),
        "queue_pressure_state": _derived_queue_pressure_state(max_total_queue_depth),
    }


def _worker_health_snapshot(orchestration_summary: dict[str, Any]) -> dict[str, Any]:
    value = orchestration_summary.get("worker_health_snapshot")
    if isinstance(value, dict):
        return dict(value)
    return {"schema_version": None, "workers": {}}


def _runtime_event_summary(
    orchestration_summary: dict[str, Any],
    runtime_events: list[dict[str, Any]],
) -> dict[str, Any]:
    value = orchestration_summary.get("runtime_event_summary")
    if isinstance(value, dict):
        summary = dict(value)
        if "event_type_counts" not in summary:
            summary["event_type_counts"] = _runtime_event_type_counts(runtime_events)
        if "event_count" not in summary:
            summary["event_count"] = len(runtime_events)
        return summary
    return {
        "schema_version": None,
        "event_count": len(runtime_events),
        "event_type_counts": _runtime_event_type_counts(runtime_events),
    }


def _runtime_event_timeline(orchestration_summary: dict[str, Any]) -> list[dict[str, Any]]:
    return _dict_list(orchestration_summary.get("runtime_event_timeline"))


def _runtime_event_type_counts(runtime_events: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in runtime_events:
        event_type = event.get("event_type")
        if not isinstance(event_type, str) or not event_type:
            event_type = "unknown"
        counts[event_type] = counts.get(event_type, 0) + 1
    return counts


def _runtime_result_event_type_counts(runtime_events: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in runtime_events:
        event_type = event.get("type") or event.get("event_type")
        if not isinstance(event_type, str) or not event_type:
            event_type = "unknown"
        counts[event_type] = counts.get(event_type, 0) + 1
    return counts


def _worker_health_counts(worker_health_snapshot: dict[str, Any]) -> dict[str, int]:
    workers = worker_health_snapshot.get("workers")
    if not isinstance(workers, dict):
        return {}
    counts: dict[str, int] = {}
    for worker in workers.values():
        if not isinstance(worker, dict):
            continue
        state = worker.get("health_state")
        if not isinstance(state, str) or not state:
            state = "unknown"
        counts[state] = counts.get(state, 0) + 1
    return counts


def _average_total_queue_depth(queue_depth_timeline: list[dict[str, Any]]) -> float:
    values = [
        _non_negative_number(item.get("total_queue_depth"))
        for item in queue_depth_timeline
        if item.get("total_queue_depth") is not None
    ]
    if not values:
        return 0.0
    return sum(values) / len(values)


def _max_queue_depth_by_task(
    queue_depth_timeline: list[dict[str, Any]],
) -> dict[str, float]:
    result: dict[str, float] = {}
    for item in queue_depth_timeline:
        queue_depth = item.get("queue_depth")
        if not isinstance(queue_depth, dict):
            continue
        for task_name, depth in queue_depth.items():
            result[str(task_name)] = max(
                result.get(str(task_name), 0.0),
                _non_negative_number(depth),
            )
    return result


def _derived_queue_pressure_state(max_total_queue_depth: float) -> str:
    if max_total_queue_depth >= 8:
        return "overloaded"
    if max_total_queue_depth >= 3:
        return "elevated"
    return "nominal"


def _load_json_dict(path: str | Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    with Path(path).open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def _non_negative_number(value: Any) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return max(float(value), 0.0)
    return 0.0


def _ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _fmt_number(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)
