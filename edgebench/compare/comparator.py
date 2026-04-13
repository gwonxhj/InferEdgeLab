from __future__ import annotations

from typing import Any, Dict, Optional


def _safe_pct_delta(base: Optional[float], new: Optional[float]) -> Optional[float]:
    """
    기준값(base) 대비 새 값(new)의 퍼센트 변화율을 계산한다.
    예:
    base=10, new=12 -> +20.0
    """
    if base is None or new is None:
        return None
    if base == 0:
        return None
    return ((new - base) / base) * 100.0


def _safe_delta(base: Optional[float], new: Optional[float]) -> Optional[float]:
    if base is None or new is None:
        return None
    return new - base


def _normalize_precision(value: Any) -> str:
    if value is None:
        return "unknown"
    return str(value).strip().lower()


def _first_non_none(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _shape_summary(batch: Any, height: Any, width: Any) -> str:
    batch_text = batch if batch is not None else "-"
    height_text = height if height is not None else "-"
    width_text = width if width is not None else "-"
    return f"b{batch_text} / h{height_text} / w{width_text}"


def compare_results(base: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """
    structured result 두 개를 비교해서 핵심 차이를 정리한다.
    """

    base_mean = base.get("mean_ms")
    new_mean = new.get("mean_ms")

    base_p99 = base.get("p99_ms")
    new_p99 = new.get("p99_ms")

    base_system = base.get("system") or {}
    new_system = new.get("system") or {}

    base_run = base.get("run_config") or {}
    new_run = new.get("run_config") or {}
    base_extra = base.get("extra") or {}
    new_extra = new.get("extra") or {}

    base_accuracy = base.get("accuracy") or {}
    new_accuracy = new.get("accuracy") or {}

    base_accuracy_metrics = base_accuracy.get("metrics") or {}
    new_accuracy_metrics = new_accuracy.get("metrics") or {}

    base_top1 = base_accuracy_metrics.get("top1_accuracy")
    new_top1 = new_accuracy_metrics.get("top1_accuracy")

    base_precision = _normalize_precision(base.get("precision"))
    new_precision = _normalize_precision(new.get("precision"))
    precision_match = base_precision == new_precision
    comparison_mode = "same_precision" if precision_match else "cross_precision"
    precision_pair = f"{base_precision}_vs_{new_precision}"

    accuracy_present = (base_top1 is not None) or (new_top1 is not None)

    return {
        "base_id": {
            "model": base.get("model"),
            "engine": base.get("engine"),
            "device": base.get("device"),
            "timestamp": base.get("timestamp"),
            "precision": base_precision,
        },
        "new_id": {
            "model": new.get("model"),
            "engine": new.get("engine"),
            "device": new.get("device"),
            "timestamp": new.get("timestamp"),
            "precision": new_precision,
        },
        "precision": {
            "base": base_precision,
            "new": new_precision,
            "match": precision_match,
            "comparison_mode": comparison_mode,
            "pair": precision_pair,
        },
        "metrics": {
            "mean_ms": {
                "base": base_mean,
                "new": new_mean,
                "delta": _safe_delta(base_mean, new_mean),
                "delta_pct": _safe_pct_delta(base_mean, new_mean),
            },
            "p99_ms": {
                "base": base_p99,
                "new": new_p99,
                "delta": _safe_delta(base_p99, new_p99),
                "delta_pct": _safe_pct_delta(base_p99, new_p99),
            },
        },
        "accuracy": {
            "present": accuracy_present,
            "task": new_accuracy.get("task") or base_accuracy.get("task"),
            "metric_name": "top1_accuracy",
            "sample_count": {
                "base": base_accuracy.get("sample_count"),
                "new": new_accuracy.get("sample_count"),
            },
            "metrics": {
                "top1_accuracy": {
                    "base": base_top1,
                    "new": new_top1,
                    "delta": _safe_delta(base_top1, new_top1),
                    "delta_pct": _safe_pct_delta(base_top1, new_top1),
                    "delta_pp": (
                        _safe_delta(base_top1, new_top1) * 100.0
                        if _safe_delta(base_top1, new_top1) is not None
                        else None
                    ),
                }
            },
        },
        "shape": {
            "base": {
                "batch": base.get("batch"),
                "height": base.get("height"),
                "width": base.get("width"),
            },
            "new": {
                "batch": new.get("batch"),
                "height": new.get("height"),
                "width": new.get("width"),
            },
        },
        "shape_context": {
            "base": {
                "requested_batch": _first_non_none(
                    base_run.get("requested_batch"),
                    base_extra.get("requested_batch"),
                    base.get("batch"),
                ),
                "requested_height": _first_non_none(
                    base_run.get("requested_height"),
                    base_extra.get("requested_height"),
                    base.get("height"),
                ),
                "requested_width": _first_non_none(
                    base_run.get("requested_width"),
                    base_extra.get("requested_width"),
                    base.get("width"),
                ),
                "effective_batch": _first_non_none(
                    base_extra.get("effective_batch"),
                    base.get("batch"),
                ),
                "effective_height": _first_non_none(
                    base_extra.get("effective_height"),
                    base.get("height"),
                ),
                "effective_width": _first_non_none(
                    base_extra.get("effective_width"),
                    base.get("width"),
                ),
                "primary_input_name": base_extra.get("primary_input_name"),
                "resolved_input_shapes": base_extra.get("resolved_input_shapes"),
            },
            "new": {
                "requested_batch": _first_non_none(
                    new_run.get("requested_batch"),
                    new_extra.get("requested_batch"),
                    new.get("batch"),
                ),
                "requested_height": _first_non_none(
                    new_run.get("requested_height"),
                    new_extra.get("requested_height"),
                    new.get("height"),
                ),
                "requested_width": _first_non_none(
                    new_run.get("requested_width"),
                    new_extra.get("requested_width"),
                    new.get("width"),
                ),
                "effective_batch": _first_non_none(
                    new_extra.get("effective_batch"),
                    new.get("batch"),
                ),
                "effective_height": _first_non_none(
                    new_extra.get("effective_height"),
                    new.get("height"),
                ),
                "effective_width": _first_non_none(
                    new_extra.get("effective_width"),
                    new.get("width"),
                ),
                "primary_input_name": new_extra.get("primary_input_name"),
                "resolved_input_shapes": new_extra.get("resolved_input_shapes"),
            },
        },
        "runtime_provenance": {
            "base": {
                "runtime_artifact_path": _first_non_none(
                    base_extra.get("runtime_artifact_path"),
                    (base_extra.get("load_kwargs") or {}).get("engine_path")
                    if isinstance(base_extra.get("load_kwargs"), dict)
                    else None,
                ),
                "primary_input_name": base_extra.get("primary_input_name"),
                "requested_shape_summary": _shape_summary(
                    _first_non_none(
                        base_run.get("requested_batch"),
                        base_extra.get("requested_batch"),
                        base.get("batch"),
                    ),
                    _first_non_none(
                        base_run.get("requested_height"),
                        base_extra.get("requested_height"),
                        base.get("height"),
                    ),
                    _first_non_none(
                        base_run.get("requested_width"),
                        base_extra.get("requested_width"),
                        base.get("width"),
                    ),
                ),
                "effective_shape_summary": _shape_summary(
                    _first_non_none(base_extra.get("effective_batch"), base.get("batch")),
                    _first_non_none(base_extra.get("effective_height"), base.get("height")),
                    _first_non_none(base_extra.get("effective_width"), base.get("width")),
                ),
            },
            "new": {
                "runtime_artifact_path": _first_non_none(
                    new_extra.get("runtime_artifact_path"),
                    (new_extra.get("load_kwargs") or {}).get("engine_path")
                    if isinstance(new_extra.get("load_kwargs"), dict)
                    else None,
                ),
                "primary_input_name": new_extra.get("primary_input_name"),
                "requested_shape_summary": _shape_summary(
                    _first_non_none(
                        new_run.get("requested_batch"),
                        new_extra.get("requested_batch"),
                        new.get("batch"),
                    ),
                    _first_non_none(
                        new_run.get("requested_height"),
                        new_extra.get("requested_height"),
                        new.get("height"),
                    ),
                    _first_non_none(
                        new_run.get("requested_width"),
                        new_extra.get("requested_width"),
                        new.get("width"),
                    ),
                ),
                "effective_shape_summary": _shape_summary(
                    _first_non_none(new_extra.get("effective_batch"), new.get("batch")),
                    _first_non_none(new_extra.get("effective_height"), new.get("height")),
                    _first_non_none(new_extra.get("effective_width"), new.get("width")),
                ),
            },
        },
        "system_diff": {
            "os": {
                "base": base_system.get("os"),
                "new": new_system.get("os"),
            },
            "python": {
                "base": base_system.get("python"),
                "new": new_system.get("python"),
            },
            "machine": {
                "base": base_system.get("machine"),
                "new": new_system.get("machine"),
            },
            "cpu_count_logical": {
                "base": base_system.get("cpu_count_logical"),
                "new": new_system.get("cpu_count_logical"),
            },
        },
        "run_config_diff": {
            "warmup": {
                "base": base_run.get("warmup"),
                "new": new_run.get("warmup"),
            },
            "runs": {
                "base": base_run.get("runs"),
                "new": new_run.get("runs"),
            },
            "intra_threads": {
                "base": base_run.get("intra_threads"),
                "new": new_run.get("intra_threads"),
            },
            "inter_threads": {
                "base": base_run.get("inter_threads"),
                "new": new_run.get("inter_threads"),
            },
            "mode": {
                "base": base_run.get("mode"),
                "new": new_run.get("mode"),
            },
            "task": {
                "base": base_run.get("task"),
                "new": new_run.get("task"),
            },
        },
    }
