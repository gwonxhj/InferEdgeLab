from __future__ import annotations

from typing import Any, Dict, Optional


def _judge_delta_pct(
    delta_pct: Optional[float],
    improve_threshold: float,
    regress_threshold: float,
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
    improve_threshold: float,
    regress_threshold: float,
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


def _classify_tradeoff_risk(
    comparison_mode: str,
    mean_judgement: str,
    p99_judgement: str,
    accuracy_present: bool,
    accuracy_delta_pp: Optional[float],
    caution_threshold: float,
    risky_threshold: float,
    severe_threshold: float,
) -> str:
    """
    cross-precision 시나리오에서 latency-accuracy trade-off 위험도를 분류한다.
    threshold는 모두 음수(pp 하락) 기준이어야 한다.
    예:
    caution=-0.30, risky=-1.0, severe=-2.0
    """
    if comparison_mode != "cross_precision":
        return "not_applicable"

    latency_faster = mean_judgement == "improvement" and p99_judgement in ("improvement", "neutral")
    latency_slower = mean_judgement == "regression" or p99_judgement == "regression"

    if latency_slower:
        return "not_beneficial"

    if not accuracy_present or accuracy_delta_pp is None:
        if latency_faster:
            return "unknown_risk"
        return "no_clear_tradeoff"

    if accuracy_delta_pp <= severe_threshold:
        return "severe_tradeoff"

    if accuracy_delta_pp <= risky_threshold:
        return "risky_tradeoff"

    if accuracy_delta_pp <= caution_threshold:
        return "caution_tradeoff"

    if latency_faster:
        return "acceptable_tradeoff"

    return "no_clear_tradeoff"


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
    accuracy_metric_name: str,
    mean_judgement: str,
    p99_judgement: str,
    accuracy_judgement: str,
    accuracy_delta_pp: Optional[float],
    accuracy_present: bool,
    tradeoff_risk: str,
    shape_match: bool,
) -> str:
    if not shape_match:
        return "Input shape mismatch detected. Comparison should be interpreted with caution."

    accuracy_text = ""
    if accuracy_present and accuracy_delta_pp is not None:
        accuracy_text = f" Primary accuracy metric ({accuracy_metric_name}) delta: {accuracy_delta_pp:+.2f}pp."
    elif accuracy_present:
        accuracy_text = f" Primary accuracy metric ({accuracy_metric_name}) is present but partially incomplete."
    else:
        accuracy_text = " Accuracy trade-offs are not available in these results."

    if comparison_mode == "cross_precision":
        risk_text = f" Trade-off risk: {tradeoff_risk}."

        if overall == "tradeoff_slower":
            return (
                f"Cross-precision comparison ({precision_pair}) shows slower latency in the new result."
                f"{accuracy_text}{risk_text}"
            )
        if overall == "tradeoff_faster":
            return (
                f"Cross-precision comparison ({precision_pair}) shows faster latency in the new result."
                f"{accuracy_text}{risk_text}"
            )
        return (
            f"Cross-precision comparison ({precision_pair}) shows no strong latency change."
            f"{accuracy_text}{risk_text}"
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
    accuracy_metric_name: str,
    accuracy_judgement: str,
    accuracy_delta_pp: Optional[float],
    tradeoff_risk: str,
    thresholds: Dict[str, float],
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
        notes.append(f"Trade-off risk classification: {tradeoff_risk}.")
        notes.append(
            "Trade-off thresholds: "
            f"caution<={thresholds['tradeoff_caution_threshold']:.2f}pp, "
            f"risky<={thresholds['tradeoff_risky_threshold']:.2f}pp, "
            f"severe<={thresholds['tradeoff_severe_threshold']:.2f}pp."
        )
    else:
        notes.append(
            "This is a same-precision comparison, so latency deltas are more suitable for regression tracking."
        )

    if accuracy_present:
        notes.append(
            f"Accuracy data is available and is compared using {accuracy_metric_name} as the primary metric with percentage-point deltas."
        )
        if accuracy_delta_pp is not None:
            notes.append(f"Primary accuracy delta (new - base, {accuracy_metric_name}): {accuracy_delta_pp:+.2f}pp.")
        if accuracy_judgement == "regression":
            notes.append(f"The new result shows a primary accuracy regression on {accuracy_metric_name}.")
        elif accuracy_judgement == "improvement":
            notes.append(f"The new result shows a primary accuracy improvement on {accuracy_metric_name}.")
        else:
            notes.append(f"The new result shows no strong primary accuracy change on {accuracy_metric_name}.")
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


def judge_comparison(
    compare_result: Dict[str, Any],
    latency_improve_threshold: float = -3.0,
    latency_regress_threshold: float = 3.0,
    accuracy_improve_threshold: float = 0.20,
    accuracy_regress_threshold: float = -0.20,
    tradeoff_caution_threshold: float = -0.30,
    tradeoff_risky_threshold: float = -1.00,
    tradeoff_severe_threshold: float = -2.00,
) -> Dict[str, Any]:
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

    mean_judgement = _judge_delta_pct(
        metrics["mean_ms"]["delta_pct"],
        improve_threshold=latency_improve_threshold,
        regress_threshold=latency_regress_threshold,
    )
    p99_judgement = _judge_delta_pct(
        metrics["p99_ms"]["delta_pct"],
        improve_threshold=latency_improve_threshold,
        regress_threshold=latency_regress_threshold,
    )

    accuracy_metric_name = str(accuracy.get("metric_name") or "top1_accuracy")
    accuracy_metric = accuracy.get("metrics", {}).get(accuracy_metric_name, {})
    accuracy_delta_pp = accuracy_metric.get("delta_pp")
    accuracy_present = accuracy.get("present", False)
    accuracy_judgement = _judge_accuracy_delta_pp(
        accuracy_delta_pp,
        improve_threshold=accuracy_improve_threshold,
        regress_threshold=accuracy_regress_threshold,
    )

    comparison_mode = precision_info["comparison_mode"]
    precision_pair = precision_info["pair"]
    precision_match = precision_info["match"]

    tradeoff_risk = _classify_tradeoff_risk(
        comparison_mode=comparison_mode,
        mean_judgement=mean_judgement,
        p99_judgement=p99_judgement,
        accuracy_present=accuracy_present,
        accuracy_delta_pp=accuracy_delta_pp,
        caution_threshold=tradeoff_caution_threshold,
        risky_threshold=tradeoff_risky_threshold,
        severe_threshold=tradeoff_severe_threshold,
    )

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
        accuracy_metric_name=accuracy_metric_name,
        mean_judgement=mean_judgement,
        p99_judgement=p99_judgement,
        accuracy_judgement=accuracy_judgement,
        accuracy_delta_pp=accuracy_delta_pp,
        accuracy_present=accuracy_present,
        tradeoff_risk=tradeoff_risk,
        shape_match=shape_match,
    )

    thresholds = {
        "latency_improve_threshold": latency_improve_threshold,
        "latency_regress_threshold": latency_regress_threshold,
        "accuracy_improve_threshold": accuracy_improve_threshold,
        "accuracy_regress_threshold": accuracy_regress_threshold,
        "tradeoff_caution_threshold": tradeoff_caution_threshold,
        "tradeoff_risky_threshold": tradeoff_risky_threshold,
        "tradeoff_severe_threshold": tradeoff_severe_threshold,
    }

    notes = _build_notes(
        comparison_mode=comparison_mode,
        precision_pair=precision_pair,
        shape_match=shape_match,
        system_match=system_match,
        accuracy_present=accuracy_present,
        accuracy_metric_name=accuracy_metric_name,
        accuracy_judgement=accuracy_judgement,
        accuracy_delta_pp=accuracy_delta_pp,
        tradeoff_risk=tradeoff_risk,
        thresholds=thresholds,
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
        "tradeoff_risk": tradeoff_risk,
        "thresholds": thresholds,
        "summary": summary,
        "notes": notes,
    }
