from __future__ import annotations

from typing import Any, Dict, Optional


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
    lines.append(f"- status: {guard_analysis.get('status')}")

    if guard_analysis.get("status") == "skipped":
        lines.append(f"- reason: {guard_analysis.get('reason')}")
        lines.append("")
        return

    lines.append(f"- confidence: {guard_analysis.get('confidence')}")

    for field in ("anomalies", "suspected_causes", "recommendations"):
        lines.append(f"- {field}:")
        values = guard_analysis.get(field) or []
        if values:
            for value in values:
                lines.append(f"  - {value}")
        else:
            lines.append("  - -")
    lines.append("")


def _append_deployment_decision(lines: list[str], deployment_decision: Dict[str, Any]) -> None:
    lines.append("## Deployment Decision")
    lines.append("")
    lines.append(f"- decision: {deployment_decision.get('decision')}")
    lines.append(f"- reason: {deployment_decision.get('reason')}")
    lines.append(f"- lab_overall: {deployment_decision.get('lab_overall')}")
    lines.append(f"- guard_status: {deployment_decision.get('guard_status')}")
    lines.append(f"- recommended_action: {deployment_decision.get('recommended_action')}")
    lines.append("")


def generate_compare_markdown(
    compare_result: Dict[str, Any],
    judgement: Dict[str, Any],
    guard_analysis: Dict[str, Any] | None = None,
    deployment_decision: Dict[str, Any] | None = None,
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

    if deployment_decision is not None:
        _append_deployment_decision(lines, deployment_decision)

    return "\n".join(lines)
