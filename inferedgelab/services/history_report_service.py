from __future__ import annotations

from typing import Any

from inferedgelab.report.history_html_generator import generate_history_html
from inferedgelab.report.history_markdown_generator import generate_history_markdown
from inferedgelab.result.loader import select_history_results


def build_history_report_outputs(
    pattern: str = "results/*.json",
    model: str = "",
    engine: str = "",
    device: str = "",
    precision: str = "",
    batch: int | None = None,
    height: int | None = None,
    width: int | None = None,
    include_markdown: bool = False,
) -> dict[str, Any]:
    """
    Build a history-report bundle for API use while keeping legacy top-level keys
    for existing CLI consumers.
    """
    history = select_history_results(
        pattern=pattern,
        model=model,
        engine=engine,
        device=device,
        precision=precision,
        batch=batch,
        height=height,
        width=width,
    )

    if not history:
        raise ValueError("조건에 맞는 structured result가 없습니다.")

    filters = {
        "model": model,
        "engine": engine,
        "device": device,
        "precision": precision,
        "batch": batch,
        "height": height,
        "width": width,
        "pattern": pattern,
    }

    markdown = None
    if include_markdown:
        markdown = generate_history_markdown(history=history, filters=filters)

    html = generate_history_html(history=history, filters=filters)
    bundle = {
        "meta": {
            "pattern": pattern,
            "filters": filters,
            "count": len(history),
        },
        "data": {
            "history": history,
        },
        "rendered": {
            "html": html,
            "markdown": markdown,
        },
    }

    return {
        **bundle,
        "history": history,
        "filters": filters,
        "html": html,
        "markdown": markdown,
    }
