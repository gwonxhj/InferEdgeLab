from __future__ import annotations

import typer
from rich import print as rprint

from edgebench.result.loader import latest_comparable_result_paths
from edgebench.commands.compare import compare_cmd

def compare_latest_cmd(
        markdown_out: str = typer.Option("", "--markdown-out", help="비교 결과 Markdown 저장 경로"),
        html_out: str = typer.Option("", "--html-out", help="비교 결과 HTML 저장 경로"),
):
    """
    가장 최근 structured result 2개를 자동 선택해서 비교한다.
    """
    base_path, new_path = latest_comparable_result_paths()

    rprint("[bold]Auto-selected latest comparable result files[/bold]")
    rprint(f"Base: {base_path}")
    rprint(f"New : {new_path}")

    compare_cmd(
        base_path=base_path,
        new_path=new_path,
        markdown_out=markdown_out,
        html_out=html_out,
    )