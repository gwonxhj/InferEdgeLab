from __future__ import annotations

import typer
from rich import print as rprint

from edgebench.result.loader import (
    load_results,
    filter_results,
    sort_results_by_timestamp,
    result_identity_key,
)
from edgebench.commands.compare import compare_cmd


def compare_latest_cmd(
        model: str = typer.Option("", "--model", help="모델 필터"),
        engine: str = typer.Option("", "--engine", help="엔진 필터"),
        device: str = typer.Option("", "--device", help="디바이스 필터"),
        precision: str = typer.Option("", "--precision", help="precision 필터 (예: fp32, int8)"),
        strict: bool = typer.Option(True, "--strict/--no-strict", help="조건 불일치 시 에러 여부"),
        markdown_out: str = typer.Option("", "--markdown-out", help="Markdown 출력 파일"),
        html_out: str = typer.Option("", "--html-out", help="HTML 출력 파일"),
        pattern: str = typer.Option("results/*.json", "--pattern", help="result glob pattern"),
):
    """
    동일 조건의 최신 2개 결과를 비교한다.
    """

    all_items = load_results(pattern)
    filtered_items = filter_results(
        all_items,
        model=model,
        engine=engine,
        device=device,
        precision=precision,
    )

    if len(filtered_items) < 2:
        msg = f"필터 조건에 맞는 result가 2개 미만입니다. 현재: {len(filtered_items)}개"
        if strict:
            rprint(f"[red]{msg}[/red]")
            raise typer.Exit(code=1)
        else:
            rprint(f"[yellow]{msg}[/yellow]")
            return

    items_desc = list(reversed(sort_results_by_timestamp(filtered_items)))
    newest_item = items_desc[0]
    target_key = result_identity_key(newest_item)

    matched_items = []
    for item in items_desc:
        if result_identity_key(item) == target_key:
            matched_items.append(item)
        if len(matched_items) == 2:
            break

    if len(matched_items) < 2:
        msg = "같은 조건(model/engine/device/precision/batch/height/width)의 최근 결과 2개를 찾지 못했습니다."
        if strict:
            rprint(f"[red]{msg}[/red]")
            raise typer.Exit(code=1)
        else:
            rprint(f"[yellow]{msg}[/yellow]")
            return

    base, new = list(reversed(matched_items))

    def _find_path(target_item):
        import glob
        import json

        paths = sorted(glob.glob(pattern))
        for path in paths:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if (
                str(data.get("model")) == str(target_item.get("model"))
                and str(data.get("engine")) == str(target_item.get("engine"))
                and str(data.get("device")) == str(target_item.get("device"))
                and str(data.get("precision", "fp32")) == str(target_item.get("precision"))
                and str(data.get("batch")) == str(target_item.get("batch"))
                and str(data.get("height")) == str(target_item.get("height"))
                and str(data.get("width")) == str(target_item.get("width"))
                and str(data.get("timestamp")) == str(target_item.get("timestamp"))
            ):
                return path
        return None

    base_path = _find_path(base)
    new_path = _find_path(new)

    if not base_path or not new_path:
        rprint("[red]비교 대상 result 파일 경로를 찾지 못했습니다.[/red]")
        raise typer.Exit(code=1)

    rprint(f"[cyan]Comparing:[/cyan]")
    rprint(f"Base: {base_path}")
    rprint(f"New : {new_path}")

    compare_cmd(
        base_path=base_path,
        new_path=new_path,
        markdown_out=markdown_out,
        html_out=html_out,
    )