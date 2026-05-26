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

RUN_CONFIG_TRACEABILITY_EVIDENCE_TYPE = "runtime_history_seed_run_config_traceability"

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
        _append_aiguard_run_config_traceability_row(rows, evidence_items)

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
