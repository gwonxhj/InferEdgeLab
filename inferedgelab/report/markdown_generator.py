from __future__ import annotations

from typing import Any, Dict, Optional

from inferedgelab.report.runtime_intelligence import (
    build_runtime_intelligence_reviewer_focus_rows,
    build_runtime_intelligence_risk_rows,
)
from inferedgelab.services.guard_analysis import guard_primary_reason, guard_status, guard_verdict


def _fmt_num(v: Optional[float]) -> str:
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{v:.4f}"
    return str(v)


def _fmt_pct(v: Optional[float]) -> str:
    if v is None:
        return "-"
    return f"{v:+.2f}%"


def _fmt_pp(v: Optional[float]) -> str:
    if v is None:
        return "-"
    return f"{v:+.2f}pp"


def _sorted_accuracy_metric_items(accuracy: Dict[str, Any]) -> list[tuple[str, Dict[str, Any]]]:
    metrics = accuracy.get("metrics") or {}
    primary_metric = str(accuracy.get("metric_name") or "")

    ordered: list[tuple[str, Dict[str, Any]]] = []
    if primary_metric and primary_metric in metrics:
        ordered.append((primary_metric, metrics[primary_metric]))

    for metric_name, values in metrics.items():
        if metric_name == primary_metric:
            continue
        ordered.append((metric_name, values))

    return ordered


def _append_guard_analysis(lines: list[str], guard_analysis: Dict[str, Any]) -> None:
    lines.append("## Guard Analysis")
    lines.append("")
    normalized_status = guard_status(guard_analysis)
    normalized_verdict = guard_verdict(guard_analysis)
    lines.append(f"- status: {normalized_status}")
    if normalized_verdict is not None:
        lines.append(f"- guard_verdict: {normalized_verdict}")
    if guard_analysis.get("severity") is not None:
        lines.append(f"- severity: {guard_analysis.get('severity')}")

    if normalized_status == "skipped":
        lines.append(f"- reason: {guard_analysis.get('reason')}")
        lines.append("")
        return

    lines.append(f"- confidence: {guard_analysis.get('confidence')}")
    primary_reason = guard_primary_reason(guard_analysis)
    if primary_reason:
        lines.append(f"- primary_reason: {primary_reason}")

    source = guard_analysis.get("source")
    if isinstance(source, dict) and source:
        lines.append("- source:")
        for key, value in source.items():
            lines.append(f"  - {key}: `{value}`")

    for field in ("anomalies", "suspected_causes", "recommendations"):
        lines.append(f"- {field}:")
        values = guard_analysis.get(field) or []
        if values:
            for value in values:
                lines.append(f"  - {value}")
        else:
            lines.append("  - -")
    evidence = guard_analysis.get("evidence")
    if isinstance(evidence, list) and evidence:
        lines.append("")
        lines.append("### Guard Evidence")
        lines.append("")
        lines.append("| type | metric | observed | baseline | threshold | status | severity |")
        lines.append("| --- | --- | ---: | ---: | ---: | --- | --- |")
        for item in evidence:
            if not isinstance(item, dict):
                continue
            lines.append(
                "| "
                f"{item.get('type', '-')} | "
                f"{item.get('metric_name', '-')} | "
                f"{item.get('observed_value', '-')} | "
                f"{item.get('baseline_value', '-')} | "
                f"{item.get('threshold', '-')} | "
                f"{item.get('status', '-')} | "
                f"{item.get('severity', '-')} |"
            )
        for item in evidence:
            if not isinstance(item, dict):
                continue
            explanation = item.get("explanation")
            why_it_matters = item.get("why_it_matters")
            suspected_causes = item.get("suspected_causes") or []
            recommendation = item.get("recommendation")
            if explanation:
                lines.append(f"- {item.get('metric_name', 'evidence')}: {explanation}")
            if why_it_matters:
                lines.append(f"  - why_it_matters: {why_it_matters}")
            if suspected_causes:
                formatted_causes = ", ".join(str(cause) for cause in suspected_causes)
                lines.append(f"  - suspected_causes: {formatted_causes}")
            if recommendation:
                lines.append(f"  - recommendation: {recommendation}")
    lines.append("")


def _append_deployment_decision(lines: list[str], deployment_decision: Dict[str, Any]) -> None:
    lines.append("## Deployment Decision")
    lines.append("")
    lines.append(f"- policy_version: {deployment_decision.get('policy_version')}")
    lines.append(f"- decision: {deployment_decision.get('decision')}")
    lines.append(f"- reason: {deployment_decision.get('reason')}")
    lines.append(f"- lab_overall: {deployment_decision.get('lab_overall')}")
    lines.append(f"- guard_status: {deployment_decision.get('guard_status')}")
    lines.append(f"- recommended_action: {deployment_decision.get('recommended_action')}")
    triggered_rules = deployment_decision.get("triggered_rules") or []
    if triggered_rules:
        lines.append("- triggered_rules:")
        for rule in triggered_rules:
            lines.append(f"  - {rule}")
    policy_summary = deployment_decision.get("policy_summary") or []
    if policy_summary:
        lines.append("")
        lines.append("### Decision Policy Summary")
        lines.append("")
        lines.append("| rule | effect | description |")
        lines.append("|---|---|---|")
        for item in policy_summary:
            if not isinstance(item, dict):
                continue
            lines.append(
                "| "
                f"{item.get('rule', '-')} | "
                f"{item.get('effect', '-')} | "
                f"{item.get('description', '-')} |"
            )
    lines.append("")


def _append_edgeenv_regression(lines: list[str], edgeenv_regression: Dict[str, Any]) -> None:
    evidence = edgeenv_regression.get("evidence") or {}
    comparability = edgeenv_regression.get("comparability") or {}
    runtime_telemetry_context = edgeenv_regression.get("runtime_telemetry_context")
    triggered = evidence.get("triggered_thresholds") or []
    lines.append("## Runtime Regression Evidence")
    lines.append("")
    lines.append("- source: EdgeEnv Runtime Regression Monitor")
    lines.append(f"- comparable: {edgeenv_regression.get('comparable')}")
    lines.append(f"- mode: {edgeenv_regression.get('mode')}")
    lines.append(f"- regression_detected: {edgeenv_regression.get('regression_detected')}")
    lines.append(f"- regression_type: {edgeenv_regression.get('regression_type')}")
    lines.append(f"- severity: {edgeenv_regression.get('severity')}")
    lines.append(f"- recommendation: {edgeenv_regression.get('recommendation')}")
    lines.append(f"- comparability_judgement: {comparability.get('comparable')}")
    reasons = comparability.get("reasons") or []
    if reasons:
        lines.append("- comparability_reasons:")
        for reason in reasons:
            lines.append(f"  - {reason}")
    lines.append("")
    lines.append("| Evidence | Value |")
    lines.append("|---|---:|")
    for field in (
        "mean_delta_pct",
        "p95_delta_pct",
        "p99_delta_pct",
        "fps_delta_pct",
        "memory_peak_delta_pct",
    ):
        lines.append(f"| {field} | {_fmt_pct(evidence.get(field))} |")
    if triggered:
        lines.append("")
        lines.append("### Triggered Thresholds")
        lines.append("")
        lines.append("| name | metric | observed | threshold | severity |")
        lines.append("|---|---|---:|---:|---|")
        for item in triggered:
            if not isinstance(item, dict):
                continue
            lines.append(
                "| "
                f"{item.get('name', '-')} | "
                f"{item.get('metric', '-')} | "
                f"{_fmt_num(item.get('observed'))} | "
                f"{_fmt_num(item.get('threshold'))} | "
                f"{item.get('severity', '-')} |"
            )
    if isinstance(runtime_telemetry_context, dict):
        _append_runtime_telemetry_context(lines, runtime_telemetry_context)
    lines.append("")
    lines.append("> EdgeEnv regression evidence is local-first report context, not cloud monitoring, ranking, or production observability.")
    lines.append("")


def _append_runtime_telemetry_context(lines: list[str], context: Dict[str, Any]) -> None:
    history = context.get("history") or {}
    evidence_gaps = context.get("evidence_gaps") or []
    lines.append("")
    lines.append("### Runtime Telemetry Context")
    lines.append("")
    lines.append(f"- role: {context.get('role')}")
    lines.append(f"- source: {context.get('source')}")
    if history:
        lines.append(f"- history_schema_version: {history.get('schema_version')}")
        summary = history.get("summary") or {}
        if summary:
            lines.append("- history_summary:")
            for key in ("registered_runs", "telemetry_runs", "missing_telemetry_runs"):
                if key in summary:
                    lines.append(f"  - {key}: {summary.get(key)}")
        coverage = history.get("telemetry_coverage")
        if isinstance(coverage, dict):
            lines.append("- history_telemetry_coverage:")
            for key in ("runs_with_coverage", "missing_field_run_count"):
                if key in coverage:
                    lines.append(f"  - {key}: {coverage.get(key)}")
            lines.append(
                "  - missing_field_runs: "
                f"{_fmt_history_missing_field_runs(coverage)}"
            )
    lines.append("")
    lines.append(
        "| Run | telemetry_present | history_entry | execution_sequence_id | history_execution_sequence_id | telemetry_source | coverage_ratio | coverage_missing_fields | missing_is_failure |"
    )
    lines.append("|---|---|---|---:|---:|---|---:|---|---|")
    for label in ("baseline", "candidate"):
        run_context = context.get(label) or {}
        coverage = _runtime_telemetry_coverage(run_context)
        lines.append(
            "| "
            f"{label} `{run_context.get('run_id', '-')}` | "
            f"{run_context.get('result_telemetry_present')} | "
            f"{run_context.get('history_entry_present')} | "
            f"{_fmt_num(run_context.get('execution_sequence_id'))} | "
            f"{_fmt_num(run_context.get('history_execution_sequence_id'))} | "
            f"{run_context.get('telemetry_source', '-')} | "
            f"{_fmt_coverage_ratio(coverage)} | "
            f"{_fmt_coverage_missing_fields(coverage)} | "
            f"{_fmt_missing_is_failure(coverage)} |"
        )
    lines.append("")
    if evidence_gaps:
        lines.append("Runtime telemetry evidence gaps:")
        for gap in evidence_gaps:
            if not isinstance(gap, dict):
                continue
            lines.append(f"- {gap.get('run_id', '-')}: {gap.get('reason', '-')}")
    else:
        lines.append("Runtime telemetry evidence gaps: none")
    notes = context.get("notes") or []
    if notes:
        lines.append("")
        lines.append("Telemetry context notes:")
        for note in notes:
            lines.append(f"- {note}")


def _runtime_telemetry_coverage(run_context: Dict[str, Any]) -> Dict[str, Any] | None:
    coverage = run_context.get("telemetry_coverage")
    if isinstance(coverage, dict):
        return coverage
    coverage = run_context.get("history_telemetry_coverage")
    if isinstance(coverage, dict):
        return coverage
    return None


def _fmt_history_missing_field_runs(coverage: Dict[str, Any]) -> str:
    missing_field_runs = coverage.get("missing_field_runs")
    if not isinstance(missing_field_runs, list) or not missing_field_runs:
        return "none"
    labels: list[str] = []
    for item in missing_field_runs:
        if not isinstance(item, dict):
            continue
        missing_fields = item.get("missing_fields")
        if not isinstance(missing_fields, list):
            missing_fields = []
        fields = ",".join(str(field) for field in missing_fields) or "none"
        labels.append(f"{item.get('run_id', '-')}={fields}")
    return "; ".join(labels) if labels else "none"


def _fmt_coverage_ratio(coverage: Dict[str, Any] | None) -> str:
    if coverage is None:
        return "-"
    ratio = coverage.get("coverage_ratio")
    return _fmt_num(ratio)


def _fmt_coverage_missing_fields(coverage: Dict[str, Any] | None) -> str:
    if coverage is None:
        return "-"
    missing_fields = coverage.get("missing_fields")
    if not isinstance(missing_fields, list) or not missing_fields:
        return "none"
    return ", ".join(str(item) for item in missing_fields)


def _fmt_missing_is_failure(coverage: Dict[str, Any] | None) -> str:
    if coverage is None:
        return "-"
    value = coverage.get("missing_telemetry_is_failure")
    if value is None:
        return "-"
    return str(value)


def _append_runtime_intelligence_risk_summary(
    lines: list[str],
    *,
    guard_analysis: Dict[str, Any] | None,
    deployment_decision: Dict[str, Any] | None,
    edgeenv_regression: Dict[str, Any] | None,
) -> None:
    rows = build_runtime_intelligence_risk_rows(
        guard_analysis=guard_analysis,
        deployment_decision=deployment_decision,
        edgeenv_regression=edgeenv_regression,
    )
    if not rows:
        return

    focus_rows = build_runtime_intelligence_reviewer_focus_rows(
        guard_analysis=guard_analysis,
        deployment_decision=deployment_decision,
        edgeenv_regression=edgeenv_regression,
    )
    lines.append("## Runtime Intelligence Risk Summary")
    lines.append("")
    lines.append(
        "Review path: start with `Reviewer Focus`, then open `Detailed Evidence Rows` "
        "only for comparable regression, telemetry/replay gaps, operation quick scan, "
        "preserved run/path, or deterministic warning evidence. Lab remains the final "
        "deployment decision owner."
    )
    lines.append("")
    if focus_rows:
        lines.append("### Reviewer Focus")
        lines.append("")
        lines.append("| Focus | Quick signal | First read |")
        lines.append("|---|---|---|")
        for focus, value, first_read in focus_rows:
            lines.append(f"| {focus} | {value} | {first_read} |")
        lines.append("")
    lines.append("### Detailed Evidence Rows")
    lines.append("")
    lines.append("| Signal | Value | Lab interpretation |")
    lines.append("|---|---|---|")
    for signal, value, interpretation in rows:
        lines.append(f"| {signal} | {value} | {interpretation} |")
    lines.append("")


def generate_compare_markdown(
    compare_result: Dict[str, Any],
    judgement: Dict[str, Any],
    guard_analysis: Dict[str, Any] | None = None,
    deployment_decision: Dict[str, Any] | None = None,
    edgeenv_regression: Dict[str, Any] | None = None,
) -> str:
    """
    compare_results() 출력 dict를 Markdown 문서 문자열로 변환한다.
    """
    base_id = compare_result["base_id"]
    new_id = compare_result["new_id"]
    precision = compare_result["precision"]
    metrics = compare_result["metrics"]
    accuracy = compare_result["accuracy"]
    accuracy_metric_name = str(accuracy.get("metric_name") or "unknown")
    accuracy_metric_items = _sorted_accuracy_metric_items(accuracy)
    shape = compare_result["shape"]
    shape_context = compare_result["shape_context"]
    runtime_provenance = compare_result["runtime_provenance"]
    system_diff = compare_result["system_diff"]
    run_config_diff = compare_result["run_config_diff"]
    thresholds = judgement.get("thresholds", {})

    lines: list[str] = []

    lines.append("# EdgeBench Compare Report")
    lines.append("")
    lines.append("## Compared Results")
    lines.append("")
    lines.append(
        f"- Base: `{base_id['model']}` / `{base_id['engine']}` / `{base_id['device']}` / `{base_id['timestamp']}`"
    )
    lines.append(
        f"- New: `{new_id['model']}` / `{new_id['engine']}` / `{new_id['device']}` / `{new_id['timestamp']}`"
    )
    lines.append("")

    lines.append("## Precision Context")
    lines.append("")
    lines.append(f"- Base precision: **`{precision['base']}`**")
    lines.append(f"- New precision: **`{precision['new']}`**")
    lines.append(f"- Precision match: **{judgement['precision_match']}**")
    lines.append(f"- Comparison mode: **`{judgement['comparison_mode']}`**")
    lines.append(f"- Precision pair: **`{judgement['precision_pair']}`**")
    lines.append("")

    if not judgement["precision_match"]:
        lines.append("> [!WARNING]")
        lines.append("> This is a cross-precision comparison.")
        lines.append("> Interpret latency deltas as a precision trade-off signal, not a strict same-condition regression result.")
        lines.append("")

    lines.append("## Judgement")
    lines.append("")
    lines.append(f"- Overall: **{judgement['overall']}**")
    if judgement["comparison_mode"] == "cross_precision":
        lines.append("- Overall semantics: **trade-off status, not same-condition regression status**")
    lines.append(f"- Shape match: **{judgement['shape_match']}**")
    lines.append(f"- System match: **{judgement['system_match']}**")
    lines.append(f"- Mean judgement: **{judgement['mean_ms']}**")
    lines.append(f"- P99 judgement: **{judgement['p99_ms']}**")
    lines.append(f"- Accuracy judgement: **{judgement['accuracy']}**")
    lines.append(f"- Accuracy present: **{judgement['accuracy_present']}**")
    lines.append(f"- Primary accuracy metric: **`{accuracy_metric_name}`**")
    lines.append(f"- Trade-off risk: **{judgement['tradeoff_risk']}**")
    lines.append(f"- Summary: {judgement['summary']}")
    lines.append("")

    if judgement["notes"]:
        lines.append("## Notes")
        lines.append("")
        for note in judgement["notes"]:
            lines.append(f"- {note}")
        lines.append("")

    lines.append("## Runtime Provenance Summary")
    lines.append("")
    lines.append("| Field | Base | New |")
    lines.append("|---|---|---|")
    for field in (
        "runtime_artifact_path",
        "primary_input_name",
        "requested_shape_summary",
        "effective_shape_summary",
    ):
        lines.append(
            f"| {field} | {_fmt_num(runtime_provenance['base'].get(field))} | {_fmt_num(runtime_provenance['new'].get(field))} |"
        )
    lines.append("")

    lines.append("## Threshold Policy")
    lines.append("")
    lines.append("| Threshold | Value |")
    lines.append("|---|---:|")
    for key in (
        "latency_improve_threshold",
        "latency_regress_threshold",
        "accuracy_improve_threshold",
        "accuracy_regress_threshold",
        "tradeoff_caution_threshold",
        "tradeoff_risky_threshold",
        "tradeoff_severe_threshold",
    ):
        value = thresholds.get(key)
        suffix = "%" if "latency" in key else "pp"
        display = "-" if value is None else f"{float(value):+.2f}{suffix}"
        lines.append(f"| {key} | {display} |")
    lines.append("")

    lines.append("## Latency Comparison")
    lines.append("")
    lines.append("| Metric | Base | New | Delta | Delta % |")
    lines.append("|---|---:|---:|---:|---:|")
    for metric_name, values in metrics.items():
        lines.append(
            f"| {metric_name} | {_fmt_num(values['base'])} | {_fmt_num(values['new'])} | {_fmt_num(values['delta'])} | {_fmt_pct(values['delta_pct'])} |"
        )
    lines.append("")

    lines.append("## Accuracy Comparison")
    lines.append("")
    lines.append(f"- Task: **`{accuracy.get('task') or 'unknown'}`**")
    lines.append(f"- Primary metric: **`{accuracy_metric_name}`**")
    lines.append("")
    lines.append("| Metric | Base | New | Delta | Delta % | Delta pp |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for metric_name, values in accuracy_metric_items:
        metric_label = f"{metric_name} (primary)" if metric_name == accuracy_metric_name else metric_name
        lines.append(
            f"| {metric_label} | {_fmt_num(values.get('base'))} | {_fmt_num(values.get('new'))} | {_fmt_num(values.get('delta'))} | {_fmt_pct(values.get('delta_pct'))} | {_fmt_pp(values.get('delta_pp'))} |"
        )
    lines.append("")
    lines.append("| Field | Base | New |")
    lines.append("|---|---:|---:|")
    lines.append(
        f"| sample_count | {_fmt_num(accuracy['sample_count']['base'])} | {_fmt_num(accuracy['sample_count']['new'])} |"
    )
    lines.append("")

    lines.append("## Input Shape")
    lines.append("")
    lines.append("| Field | Base | New |")
    lines.append("|---|---:|---:|")
    for field in ("batch", "height", "width"):
        lines.append(
            f"| {field} | {_fmt_num(shape['base'].get(field))} | {_fmt_num(shape['new'].get(field))} |"
        )
    lines.append("")

    lines.append("## Input Shape Provenance")
    lines.append("")
    lines.append("| Field | Base | New |")
    lines.append("|---|---:|---:|")
    for field in (
        "requested_batch",
        "requested_height",
        "requested_width",
        "effective_batch",
        "effective_height",
        "effective_width",
        "primary_input_name",
    ):
        lines.append(
            f"| {field} | {_fmt_num(shape_context['base'].get(field))} | {_fmt_num(shape_context['new'].get(field))} |"
        )
    lines.append("")
    lines.append("### Resolved Input Shapes")
    lines.append("")
    lines.append(f"- Base: `{str(shape_context['base'].get('resolved_input_shapes'))}`")
    lines.append(f"- New: `{str(shape_context['new'].get('resolved_input_shapes'))}`")
    lines.append("")

    lines.append("## System Info")
    lines.append("")
    lines.append("| Field | Base | New |")
    lines.append("|---|---|---|")
    for field, values in system_diff.items():
        lines.append(
            f"| {field} | {_fmt_num(values['base'])} | {_fmt_num(values['new'])} |"
        )
    lines.append("")

    lines.append("## Run Config")
    lines.append("")
    lines.append("| Field | Base | New |")
    lines.append("|---|---:|---:|")
    for field, values in run_config_diff.items():
        lines.append(
            f"| {field} | {_fmt_num(values['base'])} | {_fmt_num(values['new'])} |"
        )
    lines.append("")

    if guard_analysis is not None:
        _append_guard_analysis(lines, guard_analysis)

    if edgeenv_regression is not None:
        _append_edgeenv_regression(lines, edgeenv_regression)

    _append_runtime_intelligence_risk_summary(
        lines,
        guard_analysis=guard_analysis,
        deployment_decision=deployment_decision,
        edgeenv_regression=edgeenv_regression,
    )

    if deployment_decision is not None:
        _append_deployment_decision(lines, deployment_decision)

    return "\n".join(lines)
