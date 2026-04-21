from __future__ import annotations

import glob
import json
import os
from typing import Any, Dict, List

from inferedgelab.result.schema import normalize_result_schema


def load_result(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # legacy compatibility
    has_system = "system" in data
    has_run_config = "run_config" in data
    data = normalize_result_schema(data)
    data["legacy_result"] = not (has_system and has_run_config)

    return data


def load_results(pattern: str = "results/*.json") -> List[Dict[str, Any]]:
    paths = sorted(glob.glob(pattern))
    results: List[Dict[str, Any]] = []

    for path in paths:
        results.append(load_result(path))

    return results


def list_result_paths(pattern: str = "results/*.json") -> List[str]:
    paths = glob.glob(pattern)
    return sorted(paths, key=os.path.getmtime)


def latest_result_paths(count: int = 2, pattern: str = "results/*.json") -> List[str]:
    paths = list_result_paths(pattern)
    if len(paths) < count:
        raise ValueError(f"최소 {count}개의 result 파일이 필요합니다. 현재: {len(paths)}개")
    return paths[-count:]


def result_identity_key(item: Dict[str, Any]) -> str:
    return "::".join(
        [
            str(item.get("model")),
            str(item.get("engine")),
            str(item.get("device")),
            str(item.get("precision")),
            str(item.get("batch")),
            str(item.get("height")),
            str(item.get("width")),
        ]
    )


def result_identity_key_without_precision(item: Dict[str, Any]) -> str:
    return "::".join(
        [
            str(item.get("model")),
            str(item.get("engine")),
            str(item.get("device")),
            str(item.get("batch")),
            str(item.get("height")),
            str(item.get("width")),
        ]
    )


def latest_comparable_result_paths(pattern: str = "results/*.json") -> List[str]:
    paths = list_result_paths(pattern)
    if len(paths) < 2:
        raise ValueError(f"최소 2개의 result 파일이 필요합니다. 현재: {len(paths)}개")

    items = [(path, load_result(path)) for path in paths]
    items_desc = list(reversed(items))

    newest_path, newest_item = items_desc[0]
    target_key = result_identity_key(newest_item)

    matched_paths: List[str] = []
    for path, item in items_desc:
        if result_identity_key(item) == target_key:
            matched_paths.append(path)
        if len(matched_paths) == 2:
            break

    if len(matched_paths) < 2:
        raise ValueError("같은 조건(model/engine/device/batch/height/width)의 최근 결과 2개를 찾지 못했습니다.")

    return list(reversed(matched_paths))


def sort_results_by_timestamp(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(results, key=lambda item: str(item.get("timestamp") or ""))


def filter_results(
    results: List[Dict[str, Any]],
    model: str = "",
    engine: str = "",
    device: str = "",
    precision: str = "",
    batch: int | None = None,
    height: int | None = None,
    width: int | None = None,
) -> List[Dict[str, Any]]:
    filtered = results

    if model:
        filtered = [item for item in filtered if str(item.get("model")) == model]

    if engine:
        filtered = [item for item in filtered if str(item.get("engine")) == engine]

    if device:
        filtered = [item for item in filtered if str(item.get("device")) == device]

    if precision:
        filtered = [item for item in filtered if str(item.get("precision")) == precision]

    if batch is not None:
        filtered = [item for item in filtered if item.get("batch") == batch]

    if height is not None:
        filtered = [item for item in filtered if item.get("height") == height]

    if width is not None:
        filtered = [item for item in filtered if item.get("width") == width]

    return filtered


def select_history_results(
    pattern: str = "results/*.json",
    model: str = "",
    engine: str = "",
    device: str = "",
    precision: str = "",
    batch: int | None = None,
    height: int | None = None,
    width: int | None = None,
) -> List[Dict[str, Any]]:
    results = load_results(pattern)
    results = filter_results(
        results,
        model=model,
        engine=engine,
        device=device,
        precision=precision,
        batch=batch,
        height=height,
        width=width,
    )
    return sort_results_by_timestamp(results)


def latest_comparable_items(results: List[Dict[str, Any]], count: int = 2) -> List[Dict[str, Any]]:
    if len(results) < count:
        raise ValueError(f"최소 {count}개의 result 항목이 필요합니다. 현재: {len(results)}개")

    items_desc = list(reversed(sort_results_by_timestamp(results)))

    newest_item = items_desc[0]
    target_key = result_identity_key(newest_item)

    matched_items: List[Dict[str, Any]] = []
    for item in items_desc:
        if result_identity_key(item) == target_key:
            matched_items.append(item)
        if len(matched_items) == count:
            break

    if len(matched_items) < count:
        raise ValueError(
            "같은 조건(model/engine/device/precision/batch/height/width)의 최근 결과 2개를 찾지 못했습니다."
        )

    return list(reversed(matched_items))


def latest_cross_precision_items(results: List[Dict[str, Any]], count: int = 2) -> List[Dict[str, Any]]:
    if len(results) < count:
        raise ValueError(f"최소 {count}개의 result 항목이 필요합니다. 현재: {len(results)}개")

    items_desc = list(reversed(sort_results_by_timestamp(results)))

    newest_item = items_desc[0]
    target_key = result_identity_key_without_precision(newest_item)

    matched_items: List[Dict[str, Any]] = []
    seen_precisions: set[str] = set()

    for item in items_desc:
        if result_identity_key_without_precision(item) != target_key:
            continue

        precision = str(item.get("precision"))
        if precision in seen_precisions:
            continue

        matched_items.append(item)
        seen_precisions.add(precision)

        if len(matched_items) == count:
            break

    if len(matched_items) < count:
        raise ValueError(
            "같은 조건(model/engine/device/batch/height/width)에서 precision이 다른 최근 결과 2개를 찾지 못했습니다."
        )

    return list(reversed(matched_items))
