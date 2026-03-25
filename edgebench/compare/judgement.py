from __future__ import annotations

from typing import Any, Dict, Optional


def _judge_delta_pct(
    delta_pct: Optional[float],
    improve_threshold: float = -3.0,
    regress_threshold: float = 3.0,
) -> str:
    """
    delta_pct 기준으로 latency 성능 판정
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


def _judge_accuracy_delta_pp(
    delta_pp: Optional[float],
    improve_threshold: float = 0.20,
    regress_threshold: float = -0.20,
) -> str:
    """
    accuracy delta_pp(percentage point) 기준 판정
    - 양수면 accuracy 개선
    - 음수면 accuracy 악화
    """
    if delta_pp is None:
        return "unknown"

    if delta_pp >= improve_threshold:
        return "improvement"
    if delta_pp <= regress_threshold:
        return "regression"
    return "neutral"


def _build_overall(
    comparison_mode: str,
    shape_match: bool,
    mean_judgement: str,
    p99_judgement: str,
    accuracy_judgement: str,
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

    if accuracy_judgement == "regression":
        return "regression"

    if (
        mean_judgement == "improvement"
        and p99_judgement in ("improvement", "neutral")
        and accuracy_judgement in ("improvement", "neutral", "unknown")
    ):
        return "improvement"

    if accuracy_judgement == "improvement" and mean_judgement in ("neutral", "unknown"):
        return "improvement"

    return "neutral"


def _build_summary(
    overall: str,
    comparison_mode: str,
    precision_pair: str,
    mean_judgement: str,
    p99_judgement: str,
    accuracy_judgement: str,
    accuracy_delta_pp: Optional[float],
    accuracy_present: bool,
    shape_match: bool,
) -> str:
    if not shape_match:
        return "Input shape mismatch detected. Comparison should be interpreted with caution."

    accuracy_text = ""
    if accuracy_present and accuracy_delta_pp is not None:
        accuracy_text = f" Accuracy delta: {accuracy_delta_pp:+.2f}pp."
    elif accuracy_present:
        accuracy_text = " Accuracy data is present but partially incomplete."
    else:
        accuracy_text = " Accuracy trade-offs are not available in these results."

    if comparison_mode == "cross_precision":
        if overall == "tradeoff_slower":
            return (
                f"Cross-precision comparison ({precision_pair}) shows slower latency in the new result."
                f"{accuracy_text}"
            )
        if overall == "tradeoff_faster":
            return (
                f"Cross-precision comparison ({precision_pair}) shows faster latency in the new result."
                f"{accuracy_text}"
            )
        return (
            f"Cross-precision comparison ({precision_pair}) shows no strong latency change."
            f"{accuracy_text}"
        )

    if overall == "regression":
        return f"Same-precision comparison indicates a regression in the new result.{accuracy_text}"

    if overall == "improvement":
        return f"Same-precision comparison indicates an improvement in the new result.{accuracy_text}"

    if mean_judgement == "unknown" or p99_judgement == "unknown":
        return f"Some latency metrics are missing, so the comparison result is partially inconclusive.{accuracy_text}"

    if accuracy_judgement == "unknown" and accuracy_present:
        return f"Latency change is limited, but accuracy comparison is partially inconclusive.{accuracy_text}"

    return f"Same-precision comparison indicates no significant overall change.{accuracy_text}"


def _build_notes(
    comparison_mode: str,
    precision_pair: str,
    shape_match: bool,
    system_match: bool,
    accuracy_present: bool,
    accuracy_judgement: str,
    accuracy_delta_pp: Optional[float],
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
    else:
        notes.append(
            "This is a same-precision comparison, so latency deltas are more suitable for regression tracking."
        )

    if accuracy_present:
        notes.append(
            "Accuracy data is available and is compared using top1_accuracy with percentage-point deltas."
        )
        if accuracy_delta_pp is not None:
            notes.append(f"Accuracy delta (new - base): {accuracy_delta_pp:+.2f}pp.")
        if accuracy_judgement == "regression":
            notes.append("The new result shows an accuracy regression.")
        elif accuracy_judgement == "improvement":
            notes.append("The new result shows an accuracy improvement.")
        else:
            notes.append("The new result shows no strong accuracy change.")
    else:
        notes.append(
            "Accuracy data is not available for one or both results, so trade-off interpretation is latency-only."
        )

    if not shape_match:
        notes.append(
            "Input shape does not match between the two results. "
            "This weakens direct comparability."
        )

    if not system_match:
        notes.append(
            "System information differs between the two results. "
            "Hardware / OS / Python differences may influence results."
        )

    return notes


def judge_comparison(compare_result: Dict[str, Any]) -> Dict[str, Any]:
    metrics = compare_result["metrics"]
    accuracy = compare_result["accuracy"]
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

    accuracy_metric = accuracy["metrics"]["top1_accuracy"]
    accuracy_delta_pp = accuracy_metric.get("delta_pp")
    accuracy_present = accuracy.get("present", False)
    accuracy_judgement = _judge_accuracy_delta_pp(accuracy_delta_pp)

    comparison_mode = precision_info["comparison_mode"]
    precision_pair = precision_info["pair"]
    precision_match = precision_info["match"]

    overall = _build_overall(
        comparison_mode=comparison_mode,
        shape_match=shape_match,
        mean_judgement=mean_judgement,
        p99_judgement=p99_judgement,
        accuracy_judgement=accuracy_judgement,
    )

    summary = _build_summary(
        overall=overall,
        comparison_mode=comparison_mode,
        precision_pair=precision_pair,
        mean_judgement=mean_judgement,
        p99_judgement=p99_judgement,
        accuracy_judgement=accuracy_judgement,
        accuracy_delta_pp=accuracy_delta_pp,
        accuracy_present=accuracy_present,
        shape_match=shape_match,
    )

    notes = _build_notes(
        comparison_mode=comparison_mode,
        precision_pair=precision_pair,
        shape_match=shape_match,
        system_match=system_match,
        accuracy_present=accuracy_present,
        accuracy_judgement=accuracy_judgement,
        accuracy_delta_pp=accuracy_delta_pp,
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
        "accuracy": accuracy_judgement,
        "accuracy_present": accuracy_present,
        "summary": summary,
        "notes": notes,
    }