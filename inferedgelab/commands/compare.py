from __future__ import annotations

import typer
from typer.models import OptionInfo
from rich import print as rprint
from rich.table import Table

from inferedgelab.compare.comparator import compare_group
from inferedgelab.result.loader import load_results_grouped_by_compare_key
from inferedgelab.services.compare_service import build_compare_bundle


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
    latency_improve_threshold = _normalize_optional_float(latency_improve_threshold)
    latency_regress_threshold = _normalize_optional_float(latency_regress_threshold)
    accuracy_improve_threshold = _normalize_optional_float(accuracy_improve_threshold)
    accuracy_regress_threshold = _normalize_optional_float(accuracy_regress_threshold)
    tradeoff_caution_threshold = _normalize_optional_float(tradeoff_caution_threshold)
    tradeoff_risky_threshold = _normalize_optional_float(tradeoff_risky_threshold)
    tradeoff_severe_threshold = _normalize_optional_float(tradeoff_severe_threshold)

    bundle = build_compare_bundle(
        base_path=base_path,
        new_path=new_path,
        latency_improve_threshold=latency_improve_threshold,
        latency_regress_threshold=latency_regress_threshold,
        accuracy_improve_threshold=accuracy_improve_threshold,
        accuracy_regress_threshold=accuracy_regress_threshold,
        tradeoff_caution_threshold=tradeoff_caution_threshold,
        tradeoff_risky_threshold=tradeoff_risky_threshold,
        tradeoff_severe_threshold=tradeoff_severe_threshold,
    )
    base = bundle["base"]
    new = bundle["new"]
    result = bundle["result"]
    judgement = bundle["judgement"]
    thresholds = judgement["thresholds"]

    if bundle["legacy_warning"]:
        rprint("[yellow]Warning[/yellow]: one or both result files are legacy format. Some fields may be missing.")

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

    runtime_provenance = result["runtime_provenance"]
    runtime_table = Table(title="Runtime Provenance Summary")
    runtime_table.add_column("Field")
    runtime_table.add_column("Base", justify="right")
    runtime_table.add_column("New", justify="right")

    for field in (
        "runtime_artifact_path",
        "primary_input_name",
        "requested_shape_summary",
        "effective_shape_summary",
    ):
        runtime_table.add_row(
            field,
            _fmt_num(runtime_provenance["base"].get(field)),
            _fmt_num(runtime_provenance["new"].get(field)),
        )

    rprint(runtime_table)

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
    accuracy_metric_name = accuracy.get("metric_name") or "top1_accuracy"
    accuracy_metrics = accuracy.get("metrics") or {}

    accuracy_table = Table(title="Accuracy Comparison")
    accuracy_table.add_column("Metric")
    accuracy_table.add_column("Base", justify="right")
    accuracy_table.add_column("New", justify="right")
    accuracy_table.add_column("Delta", justify="right")
    accuracy_table.add_column("Delta %", justify="right")
    accuracy_table.add_column("Delta pp", justify="right")

    if accuracy_metrics:
        for metric_name, values in accuracy_metrics.items():
            accuracy_table.add_row(
                str(metric_name),
                _fmt_num(values.get("base")),
                _fmt_num(values.get("new")),
                _fmt_num(values.get("delta")),
                _fmt_pct(values.get("delta_pct")),
                _fmt_pp(values.get("delta_pp")),
            )
    else:
        accuracy_table.add_row("-", "-", "-", "-", "-", "-")

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
        "primary_metric",
        str(accuracy_metric_name or "-"),
        str(accuracy_metric_name or "-"),
    )
    sample_table.add_row(
        "sample_count",
        _fmt_num((accuracy.get("sample_count") or {}).get("base")),
        _fmt_num((accuracy.get("sample_count") or {}).get("new")),
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
        with open(markdown_out, "w", encoding="utf-8") as f:
            f.write(bundle["markdown"])
            f.write("\n")
        rprint(f"[green]Saved markdown report[/green]: {markdown_out}")

    if html_out:
        with open(html_out, "w", encoding="utf-8") as f:
            f.write(bundle["html"])
            f.write("\n")
        rprint(f"[green]Saved HTML report[/green]: {html_out}")


def compare_runtime_dir_cmd(
    directory: str = typer.Argument(..., help="InferEdgeRuntime compare-ready JSON directory"),
):
    """
    InferEdgeRuntime compare-ready 결과를 compare_key 기준으로 자동 그룹핑해 backend별 mean latency를 비교한다.
    """
    grouped = load_results_grouped_by_compare_key(directory)
    if not grouped:
        rprint("[yellow]No compare-ready runtime results found.[/yellow]")
        return

    compared_count = 0
    skipped_count = 0

    for compare_key in sorted(grouped):
        comparison = compare_group(grouped[compare_key])
        if comparison is None:
            skipped_count += 1
            continue

        compared_count += 1
        rprint(f"[bold]Compare Group: {comparison['compare_key']}[/bold]")
        backend_results = comparison["backend_results"]
        for backend_key in comparison["backends"]:
            mean_ms = backend_results[backend_key]["mean_ms"]
            mean_text = f"{mean_ms:.4f} ms" if mean_ms is not None else "-"
            rprint(f"  {backend_key}: {mean_text}")

        speedup = comparison["speedup"]
        speedup_text = f"{speedup:.1f}x" if speedup is not None else "n/a"
        rprint(f"  -> {comparison['fastest']} faster ({speedup_text})")
        rprint(f"  Summary: {comparison['summary']}")

    if compared_count == 0:
        rprint("[yellow]No comparable runtime groups found. At least two backend_key values are required per compare_key.[/yellow]")
    elif skipped_count:
        rprint(f"[yellow]Skipped groups without at least two comparable backends: {skipped_count}[/yellow]")
