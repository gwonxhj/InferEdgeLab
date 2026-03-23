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

    return {
        "base_id": {
            "model": base.get("model"),
            "engine": base.get("engine"),
            "device": base.get("device"),
            "timestamp": base.get("timestamp"),
        },
        "new_id": {
            "model": new.get("model"),
            "engine": new.get("engine"),
            "device": new.get("device"),
            "timestamp": new.get("timestamp"),
        },
        "metrics": {
            "mean_ms": {
                "base": base_mean,
                "new": new_mean,
                "delta": (new_mean - base_mean) if (base_mean is not None and new_mean is not None) else None,
                "delta_pct": _safe_pct_delta(base_mean, new_mean),
            },
            "p99_ms": {
                "base": base_p99,
                "new": new_p99,
                "delta": (new_p99 - base_p99) if (base_p99 is not None and new_p99 is not None) else None,
                "delta_pct": _safe_pct_delta(base_p99, new_p99),
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
        },
    }