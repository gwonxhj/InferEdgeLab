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
    "runtime_reliability_pass_note": {
        "effect": "deployable_with_note",
        "description": "Runtime reliability evidence stayed within configured thresholds.",
    },
}


def build_agent_runtime_reliability_report(
    *,
    orchestration_summary: dict[str, Any],
    guard_analysis: dict[str, Any] | None = None,
    source: dict[str, Any] | None = None,
    thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Build a Lab-owned report for an agent runtime reliability bundle."""

    policy = {**DEFAULT_AGENT_RUNTIME_THRESHOLDS, **(thresholds or {})}
    metrics = compute_agent_runtime_metrics(orchestration_summary)
    runtime_summary = _agent_runtime_summary(orchestration_summary)
    decision = build_agent_runtime_deployment_decision(
        metrics=metrics,
        guard_analysis=guard_analysis,
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
            "source_contracts": runtime_summary.get("source_contracts", {}),
        },
        "agent_runtime_summary": {
            "agents": _agent_summaries(runtime_summary),
            "totals": _totals(runtime_summary),
            "metrics": metrics,
            "timeline_summary": _timeline_summary(orchestration_summary, metrics),
            "policy_decision_reasons": metrics["policy_decision_reasons"],
            "policy_decision_log_count": len(_policy_log(orchestration_summary)),
        },
        "guard_summary": _guard_summary(guard_analysis),
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
        "policy_decision_reasons": policy_decision_reasons,
        "top_policy_decision_reason": _top_reason(policy_decision_reasons),
    }


def load_agent_runtime_reliability_bundle(
    *,
    orchestration_summary_path: str | Path,
    guard_analysis_path: str | Path | None = None,
) -> dict[str, Any]:
    orchestration_summary = _load_json_dict(orchestration_summary_path)
    guard_analysis = _load_json_dict(guard_analysis_path) if guard_analysis_path else None
    return build_agent_runtime_reliability_report(
        orchestration_summary=orchestration_summary,
        guard_analysis=guard_analysis,
        source={
            "orchestration_summary_path": str(orchestration_summary_path),
            "guard_analysis_path": str(guard_analysis_path)
            if guard_analysis_path
            else None,
        },
    )


def build_agent_runtime_reliability_markdown(report: dict[str, Any]) -> str:
    runtime = report["agent_runtime_summary"]
    metrics = runtime["metrics"]
    decision = report["agent_deployment_decision"]
    guard = report["guard_summary"]

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
            f"| top_policy_decision_reason | {metrics.get('top_policy_decision_reason') or '-'} |",
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
    run = orchestration_summary.get("run")
    if isinstance(run, dict) and isinstance(run.get("scenario_mode"), str):
        return run["scenario_mode"]
    sustained_summary = _sustained_runtime_summary(orchestration_summary)
    if isinstance(sustained_summary.get("scenario_mode"), str):
        return sustained_summary["scenario_mode"]
    return "unknown"


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


def _timeline_summary(
    orchestration_summary: dict[str, Any],
    metrics: dict[str, Any],
) -> dict[str, Any]:
    return {
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
