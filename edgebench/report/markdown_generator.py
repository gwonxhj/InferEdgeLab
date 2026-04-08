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


def generate_compare_markdown(compare_result: Dict[str, Any], judgement: Dict[str, Any]) -> str:
    """
    compare_results() 출력 dict를 Markdown 문서 문자열로 변환한다.
    """
    base_id = compare_result["base_id"]
    new_id = compare_result["new_id"]
    precision = compare_result["precision"]
    metrics = compare_result["metrics"]
    accuracy = compare_result["accuracy"]
    accuracy_metric = accuracy["metrics"]["top1_accuracy"]
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
    lines.append("")
    lines.append("| Metric | Base | New | Delta | Delta % | Delta pp |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    lines.append(
        f"| top1_accuracy | {_fmt_num(accuracy_metric['base'])} | {_fmt_num(accuracy_metric['new'])} | {_fmt_num(accuracy_metric['delta'])} | {_fmt_pct(accuracy_metric['delta_pct'])} | {_fmt_pp(accuracy_metric['delta_pp'])} |"
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

    return "\n".join(lines)
