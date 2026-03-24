from __future__ import annotations

import typer
from rich import print as rprint
from rich.table import Table

from edgebench.result.loader import list_result_paths, load_result


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
    batch: int = typer.Option(-1, "--batch", help="batch 필터"),
    height: int = typer.Option(-1, "--height", help="height 필터"),
    width: int = typer.Option(-1, "--width", help="width 필터"),
    legacy_only: bool = typer.Option(False, "--legacy-only", help="legacy 결과만 표시"),
):
    """
    저장된 structured benchmark result 목록을 최신순으로 보여준다.
    """
    paths = list_result_paths()

    if not paths:
        rprint("[yellow]No structured results found in results/[/yellow]")
        return

    paths = list(reversed(paths))

    def _match(item):
        if model and item.get("model") != model:
            return False
        if engine and item.get("engine") != engine:
            return False
        if device and item.get("device") != device:
            return False
        if batch >= 0 and item.get("batch") != batch:
            return False
        if height >= 0 and item.get("height") != height:
            return False
        if width >= 0 and item.get("width") != width:
            return False
        if legacy_only and not item.get("legacy_result"):
            return False
        return True

    filtered_items = []

    for path in paths:
        item = load_result(path)
        if _match(item):
            filtered_items.append(item)

    if limit > 0:
        filtered_items = filtered_items[:limit]

    if not filtered_items:
        rprint("[yellow]No results matched given filters[/yellow]")
        return

    table = Table(title="Structured Benchmark Results")
    table.add_column("Timestamp")
    table.add_column("Model")
    table.add_column("Engine")
    table.add_column("Device")
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
            shape,
            _fmt_num(item.get("mean_ms")),
            _fmt_num(item.get("p99_ms")),
            str(item.get("legacy_result")),
        )

    rprint(table)