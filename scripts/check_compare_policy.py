from __future__ import annotations

import glob
from pathlib import Path
from typing import Any, Dict, List

import typer
from rich import print as rprint

from edgebench.compare.comparator import compare_results
from edgebench.compare.judgement import judge_comparison
from edgebench.config import resolve_compare_thresholds
from edgebench.result.loader import (
    filter_results,
    latest_comparable_items,
    latest_cross_precision_items,
    load_results,
)


def _normalize_selection_mode(value: str) -> str:
    return str(value or "").strip().lower().replace("-", "_")


def _fmt_identity(item: Dict[str, Any]) -> str:
    return (
        f"{item.get('model')} / {item.get('engine')} / {item.get('device')} / "
        f"b{item.get('batch')} / h{item.get('height')} / w{item.get('width')} / "
        f"{item.get('precision')} / {item.get('timestamp')}"
    )


def _select_pair(
    *,
    pattern: str,
    selection_mode: str,
    model: str,
    engine: str,
    device: str,
    precision: str,
) -> List[Dict[str, Any]]:
    items = load_results(pattern)

    if selection_mode == "same_precision":
        filtered = filter_results(
            items,
            model=model,
            engine=engine,
            device=device,
            precision=precision,
        )
        return latest_comparable_items(filtered, count=2)

    filtered = filter_results(
        items,
        model=model,
        engine=engine,
        device=device,
    )
    return latest_cross_precision_items(filtered, count=2)


def _build_summary_markdown(
    *,
    selection_mode: str,
    base: Dict[str, Any],
    new: Dict[str, Any],
    judgement: Dict[str, Any],
    failed: bool,
) -> str:
    status_emoji = "❌" if failed else "✅"
    lines: list[str] = []

    lines.append("## CI Compare Policy Gate")
    lines.append("")
    lines.append(f"- Status: {status_emoji} **{'failed' if failed else 'passed'}**")
    lines.append(f"- Selection mode: `{selection_mode}`")
    lines.append(f"- Overall: **{judgement['overall']}**")
    lines.append(f"- Trade-off risk: **{judgement['tradeoff_risk']}**")
    lines.append(f"- Base candidate: `{_fmt_identity(base)}`")
    lines.append(f"- New candidate: `{_fmt_identity(new)}`")
    lines.append("")
    lines.append(f"**Summary**: {judgement['summary']}")
    lines.append("")

    if judgement.get("notes"):
        lines.append("### Notes")
        lines.append("")
        for note in judgement["notes"]:
            lines.append(f"- {note}")
        lines.append("")

    return "\n".join(lines)


def _write_summary(path: str, text: str) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text + "\n", encoding="utf-8")


def main(
    pattern: str = typer.Option("results/*.json", "--pattern", help="structured result glob pattern"),
    selection_mode: str = typer.Option(
        "same_precision",
        "--selection-mode",
        help="same_precision or cross_precision",
    ),
    model: str = typer.Option("", "--model", help="model filter"),
    engine: str = typer.Option("", "--engine", help="engine filter"),
    device: str = typer.Option("", "--device", help="device filter"),
    precision: str = typer.Option("", "--precision", help="precision filter for same_precision mode"),
    fail_on_same_precision_regression: bool = typer.Option(
        True,
        "--fail-on-same-precision-regression/--no-fail-on-same-precision-regression",
        help="fail when same-precision overall judgement is regression",
    ),
    fail_on_severe_tradeoff: bool = typer.Option(
        True,
        "--fail-on-severe-tradeoff/--no-fail-on-severe-tradeoff",
        help="fail when cross-precision tradeoff risk is severe_tradeoff",
    ),
    latency_improve_threshold: float | None = typer.Option(None, "--latency-improve-threshold"),
    latency_regress_threshold: float | None = typer.Option(None, "--latency-regress-threshold"),
    accuracy_improve_threshold: float | None = typer.Option(None, "--accuracy-improve-threshold"),
    accuracy_regress_threshold: float | None = typer.Option(None, "--accuracy-regress-threshold"),
    tradeoff_caution_threshold: float | None = typer.Option(None, "--tradeoff-caution-threshold"),
    tradeoff_risky_threshold: float | None = typer.Option(None, "--tradeoff-risky-threshold"),
    tradeoff_severe_threshold: float | None = typer.Option(None, "--tradeoff-severe-threshold"),
    summary_out: str = typer.Option("", "--summary-out", help="write markdown summary to a file"),
) -> int:
    selection_mode = _normalize_selection_mode(selection_mode)
    if selection_mode not in {"same_precision", "cross_precision"}:
        raise typer.BadParameter("--selection-mode must be one of: same_precision, cross_precision")

    if selection_mode == "cross_precision" and precision:
        raise typer.BadParameter("--precision cannot be used with cross_precision mode")

    matched_paths = sorted(glob.glob(pattern))
    if not matched_paths:
        rprint(f"[red]No structured result files matched:[/red] {pattern}")
        return 2

    try:
        base, new = _select_pair(
            pattern=pattern,
            selection_mode=selection_mode,
            model=model,
            engine=engine,
            device=device,
            precision=precision,
        )
    except Exception as exc:
        rprint(f"[red]Failed to select compare pair:[/red] {exc}")
        return 2

    thresholds = resolve_compare_thresholds(
        latency_improve_threshold=latency_improve_threshold,
        latency_regress_threshold=latency_regress_threshold,
        accuracy_improve_threshold=accuracy_improve_threshold,
        accuracy_regress_threshold=accuracy_regress_threshold,
        tradeoff_caution_threshold=tradeoff_caution_threshold,
        tradeoff_risky_threshold=tradeoff_risky_threshold,
        tradeoff_severe_threshold=tradeoff_severe_threshold,
    )

    compare_result = compare_results(base, new)
    judgement = judge_comparison(
        compare_result,
        latency_improve_threshold=thresholds["latency_improve_threshold"],
        latency_regress_threshold=thresholds["latency_regress_threshold"],
        accuracy_improve_threshold=thresholds["accuracy_improve_threshold"],
        accuracy_regress_threshold=thresholds["accuracy_regress_threshold"],
        tradeoff_caution_threshold=thresholds["tradeoff_caution_threshold"],
        tradeoff_risky_threshold=thresholds["tradeoff_risky_threshold"],
        tradeoff_severe_threshold=thresholds["tradeoff_severe_threshold"],
    )

    rprint("[bold]CI Compare Policy Gate[/bold]")
    rprint(f"Selection mode : {selection_mode}")
    rprint(f"Base candidate : {_fmt_identity(base)}")
    rprint(f"New candidate  : {_fmt_identity(new)}")
    rprint(f"Overall        : {judgement['overall']}")
    rprint(f"Trade-off risk : {judgement['tradeoff_risk']}")
    rprint(f"Summary        : {judgement['summary']}")

    failed = False

    if selection_mode == "same_precision":
        if fail_on_same_precision_regression and judgement["overall"] == "regression":
            rprint("[red]Policy failure[/red]: same-precision regression detected.")
            failed = True

    if selection_mode == "cross_precision":
        if fail_on_severe_tradeoff and judgement["tradeoff_risk"] == "severe_tradeoff":
            rprint("[red]Policy failure[/red]: severe trade-off detected.")
            failed = True

    if summary_out:
        summary_text = _build_summary_markdown(
            selection_mode=selection_mode,
            base=base,
            new=new,
            judgement=judgement,
            failed=failed,
        )
        _write_summary(summary_out, summary_text)
        rprint(f"[cyan]Summary written[/cyan]: {summary_out}")

    if failed:
        rprint("[red]Compare policy gate failed[/red]")
        return 2

    rprint("[green]Compare policy gate passed[/green]")
    return 0


if __name__ == "__main__":
    typer.run(main)