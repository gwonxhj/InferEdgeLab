from __future__ import annotations

from pathlib import Path

import typer
from rich import print as rprint

from edgebench.result.loader import select_history_results
from edgebench.report.history_html_generator import generate_history_html
from edgebench.report.history_markdown_generator import generate_history_markdown


def history_report_cmd(
    model: str = typer.Option("", "--model", help="모델명 필터 (예: toy640.onnx)"),
    engine: str = typer.Option("", "--engine", help="엔진 필터"),
    device: str = typer.Option("", "--device", help="디바이스 필터"),
    precision: str = typer.Option("", "--precision", help="precision 필터 (예: fp32, int8)"),
    batch: int = typer.Option(-1, "--batch", help="batch 필터"),
    height: int = typer.Option(-1, "--height", help="height 필터"),
    width: int = typer.Option(-1, "--width", help="width 필터"),
    html_out: str = typer.Option("history_report.html", "--html-out", help="HTML 출력 파일"),
    markdown_out: str = typer.Option("", "--markdown-out", help="Markdown 출력 파일"),
    pattern: str = typer.Option("results/*.json", "--pattern", help='result glob pattern'),
):
    history = select_history_results(
        pattern=pattern,
        model=model,
        engine=engine,
        device=device,
        precision=precision,
        batch=None if batch < 0 else batch,
        height=None if height < 0 else height,
        width=None if width < 0 else width,
    )

    if not history:
        raise typer.BadParameter("조건에 맞는 structured result가 없습니다.")

    filters={
        "model": model,
        "engine": engine,
        "device": device,
        "precision": precision,
        "batch": None if batch < 0 else batch,
        "height": None if height < 0 else height,
        "width": None if width < 0 else width,
        "pattern": pattern,
    }

    html = generate_history_html(
        history=history,
        filters=filters,
    )


    Path(html_out).write_text(html, encoding="utf-8")

    if markdown_out:
        markdown = generate_history_markdown(
            history=history,
            filters=filters,
        )
        Path(markdown_out).write_text(markdown, encoding="utf-8")
        rprint(f"[green]Saved history Markdown report[/green]: {markdown_out}")

    rprint(f"[green]Saved history HTML report[/green]: {html_out}")