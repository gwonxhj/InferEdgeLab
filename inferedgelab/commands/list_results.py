from __future__ import annotations

import typer
from rich import print as rprint
from rich.table import Table

from inferedgelab.services.list_results_service import build_list_result_items


def _fmt_num(v):
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{v:.4f}"
    return str(v)


def list_results_cmd(
    limit: int = typer.Option(10, "--limit", help="최근 N개 결과만 표시"),
    model: str = typer.Option("", "--model", help="모델명 필터"),
    engine: str = typer.Option("", "--engine", help="엔진 필터"),
    device: str = typer.Option("", "--device", help="디바이스 필터"),
    precision: str = typer.Option("", "--precision", help="precision 필터 (예: fp32, int8)"),
    batch: int = typer.Option(-1, "--batch", help="batch 필터"),
    height: int = typer.Option(-1, "--height", help="height 필터"),
    width: int = typer.Option(-1, "--width", help="width 필터"),
    legacy_only: bool = typer.Option(False, "--legacy-only", help="legacy 결과만 표시"),
):
    """
    저장된 structured benchmark result 목록을 최신순으로 보여준다.
    """
    batch_filter = None if batch < 0 else batch
    height_filter = None if height < 0 else height
    width_filter = None if width < 0 else width

    all_items = build_list_result_items(limit=0)
    if not all_items:
        rprint("[yellow]No structured results found in results/[/yellow]")
        return

    filtered_items = build_list_result_items(
        limit=limit,
        model=model,
        engine=engine,
        device=device,
        precision=precision,
        batch=batch_filter,
        height=height_filter,
        width=width_filter,
        legacy_only=legacy_only,
    )

    if not filtered_items:
        rprint("[yellow]No results matched given filters[/yellow]")
        return

    table = Table(title="Structured Benchmark Results")
    table.add_column("Timestamp")
    table.add_column("Model")
    table.add_column("Engine")
    table.add_column("Device")
    table.add_column("Precision")
    table.add_column("Shape", justify="right")
    table.add_column("Mean (ms)", justify="right")
    table.add_column("P99 (ms)", justify="right")
    table.add_column("Legacy")

    for item in filtered_items:
        shape = f"{item.get('batch')}x{item.get('height')}x{item.get('width')}"
        table.add_row(
            str(item.get("timestamp")),
            str(item.get("model")),
            str(item.get("engine")),
            str(item.get("device")),
            str(item.get("precision")),
            shape,
            _fmt_num(item.get("mean_ms")),
            _fmt_num(item.get("p99_ms")),
            str(item.get("legacy_result")),
        )

    rprint(table)
