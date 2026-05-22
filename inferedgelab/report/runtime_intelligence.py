from __future__ import annotations

from typing import Any

from inferedgelab.services.guard_analysis import guard_status, guard_verdict


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
