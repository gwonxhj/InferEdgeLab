from __future__ import annotations

from typing import Any, Dict, List, Optional


def _fmt_num(v: Optional[float]) -> str:
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{v:.4f}"
    return str(v)


def generate_history_markdown(
    history: List[Dict[str, Any]],
    filters: Dict[str, Any],
) -> str:
    latest = history[-1] if history else {}
    oldest = history[0] if history else {}

    lines: List[str] = []
    lines.append("# EdgeBench History Report")
    lines.append("")
    lines.append("## Filters")
    lines.append("")

    has_filter = False
    for k, v in filters.items():
        if v not in ("", None):
            has_filter = True
            lines.append(f"- **{k}**: `{v}`")

    if not has_filter:
        lines.append("- No filters")

    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Total records**: `{len(history)}`")
    lines.append(f"- **Oldest timestamp**: `{oldest.get('timestamp', '-')}`")
    lines.append(f"- **Latest timestamp**: `{latest.get('timestamp', '-')}`")
    lines.append("")

    lines.append("## History Table")
    lines.append("")
    lines.append("| Timestamp | Model | Engine | Device | Batch | Input | Mean (ms) | P99 (ms) |")
    lines.append("|---|---|---|---|---:|---|---:|---:|")

    for item in history:
        timestamp = item.get("timestamp", "-")
        model = item.get("model", "-")
        engine = item.get("engine", "-")
        device = item.get("device", "-")
        batch = item.get("batch", "-")
        height = item.get("height", "-")
        width = item.get("width", "-")
        mean_ms = _fmt_num(item.get("mean_ms"))
        p99_ms = _fmt_num(item.get("p99_ms"))

        lines.append(
            f"| {timestamp} | {model} | {engine} | {device} | {batch} | {height}x{width} | {mean_ms} | {p99_ms} |"
        )

    lines.append("")
    return "\n".join(lines)