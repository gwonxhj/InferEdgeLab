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

def generate_compare_markdown(compare_result: Dict[str, Any], judgement: Dict[str, Any]) -> str:
    """
    compare_results() 출력 dict를 Markdown 문서 문자열로 변환한다.
    """
    base_id = compare_result["base_id"]
    new_id = compare_result["new_id"]
    metrics = compare_result["metrics"]
    shape = compare_result["shape"]
    system_diff = compare_result["system_diff"]
    run_config_diff = compare_result["run_config_diff"]

    lines: list[str] = []

    lines.append("# EdgeBench Compare Report")
    lines.append("")
    lines.append("## Compared Results")
    lines.append("")
    lines.append(f"- Base: `{base_id['model']}` / `{base_id['engine']}` / `{base_id['device']}` / `{base_id['timestamp']}`")
    lines.append(f"- New: `{new_id['model']}` / `{new_id['engine']}` / `{new_id['device']}` / `{new_id['timestamp']}`")
    lines.append("")
    lines.append("## Judgement")
    lines.append("")
    lines.append(f"- Overall: **{judgement['overall']}**")
    lines.append(f"- Shape match: **{judgement['shape_match']}**")
    lines.append(f"- System match: **{judgement['system_match']}**")
    lines.append(f"- Mean judgement: **{judgement['mean_ms']}**")
    lines.append(f"- P99 judgement: **{judgement['p99_ms']}**")
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

    lines.append("## Input Shape")
    lines.append("")
    lines.append("| Field | Base | New |")
    lines.append("|---|---:|---:|")
    for field in ("batch", "height", "width"):
        lines.append(
            f"| {field} | {_fmt_num(shape['base'].get(field))} | {_fmt_num(shape['new'].get(field))} |"
        )
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