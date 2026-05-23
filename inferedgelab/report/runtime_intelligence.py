from __future__ import annotations

from typing import Any

from inferedgelab.services.guard_analysis import guard_status, guard_verdict


RUNTIME_OPERATION_ANOMALY_TYPES = {
    "runtime_queue_overload",
    "runtime_thermal_instability",
}


def build_runtime_intelligence_risk_rows(
    *,
    guard_analysis: dict[str, Any] | None,
    deployment_decision: dict[str, Any] | None,
    edgeenv_regression: dict[str, Any] | None,
) -> list[tuple[str, str, str]]:
    if guard_analysis is None and edgeenv_regression is None:
        return []

    rows: list[tuple[str, str, str]] = []
    if deployment_decision is not None:
        rows.append(
            (
                "Lab deployment decision",
                str(deployment_decision.get("decision")),
                "Lab remains the final deployment decision owner.",
            )
        )

    if edgeenv_regression is not None:
        comparability = edgeenv_regression.get("comparability") or {}
        rows.append(
            (
                "EdgeEnv comparability",
                (
                    f"{comparability.get('comparable', edgeenv_regression.get('comparable'))} / "
                    f"{edgeenv_regression.get('mode')}"
                ),
                "Regression evidence is interpreted only through EdgeEnv comparability judgement.",
            )
        )
        rows.append(
            (
                "Runtime regression",
                (
                    f"{edgeenv_regression.get('regression_detected')} / "
                    f"{edgeenv_regression.get('regression_type')} / "
                    f"{edgeenv_regression.get('severity')}"
                ),
                "Same-condition runtime regression is deployment risk evidence, not a leaderboard score.",
            )
        )
        _append_telemetry_context_rows(rows, edgeenv_regression)

    if guard_analysis is not None:
        evidence_items = [
            item
            for item in (guard_analysis.get("evidence") or [])
            if isinstance(item, dict)
        ]
        warning_items = [
            item
            for item in evidence_items
            if str(item.get("status")).lower() in {"warning", "failed", "error"}
        ]
        rows.append(
            (
                "AIGuard deterministic evidence",
                f"{guard_status(guard_analysis)} / {guard_verdict(guard_analysis)}",
                "AIGuard explains runtime/anomaly evidence but does not replace Lab decision policy.",
            )
        )
        if evidence_items:
            rows.append(
                (
                    "AIGuard evidence items needing review",
                    str(len(warning_items)),
                    "Review count is derived from deterministic evidence statuses.",
                )
            )
        _append_aiguard_runtime_operation_rows(rows, guard_analysis, warning_items)

    return rows


def _append_telemetry_context_rows(
    rows: list[tuple[str, str, str]],
    edgeenv_regression: dict[str, Any],
) -> None:
    telemetry_context = edgeenv_regression.get("runtime_telemetry_context")
    if not isinstance(telemetry_context, dict):
        return

    gaps = [
        gap
        for gap in telemetry_context.get("evidence_gaps") or []
        if isinstance(gap, dict)
    ]
    rows.append(
        (
            "Telemetry evidence gaps",
            str(len(gaps)),
            "Missing telemetry remains an evidence gap, not a benchmark failure.",
        )
    )

    history = telemetry_context.get("history") or {}
    history_summary = history.get("summary") or {}
    if "missing_telemetry_runs" in history_summary:
        rows.append(
            (
                "Telemetry history replay gaps",
                str(history_summary.get("missing_telemetry_runs")),
                "Replay coverage is reviewed separately from comparability gating.",
            )
        )
    if "orchestrator_feed_runs" in history_summary:
        rows.append(
            (
                "Orchestrator operation feed context",
                str(history_summary.get("orchestrator_feed_runs")),
                "EdgeEnv preserved Orchestrator context as supplemental telemetry evidence, not a comparability gate.",
            )
        )

    coverage_labels = _runtime_telemetry_coverage_labels(telemetry_context)
    if coverage_labels:
        rows.append(
            (
                "Runtime telemetry coverage gaps",
                "; ".join(coverage_labels),
                "Coverage gaps describe evidence quality and do not override EdgeEnv comparability gating.",
            )
        )

    context_labels = _orchestrator_context_labels(telemetry_context)
    if context_labels:
        rows.append(
            (
                "Orchestrator context attached runs",
                ", ".join(context_labels),
                "Attached operation context can explain runtime anomaly evidence without becoming a deployment decision.",
            )
        )


def _runtime_telemetry_coverage_labels(context: dict[str, Any]) -> list[str]:
    labels: list[str] = []
    for run_label in ("baseline", "candidate"):
        run_context = context.get(run_label)
        if not isinstance(run_context, dict):
            continue
        coverage = _coverage_payload(run_context)
        if coverage is None:
            continue
        missing_fields = coverage.get("missing_fields")
        if not isinstance(missing_fields, list):
            missing_fields = []
        missing_label = (
            ",".join(str(item) for item in missing_fields) if missing_fields else "none"
        )
        labels.append(f"{run_label}={missing_label}")
    return labels


def _coverage_payload(run_context: dict[str, Any]) -> dict[str, Any] | None:
    coverage = run_context.get("telemetry_coverage")
    if isinstance(coverage, dict):
        return coverage
    coverage = run_context.get("history_telemetry_coverage")
    if isinstance(coverage, dict):
        return coverage
    return None


def _append_aiguard_runtime_operation_rows(
    rows: list[tuple[str, str, str]],
    guard_analysis: dict[str, Any],
    warning_items: list[dict[str, Any]],
) -> None:
    anomaly_types = sorted(
        {
            str(item.get("type"))
            for item in warning_items
            if item.get("type") in RUNTIME_OPERATION_ANOMALY_TYPES
        }
    )
    if anomaly_types:
        rows.append(
            (
                "AIGuard runtime operation anomalies",
                ", ".join(anomaly_types),
                "Thermal/queue anomaly evidence is deterministic Lab review context; AIGuard does not own the final decision.",
            )
        )

    candidate_summary = guard_analysis.get("candidate_summary")
    if not isinstance(candidate_summary, dict):
        return
    edgeenv_metrics = candidate_summary.get("edgeenv_regression")
    if not isinstance(edgeenv_metrics, dict):
        return

    context_parts: list[str] = []
    feed_runs = edgeenv_metrics.get("history_orchestrator_feed_runs")
    if feed_runs is not None:
        context_parts.append(f"feeds={feed_runs}")
    if edgeenv_metrics.get("baseline_orchestrator_context_present") is True:
        context_parts.append("baseline")
    if edgeenv_metrics.get("candidate_orchestrator_context_present") is True:
        context_parts.append("candidate")
    if context_parts:
        rows.append(
            (
                "AIGuard Orchestrator context handoff",
                ", ".join(context_parts),
                "AIGuard interpreted EdgeEnv-preserved Orchestrator context as supplemental operation evidence.",
            )
        )


def _orchestrator_context_labels(telemetry_context: dict[str, Any]) -> list[str]:
    labels: list[str] = []
    for label in ("baseline", "candidate"):
        run_context = telemetry_context.get(label)
        if not isinstance(run_context, dict):
            continue
        if run_context.get("orchestrator_context_present") is True or isinstance(
            run_context.get("orchestrator_operation_context"),
            dict,
        ):
            labels.append(label)
    return labels
