from __future__ import annotations

import typer
from rich import print as rprint

from edgebench.result.loader import (
    load_results,
    load_result,
    list_result_paths,
    filter_results,
    latest_comparable_items,
    latest_cross_precision_items,
)
from edgebench.commands.compare import compare_cmd


def _normalize_selection_mode(value: str) -> str:
    return str(value or "").strip().lower().replace("-", "_")


def _handle_error_or_warning(message: str, strict: bool) -> None:
    if strict:
        rprint(f"[red]{message}[/red]")
        raise typer.Exit(code=1)
    rprint(f"[yellow]{message}[/yellow]")


def _find_path_for_item(pattern: str, target_item):
    paths = list_result_paths(pattern)

    for path in paths:
        data = load_result(path)
        if (
            str(data.get("model")) == str(target_item.get("model"))
            and str(data.get("engine")) == str(target_item.get("engine"))
            and str(data.get("device")) == str(target_item.get("device"))
            and str(data.get("precision")) == str(target_item.get("precision"))
            and str(data.get("batch")) == str(target_item.get("batch"))
            and str(data.get("height")) == str(target_item.get("height"))
            and str(data.get("width")) == str(target_item.get("width"))
            and str(data.get("timestamp")) == str(target_item.get("timestamp"))
        ):
            return path

    return None


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
    selection_mode = _normalize_selection_mode(selection_mode)
    allowed_modes = {"same_precision", "cross_precision"}

    if selection_mode not in allowed_modes:
        _handle_error_or_warning(
            f"지원하지 않는 --selection-mode 값입니다: {selection_mode}. "
            "same_precision 또는 cross_precision 을 사용하세요.",
            strict,
        )
        return

    if selection_mode == "cross_precision" and precision:
        _handle_error_or_warning(
            "cross_precision 모드에서는 --precision 필터를 함께 사용할 수 없습니다.",
            strict,
        )
        return

    all_items = load_results(pattern)

    if selection_mode == "same_precision":
        filtered_items = filter_results(
            all_items,
            model=model,
            engine=engine,
            device=device,
            precision=precision,
        )
    else:
        filtered_items = filter_results(
            all_items,
            model=model,
            engine=engine,
            device=device,
        )

    if len(filtered_items) < 2:
        msg = f"필터 조건에 맞는 result가 2개 미만입니다. 현재: {len(filtered_items)}개"
        _handle_error_or_warning(msg, strict)
        return

    try:
        if selection_mode == "same_precision":
            matched_items = latest_comparable_items(filtered_items, count=2)
        else:
            matched_items = latest_cross_precision_items(filtered_items, count=2)
    except ValueError as exc:
        _handle_error_or_warning(str(exc), strict)
        return

    base, new = matched_items

    base_path = _find_path_for_item(pattern, base)
    new_path = _find_path_for_item(pattern, new)

    if not base_path or not new_path:
        rprint("[red]비교 대상 result 파일 경로를 찾지 못했습니다.[/red]")
        raise typer.Exit(code=1)

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

    compare_cmd(
        base_path=base_path,
        new_path=new_path,
        markdown_out=markdown_out,
        html_out=html_out,
    )