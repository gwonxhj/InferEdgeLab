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
):
    """
    저장된 structured benchmark result 목록을 최신순으로 보여준다.
    """
    paths = list_result_paths()

    if not paths:
        rprint("[yellow]No structured results found in results/[/yello]")
        return
    
    paths = list(reversed(paths))
    if limit > 0:
        paths = paths[:limit]

    table = Table(title="Structured Benchmark Results")
    table.add_column("Timestamp")
    table.add_column("Model")
    table.add_column("Engine")
    table.add_column("Device")
    table.add_column("Shape", justify="right")
    table.add_column("Mean (ms)", justify="right")
    table.add_column("P99 (ms)", justify="right")
    table.add_column("Legacy")

    for path in paths:
        item = load_result(path)
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