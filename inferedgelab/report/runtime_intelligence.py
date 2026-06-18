from __future__ import annotations

from typing import Any

from inferedgelab.services.guard_analysis import guard_status, guard_verdict


RUNTIME_OPERATION_ANOMALY_TYPES = {
    "runtime_queue_overload",
    "runtime_thermal_instability",
}

ORCHESTRATOR_PRODUCER_LINEAGE_EVIDENCE_TYPE = (
    "edgeenv_orchestrator_producer_lineage"
)

ORCHESTRATOR_OPERATION_RISK_EVIDENCE_TYPE = (
    "edgeenv_orchestrator_operation_risk_summary"
)

ORCHESTRATOR_OPERATION_RISK_ROLLUP_EVIDENCE_TYPE = (
    "edgeenv_orchestrator_operation_risk_rollup"
)

ORCHESTRATOR_TASK_EVENT_ROLLUP_EVIDENCE_TYPE = (
    "edgeenv_orchestrator_task_event_rollup"
)

ORCHESTRATOR_OPERATION_TIMELINE_EVIDENCE_TYPE = (
    "edgeenv_orchestrator_operation_timeline_summary"
)

ORCHESTRATOR_SCHEDULER_FAIRNESS_EVIDENCE_TYPE = (
    "edgeenv_orchestrator_scheduler_fairness_summary"
)

RUN_CONFIG_TRACEABILITY_EVIDENCE_TYPE = "runtime_history_seed_run_config_traceability"

REMOTE_RUNTIME_EVENT_SUMMARY_MISMATCH_EVIDENCE_TYPE = (
    "remote_runtime_event_summary_mismatch"
)

REMOTE_DISPATCH_EVIDENCE_TYPES = {
    "remote_execution_failed",
    "remote_execution_recovered_by_fallback",
    "remote_fallback_execution_failed",
    "remote_execution_plan_only",
    "remote_execution_starter_success",
    REMOTE_RUNTIME_EVENT_SUMMARY_MISMATCH_EVIDENCE_TYPE,
}
REMOTE_FALLBACK_LAB_CONTEXT_LABEL = "Remote fallback starter evidence"

REVIEWER_OPERATION_QUICK_SCAN_LABEL = "Reviewer operation quick scan"
REVIEWER_OPERATION_QUICK_SCAN_RAW_MARKER = "reviewer_focus_operation_quick_scan"
EDGEENV_FIXTURE_MATRIX_LABEL = "EdgeEnv fixture matrix coverage"

RUN_CONFIG_MARKER_FIELDS = (
    "input_mode",
    "input_preprocess",
    "power_mode",
    "jetson_clocks",
    "warmup",
    "runs",
)


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
        fixture_matrix_label = _edgeenv_fixture_matrix_label(edgeenv_regression)
        if fixture_matrix_label:
            rows.append(
                (
                    EDGEENV_FIXTURE_MATRIX_LABEL,
                    fixture_matrix_label,
                    "EdgeEnv replay fixture coverage is reviewer navigation context; Lab does not recompute registry or comparability ownership.",
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
        _append_aiguard_runtime_operation_rows(
            rows,
            guard_analysis,
            warning_items,
            evidence_items,
        )
        _append_aiguard_max_queue_traceability_row(
            rows,
            edgeenv_regression,
            evidence_items,
            guard_analysis,
        )
        _append_aiguard_remote_dispatch_rows(rows, guard_analysis, evidence_items)
        _append_aiguard_run_config_traceability_row(rows, evidence_items)

    return rows


def build_runtime_intelligence_reviewer_focus_rows(
    *,
    guard_analysis: dict[str, Any] | None,
    deployment_decision: dict[str, Any] | None,
    edgeenv_regression: dict[str, Any] | None,
) -> list[tuple[str, str, str]]:
    if guard_analysis is None and edgeenv_regression is None:
        return []

    rows: list[tuple[str, str, str]] = []
    if deployment_decision is not None:
        triggered_rules = _string_list(deployment_decision.get("triggered_rules"))
        rows.append(
            (
                "Decision owner",
                (
                    f"Lab={deployment_decision.get('decision')}; "
                    f"triggered_rules={_compact_join(triggered_rules)}"
                ),
                "Start here: Lab is the final policy owner and downstream evidence is context.",
            )
        )

    if edgeenv_regression is not None:
        rows.append(_edgeenv_reviewer_focus_row(edgeenv_regression))
        fixture_matrix_row = _edgeenv_fixture_matrix_reviewer_focus_row(
            edgeenv_regression
        )
        if fixture_matrix_row is not None:
            rows.append(fixture_matrix_row)
        telemetry_row = _telemetry_reviewer_focus_row(edgeenv_regression)
        if telemetry_row is not None:
            rows.append(telemetry_row)
        operation_quick_scan_row = _operation_quick_scan_reviewer_focus_row(
            edgeenv_regression
        )
        if operation_quick_scan_row is not None:
            rows.append(operation_quick_scan_row)
        operation_row = _operation_reviewer_focus_row(edgeenv_regression)
        if operation_row is not None:
            rows.append(operation_row)

    if guard_analysis is not None:
        rows.append(_aiguard_reviewer_focus_row(guard_analysis))

    return rows


def _edgeenv_reviewer_focus_row(
    edgeenv_regression: dict[str, Any],
) -> tuple[str, str, str]:
    comparability = edgeenv_regression.get("comparability") or {}
    evidence = edgeenv_regression.get("evidence")
    if not isinstance(evidence, dict):
        evidence = {}
    metric_parts = [
        _focus_percent("mean", evidence.get("mean_delta_pct")),
        _focus_percent("p99", evidence.get("p99_delta_pct")),
        _focus_percent("fps", evidence.get("fps_delta_pct")),
        _focus_percent("memory", evidence.get("memory_peak_delta_pct")),
    ]
    metric_label = _compact_join([part for part in metric_parts if part])
    return (
        "EdgeEnv regression gate",
        (
            f"comparable={_first_present(comparability.get('comparable'), edgeenv_regression.get('comparable'))}; "
            f"mode={edgeenv_regression.get('mode')}; "
            f"regression={edgeenv_regression.get('regression_detected')}; "
            f"type={edgeenv_regression.get('regression_type')}; "
            f"severity={edgeenv_regression.get('severity')}; "
            f"deltas={metric_label}"
        ),
        "Check comparability first, then read latency/resource deltas as deployment risk evidence.",
    )


def _edgeenv_fixture_matrix_reviewer_focus_row(
    edgeenv_regression: dict[str, Any],
) -> tuple[str, str, str] | None:
    label = _edgeenv_fixture_matrix_label(edgeenv_regression)
    if not label:
        return None
    return (
        "EdgeEnv fixture matrix",
        label,
        "Confirms EdgeEnv replay fixture roles are visible before opening detailed regression evidence.",
    )


def _edgeenv_fixture_matrix_label(edgeenv_regression: dict[str, Any]) -> str:
    context = _edgeenv_fixture_matrix_context(edgeenv_regression)
    if context is None:
        return ""

    required_roles = _fixture_matrix_required_roles(context)
    covered_roles = _fixture_matrix_covered_roles(context)
    modes = _fixture_matrix_modes(context)
    telemetry_gap_roles = _fixture_matrix_roles_with_flag(
        context,
        "telemetry_gap_expected",
    )
    replay_sequence_roles = _fixture_matrix_replay_sequence_roles(context)
    boundaries = context.get("boundaries")
    if not isinstance(boundaries, dict):
        boundaries = context

    required_count = _first_present(
        context.get("required_role_count"),
        len(required_roles) if required_roles else None,
    )
    covered_count = _first_present(
        context.get("covered_role_count"),
        len(covered_roles) if covered_roles else None,
    )

    parts: list[str] = []
    schema_version = context.get("schema_version")
    if schema_version is not None:
        parts.append(f"schema={schema_version}")
    owner = context.get("owner")
    if owner is not None:
        parts.append(f"owner={owner}")
    if covered_count is not None or required_count is not None:
        parts.append(
            f"roles={_format_compact_value(covered_count or '-')}/"
            f"{_format_compact_value(required_count or '-')}"
        )
    if modes:
        parts.append(f"modes={_compact_join(modes, limit=4)}")
    if telemetry_gap_roles:
        parts.append(f"telemetry_gap={_compact_join(telemetry_gap_roles, limit=2)}")
    if replay_sequence_roles:
        parts.append(
            f"replay_sequence={_compact_join(replay_sequence_roles, limit=2)}"
        )

    comparability_first = _first_present(
        boundaries.get("comparability_first"),
        context.get("comparability_first"),
    )
    if comparability_first is not None:
        parts.append(f"comparability_first={comparability_first}")

    for field in (
        "not_a_deployment_decision",
        "not_a_guard_analysis",
        "not_production_monitoring",
    ):
        value = _first_present(boundaries.get(field), context.get(field))
        if value is not None:
            parts.append(f"{field}={value}")

    return "; ".join(parts)


def _edgeenv_fixture_matrix_context(
    edgeenv_regression: dict[str, Any],
) -> dict[str, Any] | None:
    for field in (
        "fixture_matrix_context",
        "regression_fixture_matrix",
        "fixture_matrix",
    ):
        context = edgeenv_regression.get(field)
        if isinstance(context, dict):
            return context

    telemetry_context = edgeenv_regression.get("runtime_telemetry_context")
    if isinstance(telemetry_context, dict):
        context = telemetry_context.get("fixture_matrix_context")
        if isinstance(context, dict):
            return context
    return None


def _fixture_matrix_required_roles(context: dict[str, Any]) -> list[str]:
    roles = _string_list(context.get("required_roles"))
    if roles:
        return roles
    role_coverage = context.get("role_coverage")
    if isinstance(role_coverage, dict):
        return _string_list(role_coverage.get("required_roles"))
    return []


def _fixture_matrix_covered_roles(context: dict[str, Any]) -> list[str]:
    roles = _string_list(context.get("covered_roles"))
    if roles:
        return roles
    role_coverage = context.get("role_coverage")
    if isinstance(role_coverage, dict):
        roles = _string_list(role_coverage.get("covered_roles"))
        if roles:
            return roles
    fixtures = context.get("fixtures")
    if not isinstance(fixtures, list):
        return []
    return [
        str(item.get("role"))
        for item in fixtures
        if isinstance(item, dict) and isinstance(item.get("role"), str)
    ]


def _fixture_matrix_modes(context: dict[str, Any]) -> list[str]:
    modes = _string_list(context.get("covered_modes"))
    if modes:
        return modes
    fixtures = context.get("fixtures")
    if not isinstance(fixtures, list):
        return []
    unique_modes: list[str] = []
    for item in fixtures:
        if not isinstance(item, dict):
            continue
        mode = item.get("mode")
        if isinstance(mode, str) and mode and mode not in unique_modes:
            unique_modes.append(mode)
    return unique_modes


def _fixture_matrix_roles_with_flag(
    context: dict[str, Any],
    field: str,
) -> list[str]:
    roles = _string_list(context.get(field + "_roles"))
    if roles:
        return roles
    fixtures = context.get("fixtures")
    if not isinstance(fixtures, list):
        return []
    return [
        str(item.get("role"))
        for item in fixtures
        if isinstance(item, dict)
        and item.get(field) is True
        and isinstance(item.get("role"), str)
    ]


def _fixture_matrix_replay_sequence_roles(context: dict[str, Any]) -> list[str]:
    roles = _string_list(context.get("replay_sequence_roles"))
    if roles:
        return roles
    fixtures = context.get("fixtures")
    if not isinstance(fixtures, list):
        return []
    return [
        str(item.get("role"))
        for item in fixtures
        if isinstance(item, dict)
        and (
            item.get("sequence_context") is not None
            or item.get("role") == "replay_sequence_context"
        )
        and isinstance(item.get("role"), str)
    ]


def _telemetry_reviewer_focus_row(
    edgeenv_regression: dict[str, Any],
) -> tuple[str, str, str] | None:
    telemetry_context = edgeenv_regression.get("runtime_telemetry_context")
    if not isinstance(telemetry_context, dict):
        return None

    gaps = [
        gap
        for gap in telemetry_context.get("evidence_gaps") or []
        if isinstance(gap, dict)
    ]
    history = telemetry_context.get("history") or {}
    history_summary = history.get("summary") if isinstance(history, dict) else {}
    if not isinstance(history_summary, dict):
        history_summary = {}
    coverage_labels = _runtime_telemetry_coverage_labels(telemetry_context)
    replay_labels = _runtime_replay_scope_labels(telemetry_context)

    return (
        "Telemetry/replay quality",
        (
            f"gaps={len(gaps)}; "
            f"history_missing_runs={history_summary.get('missing_telemetry_runs', '-')}; "
            f"run_config_seeds={history_summary.get('history_seed_run_config_runs', '-')}; "
            f"coverage={_compact_join(coverage_labels)}; "
            f"replay={_compact_join(replay_labels, limit=1)}"
        ),
        "Missing telemetry and replay scope are evidence-quality context, not failure or policy override.",
    )


def _operation_reviewer_focus_row(
    edgeenv_regression: dict[str, Any],
) -> tuple[str, str, str] | None:
    telemetry_context = edgeenv_regression.get("runtime_telemetry_context")
    if not isinstance(telemetry_context, dict):
        return None

    marker_labels = _orchestrator_queue_deadline_fallback_labels(telemetry_context)
    risk_labels = _orchestrator_operation_risk_labels(telemetry_context)
    preservation_labels = _edgeenv_preservation_run_labels(telemetry_context)
    task_labels = _orchestrator_task_event_rollup_labels(telemetry_context)
    if not any((marker_labels, risk_labels, preservation_labels, task_labels)):
        return None

    parts = [
        f"queue_deadline_fallback={'present' if marker_labels else 'missing'}",
        f"operation_risk={'present' if risk_labels else 'missing'}",
        f"device_local_preservation={'present' if preservation_labels else 'missing'}",
        f"task_rollup={'present' if task_labels else 'missing'}",
    ]
    return (
        "Operation context",
        "; ".join(parts),
        "Use this row to decide whether to scan Orchestrator/EdgeEnv operation evidence next.",
    )


def _operation_quick_scan_reviewer_focus_row(
    edgeenv_regression: dict[str, Any],
) -> tuple[str, str, str] | None:
    telemetry_context = edgeenv_regression.get("runtime_telemetry_context")
    if not isinstance(telemetry_context, dict):
        return None

    labels = _operation_quick_scan_focus_labels(telemetry_context)
    if not labels:
        return None

    return (
        "Operation quick scan",
        "; ".join(labels),
        "Start here for the compact queue/deadline/fallback signal and Jetson/device-local preservation identity.",
    )


def _aiguard_reviewer_focus_row(
    guard_analysis: dict[str, Any],
) -> tuple[str, str, str]:
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
    anomaly_types = sorted(
        {
            str(item.get("type"))
            for item in warning_items
            if item.get("type") in RUNTIME_OPERATION_ANOMALY_TYPES
        }
    )
    remote_dispatch_types = sorted(
        {
            str(item.get("type"))
            for item in evidence_items
            if item.get("type") in REMOTE_DISPATCH_EVIDENCE_TYPES
        }
    )
    return (
        "AIGuard warnings",
        (
            f"status={guard_status(guard_analysis)}; "
            f"verdict={guard_verdict(guard_analysis)}; "
            f"review_items={len(warning_items)}; "
            f"anomalies={_compact_join(anomaly_types)}; "
            f"remote_dispatch={_compact_join(remote_dispatch_types, limit=1)}"
        ),
        "AIGuard provides deterministic warning evidence; Lab keeps the final decision.",
    )


def _focus_percent(label: str, value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"{label}={value:+.1f}%"
    return f"{label}={value}"


def _compact_join(values: list[str], *, limit: int = 3) -> str:
    compact_values = [value for value in values if value]
    if not compact_values:
        return "none"
    if len(compact_values) <= limit:
        return ",".join(compact_values)
    visible = ",".join(compact_values[:limit])
    return f"{visible},+{len(compact_values) - limit} more"


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
    if "history_seed_runs" in history_summary:
        rows.append(
            (
                "Runtime telemetry history seed",
                str(history_summary.get("history_seed_runs")),
                "EdgeEnv preserves Runtime history seeds as replay traceability; Lab owns the final decision.",
            )
        )
    if "history_seed_run_config_runs" in history_summary:
        rows.append(
            (
                "Runtime history seed run_config",
                str(history_summary.get("history_seed_run_config_runs")),
                "Runtime run_config snapshots are replay/comparability context from EdgeEnv, not a Lab regression override.",
            )
        )

    replay_scope_labels = _runtime_replay_scope_labels(telemetry_context)
    if replay_scope_labels:
        rows.append(
            (
                "Runtime replay duration scope",
                "; ".join(replay_scope_labels),
                "Duration metadata helps reviewers choose the right replay bundle; it is navigation context and does not change Lab deployment policy.",
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

    operation_quick_scan_labels = _operation_quick_scan_labels(telemetry_context)
    if operation_quick_scan_labels:
        operation_quick_scan_labels = _append_operation_quick_scan_traceability(
            operation_quick_scan_labels
        )
        rows.append(
            (
                REVIEWER_OPERATION_QUICK_SCAN_LABEL,
                "; ".join(operation_quick_scan_labels),
                "One-line navigation labels combine queue/deadline/fallback and Jetson/device-local preservation context without changing Lab policy.",
            )
        )

    operation_risk_labels = _orchestrator_operation_risk_labels(telemetry_context)
    if operation_risk_labels:
        rows.append(
            (
                "Orchestrator operation risk summary",
                "; ".join(operation_risk_labels),
                "Operation risk markers are EdgeEnv-preserved navigation context; Lab still owns the deployment decision.",
            )
        )

    operation_marker_labels = _orchestrator_queue_deadline_fallback_labels(
        telemetry_context
    )
    if operation_marker_labels:
        rows.append(
            (
                "Orchestrator queue/deadline/fallback markers",
                "; ".join(operation_marker_labels),
                "Compact queue, deadline, and fallback markers point reviewers to operation evidence without changing Lab deployment policy.",
            )
        )

    preservation_labels = _edgeenv_preservation_run_labels(telemetry_context)
    if preservation_labels:
        preservation_detail_labels = _edgeenv_preservation_detail_labels(
            telemetry_context
        )
        rows.append(
            (
                "Jetson/device-local EdgeEnv preservation run",
                "; ".join(preservation_labels),
                "Device-local or Jetson starter evidence identity is preserved through EdgeEnv for Lab review; Lab remains the final decision owner.",
            )
        )
        if preservation_detail_labels:
            rows.append(
                (
                    "Jetson/device-local EdgeEnv preservation details",
                    "; ".join(preservation_detail_labels),
                    "Producer, stage, resource, and queue markers stay as navigation context rather than deployment decision policy.",
                )
            )
        rows.append(
            (
                "Lab EdgeEnv preservation context",
                "lab_report_preservation_context_present=True; lab_preservation=present; lab_context=present",
                "Lab-owned Runtime Intelligence gates use the same EdgeEnv preservation marker vocabulary as entrypoint evidence indexes.",
            )
        )

    task_event_labels = _orchestrator_task_event_rollup_labels(telemetry_context)
    if task_event_labels:
        rows.append(
            (
                "Orchestrator task event rollup",
                "; ".join(task_event_labels),
                "Task-level delay/fallback markers explain operation risk without making Orchestrator the deployment decision owner.",
            )
        )


def _runtime_telemetry_coverage_labels(context: dict[str, Any]) -> list[str]:
    history_labels = _history_telemetry_coverage_labels(context)
    if history_labels:
        return history_labels

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


def _history_telemetry_coverage_labels(context: dict[str, Any]) -> list[str]:
    history = context.get("history")
    if not isinstance(history, dict):
        return []
    coverage = history.get("telemetry_coverage")
    if not isinstance(coverage, dict):
        return []
    run_summaries = coverage.get("run_summaries")
    if isinstance(run_summaries, list):
        labels = _coverage_labels_from_run_summaries(context, run_summaries)
        if labels:
            return labels
    missing_field_runs = coverage.get("missing_field_runs")
    if isinstance(missing_field_runs, list):
        return _coverage_labels_from_missing_field_runs(context, missing_field_runs)
    return []


def _coverage_labels_from_run_summaries(
    context: dict[str, Any],
    run_summaries: list[Any],
) -> list[str]:
    summary_by_run_id = {
        item.get("run_id"): item
        for item in run_summaries
        if isinstance(item, dict) and isinstance(item.get("run_id"), str)
    }
    labels: list[str] = []
    for run_label in ("baseline", "candidate"):
        run_context = context.get(run_label)
        if not isinstance(run_context, dict):
            continue
        summary = summary_by_run_id.get(run_context.get("run_id"))
        if not isinstance(summary, dict):
            continue
        labels.append(f"{run_label}={_missing_fields_label(summary)}")
    return labels


def _coverage_labels_from_missing_field_runs(
    context: dict[str, Any],
    missing_field_runs: list[Any],
) -> list[str]:
    label_by_run_id: dict[str, str] = {}
    for item in missing_field_runs:
        if not isinstance(item, dict):
            continue
        run_id = item.get("run_id")
        if isinstance(run_id, str):
            label_by_run_id[run_id] = _missing_fields_label(item)
    labels: list[str] = []
    for run_label in ("baseline", "candidate"):
        run_context = context.get(run_label)
        if not isinstance(run_context, dict):
            continue
        run_id = run_context.get("run_id")
        if isinstance(run_id, str) and run_id in label_by_run_id:
            labels.append(f"{run_label}={label_by_run_id[run_id]}")
    return labels


def _missing_fields_label(payload: dict[str, Any]) -> str:
    missing_fields = payload.get("missing_fields")
    if not isinstance(missing_fields, list):
        missing_fields = []
    return ",".join(str(item) for item in missing_fields) if missing_fields else "none"


def _coverage_payload(run_context: dict[str, Any]) -> dict[str, Any] | None:
    coverage = run_context.get("telemetry_coverage")
    if isinstance(coverage, dict):
        return coverage
    coverage = run_context.get("history_telemetry_coverage")
    if isinstance(coverage, dict):
        return coverage
    return None


def _orchestrator_operation_risk_labels(context: dict[str, Any]) -> list[str]:
    labels: list[str] = []
    for run_label in ("baseline", "candidate"):
        run_context = context.get(run_label)
        if not isinstance(run_context, dict):
            continue
        operation_context = run_context.get("orchestrator_operation_context")
        if not isinstance(operation_context, dict):
            continue
        summary = operation_context.get("operation_risk_summary")
        if not isinstance(summary, dict):
            continue
        parts = _operation_risk_summary_parts(summary)
        if parts:
            labels.append(f"{run_label}: " + ", ".join(parts))
    return labels


def _operation_risk_summary_parts(summary: dict[str, Any]) -> list[str]:
    parts: list[str] = []
    field_labels = (
        ("queue_pressure_reason", "queue"),
        ("max_pressure_task", "max_task"),
        ("primary_health_reason", "health"),
        ("device_local_event_count", "device_local_events"),
        ("producer_event_count", "producer_events"),
    )
    for field, label in field_labels:
        value = summary.get(field)
        if value is None:
            continue
        parts.append(f"{label}={value}")
    degraded_workers = summary.get("degraded_worker_ids")
    if isinstance(degraded_workers, list) and degraded_workers:
        parts.append(
            "degraded_workers="
            + ",".join(str(item) for item in degraded_workers if item is not None)
        )
    return parts


def _orchestrator_queue_deadline_fallback_labels(
    context: dict[str, Any],
) -> list[str]:
    labels: list[str] = []
    for run_label in ("baseline", "candidate"):
        run_context = context.get(run_label)
        if not isinstance(run_context, dict):
            continue
        operation_context = run_context.get("orchestrator_operation_context")
        if not isinstance(operation_context, dict):
            continue

        candidate_context = operation_context.get("candidate_context")
        if not isinstance(candidate_context, dict):
            candidate_context = {}
        operation = candidate_context.get("operation")
        if not isinstance(operation, dict):
            operation = {}
        operation_summary = operation_context.get("operation_risk_summary")
        if not isinstance(operation_summary, dict):
            operation_summary = {}
        queue_state = operation_context.get("queue_state_summary")
        if not isinstance(queue_state, dict):
            queue_state = {}
        runtime_event_summary = operation_context.get("runtime_event_summary")
        if not isinstance(runtime_event_summary, dict):
            runtime_event_summary = {}

        parts: list[str] = []
        queue_pressure = _first_present(
            operation_summary.get("queue_pressure_reason"),
            queue_state.get("queue_pressure_reason"),
            operation.get("queue_pressure_reason"),
            candidate_context.get("queue_pressure_reason"),
        )
        if queue_pressure is not None:
            parts.append(f"queue_pressure_reason={queue_pressure}")

        max_total_queue_depth = _first_present(
            operation_summary.get("max_total_queue_depth"),
            queue_state.get("max_total_queue_depth"),
            operation.get("max_total_queue_depth"),
            candidate_context.get("max_total_queue_depth"),
        )
        if max_total_queue_depth is not None:
            parts.append(
                "max_total_queue_depth="
                f"{_format_compact_value(max_total_queue_depth)}"
            )
        else:
            queue_depth = _first_present(
                operation.get("queue_depth"),
                candidate_context.get("queue_depth"),
                run_context.get("queue_depth"),
            )
            if queue_depth is not None:
                parts.append(f"queue_depth={_format_compact_value(queue_depth)}")

        deadline_missed_count = _first_present(
            operation_summary.get("deadline_missed_count"),
            operation.get("deadline_missed_count"),
            runtime_event_summary.get("deadline_missed_count"),
            candidate_context.get("deadline_missed_count"),
        )
        if deadline_missed_count is not None:
            parts.append(
                "deadline_missed_count="
                f"{_format_compact_value(deadline_missed_count)}"
            )

        fallback_count = _first_present(
            operation_summary.get("fallback_count"),
            operation.get("fallback_count"),
            runtime_event_summary.get("fallback_count"),
            runtime_event_summary.get("fallback_decision_count"),
            candidate_context.get("fallback_count"),
        )
        if fallback_count is not None:
            parts.append(f"fallback_count={_format_compact_value(fallback_count)}")

        if parts:
            labels.append(f"{run_label}: " + ", ".join(parts))
    return labels


def _operation_quick_scan_labels(context: dict[str, Any]) -> list[str]:
    marker_by_run = _label_values_by_run(
        _orchestrator_queue_deadline_fallback_labels(context)
    )
    risk_by_run = _label_values_by_run(_orchestrator_operation_risk_labels(context))
    preservation_by_run = _label_values_by_run(
        _edgeenv_preservation_run_labels(context)
    )
    task_by_run = _label_values_by_run(_orchestrator_task_event_rollup_labels(context))

    labels: list[str] = []
    for run_label in ("baseline", "candidate"):
        parts: list[str] = []
        marker_label = marker_by_run.get(run_label)
        risk_label = risk_by_run.get(run_label)
        if marker_label:
            parts.append(marker_label)
        elif risk_label:
            parts.append(f"risk={risk_label}")

        preservation_label = preservation_by_run.get(run_label)
        if preservation_label:
            parts.append(f"preservation={preservation_label}")

        if task_by_run.get(run_label):
            parts.append("task_rollup=present")

        if parts:
            labels.append(f"{run_label}: " + "; ".join(parts))
    return labels


def _operation_quick_scan_focus_labels(context: dict[str, Any]) -> list[str]:
    marker_by_run = _label_values_by_run(
        _orchestrator_queue_deadline_fallback_labels(context)
    )
    risk_by_run = _label_values_by_run(_orchestrator_operation_risk_labels(context))
    preservation_by_run = _label_values_by_run(
        _edgeenv_preservation_run_labels(context)
    )
    task_by_run = _label_values_by_run(_orchestrator_task_event_rollup_labels(context))

    labels: list[str] = []
    for run_label in ("baseline", "candidate"):
        parts: list[str] = []
        marker_label = marker_by_run.get(run_label)
        risk_label = risk_by_run.get(run_label)
        operation_summary_label = _operation_summary_focus_label(context, run_label)
        if operation_summary_label:
            parts.append(f"operation_summary: {operation_summary_label}")
        elif marker_label:
            parts.append(_compact_operation_quick_scan_marker_label(marker_label))
        elif risk_label:
            parts.append(
                "risk="
                + _compact_operation_quick_scan_marker_label(risk_label)
            )

        preservation_label = preservation_by_run.get(run_label)
        if preservation_label:
            parts.append(
                "preservation="
                + _compact_operation_quick_scan_preservation_label(
                    preservation_label
                )
            )

        if task_by_run.get(run_label):
            parts.append("task_rollup=present")

        if parts:
            labels.append(f"{run_label}: " + "; ".join(parts))
    return labels


def _operation_summary_focus_label(
    context: dict[str, Any],
    run_label: str,
) -> str:
    run_context = context.get(run_label)
    if not isinstance(run_context, dict):
        return ""
    operation_context = run_context.get("orchestrator_operation_context")
    if not isinstance(operation_context, dict):
        return ""

    candidate_context = operation_context.get("candidate_context")
    if not isinstance(candidate_context, dict):
        candidate_context = {}
    operation = candidate_context.get("operation")
    if not isinstance(operation, dict):
        operation = {}
    operation_summary = operation_context.get("operation_risk_summary")
    if not isinstance(operation_summary, dict):
        operation_summary = {}
    queue_state = operation_context.get("queue_state_summary")
    if not isinstance(queue_state, dict):
        queue_state = {}
    runtime_event_summary = operation_context.get("runtime_event_summary")
    if not isinstance(runtime_event_summary, dict):
        runtime_event_summary = {}
    producer = candidate_context.get("producer")
    if not isinstance(producer, dict):
        producer = {}

    has_operation_signal = any(
        value is not None
        for value in (
            operation_summary.get("max_total_queue_depth"),
            queue_state.get("max_total_queue_depth"),
            operation.get("max_total_queue_depth"),
            candidate_context.get("max_total_queue_depth"),
            operation.get("queue_depth"),
            candidate_context.get("queue_depth"),
            operation_summary.get("queue_pressure_state"),
            queue_state.get("queue_pressure_state"),
            operation.get("queue_pressure_state"),
            operation_summary.get("queue_pressure_reason"),
            queue_state.get("queue_pressure_reason"),
            operation.get("queue_pressure_reason"),
            candidate_context.get("queue_pressure_reason"),
            operation_summary.get("deadline_missed_count"),
            operation.get("deadline_missed_count"),
            runtime_event_summary.get("deadline_missed_count"),
            candidate_context.get("deadline_missed_count"),
            operation_summary.get("fallback_count"),
            operation.get("fallback_count"),
            runtime_event_summary.get("fallback_count"),
            runtime_event_summary.get("fallback_decision_count"),
            candidate_context.get("fallback_count"),
            operation_summary.get("dropped_count"),
            operation.get("dropped_count"),
            runtime_event_summary.get("dropped_count"),
            runtime_event_summary.get("drop_count"),
            candidate_context.get("dropped_count"),
        )
    )
    if not has_operation_signal:
        return ""

    payloads = [
        operation_context,
        candidate_context,
        producer,
        operation_summary,
        run_context,
    ]
    mode = _first_payload_value(payloads, "scenario_mode")
    if mode is None and _has_device_local_signal(
        producer,
        operation_summary,
        candidate_context,
    ):
        mode = "device_local"

    max_queue = _first_present(
        operation_summary.get("max_total_queue_depth"),
        queue_state.get("max_total_queue_depth"),
        operation.get("max_total_queue_depth"),
        candidate_context.get("max_total_queue_depth"),
        operation.get("queue_depth"),
        candidate_context.get("queue_depth"),
        run_context.get("queue_depth"),
    )
    queue_pressure = _first_present(
        operation_summary.get("queue_pressure_state"),
        queue_state.get("queue_pressure_state"),
        operation.get("queue_pressure_state"),
        operation_summary.get("queue_pressure_reason"),
        queue_state.get("queue_pressure_reason"),
        operation.get("queue_pressure_reason"),
        candidate_context.get("queue_pressure_reason"),
    )
    deadline_missed = _first_present(
        operation_summary.get("deadline_missed_count"),
        operation.get("deadline_missed_count"),
        runtime_event_summary.get("deadline_missed_count"),
        candidate_context.get("deadline_missed_count"),
        0,
    )
    fallback = _first_present(
        operation_summary.get("fallback_count"),
        operation.get("fallback_count"),
        runtime_event_summary.get("fallback_count"),
        runtime_event_summary.get("fallback_decision_count"),
        candidate_context.get("fallback_count"),
        0,
    )
    dropped = _first_present(
        operation_summary.get("dropped_count"),
        operation.get("dropped_count"),
        runtime_event_summary.get("dropped_count"),
        runtime_event_summary.get("drop_count"),
        candidate_context.get("dropped_count"),
        0,
    )

    return (
        f"mode={mode or 'unknown'}, "
        f"max_queue={_format_compact_value(max_queue) if max_queue is not None else 'unknown'}, "
        f"queue_pressure={queue_pressure or 'unknown'}, "
        f"deadline_missed={_format_compact_value(deadline_missed)}, "
        f"fallback={_format_compact_value(fallback)}, "
        f"dropped={_format_compact_value(dropped)}"
    )


def _has_device_local_signal(*payloads: dict[str, Any]) -> bool:
    for payload in payloads:
        for value in payload.values():
            if isinstance(value, str) and "device_local" in value:
                return True
            if isinstance(value, list) and any(
                isinstance(item, str) and "device_local" in item for item in value
            ):
                return True
            if isinstance(value, dict) and _has_device_local_signal(value):
                return True
    return False


def _compact_operation_quick_scan_marker_label(label: str) -> str:
    replacements = (
        ("queue_pressure_reason=", "queue="),
        ("max_total_queue_depth=", "depth="),
        ("deadline_missed_count=", "deadline_miss="),
        ("fallback_count=", "fallback="),
        ("max_pressure_task=", "task="),
        ("primary_health_reason=", "health="),
        ("device_local_event_count=", "device_local_events="),
        ("producer_event_count=", "producer_events="),
    )
    compact = label
    for source, target in replacements:
        compact = compact.replace(source, target)
    return compact


def _compact_operation_quick_scan_preservation_label(label: str) -> str:
    return label.replace("identity=", "")


def _append_operation_quick_scan_traceability(labels: list[str]) -> list[str]:
    if not labels:
        return labels
    return [
        *labels,
        f"rendered_label={REVIEWER_OPERATION_QUICK_SCAN_LABEL}",
        f"raw_marker={REVIEWER_OPERATION_QUICK_SCAN_RAW_MARKER}",
    ]


def _label_values_by_run(labels: list[str]) -> dict[str, str]:
    values_by_run: dict[str, str] = {}
    for label in labels:
        if ": " not in label:
            continue
        run_label, value = label.split(": ", 1)
        if run_label and value and run_label not in values_by_run:
            values_by_run[run_label] = value
    return values_by_run


def _runtime_replay_scope_labels(context: dict[str, Any]) -> list[str]:
    labels: list[str] = []
    for run_label in ("baseline", "candidate"):
        run_context = context.get(run_label)
        if not isinstance(run_context, dict):
            continue
        label = _runtime_replay_scope_label(run_label, run_context)
        if label:
            labels.append(label)
    return labels


def _runtime_replay_scope_label(run_label: str, run_context: dict[str, Any]) -> str:
    operation_context = run_context.get("orchestrator_operation_context")
    if not isinstance(operation_context, dict):
        operation_context = {}
    candidate_context = operation_context.get("candidate_context")
    if not isinstance(candidate_context, dict):
        candidate_context = {}
    producer = candidate_context.get("producer")
    if not isinstance(producer, dict):
        producer = {}
    operation_summary = operation_context.get("operation_risk_summary")
    if not isinstance(operation_summary, dict):
        operation_summary = {}

    payloads = [
        run_context,
        operation_context,
        candidate_context,
        producer,
        operation_summary,
    ]
    duration_label = _first_payload_value(payloads, "duration_label")
    duration_class = _first_payload_value(payloads, "duration_class")
    duration_source = _first_payload_value(payloads, "duration_source")
    duration_scope_label = _first_payload_value(payloads, "duration_scope_label")
    frames = _first_payload_value(payloads, "frames")
    if frames is None:
        frames = _first_payload_value(payloads, "requested_frames")
    if frames is None:
        frames = _first_payload_value(payloads, "frame_count")

    parts: list[str] = []
    if duration_scope_label is not None:
        parts.append(f"scope_label={duration_scope_label}")
    elif duration_label is not None:
        parts.append(f"label={duration_label}")
        if duration_class is not None:
            parts.append(f"class={duration_class}")
        if frames is not None:
            parts.append(f"frames={_format_compact_value(frames)}")
    else:
        if duration_class is not None:
            parts.append(f"class={duration_class}")
        if frames is not None:
            parts.append(f"frames={_format_compact_value(frames)}")
    if duration_source is not None and str(duration_source) not in ",".join(parts):
        parts.append(f"source={duration_source}")
    if not parts:
        return ""
    return f"{run_label}: " + ", ".join(parts)


def _first_payload_value(payloads: list[dict[str, Any]], field: str) -> Any:
    for payload in payloads:
        value = payload.get(field)
        if value not in (None, ""):
            return value
        run_summary = payload.get("run_summary")
        if isinstance(run_summary, dict):
            value = run_summary.get(field)
            if value not in (None, ""):
                return value
    return None


def _edgeenv_preservation_run_labels(context: dict[str, Any]) -> list[str]:
    labels: list[str] = []
    for run_label in ("baseline", "candidate"):
        run_context = context.get(run_label)
        if not isinstance(run_context, dict):
            continue
        operation_context = run_context.get("orchestrator_operation_context")
        if not isinstance(operation_context, dict):
            continue
        label, _ = _edgeenv_preservation_run_label_pair(
            run_label,
            operation_context,
        )
        if label:
            labels.append(label)
    return labels


def _edgeenv_preservation_detail_labels(context: dict[str, Any]) -> list[str]:
    labels: list[str] = []
    for run_label in ("baseline", "candidate"):
        run_context = context.get(run_label)
        if not isinstance(run_context, dict):
            continue
        operation_context = run_context.get("orchestrator_operation_context")
        if not isinstance(operation_context, dict):
            continue
        _, detail_label = _edgeenv_preservation_run_label_pair(
            run_label,
            operation_context,
        )
        if detail_label:
            labels.append(detail_label)
    return labels


def _edgeenv_preservation_run_label_pair(
    run_label: str,
    operation_context: dict[str, Any],
) -> tuple[str, str]:
    candidate_context = operation_context.get("candidate_context")
    if not isinstance(candidate_context, dict):
        candidate_context = {}
    producer = candidate_context.get("producer")
    if not isinstance(producer, dict):
        producer = {}

    sources = _string_list(producer.get("device_local_producer_sources"))
    if not sources:
        sources = [
            source
            for source in _string_list(producer.get("producer_sources"))
            if _is_device_local_preservation_marker(source)
        ]
    stage_labels = _producer_stage_labels(producer.get("producer_stage_by_task"))
    resource = candidate_context.get("resource")
    if not isinstance(resource, dict):
        resource = {}
    operation_summary = operation_context.get("operation_risk_summary")
    if not isinstance(operation_summary, dict):
        operation_summary = {}

    device_local_count = _first_present(
        producer.get("device_local_event_count"),
        operation_summary.get("device_local_event_count"),
    )
    has_preservation_marker = (
        bool(sources)
        or any(_is_device_local_preservation_marker(label) for label in stage_labels)
        or device_local_count is not None
        or resource.get("source") == "tegrastats_timeline"
    )
    if not has_preservation_marker:
        return "", ""

    identity_parts: list[str] = ["identity=jetson_device_local_preservation"]
    stage_paths = _producer_stage_paths(stage_labels)
    if stage_paths:
        identity_parts.append("path=" + ",".join(stage_paths))
    run_id = _first_present(
        operation_context.get("run_id"),
        candidate_context.get("run_id"),
    )
    if run_id is not None:
        identity_parts.append(f"run={run_id}")

    detail_parts: list[str] = []
    if sources:
        detail_parts.append("sources=" + ",".join(sources))
    if stage_labels:
        detail_parts.append("stages=" + ",".join(stage_labels))
    if device_local_count is not None:
        detail_parts.append(
            f"device_local_events={_format_compact_value(device_local_count)}"
        )

    resource_source = resource.get("source")
    if resource_source is not None:
        detail_parts.append(f"resource={resource_source}")
    queue_pressure = operation_summary.get("queue_pressure_reason")
    if queue_pressure is not None:
        detail_parts.append(f"queue={queue_pressure}")

    identity_label = f"{run_label}: " + ", ".join(identity_parts)
    detail_label = f"{run_label}: " + ", ".join(detail_parts) if detail_parts else ""
    return identity_label, detail_label


def _producer_stage_labels(stage_by_task: Any) -> list[str]:
    if not isinstance(stage_by_task, dict):
        return []
    labels: list[str] = []
    for task_name, stage in stage_by_task.items():
        if (
            isinstance(task_name, str)
            and task_name
            and isinstance(stage, str)
            and stage
        ):
            labels.append(f"{task_name}:{stage}")
    return labels


def _producer_stage_paths(stage_labels: list[str]) -> list[str]:
    paths: list[str] = []
    for label in stage_labels:
        stage = label.split(":", 1)[1] if ":" in label else label
        if _is_device_local_preservation_marker(stage) and stage not in paths:
            paths.append(stage)
    return paths


def _is_device_local_preservation_marker(value: str) -> bool:
    normalized = value.lower()
    return "device_local" in normalized or "jetson" in normalized


def _orchestrator_task_event_rollup_labels(context: dict[str, Any]) -> list[str]:
    labels: list[str] = []
    for run_label in ("baseline", "candidate"):
        run_context = context.get(run_label)
        if not isinstance(run_context, dict):
            continue
        operation_context = run_context.get("orchestrator_operation_context")
        if not isinstance(operation_context, dict):
            continue
        operation = (
            (operation_context.get("candidate_context") or {}).get("operation")
            if isinstance(operation_context.get("candidate_context"), dict)
            else None
        )
        if not isinstance(operation, dict):
            continue
        summary = operation.get("runtime_task_event_summary")
        if not isinstance(summary, dict):
            continue
        task_labels = _task_event_summary_labels(summary)
        if task_labels:
            labels.append(f"{run_label}: " + ", ".join(task_labels))
    return labels


def _task_event_summary_labels(summary: dict[str, Any]) -> list[str]:
    labels: list[str] = []
    for task_name, task_summary in summary.items():
        if not isinstance(task_name, str) or not isinstance(task_summary, dict):
            continue
        parts = _task_event_summary_parts(task_summary)
        if parts:
            labels.append(f"{task_name}(" + ",".join(parts) + ")")
    return labels


def _task_event_summary_parts(task_summary: dict[str, Any]) -> list[str]:
    parts: list[str] = []
    field_labels = (
        ("scheduler_delay_event_count", "delay"),
        ("deadline_missed_count", "miss"),
        ("fallback_decision_count", "fallback"),
        ("max_scheduler_delay_cycles", "max_delay_cycles"),
        ("max_queue_wait_ms", "max_wait_ms"),
    )
    for field, label in field_labels:
        value = task_summary.get(field)
        if value is None:
            continue
        if isinstance(value, (int, float)) and not isinstance(value, bool) and value == 0:
            continue
        parts.append(f"{label}={_format_compact_value(value)}")

    reason_counts = task_summary.get("policy_decision_reason_counts")
    if isinstance(reason_counts, dict) and reason_counts:
        parts.append("policy=" + _format_reason_count_label(reason_counts))
    drop_counts = task_summary.get("drop_reason_counts")
    if isinstance(drop_counts, dict) and drop_counts:
        parts.append("drop=" + _format_reason_count_label(drop_counts))
    return parts


def _format_reason_count_label(reason_counts: dict[str, Any]) -> str:
    labels: list[str] = []
    for reason, count in reason_counts.items():
        if not isinstance(reason, str) or not reason:
            continue
        labels.append(f"{reason}:{_format_compact_value(count)}")
    return ",".join(labels)


def _append_aiguard_runtime_operation_rows(
    rows: list[tuple[str, str, str]],
    guard_analysis: dict[str, Any],
    warning_items: list[dict[str, Any]],
    evidence_items: list[dict[str, Any]],
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

    operation_risk_label = _aiguard_operation_risk_summary_label(evidence_items)
    if operation_risk_label:
        rows.append(
            (
                "AIGuard operation risk summary evidence",
                operation_risk_label,
                "AIGuard explains EdgeEnv-preserved operation risk markers; Lab still owns the deployment decision.",
            )
        )

    operation_risk_rollup_label = _aiguard_operation_risk_rollup_label(
        evidence_items
    )
    if operation_risk_rollup_label:
        rows.append(
            (
                "AIGuard operation risk rollup evidence",
                operation_risk_rollup_label,
                "AIGuard preserves compact operation risk rollup markers as deterministic warning context; Lab still owns the deployment decision.",
            )
        )

    task_event_rollup_label = _aiguard_task_event_rollup_label(evidence_items)
    if task_event_rollup_label:
        rows.append(
            (
                "AIGuard task event rollup evidence",
                task_event_rollup_label,
                "AIGuard preserves task-level scheduler/deadline/fallback evidence as deterministic review context; Lab still owns the deployment decision.",
            )
        )

    operation_timeline_label = _aiguard_operation_timeline_label(evidence_items)
    if operation_timeline_label:
        rows.append(
            (
                "AIGuard operation timeline evidence",
                operation_timeline_label,
                "AIGuard preserves compact queue/latency/policy timeline markers as deterministic navigation context; Lab still owns the deployment decision.",
            )
        )

    scheduler_fairness_label = _aiguard_scheduler_fairness_label(evidence_items)
    if scheduler_fairness_label:
        rows.append(
            (
                "AIGuard scheduler fairness evidence",
                scheduler_fairness_label,
                "AIGuard preserves scheduler fairness context as deterministic review evidence; Lab still owns the deployment decision.",
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

    producer_label = _aiguard_producer_lineage_label(edgeenv_metrics)
    if producer_label:
        rows.append(
            (
                "AIGuard producer lineage handoff",
                producer_label,
                "Device-local producer provenance is traceability evidence; Lab still owns the deployment decision.",
            )
        )

    guard_alignment_label = _aiguard_guard_alignment_label(
        edgeenv_metrics,
        evidence_items,
    )
    if guard_alignment_label:
        rows.append(
            (
                "AIGuard producer-lineage guard alignment",
                guard_alignment_label,
                "Orchestrator declares the downstream AIGuard evidence type while Lab remains the final decision owner.",
            )
        )

    seed_runs = edgeenv_metrics.get("history_telemetry_seed_runs")
    if seed_runs is not None:
        seed_schema = edgeenv_metrics.get(
            "candidate_runtime_telemetry_history_seed_schema_version"
        )
        registry_owner = edgeenv_metrics.get(
            "candidate_runtime_telemetry_history_seed_registry_owner"
        )
        decision_owner = edgeenv_metrics.get(
            "candidate_runtime_telemetry_history_seed_decision_owner"
        )
        point_count = edgeenv_metrics.get(
            "candidate_runtime_telemetry_history_seed_point_count"
        )
        rows.append(
            (
                "AIGuard history seed handoff",
                (
                    f"seeds={seed_runs}, schema={seed_schema}, "
                    f"registry={registry_owner}, decision={decision_owner}, "
                    f"candidate_points={point_count}"
                ),
                "AIGuard preserves EdgeEnv/Runtime seed markers as raw context, not as deployment policy.",
            )
        )

    run_config_label = _aiguard_history_seed_run_config_label(edgeenv_metrics)
    if run_config_label:
        rows.append(
            (
                "AIGuard history seed run_config markers",
                run_config_label,
                "Compact Runtime run_config markers improve replay traceability without changing Lab policy.",
            )
        )


def _append_aiguard_max_queue_traceability_row(
    rows: list[tuple[str, str, str]],
    edgeenv_regression: dict[str, Any] | None,
    evidence_items: list[dict[str, Any]],
    guard_analysis: dict[str, Any],
) -> None:
    label = _aiguard_max_queue_traceability_label(
        edgeenv_regression,
        evidence_items,
        guard_analysis,
    )
    if not label:
        return

    rows.append(
        (
            "AIGuard max queue raw-context traceability",
            label,
            (
                "The visible Lab max_total_queue_depth marker is traceable "
                "through AIGuard raw context to Orchestrator operation evidence; "
                "it remains review context, not a decision override."
            ),
        )
    )


def _aiguard_max_queue_traceability_label(
    edgeenv_regression: dict[str, Any] | None,
    evidence_items: list[dict[str, Any]],
    guard_analysis: dict[str, Any],
) -> str:
    report_values: dict[str, Any] = {}
    if isinstance(edgeenv_regression, dict):
        telemetry_context = edgeenv_regression.get("runtime_telemetry_context")
        if isinstance(telemetry_context, dict):
            report_values = _orchestrator_max_queue_depth_by_run(telemetry_context)

    raw_values = _aiguard_max_queue_raw_context_by_run(
        evidence_items,
        guard_analysis,
    )
    if not report_values or not raw_values:
        return ""

    labels: list[str] = []
    for run_label in ("baseline", "candidate"):
        report_value = report_values.get(run_label)
        raw_value = raw_values.get(run_label)
        if report_value is None or raw_value is None:
            continue
        labels.append(
            (
                f"{run_label}: report=max_total_queue_depth="
                f"{_format_compact_value(report_value)}, "
                f"raw_context=orchestrator_{run_label}_operation_"
                "max_total_queue_depth="
                f"{_format_compact_value(raw_value)}, "
                f"match={_compact_values_match(report_value, raw_value)}"
            )
        )
    return "; ".join(labels)


def _orchestrator_max_queue_depth_by_run(
    context: dict[str, Any],
) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for run_label in ("baseline", "candidate"):
        run_context = context.get(run_label)
        if not isinstance(run_context, dict):
            continue
        operation_context = run_context.get("orchestrator_operation_context")
        if not isinstance(operation_context, dict):
            continue

        candidate_context = operation_context.get("candidate_context")
        if not isinstance(candidate_context, dict):
            candidate_context = {}
        operation = candidate_context.get("operation")
        if not isinstance(operation, dict):
            operation = {}
        operation_summary = operation_context.get("operation_risk_summary")
        if not isinstance(operation_summary, dict):
            operation_summary = {}
        queue_state = operation_context.get("queue_state_summary")
        if not isinstance(queue_state, dict):
            queue_state = {}

        value = _first_present(
            operation_summary.get("max_total_queue_depth"),
            queue_state.get("max_total_queue_depth"),
            operation.get("max_total_queue_depth"),
            candidate_context.get("max_total_queue_depth"),
        )
        if value is not None:
            values[run_label] = value
    return values


def _aiguard_max_queue_raw_context_by_run(
    evidence_items: list[dict[str, Any]],
    guard_analysis: dict[str, Any],
) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for edgeenv_metrics in _aiguard_edgeenv_metric_sources(
        evidence_items,
        guard_analysis,
    ):
        for run_label in ("baseline", "candidate"):
            field = f"orchestrator_{run_label}_operation_max_total_queue_depth"
            value = edgeenv_metrics.get(field)
            if value is not None and run_label not in values:
                values[run_label] = value
    return values


def _aiguard_edgeenv_metric_sources(
    evidence_items: list[dict[str, Any]],
    guard_analysis: dict[str, Any],
) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for item in evidence_items:
        raw_context = item.get("raw_context")
        if not isinstance(raw_context, dict):
            continue
        edgeenv_metrics = raw_context.get("edgeenv_regression")
        if isinstance(edgeenv_metrics, dict):
            sources.append(edgeenv_metrics)

    candidate_summary = guard_analysis.get("candidate_summary")
    if isinstance(candidate_summary, dict):
        edgeenv_metrics = candidate_summary.get("edgeenv_regression")
        if isinstance(edgeenv_metrics, dict):
            sources.append(edgeenv_metrics)
    return sources


def _compact_values_match(left: Any, right: Any) -> bool:
    try:
        return float(left) == float(right)
    except (TypeError, ValueError):
        return str(left) == str(right)


def _append_aiguard_run_config_traceability_row(
    rows: list[tuple[str, str, str]],
    evidence_items: list[dict[str, Any]],
) -> None:
    evidence = _find_evidence_item(evidence_items, RUN_CONFIG_TRACEABILITY_EVIDENCE_TYPE)
    if evidence is None:
        return

    label = _aiguard_run_config_traceability_label(evidence)
    if not label:
        return
    rows.append(
        (
            "AIGuard run_config traceability evidence",
            label,
            "AIGuard confirms Runtime history seed run_config traceability; Lab still owns the deployment decision.",
        )
    )


def _aiguard_operation_risk_summary_label(
    evidence_items: list[dict[str, Any]],
) -> str:
    evidence = _find_evidence_item(
        evidence_items,
        ORCHESTRATOR_OPERATION_RISK_EVIDENCE_TYPE,
    )
    if evidence is None:
        return ""

    parts: list[str] = []
    status = evidence.get("status")
    if status is not None:
        parts.append(f"status={status}")
    observed = evidence.get("observed_value")
    if observed is not None:
        parts.append(f"markers={_format_compact_value(observed)}")

    raw_context = evidence.get("raw_context")
    if isinstance(raw_context, dict):
        context = raw_context.get("operation_risk_summary")
        if isinstance(context, dict):
            for field, label in (
                ("queue_pressure_reason", "queue"),
                ("max_pressure_task", "max_task"),
                ("primary_health_reason", "health"),
                ("device_local_event_count", "device_local_events"),
                ("producer_event_count", "producer_events"),
            ):
                value = context.get(field)
                if value is not None:
                    parts.append(f"{label}={_format_compact_value(value)}")
            degraded_workers = _string_list(context.get("degraded_worker_ids"))
            if degraded_workers:
                parts.append("degraded_workers=" + ",".join(degraded_workers))
            boundary_valid = context.get("boundary_markers_valid")
            if boundary_valid is not None:
                parts.append(f"boundary_valid={boundary_valid}")
    return ", ".join(parts)


def _aiguard_operation_risk_rollup_label(
    evidence_items: list[dict[str, Any]],
) -> str:
    evidence = _find_evidence_item(
        evidence_items,
        ORCHESTRATOR_OPERATION_RISK_ROLLUP_EVIDENCE_TYPE,
    )
    if evidence is None:
        return ""

    parts: list[str] = []
    status = evidence.get("status")
    if status is not None:
        parts.append(f"status={status}")
    observed = evidence.get("observed_value")
    if observed is not None:
        parts.append(f"markers={_format_compact_value(observed)}")

    raw_context = evidence.get("raw_context")
    if isinstance(raw_context, dict):
        context = raw_context.get("operation_risk_rollup")
        if isinstance(context, dict):
            for field, label in (
                ("risk_level", "risk"),
                ("queue_pressure_reason", "queue"),
                ("max_total_queue_depth", "max_queue"),
                ("deadline_missed_count", "deadline"),
                ("fallback_count", "fallback"),
                ("drop_count", "drop"),
                ("scheduler_delay_event_count", "scheduler_delay"),
            ):
                value = context.get(field)
                if value is not None:
                    parts.append(f"{label}={_format_compact_value(value)}")
            primary_reasons = _string_list(context.get("primary_reasons"))
            if primary_reasons:
                parts.append("reasons=" + ",".join(primary_reasons))
            affected_tasks = _string_list(context.get("affected_tasks"))
            if affected_tasks:
                parts.append("tasks=" + ",".join(affected_tasks))
            boundary_valid = context.get("boundary_markers_valid")
            if boundary_valid is not None:
                parts.append(f"boundary_valid={boundary_valid}")
    return ", ".join(parts)


def _aiguard_task_event_rollup_label(
    evidence_items: list[dict[str, Any]],
) -> str:
    evidence = _find_evidence_item(
        evidence_items,
        ORCHESTRATOR_TASK_EVENT_ROLLUP_EVIDENCE_TYPE,
    )
    if evidence is None:
        return ""

    parts: list[str] = []
    status = evidence.get("status")
    if status is not None:
        parts.append(f"status={status}")
    observed = evidence.get("observed_value")
    if observed is not None:
        parts.append(f"affected={_format_compact_value(observed)}")

    raw_context = evidence.get("raw_context")
    if isinstance(raw_context, dict):
        context = raw_context.get("task_event_rollup")
        if isinstance(context, dict):
            affected_tasks = _string_list(context.get("affected_tasks"))
            if affected_tasks:
                parts.append("tasks=" + ",".join(affected_tasks))
            deadline_tasks = _string_list(context.get("tasks_with_deadline_miss"))
            if deadline_tasks:
                parts.append("deadline=" + ",".join(deadline_tasks))
            fallback_tasks = _string_list(context.get("tasks_with_fallback"))
            if fallback_tasks:
                parts.append("fallback=" + ",".join(fallback_tasks))
            scheduler_delay_tasks = _string_list(
                context.get("tasks_with_scheduler_delay")
            )
            if scheduler_delay_tasks:
                parts.append("scheduler_delay=" + ",".join(scheduler_delay_tasks))
            reason_counts = context.get("reason_counts")
            if isinstance(reason_counts, dict) and reason_counts:
                parts.append("reasons=" + _format_reason_count_label(reason_counts))
            boundary_valid = context.get("boundary_markers_valid")
            if boundary_valid is not None:
                parts.append(f"boundary_valid={boundary_valid}")
    return ", ".join(parts)


def _aiguard_operation_timeline_label(
    evidence_items: list[dict[str, Any]],
) -> str:
    evidence = _find_evidence_item(
        evidence_items,
        ORCHESTRATOR_OPERATION_TIMELINE_EVIDENCE_TYPE,
    )
    if evidence is None:
        return ""

    parts: list[str] = []
    status = evidence.get("status")
    if status is not None:
        parts.append(f"status={status}")
    observed = evidence.get("observed_value")
    if observed is not None:
        parts.append(f"markers={_format_compact_value(observed)}")

    raw_context = evidence.get("raw_context")
    if isinstance(raw_context, dict):
        context = raw_context.get("operation_timeline_summary")
        if isinstance(context, dict):
            affected_tasks = _string_list(context.get("affected_tasks"))
            if affected_tasks:
                parts.append("tasks=" + ",".join(affected_tasks))
            review_hints = _string_list(context.get("review_hints"))
            if review_hints:
                parts.append("hints=" + ",".join(review_hints))
            queue_reason = context.get("queue_pressure_reason")
            if queue_reason is not None:
                parts.append(f"queue={_format_compact_value(queue_reason)}")
            max_wait = context.get("max_queue_wait_ms")
            if max_wait is not None:
                parts.append(f"max_wait_ms={_format_compact_value(max_wait)}")
            max_latency = context.get("max_latency_ms")
            if max_latency is not None:
                parts.append(
                    f"max_latency_ms={_format_compact_value(max_latency)}"
                )
            policy_count = context.get("policy_decision_count")
            if policy_count is not None:
                parts.append(f"policy_decisions={_format_compact_value(policy_count)}")
            policy_reasons = _string_list(context.get("policy_decision_reasons"))
            if policy_reasons:
                parts.append("policy=" + ",".join(policy_reasons))
            boundary_valid = context.get("boundary_markers_valid")
            if boundary_valid is not None:
                parts.append(f"boundary_valid={boundary_valid}")
    return ", ".join(parts)


def _aiguard_scheduler_fairness_label(
    evidence_items: list[dict[str, Any]],
) -> str:
    evidence = _find_evidence_item(
        evidence_items,
        ORCHESTRATOR_SCHEDULER_FAIRNESS_EVIDENCE_TYPE,
    )
    if evidence is None:
        return ""

    parts: list[str] = []
    status = evidence.get("status")
    if status is not None:
        parts.append(f"status={status}")
    observed = evidence.get("observed_value")
    if observed is not None:
        parts.append(f"markers={_format_compact_value(observed)}")

    raw_context = evidence.get("raw_context")
    if isinstance(raw_context, dict):
        context = raw_context.get("scheduler_fairness_summary")
        if isinstance(context, dict):
            protected_tasks = _string_list(context.get("protected_high_priority_tasks"))
            if protected_tasks:
                parts.append("protected=" + ",".join(protected_tasks))
            starvation_tasks = _string_list(context.get("tasks_with_starvation_risk"))
            if starvation_tasks:
                parts.append("starvation=" + ",".join(starvation_tasks))
            delay_tasks = _string_list(context.get("tasks_with_scheduler_delay"))
            if delay_tasks:
                parts.append("scheduler_delay=" + ",".join(delay_tasks))
            degraded_tasks = _string_list(context.get("tasks_with_degradation"))
            if degraded_tasks:
                parts.append("degraded=" + ",".join(degraded_tasks))
            boundary_valid = context.get("boundary_markers_valid")
            if boundary_valid is not None:
                parts.append(f"boundary_valid={boundary_valid}")
    return ", ".join(parts)


def _append_aiguard_remote_dispatch_rows(
    rows: list[tuple[str, str, str]],
    guard_analysis: dict[str, Any],
    evidence_items: list[dict[str, Any]],
) -> None:
    remote_dispatch = _aiguard_remote_dispatch_summary(
        guard_analysis,
        evidence_items,
    )
    if isinstance(remote_dispatch, dict):
        event_label = _remote_dispatch_event_summary_label(remote_dispatch)
        if event_label:
            rows.append(
                (
                    "AIGuard remote dispatch event summary",
                    event_label,
                    "Remote dispatch starter evidence is deterministic operation context; Lab remains the final decision owner.",
                )
            )

        consistency_label = _remote_runtime_event_consistency_label(remote_dispatch)
        if consistency_label:
            rows.append(
                (
                    "AIGuard remote event summary consistency",
                    consistency_label,
                    "Compact remote event summaries are checked before Lab reports trust them as operation context.",
                )
            )

        boundary_label = _remote_runtime_event_boundary_label(remote_dispatch)
        if boundary_label:
            rows.append(
                (
                    "AIGuard remote summary boundary",
                    boundary_label,
                    "Remote dispatch remains starter evidence only; Lab does not treat it as production remote execution.",
                )
            )

        fallback_context_label = _remote_fallback_lab_context_label(
            remote_dispatch,
            evidence_items,
        )
        if fallback_context_label:
            rows.append(
                (
                    REMOTE_FALLBACK_LAB_CONTEXT_LABEL,
                    fallback_context_label,
                    "Lab-facing remote fallback label matches the entrypoint registry while remaining starter-only review context.",
                )
            )

    evidence_types = sorted(
        {
            str(item.get("type"))
            for item in evidence_items
            if item.get("type") in REMOTE_DISPATCH_EVIDENCE_TYPES
        }
    )
    if evidence_types:
        rows.append(
            (
                "AIGuard remote dispatch evidence",
                ", ".join(evidence_types),
                "AIGuard warning evidence informs Lab review policy but does not own deployment decision.",
            )
        )


def _aiguard_remote_dispatch_summary(
    guard_analysis: dict[str, Any],
    evidence_items: list[dict[str, Any]],
) -> dict[str, Any] | None:
    candidate_summary = guard_analysis.get("candidate_summary")
    if isinstance(candidate_summary, dict):
        remote_dispatch = candidate_summary.get("remote_dispatch")
        if isinstance(remote_dispatch, dict):
            return remote_dispatch

    for item in evidence_items:
        raw_context = item.get("raw_context")
        if not isinstance(raw_context, dict):
            continue
        remote_dispatch = raw_context.get("remote_dispatch")
        if isinstance(remote_dispatch, dict):
            return remote_dispatch
    return None


def _remote_dispatch_event_summary_label(remote_dispatch: dict[str, Any]) -> str:
    event_summary = remote_dispatch.get("remote_runtime_event_summary")
    if not isinstance(event_summary, dict):
        event_summary = {}

    event_count = _first_present(
        remote_dispatch.get("remote_runtime_event_summary_runtime_event_count"),
        event_summary.get("runtime_event_count"),
        remote_dispatch.get("runtime_event_count"),
    )
    final_status = _first_present(
        remote_dispatch.get("remote_runtime_event_summary_final_status"),
        event_summary.get("final_status"),
        remote_dispatch.get("fallback_final_status"),
        remote_dispatch.get("execution_status"),
    )
    fallback_recovered = _first_present(
        remote_dispatch.get("remote_runtime_event_summary_fallback_recovered"),
        event_summary.get("fallback_recovered"),
        remote_dispatch.get("fallback_recovered"),
    )

    parts: list[str] = []
    if event_count is not None:
        parts.append(f"events={_format_compact_value(event_count)}")
    if final_status is not None:
        parts.append(f"final={final_status}")
    if fallback_recovered is not None:
        parts.append(f"fallback_recovered={fallback_recovered}")
    return ", ".join(parts)


def _remote_runtime_event_consistency_label(remote_dispatch: dict[str, Any]) -> str:
    event_summary = remote_dispatch.get("remote_runtime_event_summary")
    if not isinstance(event_summary, dict):
        event_summary = {}

    present = _first_present(
        remote_dispatch.get("remote_runtime_event_summary_present"),
        bool(event_summary) if event_summary else None,
    )
    consistent = _first_present(
        remote_dispatch.get("remote_runtime_event_summary_consistent"),
        event_summary.get("consistent"),
    )
    mismatch_errors = _string_list(
        remote_dispatch.get("remote_runtime_event_summary_mismatch_errors")
    )
    if not mismatch_errors:
        mismatch_errors = _string_list(event_summary.get("mismatch_errors"))

    if present is False:
        return "missing"
    if consistent is True:
        return "consistent"
    if consistent is False:
        return "mismatch=" + (",".join(mismatch_errors) if mismatch_errors else "unknown")
    return ""


def _remote_runtime_event_boundary_label(remote_dispatch: dict[str, Any]) -> str:
    event_summary = remote_dispatch.get("remote_runtime_event_summary")
    if not isinstance(event_summary, dict):
        event_summary = {}

    role = _first_present(
        remote_dispatch.get("remote_runtime_event_summary_evidence_role"),
        remote_dispatch.get("evidence_role"),
        event_summary.get("evidence_role"),
    )
    boundary = _first_present(
        remote_dispatch.get("remote_runtime_event_summary_operation_boundary"),
        remote_dispatch.get("operation_boundary"),
        event_summary.get("operation_boundary"),
    )
    production_remote_execution = _first_present(
        remote_dispatch.get("remote_runtime_event_summary_production_remote_execution"),
        remote_dispatch.get("production_remote_execution"),
        event_summary.get("production_remote_execution"),
    )
    parts = []
    if role is not None:
        parts.append(f"role={role}")
    if boundary is not None:
        parts.append(f"boundary={boundary}")
    if production_remote_execution is not None:
        parts.append(f"production_remote_execution={production_remote_execution}")
    if not parts:
        return ""
    return ", ".join(str(part) for part in parts)


def _remote_fallback_lab_context_label(
    remote_dispatch: dict[str, Any],
    evidence_items: list[dict[str, Any]],
) -> str:
    evidence_type = "remote_execution_recovered_by_fallback"
    evidence_types = {
        str(item.get("type"))
        for item in evidence_items
        if item.get("type") in REMOTE_DISPATCH_EVIDENCE_TYPES
    }
    event_summary = remote_dispatch.get("remote_runtime_event_summary")
    if not isinstance(event_summary, dict):
        event_summary = {}

    fallback_recovered = _first_present(
        remote_dispatch.get("remote_runtime_event_summary_fallback_recovered"),
        event_summary.get("fallback_recovered"),
        remote_dispatch.get("fallback_recovered"),
    )
    fallback_final_status = _first_present(
        remote_dispatch.get("fallback_final_status"),
        event_summary.get("final_status"),
    )
    if (
        evidence_type in evidence_types
        or fallback_recovered is True
        or str(fallback_final_status).lower() == "succeeded"
    ):
        return f"lab={REMOTE_FALLBACK_LAB_CONTEXT_LABEL}; evidence={evidence_type}"
    return ""


def _first_present(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _find_evidence_item(
    evidence_items: list[dict[str, Any]],
    evidence_type: str,
) -> dict[str, Any] | None:
    for item in evidence_items:
        if item.get("type") == evidence_type:
            return item
    return None


def _aiguard_run_config_traceability_label(evidence: dict[str, Any]) -> str:
    parts: list[str] = []
    status = evidence.get("status")
    if status is not None:
        parts.append(f"status={status}")

    observed = evidence.get("observed_value")
    baseline = evidence.get("baseline_value")
    if observed is not None or baseline is not None:
        observed_label = _format_compact_value(observed)
        baseline_label = _format_compact_value(baseline)
        parts.append(f"count={observed_label}/{baseline_label}")

    marker_labels = _aiguard_run_config_traceability_marker_labels(evidence)
    if marker_labels:
        parts.append("markers=" + "; ".join(marker_labels))
    return ", ".join(parts)


def _aiguard_run_config_traceability_marker_labels(
    evidence: dict[str, Any],
) -> list[str]:
    raw_context = evidence.get("raw_context")
    if not isinstance(raw_context, dict):
        return []

    context = raw_context.get("history_seed_run_config")
    if isinstance(context, dict):
        labels = _string_list(context.get("marker_labels"))
        if labels:
            return labels
        markers = context.get("markers")
        if isinstance(markers, str) and markers:
            return [markers]
        if isinstance(markers, dict):
            labels = _string_list(list(markers.values()))
            if labels:
                return labels

    edgeenv_metrics = raw_context.get("edgeenv_regression")
    if isinstance(edgeenv_metrics, dict):
        label = _aiguard_history_seed_run_config_label(edgeenv_metrics)
        return [label] if label else []

    return []


def _format_compact_value(value: Any) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _aiguard_producer_lineage_label(edgeenv_metrics: dict[str, Any]) -> str:
    sources = _string_list(
        edgeenv_metrics.get("orchestrator_candidate_device_local_producer_sources")
    )
    if not sources:
        sources = _string_list(
            edgeenv_metrics.get("orchestrator_candidate_producer_sources")
        )
    stage_by_task = edgeenv_metrics.get("orchestrator_candidate_producer_stage_by_task")
    stage_labels: list[str] = []
    if isinstance(stage_by_task, dict):
        for task_name, stage in stage_by_task.items():
            if (
                isinstance(task_name, str)
                and task_name
                and isinstance(stage, str)
                and stage
            ):
                stage_labels.append(f"{task_name}:{stage}")
    role = edgeenv_metrics.get("orchestrator_candidate_operation_context_role")
    event_count = edgeenv_metrics.get("orchestrator_candidate_device_local_event_count")

    parts: list[str] = []
    if sources:
        parts.append("sources=" + ",".join(sources))
    if stage_labels:
        parts.append("stages=" + ",".join(stage_labels))
    if event_count is not None:
        parts.append(f"device_local_events={event_count}")
    if role is not None:
        parts.append(f"role={role}")
    return ", ".join(parts)


def _aiguard_guard_alignment_label(
    edgeenv_metrics: dict[str, Any],
    evidence_items: list[dict[str, Any]],
) -> str:
    evidence_type = edgeenv_metrics.get(
        "orchestrator_guard_alignment_producer_lineage_evidence_type"
    )
    candidates = _string_list(
        edgeenv_metrics.get(
            "orchestrator_guard_alignment_operation_evidence_candidates"
        )
    )
    lab_owner = edgeenv_metrics.get(
        "orchestrator_guard_alignment_lab_is_final_decision_owner"
    )

    if not evidence_type:
        lineage_evidence = _find_evidence_item(
            evidence_items,
            ORCHESTRATOR_PRODUCER_LINEAGE_EVIDENCE_TYPE,
        )
        if isinstance(lineage_evidence, dict):
            producer_lineage = (lineage_evidence.get("raw_context") or {}).get(
                "producer_lineage"
            )
            if isinstance(producer_lineage, dict):
                evidence_type = producer_lineage.get(
                    "candidate_guard_alignment_producer_lineage_evidence_type"
                )
                candidates = _string_list(
                    producer_lineage.get(
                        "candidate_guard_alignment_operation_evidence_candidates"
                    )
                )

    parts: list[str] = []
    if isinstance(evidence_type, str) and evidence_type:
        parts.append(f"evidence={evidence_type}")
    if candidates:
        parts.append("candidates=" + ",".join(candidates))
    if lab_owner is not None:
        parts.append(f"lab_final_owner={str(lab_owner).lower()}")
    return ", ".join(parts)


def _aiguard_history_seed_run_config_label(edgeenv_metrics: dict[str, Any]) -> str:
    baseline = edgeenv_metrics.get("baseline_runtime_telemetry_history_seed_run_config")
    candidate = edgeenv_metrics.get(
        "candidate_runtime_telemetry_history_seed_run_config"
    )
    if not isinstance(baseline, dict) and not isinstance(candidate, dict):
        return ""

    if (
        isinstance(baseline, dict)
        and isinstance(candidate, dict)
        and baseline == candidate
    ):
        markers = _format_run_config_markers(candidate)
        return f"baseline/candidate={markers}" if markers else ""

    labels: list[str] = []
    if isinstance(baseline, dict):
        markers = _format_run_config_markers(baseline)
        if markers:
            labels.append(f"baseline={markers}")
    if isinstance(candidate, dict):
        markers = _format_run_config_markers(candidate)
        if markers:
            labels.append(f"candidate={markers}")
    return "; ".join(labels)


def _format_run_config_markers(run_config: dict[str, Any]) -> str:
    markers: list[str] = []
    shape = _run_config_shape_label(run_config)
    if shape:
        markers.append(f"shape={shape}")
    for field in RUN_CONFIG_MARKER_FIELDS:
        if field in run_config:
            markers.append(f"{field}={run_config.get(field)}")
    return ", ".join(markers)


def _run_config_shape_label(run_config: dict[str, Any]) -> str:
    batch = run_config.get("batch")
    height = run_config.get("height")
    width = run_config.get("width")
    if batch is None and height is None and width is None:
        return ""
    return f"{batch or '-'}x{height or '-'}x{width or '-'}"


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


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
