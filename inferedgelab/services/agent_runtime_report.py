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
            "policy_decision_log_count": len(_policy_log(orchestration_summary)),
        },
        "guard_summary": _guard_summary(guard_analysis),
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
    totals = _totals(runtime_summary)
    executed_count = _non_negative_number(totals.get("executed_count"))
    dropped_count = _non_negative_number(totals.get("dropped_count"))
    deadline_missed_count = _non_negative_number(totals.get("deadline_missed_count"))
    fallback_count = _non_negative_number(totals.get("fallback_count"))
    total_task_events = executed_count + dropped_count
    policy_log = _policy_log(orchestration_summary)
    queue_backlog_count = sum(
        1
        for item in policy_log
        if "backlog" in str(item.get("reason", "")).lower()
        or "backlog" in str(item.get("decision", "")).lower()
    )
    return {
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
            "",
            "## AIGuard Runtime Reliability Evidence",
            "",
            f"- guard_status: `{guard.get('status')}`",
            f"- guard_verdict: `{guard.get('guard_verdict')}`",
            f"- severity: `{guard.get('severity')}`",
            f"- primary_reason: {guard.get('primary_reason')}",
            f"- evidence_count: `{guard.get('evidence_count')}`",
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
    return {
        "schema_version": guard_analysis.get("schema_version")
        if isinstance(guard_analysis, dict)
        else None,
        "status": guard_status(guard_analysis),
        "guard_verdict": guard_verdict(guard_analysis),
        "severity": guard_analysis.get("severity") if isinstance(guard_analysis, dict) else None,
        "primary_reason": guard_primary_reason(guard_analysis),
        "evidence_count": len(guard_evidence_items(guard_analysis)),
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
