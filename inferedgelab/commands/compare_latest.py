from __future__ import annotations

import typer
from rich import print as rprint
from rich.table import Table

from inferedgelab.services.compare_service import build_compare_latest_bundle


def _handle_error_or_warning(message: str, strict: bool) -> None:
    if strict:
        rprint(f"[red]{message}[/red]")
        raise typer.Exit(code=1)
    rprint(f"[yellow]{message}[/yellow]")


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


def _render_guard_analysis(guard_analysis: dict | None) -> None:
    if not guard_analysis:
        return

    if guard_analysis.get("status") == "skipped":
        rprint("[yellow]Warning[/yellow]: InferEdgeAIGuard is not installed. Guard analysis skipped.")
        return

    rprint("[bold]Guard Analysis[/bold]")
    rprint(f"- status: {guard_analysis.get('status')}")
    rprint(f"- confidence: {guard_analysis.get('confidence')}")

    for field in ("anomalies", "suspected_causes", "recommendations"):
        rprint(f"- {field}:")
        values = guard_analysis.get(field) or []
        if values:
            for value in values:
                rprint(f"  - {value}")
        else:
            rprint("  - -")


def _render_deployment_decision(deployment_decision: dict | None) -> None:
    if not deployment_decision:
        return

    rprint("[bold]Deployment Decision[/bold]")
    rprint(f"- decision: {deployment_decision.get('decision')}")
    rprint(f"- reason: {deployment_decision.get('reason')}")
    rprint(f"- recommended_action: {deployment_decision.get('recommended_action')}")


def _render_compare_bundle(bundle: dict, markdown_out: str, html_out: str) -> None:
    result = bundle["result"]
    judgement = bundle["judgement"]
    thresholds = judgement["thresholds"]
    base_path = bundle["base_path"]
    new_path = bundle["new_path"]

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
    sample_table.add_row("task", str(accuracy.get("task") or "-"), str(accuracy.get("task") or "-"))
    sample_table.add_row("primary_metric", str(accuracy_metric_name or "-"), str(accuracy_metric_name or "-"))
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
    precision_table.add_row("precision", str(precision_info["base"]), str(precision_info["new"]))
    rprint(precision_table)

    shape = result["shape"]
    shape_table = Table(title="Input Shape")
    shape_table.add_column("Field")
    shape_table.add_column("Base", justify="right")
    shape_table.add_column("New", justify="right")
    for field in ("batch", "height", "width"):
        shape_table.add_row(field, _fmt_num(shape["base"].get(field)), _fmt_num(shape["new"].get(field)))
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
        system_table.add_row(field, _fmt_num(values["base"]), _fmt_num(values["new"]))
    rprint(system_table)

    run_config_diff = result["run_config_diff"]
    run_table = Table(title="Run Config")
    run_table.add_column("Field")
    run_table.add_column("Base", justify="right")
    run_table.add_column("New", justify="right")
    for field, values in run_config_diff.items():
        run_table.add_row(field, _fmt_num(values["base"]), _fmt_num(values["new"]))
    rprint(run_table)

    _render_guard_analysis(bundle.get("guard_analysis"))
    _render_deployment_decision(bundle.get("deployment_decision"))

    if markdown_out:
        with open(markdown_out, "w", encoding="utf-8") as f:
            f.write(bundle["rendered"]["markdown"])
            f.write("\n")
        rprint(f"[green]Saved markdown report[/green]: {markdown_out}")

    if html_out:
        with open(html_out, "w", encoding="utf-8") as f:
            f.write(bundle["rendered"]["html"])
            f.write("\n")
        rprint(f"[green]Saved HTML report[/green]: {html_out}")


def compare_latest_cmd(
    model: str = typer.Option("", "--model", help="모델 필터"),
    engine: str = typer.Option("", "--engine", help="엔진 필터"),
    device: str = typer.Option("", "--device", help="디바이스 필터"),
    precision: str = typer.Option("", "--precision", help="precision 필터 (예: fp32, int8)"),
    selection_mode: str = typer.Option(
        "same_precision",
        "--selection-mode",
        help="pair 선택 방식: same_precision 또는 cross_precision",
    ),
    strict: bool = typer.Option(True, "--strict/--no-strict", help="조건 불일치 시 에러 여부"),
    markdown_out: str = typer.Option("", "--markdown-out", help="Markdown 출력 파일"),
    html_out: str = typer.Option("", "--html-out", help="HTML 출력 파일"),
    pattern: str = typer.Option("results/*.json", "--pattern", help="result glob pattern"),
    with_guard: bool = typer.Option(
        False,
        "--with-guard",
        help="Run InferEdgeAIGuard reasoning on the selected latest compare result",
    ),
):
    """
    조건에 맞는 최신 comparable pair를 선택해 비교한다.
    """
    try:
        bundle = build_compare_latest_bundle(
            pattern=pattern,
            model=model,
            engine=engine,
            device=device,
            precision=precision,
            selection_mode=selection_mode,
            with_guard=with_guard,
        )
    except ValueError as exc:
        _handle_error_or_warning(str(exc), strict)
        return

    pair = bundle["pair"]
    selection_mode = bundle["selection_mode"]
    base = bundle["base"]
    new = bundle["new"]
    base_path = bundle["base_path"]
    new_path = bundle["new_path"]

    rprint("[cyan]Comparing latest pair:[/cyan]")
    rprint(f"Selection mode: {selection_mode}")
    rprint(
        "Identity: "
        f"{base.get('model')} / {base.get('engine')} / {base.get('device')} / "
        f"b{base.get('batch')} / h{base.get('height')} / w{base.get('width')}"
    )
    rprint(f"Base candidate: {base.get('timestamp')} / {base.get('precision')}")
    rprint(f"New candidate : {new.get('timestamp')} / {new.get('precision')}")
    rprint(f"Base path: {base_path}")
    rprint(f"New path : {new_path}")

    run_config_mismatch_fields = bundle["run_config_mismatch_fields"]
    if selection_mode == "same_precision" and run_config_mismatch_fields:
        mismatch_fields = ", ".join(run_config_mismatch_fields)
        rprint(
            "[yellow]Warning: same-precision latest pair was selected, but core run_config differs "
            f"({mismatch_fields}). Direct regression tracking should be interpreted with caution.[/yellow]"
        )

    _render_compare_bundle(bundle, markdown_out=markdown_out, html_out=html_out)
