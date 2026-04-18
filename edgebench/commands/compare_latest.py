from __future__ import annotations

import typer
from rich import print as rprint

from edgebench.commands.compare import compare_cmd
from edgebench.services.compare_service import select_latest_compare_pair


def _handle_error_or_warning(message: str, strict: bool) -> None:
    if strict:
        rprint(f"[red]{message}[/red]")
        raise typer.Exit(code=1)
    rprint(f"[yellow]{message}[/yellow]")


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
):
    """
    조건에 맞는 최신 comparable pair를 선택해 비교한다.
    """
    try:
        pair = select_latest_compare_pair(
            pattern=pattern,
            model=model,
            engine=engine,
            device=device,
            precision=precision,
            selection_mode=selection_mode,
        )
    except ValueError as exc:
        _handle_error_or_warning(str(exc), strict)
        return

    selection_mode = pair["selection_mode"]
    base = pair["base"]
    new = pair["new"]
    base_path = pair["base_path"]
    new_path = pair["new_path"]

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

    run_config_mismatch_fields = pair["run_config_mismatch_fields"]
    if selection_mode == "same_precision" and run_config_mismatch_fields:
        mismatch_fields = ", ".join(run_config_mismatch_fields)
        rprint(
            "[yellow]Warning: same-precision latest pair was selected, but core run_config differs "
            f"({mismatch_fields}). Direct regression tracking should be interpreted with caution.[/yellow]"
        )

    compare_cmd(
        base_path=base_path,
        new_path=new_path,
        markdown_out=markdown_out,
        html_out=html_out,
    )
