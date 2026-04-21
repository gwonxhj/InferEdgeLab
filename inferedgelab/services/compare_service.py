from __future__ import annotations

from typing import Any

from inferedgelab.compare.comparator import compare_results
from inferedgelab.compare.judgement import judge_comparison
from inferedgelab.config import resolve_compare_thresholds
from inferedgelab.report.html_generator import generate_compare_html
from inferedgelab.report.markdown_generator import generate_compare_markdown
from inferedgelab.result.loader import (
    filter_results,
    latest_comparable_items,
    latest_cross_precision_items,
    list_result_paths,
    load_result,
    load_results,
)


def build_compare_bundle(
    *,
    base_path: str,
    new_path: str,
    latency_improve_threshold: float | None = None,
    latency_regress_threshold: float | None = None,
    accuracy_improve_threshold: float | None = None,
    accuracy_regress_threshold: float | None = None,
    tradeoff_caution_threshold: float | None = None,
    tradeoff_risky_threshold: float | None = None,
    tradeoff_severe_threshold: float | None = None,
    pyproject_path: str = "pyproject.toml",
) -> dict[str, Any]:
    """
    Build a compare bundle for API use while preserving legacy top-level fields
    used by CLI consumers.
    """
    base = load_result(base_path)
    new = load_result(new_path)

    thresholds = resolve_compare_thresholds(
        latency_improve_threshold=latency_improve_threshold,
        latency_regress_threshold=latency_regress_threshold,
        accuracy_improve_threshold=accuracy_improve_threshold,
        accuracy_regress_threshold=accuracy_regress_threshold,
        tradeoff_caution_threshold=tradeoff_caution_threshold,
        tradeoff_risky_threshold=tradeoff_risky_threshold,
        tradeoff_severe_threshold=tradeoff_severe_threshold,
        pyproject_path=pyproject_path,
    )

    result = compare_results(base, new)
    judgement = judge_comparison(
        result,
        latency_improve_threshold=thresholds["latency_improve_threshold"],
        latency_regress_threshold=thresholds["latency_regress_threshold"],
        accuracy_improve_threshold=thresholds["accuracy_improve_threshold"],
        accuracy_regress_threshold=thresholds["accuracy_regress_threshold"],
        tradeoff_caution_threshold=thresholds["tradeoff_caution_threshold"],
        tradeoff_risky_threshold=thresholds["tradeoff_risky_threshold"],
        tradeoff_severe_threshold=thresholds["tradeoff_severe_threshold"],
    )

    markdown = generate_compare_markdown(result, judgement)
    html = generate_compare_html(result, judgement)
    legacy_warning = bool(base.get("legacy_result") or new.get("legacy_result"))
    bundle = {
        "meta": {
            "base_path": base_path,
            "new_path": new_path,
            "legacy_warning": legacy_warning,
        },
        "data": {
            "base": base,
            "new": new,
            "result": result,
            "judgement": judgement,
        },
        "rendered": {
            "markdown": markdown,
            "html": html,
        },
    }

    return {
        **bundle,
        "base": base,
        "new": new,
        "base_path": base_path,
        "new_path": new_path,
        "result": result,
        "judgement": judgement,
        "markdown": markdown,
        "html": html,
        "legacy_warning": legacy_warning,
    }


def build_compare_latest_bundle(
    *,
    pattern: str = "results/*.json",
    model: str = "",
    engine: str = "",
    device: str = "",
    precision: str = "",
    selection_mode: str = "same_precision",
    latency_improve_threshold: float | None = None,
    latency_regress_threshold: float | None = None,
    accuracy_improve_threshold: float | None = None,
    accuracy_regress_threshold: float | None = None,
    tradeoff_caution_threshold: float | None = None,
    tradeoff_risky_threshold: float | None = None,
    tradeoff_severe_threshold: float | None = None,
    pyproject_path: str = "pyproject.toml",
) -> dict[str, Any]:
    """
    Build a latest-compare bundle with API-ready structure while preserving
    convenience top-level fields used by CLI consumers.
    """
    pair = select_latest_compare_pair(
        pattern=pattern,
        model=model,
        engine=engine,
        device=device,
        precision=precision,
        selection_mode=selection_mode,
    )
    compare_bundle = build_compare_bundle(
        base_path=pair["base_path"],
        new_path=pair["new_path"],
        latency_improve_threshold=latency_improve_threshold,
        latency_regress_threshold=latency_regress_threshold,
        accuracy_improve_threshold=accuracy_improve_threshold,
        accuracy_regress_threshold=accuracy_regress_threshold,
        tradeoff_caution_threshold=tradeoff_caution_threshold,
        tradeoff_risky_threshold=tradeoff_risky_threshold,
        tradeoff_severe_threshold=tradeoff_severe_threshold,
        pyproject_path=pyproject_path,
    )

    latest_bundle = {
        "meta": {
            "pattern": pattern,
            "model": model,
            "engine": engine,
            "device": device,
            "precision": precision,
            "selection_mode": pair["selection_mode"],
            "base_path": pair["base_path"],
            "new_path": pair["new_path"],
            "run_config_mismatch_fields": pair["run_config_mismatch_fields"],
            "legacy_warning": compare_bundle["legacy_warning"],
        },
        "data": {
            "pair": pair,
            "base": compare_bundle["base"],
            "new": compare_bundle["new"],
            "result": compare_bundle["result"],
            "judgement": compare_bundle["judgement"],
        },
        "rendered": {
            "markdown": compare_bundle["markdown"],
            "html": compare_bundle["html"],
        },
    }

    return {
        **latest_bundle,
        "pair": pair,
        "base": compare_bundle["base"],
        "new": compare_bundle["new"],
        "base_path": pair["base_path"],
        "new_path": pair["new_path"],
        "result": compare_bundle["result"],
        "judgement": compare_bundle["judgement"],
        "markdown": compare_bundle["markdown"],
        "html": compare_bundle["html"],
        "legacy_warning": compare_bundle["legacy_warning"],
        "run_config_mismatch_fields": pair["run_config_mismatch_fields"],
        "selection_mode": pair["selection_mode"],
    }


def _normalize_selection_mode(value: str) -> str:
    return str(value or "").strip().lower().replace("-", "_")


def _core_run_config_mismatch_fields(base_item: dict[str, Any], new_item: dict[str, Any]) -> list[str]:
    base_run_config = base_item.get("run_config") or {}
    new_run_config = new_item.get("run_config") or {}
    core_fields = ("warmup", "runs", "intra_threads", "inter_threads", "mode", "task")

    return [field for field in core_fields if base_run_config.get(field) != new_run_config.get(field)]


def _matches_target_item(candidate: dict[str, Any], target_item: dict[str, Any]) -> bool:
    comparable_fields = (
        "model",
        "engine",
        "device",
        "precision",
        "batch",
        "height",
        "width",
        "timestamp",
    )
    return all(str(candidate.get(field)) == str(target_item.get(field)) for field in comparable_fields)


def _find_path_for_item(pattern: str, target_item: dict[str, Any]) -> str | None:
    for path in list_result_paths(pattern):
        data = load_result(path)
        if _matches_target_item(data, target_item):
            return path
    return None


def select_latest_compare_pair(
    *,
    pattern: str = "results/*.json",
    model: str = "",
    engine: str = "",
    device: str = "",
    precision: str = "",
    selection_mode: str = "same_precision",
) -> dict[str, Any]:
    normalized_selection_mode = _normalize_selection_mode(selection_mode)
    allowed_modes = {"same_precision", "cross_precision"}

    if normalized_selection_mode not in allowed_modes:
        raise ValueError(
            f"지원하지 않는 --selection-mode 값입니다: {normalized_selection_mode}. "
            "same_precision 또는 cross_precision 을 사용하세요."
        )

    if normalized_selection_mode == "cross_precision" and precision:
        raise ValueError("cross_precision 모드에서는 --precision 필터를 함께 사용할 수 없습니다.")

    all_items = load_results(pattern)

    if normalized_selection_mode == "same_precision":
        filtered_items = filter_results(
            all_items,
            model=model,
            engine=engine,
            device=device,
            precision=precision,
        )
        selected_items = latest_comparable_items
    else:
        filtered_items = filter_results(
            all_items,
            model=model,
            engine=engine,
            device=device,
        )
        selected_items = latest_cross_precision_items

    if len(filtered_items) < 2:
        raise ValueError(f"필터 조건에 맞는 result가 2개 미만입니다. 현재: {len(filtered_items)}개")

    base, new = selected_items(filtered_items, count=2)

    base_path = _find_path_for_item(pattern, base)
    new_path = _find_path_for_item(pattern, new)

    if not base_path or not new_path:
        raise ValueError("비교 대상 result 파일 경로를 찾지 못했습니다.")

    return {
        "selection_mode": normalized_selection_mode,
        "base": base,
        "new": new,
        "base_path": base_path,
        "new_path": new_path,
        "run_config_mismatch_fields": _core_run_config_mismatch_fields(base, new),
    }
