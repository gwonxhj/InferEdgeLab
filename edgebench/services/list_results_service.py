from __future__ import annotations

from typing import Any

from edgebench.result.loader import list_result_paths, load_result


def build_list_result_items(
    pattern: str = "results/*.json",
    limit: int = 10,
    model: str = "",
    engine: str = "",
    device: str = "",
    precision: str = "",
    batch: int | None = None,
    height: int | None = None,
    width: int | None = None,
    legacy_only: bool = False,
) -> list[dict[str, Any]]:
    paths = list(reversed(list_result_paths(pattern)))
    items: list[dict[str, Any]] = []

    for path in paths:
        item = load_result(path)

        if model and item.get("model") != model:
            continue
        if engine and item.get("engine") != engine:
            continue
        if device and item.get("device") != device:
            continue
        if precision and item.get("precision") != precision:
            continue
        if batch is not None and item.get("batch") != batch:
            continue
        if height is not None and item.get("height") != height:
            continue
        if width is not None and item.get("width") != width:
            continue
        if legacy_only and not item.get("legacy_result"):
            continue

        items.append(item)

    if limit > 0:
        return items[:limit]
    return items
