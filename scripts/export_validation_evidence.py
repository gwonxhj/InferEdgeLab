from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any, Dict

from edgebench.compare.comparator import compare_results
from edgebench.compare.judgement import judge_comparison
from edgebench.result.loader import load_result


def _fmt_value(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _stringify(value: Any) -> str:
    if value is None:
        return "-"
    return str(value)


def build_validation_evidence_markdown(
    *,
    label: str,
    compare_result: Dict[str, Any],
    judgement: Dict[str, Any],
    report_markdown_path: str = "",
    report_html_path: str = "",
) -> str:
    base_id = compare_result["base_id"]
    precision = compare_result["precision"]
    metrics = compare_result["metrics"]
    runtime_provenance = compare_result["runtime_provenance"]
    shape_context = compare_result["shape_context"]

    lines: list[str] = []
    lines.append(f"## {label}")
    lines.append("")
    lines.append(f"- Model: `{base_id.get('model')}`")
    lines.append(f"- Engine: `{base_id.get('engine')}`")
    lines.append(f"- Device: `{base_id.get('device')}`")
    lines.append(f"- Precision pair: `{precision.get('pair')}`")
    lines.append(f"- Overall: **{judgement.get('overall')}**")
    lines.append("")
    lines.append("| Metric | Base | New |")
    lines.append("|---|---:|---:|")
    lines.append(
        f"| mean_ms | {_fmt_value(metrics['mean_ms'].get('base'))} | {_fmt_value(metrics['mean_ms'].get('new'))} |"
    )
    lines.append(
        f"| p99_ms | {_fmt_value(metrics['p99_ms'].get('base'))} | {_fmt_value(metrics['p99_ms'].get('new'))} |"
    )
    lines.append("")
    lines.append("### Runtime Provenance")
    lines.append(f"- Base runtime_artifact_path: `{_stringify(runtime_provenance['base'].get('runtime_artifact_path'))}`")
    lines.append(f"- New runtime_artifact_path: `{_stringify(runtime_provenance['new'].get('runtime_artifact_path'))}`")
    lines.append(f"- Base primary_input_name: `{_stringify(runtime_provenance['base'].get('primary_input_name'))}`")
    lines.append(f"- New primary_input_name: `{_stringify(runtime_provenance['new'].get('primary_input_name'))}`")
    lines.append(f"- Base resolved_input_shapes: `{_stringify(shape_context['base'].get('resolved_input_shapes'))}`")
    lines.append(f"- New resolved_input_shapes: `{_stringify(shape_context['new'].get('resolved_input_shapes'))}`")

    report_lines: list[str] = []
    if report_markdown_path:
        report_lines.append(f"- Markdown: `{report_markdown_path}`")
    if report_html_path:
        report_lines.append(f"- HTML: `{report_html_path}`")

    if report_lines:
        lines.append("")
        lines.append("### Reports")
        lines.extend(report_lines)

    lines.append("")
    lines.append(f"**Summary**: {judgement.get('summary')}")
    lines.append("")
    return "\n".join(lines)


def export_validation_evidence(
    *,
    base_result: str,
    new_result: str,
    label: str,
    markdown_out: str,
    report_markdown_path: str = "",
    report_html_path: str = "",
) -> str:
    base = load_result(base_result)
    new = load_result(new_result)
    compare_result = compare_results(base, new)
    judgement = judge_comparison(compare_result)
    markdown = build_validation_evidence_markdown(
        label=label,
        compare_result=compare_result,
        judgement=judgement,
        report_markdown_path=report_markdown_path,
        report_html_path=report_html_path,
    )

    out_path = Path(markdown_out)
    os.makedirs(out_path.parent or Path("."), exist_ok=True)
    out_path.write_text(markdown, encoding="utf-8")
    return str(out_path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export compare/judgement output as a markdown validation evidence block."
    )
    parser.add_argument("--base-result", required=True)
    parser.add_argument("--new-result", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--markdown-out", required=True)
    parser.add_argument("--report-markdown-path", default="")
    parser.add_argument("--report-html-path", default="")
    args = parser.parse_args()

    saved_path = export_validation_evidence(
        base_result=args.base_result,
        new_result=args.new_result,
        label=args.label,
        markdown_out=args.markdown_out,
        report_markdown_path=args.report_markdown_path,
        report_html_path=args.report_html_path,
    )
    print(saved_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
