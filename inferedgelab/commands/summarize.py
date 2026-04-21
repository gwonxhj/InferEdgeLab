from __future__ import annotations

import os

import typer
from rich import print as rprint

from inferedgelab.services.summarize_service import build_summary_markdown


def summarize(
    pattern: str = typer.Argument(..., help='예: reports/*.json'),
    format: str = typer.Option("md", "--format", help="md"),
    mode: str = typer.Option("latest", "--mode", help="latest/history/both (latest=중복 제거, history=전체)"),
    sort: str = typer.Option("p99", "--sort", help="p99/mean/flops/time"),
    recent: int = typer.Option(0, "--recent", help="0이면 전체, 아니면 최근 N개(시간 기준)"),
    top: int = typer.Option(0, "--top", help="0이면 전체, 아니면 상위 N개 (sort 기준)"),
    output: str = typer.Option("", "--output", "-o", help="출력 파일 경로(미지정 시 stdout)"),
):
    try:
        text = build_summary_markdown(
            pattern=pattern,
            format=format,
            mode=mode,
            sort=sort,
            recent=recent,
            top=top,
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    if output:
        os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
        with open(output, "w", encoding="utf-8") as f:
            f.write(text)
        rprint(f"[green]Saved[/green]: {output}")
    else:
        print(text, end="")
