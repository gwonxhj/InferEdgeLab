from __future__ import annotations

import typer
from rich import print as rprint

from edgebench.result.loader import(
    latest_comparable_result_paths,
    load_result,
)
from edgebench.commands.compare import compare_cmd

def compare_latest_cmd(
        model: str = typer.Option("", "--model", help="모델 필터"),
        engine: str = typer.Option("", "--engine", help="엔진 필터"),
        device: str = typer.Option("", "--device", help="디바이스 필터"),
        strict: bool = typer.Option(True, "--strict/--no-strict", help="조건 불일치 시 에러 여부"),
):
    """
    동일 조건의 최신 2개 결과를 비교한다.
    """

    try:
        paths = latest_comparable_result_paths()
    except ValueError as e:
        rprint(f"[red]{e}[/red]")
        raise typer.Exit(code=1)
    
    base_path, new_path = paths

    base = load_result(base_path)
    new = load_result(new_path)

    # 필터 체크
    def _match(item):
        if model and item.get("model") != model:
            return False
        if engine and item.get("engine") != engine:
            return False
        if device and item.get("device") != device:
            return False
        return True
    
    if not (_match(base) and _match(new)):
        msg = "필터 조건과 일치하는 comparable 결과를 찾지 못했습니다."
        if strict:
            rprint(f"[red]{msg}[/red]")
            raise typer.Exit(code=1)
        else:
            rprint(f"[yellow]{msg} -> fallback으로 기본 비교 진행[/yellow]")

    rprint(f"[cyan]Comparing:[/cyan]")
    rprint(f"Base: {base_path}")
    rprint(f"New : {new_path}")

    compare_cmd(
        base_path=base_path,
        new_path=new_path,
        markdown_out="",
        html_out="",
    )