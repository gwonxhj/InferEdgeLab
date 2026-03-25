from __future__ import annotations

from typing import Any, Dict, Optional


def _judge_delta_pct(
    delta_pct: Optional[float],
    improve_threshold: float = -3.0,
    regress_threshold: float = 3.0,
) -> str:
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
    return "neutral"


def _build_overall(
    comparison_mode: str,
    shape_match: bool,
    mean_judgement: str,
    p99_judgement: str,
) -> str:
    if not shape_match:
        return "mismatch"

    if comparison_mode == "cross_precision":
        if mean_judgement == "regression" or p99_judgement == "regression":
            return "tradeoff_slower"
        if mean_judgement == "improvement" and p99_judgement in ("improvement", "neutral"):
            return "tradeoff_faster"
        return "tradeoff_neutral"

    if mean_judgement == "regression" or p99_judgement == "regression":
        return "regression"
    if mean_judgement == "improvement" and p99_judgement in ("improvement", "neutral"):
        return "improvement"
    return "neutral"


def _build_summary(
    overall: str,
    comparison_mode: str,
    precision_pair: str,
    mean_judgement: str,
    p99_judgement: str,
    shape_match: bool,
) -> str:
    if not shape_match:
        return "Input shape mismatch detected. Latency comparison should be interpreted with caution."

    if comparison_mode == "cross_precision":
        if overall == "tradeoff_slower":
            return (
                f"Cross-precision comparison ({precision_pair}) shows slower latency in the new result. "
                "Interpret this as a precision trade-off outcome rather than a same-condition regression."
            )
        if overall == "tradeoff_faster":
            return (
                f"Cross-precision comparison ({precision_pair}) shows faster latency in the new result. "
                "This is a useful optimization signal, but accuracy trade-offs are not evaluated here."
            )
        return (
            f"Cross-precision comparison ({precision_pair}) shows no strong latency change. "
            "Interpret this as a precision trade-off check rather than a strict regression test."
        )

    if overall == "regression":
        return "Same-precision comparison indicates a latency regression in the new result."
    if overall == "improvement":
        return "Same-precision comparison indicates a latency improvement in the new result."
    if mean_judgement == "unknown" or p99_judgement == "unknown":
        return "Some latency metrics are missing, so the comparison result is partially inconclusive."
    return "Same-precision comparison indicates no significant latency change."


def _build_notes(
    comparison_mode: str,
    precision_pair: str,
    shape_match: bool,
    system_match: bool,
) -> list[str]:
    notes: list[str] = []

    if comparison_mode == "cross_precision":
        notes.append(
            f"This is a cross-precision comparison: {precision_pair}. "
            "Latency differences can be caused by precision changes as well as runtime behavior."
        )
        notes.append(
            "Cross-precision overall status uses trade-off semantics instead of same-condition regression semantics."
        )
        notes.append(
            "A faster INT8 result does not guarantee equivalent model accuracy. "
            "Accuracy / quality validation must be checked separately."
        )
    else:
        notes.append(
            "This is a same-precision comparison, so latency deltas are more suitable for regression tracking."
        )

    if not shape_match:
        notes.append(
            "Input shape does not match between the two results. "
            "This weakens direct latency comparability."
        )

    if not system_match:
        notes.append(
            "System information differs between the two results. "
            "Hardware / OS / Python differences may influence latency."
        )

    return notes


def judge_comparison(compare_result: Dict[str, Any]) -> Dict[str, Any]:
    metrics = compare_result["metrics"]
    shape = compare_result["shape"]
    system_diff = compare_result["system_diff"]
    precision_info = compare_result["precision"]

    shape_match = shape["base"] == shape["new"]

    system_match = all(
        values["base"] == values["new"]
        for values in system_diff.values()
    )

    mean_judgement = _judge_delta_pct(metrics["mean_ms"]["delta_pct"])
    p99_judgement = _judge_delta_pct(metrics["p99_ms"]["delta_pct"])

    comparison_mode = precision_info["comparison_mode"]
    precision_pair = precision_info["pair"]
    precision_match = precision_info["match"]

    overall = _build_overall(
        comparison_mode=comparison_mode,
        shape_match=shape_match,
        mean_judgement=mean_judgement,
        p99_judgement=p99_judgement,
    )

    summary = _build_summary(
        overall=overall,
        comparison_mode=comparison_mode,
        precision_pair=precision_pair,
        mean_judgement=mean_judgement,
        p99_judgement=p99_judgement,
        shape_match=shape_match,
    )

    notes = _build_notes(
        comparison_mode=comparison_mode,
        precision_pair=precision_pair,
        shape_match=shape_match,
        system_match=system_match,
    )

    return {
        "overall": overall,
        "shape_match": shape_match,
        "system_match": system_match,
        "precision_match": precision_match,
        "comparison_mode": comparison_mode,
        "precision_pair": precision_pair,
        "mean_ms": mean_judgement,
        "p99_ms": p99_judgement,
        "summary": summary,
        "notes": notes,
    }