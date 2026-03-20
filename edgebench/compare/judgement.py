from __future__ import annotations

from typing import Any, Dict, Optional

def _judge_delta_pct(delta_pct: Optional[float], improve_threshold: float = -3.0, regress_threshold: float = 3.0) -> str:
    """
    delta_pct 기준으로 성능 판정
    latency 기준:
    - 음수면 개선
    - 양수면 악화
    """
    if delta_pct is None:
        return "unknown"
    
    if delta_pct <= improve_threshold:
        return "improvement"
    if delta_pct >= regress_threshold:
        return "regression"
    return "newtral"

def judge_comparison(compare_result: Dict[str, Any]) -> Dict[str, Any]:
    metrics = compare_result["metrics"]
    shape = compare_result["shape"]
    system_diff = compare_result["system_diff"]

    shape_match = shape["base"] == shape["new"]

    system_match = all(
        values["base"] == values["new"]
        for values in system_diff.values()
    )

    mean_judgement = _judge_delta_pct(metrics["mean_ms"]["delta_pct"])
    p99_judgement = _judge_delta_pct(metrics["p99_ms"]["delta_pct"])

    overall = "neutral"

    if not shape_match:
        overall = "mismatch"
    elif mean_judgement == "regression" or p99_judgement == "regression":
        overall = "regression"
    elif mean_judgement == "improvement" and p99_judgement in ("improvement", "neutral"):
        overall = "improvement"

    return {
        "overall": overall,
        "shape_match": shape_match,
        "system_match": system_match,
        "mean_ms": mean_judgement,
        "p99_ms": p99_judgement,
    }