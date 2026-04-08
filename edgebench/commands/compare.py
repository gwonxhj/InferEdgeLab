from __future__ import annotations

import typer
from typer.models import OptionInfo
from rich import print as rprint
from rich.table import Table

from edgebench.config import resolve_compare_thresholds
from edgebench.result.loader import load_result

from edgebench.compare.comparator import compare_results
from edgebench.compare.judgement import judge_comparison

from edgebench.report.markdown_generator import generate_compare_markdown
from edgebench.report.html_generator import generate_compare_html


def _fmt_num(v):
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{v:.4f}"
    return str(v)


def _fmt_pct(v):
    if v is None:
        return "-"
    return f"{v:+.2f}%"


def _fmt_pp(v):
    if v is None:
        return "-"
    return f"{v:+.2f}pp"

def _normalize_optional_float(value):
    if isinstance(value, OptionInfo):
        return None
    return value


def compare_cmd(
    base_path: str = typer.Argument(..., help="기준 result JSON 경로"),
    new_path: str = typer.Argument(..., help="비교 대상 result JSON 경로"),
    latency_improve_threshold: float | None = typer.Option(
        None, "--latency-improve-threshold", help="latency improvement threshold (%)"
    ),
    latency_regress_threshold: float | None = typer.Option(
        None, "--latency-regress-threshold", help="latency regression threshold (%)"
    ),
    accuracy_improve_threshold: float | None = typer.Option(
        None, "--accuracy-improve-threshold", help="accuracy improvement threshold (pp)"
    ),
    accuracy_regress_threshold: float | None = typer.Option(
        None, "--accuracy-regress-threshold", help="accuracy regression threshold (pp)"
    ),
    tradeoff_caution_threshold: float | None = typer.Option(
        None, "--tradeoff-caution-threshold", help="trade-off caution threshold (pp)"
    ),
    tradeoff_risky_threshold: float | None = typer.Option(
        None, "--tradeoff-risky-threshold", help="trade-off risky threshold (pp)"
    ),
    tradeoff_severe_threshold: float | None = typer.Option(
        None, "--tradeoff-severe-threshold", help="trade-off severe threshold (pp)"
    ),
    markdown_out: str = typer.Option("", "--markdown-out", help="비교 결과 Markdown 저장 경로"),
    html_out: str = typer.Option("", "--html-out", help="비교 결과 HTML 저장 경로"),
):
    """
    structured benchmark result 두 개를 비교해서 콘솔 표로 출력한다.
    """
    base = load_result(base_path)
    new = load_result(new_path)

    if base.get("legacy_result") or new.get("legacy_result"):
        rprint("[yellow]Warning[/yellow]: one or both result files are legacy format. Some fields may be missing.")

    latency_improve_threshold = _normalize_optional_float(latency_improve_threshold)
    latency_regress_threshold = _normalize_optional_float(latency_regress_threshold)
    accuracy_improve_threshold = _normalize_optional_float(accuracy_improve_threshold)
    accuracy_regress_threshold = _normalize_optional_float(accuracy_regress_threshold)
    tradeoff_caution_threshold = _normalize_optional_float(tradeoff_caution_threshold)
    tradeoff_risky_threshold = _normalize_optional_float(tradeoff_risky_threshold)
    tradeoff_severe_threshold = _normalize_optional_float(tradeoff_severe_threshold)

    thresholds = resolve_compare_thresholds(
        latency_improve_threshold=latency_improve_threshold,
        latency_regress_threshold=latency_regress_threshold,
        accuracy_improve_threshold=accuracy_improve_threshold,
        accuracy_regress_threshold=accuracy_regress_threshold,
        tradeoff_caution_threshold=tradeoff_caution_threshold,
        tradeoff_risky_threshold=tradeoff_risky_threshold,
        tradeoff_severe_threshold=tradeoff_severe_threshold,
    )

    result = compare_results(base, new)
    judgement = judge_comparison(
        result,
        latency_improve_threshold=thresholds["latency_improve_threshold"],
        latency_regress_threshold=thresholds["latency_regress_threshold"],
        accuracy_improve_threshold=thresholds["accuracy_improve_threshold"],
        accuracy_regress_threshold=thresholds["accuracy_regress_threshold"],
        tradeoff_caution_threshold=thresholds["tradeoff_caution_threshold"],
        tradeoff_risky_threshold=thresholds["tradeoff_risky_threshold"],
        tradeoff_severe_threshold=thresholds["tradeoff_severe_threshold"],
    )
    precision_info = result["precision"]

    rprint("[bold]Compare Results[/bold]")
    rprint(f"Base: {base_path}")
    rprint(f"New : {new_path}")
    rprint(f"Base precision   : {precision_info['base']}")
    rprint(f"New precision    : {precision_info['new']}")
    rprint(f"Precision match  : {judgement['precision_match']}")
    rprint(f"Comparison mode  : {judgement['comparison_mode']}")
    rprint(f"Precision pair   : {judgement['precision_pair']}")
    rprint(f"Overall judgement: [bold]{judgement['overall']}[/bold]")
    rprint(f"Shape match      : {judgement['shape_match']}")
    rprint(f"System match     : {judgement['system_match']}")
    rprint(f"Mean judgement   : {judgement['mean_ms']}")
    rprint(f"P99 judgement    : {judgement['p99_ms']}")
    rprint(f"Accuracy judge   : {judgement['accuracy']}")
    rprint(f"Trade-off risk   : {judgement['tradeoff_risk']}")
    rprint(f"Summary          : {judgement['summary']}")

    rprint("[bold]Thresholds[/bold]")
    rprint(f"Latency improve threshold : {thresholds['latency_improve_threshold']:+.2f}%")
    rprint(f"Latency regress threshold : {thresholds['latency_regress_threshold']:+.2f}%")
    rprint(f"Accuracy improve threshold: {thresholds['accuracy_improve_threshold']:+.2f}pp")
    rprint(f"Accuracy regress threshold: {thresholds['accuracy_regress_threshold']:+.2f}pp")
    rprint(f"Tradeoff caution threshold: {thresholds['tradeoff_caution_threshold']:+.2f}pp")
    rprint(f"Tradeoff risky threshold  : {thresholds['tradeoff_risky_threshold']:+.2f}pp")
    rprint(f"Tradeoff severe threshold : {thresholds['tradeoff_severe_threshold']:+.2f}pp")

    if not judgement["precision_match"]:
        rprint(
            "[yellow]Warning[/yellow]: cross-precision comparison detected. "
            "Interpret latency deltas as a precision trade-off signal, not a strict same-condition regression result."
        )

    if judgement["notes"]:
        rprint("[bold]Notes[/bold]")
        for note in judgement["notes"]:
            rprint(f"- {note}")

    metrics = result["metrics"]
    metric_table = Table(title="Latency Comparison")
    metric_table.add_column("Metric")
    metric_table.add_column("Base", justify="right")
    metric_table.add_column("New", justify="right")
    metric_table.add_column("Delta", justify="right")
    metric_table.add_column("Delta %", justify="right")

    for metric_name, values in metrics.items():
        metric_table.add_row(
            metric_name,
            _fmt_num(values["base"]),
            _fmt_num(values["new"]),
            _fmt_num(values["delta"]),
            _fmt_pct(values["delta_pct"]),
        )

    rprint(metric_table)

    accuracy = result["accuracy"]
    accuracy_metric = accuracy["metrics"]["top1_accuracy"]

    accuracy_table = Table(title="Accuracy Comparison")
    accuracy_table.add_column("Metric")
    accuracy_table.add_column("Base", justify="right")
    accuracy_table.add_column("New", justify="right")
    accuracy_table.add_column("Delta", justify="right")
    accuracy_table.add_column("Delta %", justify="right")
    accuracy_table.add_column("Delta pp", justify="right")

    accuracy_table.add_row(
        "top1_accuracy",
        _fmt_num(accuracy_metric["base"]),
        _fmt_num(accuracy_metric["new"]),
        _fmt_num(accuracy_metric["delta"]),
        _fmt_pct(accuracy_metric["delta_pct"]),
        _fmt_pp(accuracy_metric["delta_pp"]),
    )

    rprint(accuracy_table)

    sample_table = Table(title="Accuracy Context")
    sample_table.add_column("Field")
    sample_table.add_column("Base", justify="right")
    sample_table.add_column("New", justify="right")

    sample_table.add_row(
        "task",
        str(accuracy.get("task") or "-"),
        str(accuracy.get("task") or "-"),
    )
    sample_table.add_row(
        "sample_count",
        _fmt_num(accuracy["sample_count"]["base"]),
        _fmt_num(accuracy["sample_count"]["new"]),
    )

    rprint(sample_table)

    precision_table = Table(title="Precision")
    precision_table.add_column("Field")
    precision_table.add_column("Base")
    precision_table.add_column("New")

    precision_table.add_row(
        "precision",
        str(precision_info["base"]),
        str(precision_info["new"]),
    )

    rprint(precision_table)

    shape = result["shape"]
    shape_table = Table(title="Input Shape")
    shape_table.add_column("Field")
    shape_table.add_column("Base", justify="right")
    shape_table.add_column("New", justify="right")

    for field in ("batch", "height", "width"):
        shape_table.add_row(
            field,
            _fmt_num(shape["base"].get(field)),
            _fmt_num(shape["new"].get(field)),
        )

    rprint(shape_table)

    shape_context = result["shape_context"]
    provenance_table = Table(title="Input Shape Provenance")
    provenance_table.add_column("Field")
    provenance_table.add_column("Base", justify="right")
    provenance_table.add_column("New", justify="right")

    for field in (
        "requested_batch",
        "requested_height",
        "requested_width",
        "effective_batch",
        "effective_height",
        "effective_width",
        "primary_input_name",
        "resolved_input_shapes",
    ):
        base_value = shape_context["base"].get(field)
        new_value = shape_context["new"].get(field)
        provenance_table.add_row(
            field,
            str(base_value) if isinstance(base_value, (dict, list)) else _fmt_num(base_value),
            str(new_value) if isinstance(new_value, (dict, list)) else _fmt_num(new_value),
        )

    rprint(provenance_table)

    system_diff = result["system_diff"]
    system_table = Table(title="System Info")
    system_table.add_column("Field")
    system_table.add_column("Base")
    system_table.add_column("New")

    for field, values in system_diff.items():
        system_table.add_row(
            field,
            _fmt_num(values["base"]),
            _fmt_num(values["new"]),
        )

    rprint(system_table)

    run_config_diff = result["run_config_diff"]
    run_table = Table(title="Run Config")
    run_table.add_column("Field")
    run_table.add_column("Base", justify="right")
    run_table.add_column("New", justify="right")

    for field, values in run_config_diff.items():
        run_table.add_row(
            field,
            _fmt_num(values["base"]),
            _fmt_num(values["new"]),
        )

    rprint(run_table)

    if markdown_out:
        md_text = generate_compare_markdown(result, judgement)
        with open(markdown_out, "w", encoding="utf-8") as f:
            f.write(md_text)
            f.write("\n")
        rprint(f"[green]Saved markdown report[/green]: {markdown_out}")

    if html_out:
        html_text = generate_compare_html(result, judgement)
        with open(html_out, "w", encoding="utf-8") as f:
            f.write(html_text)
            f.write("\n")
        rprint(f"[green]Saved HTML report[/green]: {html_out}")
