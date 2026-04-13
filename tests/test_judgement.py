from __future__ import annotations

from edgebench.compare.judgement import judge_comparison


def make_compare_result(
    *,
    comparison_mode: str = "same_precision",
    mean_delta_pct: float | None = 0.0,
    p99_delta_pct: float | None = 0.0,
    accuracy_present: bool = False,
    accuracy_delta_pp: float | None = None,
    shape_match: bool = True,
    accuracy_task: str = "classification",
    primary_metric_name: str = "top1_accuracy",
    extra_accuracy_metrics: dict | None = None,
) -> dict:
    base_metrics: dict = {}
    new_metrics: dict = {}

    if accuracy_present:
        if accuracy_delta_pp is None:
            base_value = 0.90
            new_value = 0.90
        else:
            base_value = 0.90
            new_value = base_value + (accuracy_delta_pp / 100.0)

        base_metrics[primary_metric_name] = base_value
        new_metrics[primary_metric_name] = new_value

        if extra_accuracy_metrics:
            for metric_name, metric_values in extra_accuracy_metrics.items():
                base_metrics[metric_name] = metric_values.get("base")
                new_metrics[metric_name] = metric_values.get("new")

    return {
        "metrics": {
            "mean_ms": {"delta_pct": mean_delta_pct},
            "p99_ms": {"delta_pct": p99_delta_pct},
        },
        "accuracy": {
            "present": accuracy_present,
            "task": accuracy_task,
            "metric_name": primary_metric_name,
            "sample_count": {"base": 100, "new": 100} if accuracy_present else {"base": None, "new": None},
            "metrics": {
                metric_name: {
                    "base": base_value,
                    "new": new_value,
                    "delta": (new_value - base_value) if accuracy_present else None,
                    "delta_pct": (((new_value - base_value) / base_value) * 100.0)
                    if accuracy_present and base_value not in (None, 0)
                    else None,
                    "delta_pp": accuracy_delta_pp if accuracy_present else None,
                }
                for metric_name, base_value, new_value in (
                    [
                        (
                            primary_metric_name,
                            base_metrics.get(primary_metric_name),
                            new_metrics.get(primary_metric_name),
                        )
                    ]
                    if accuracy_present
                    else []
                )
            }
            | {
                metric_name: {
                    "base": metric_values.get("base"),
                    "new": metric_values.get("new"),
                    "delta": (
                        metric_values.get("new") - metric_values.get("base")
                        if metric_values.get("base") is not None and metric_values.get("new") is not None
                        else None
                    ),
                    "delta_pct": (
                        ((metric_values.get("new") - metric_values.get("base")) / metric_values.get("base")) * 100.0
                        if metric_values.get("base") not in (None, 0) and metric_values.get("new") is not None
                        else None
                    ),
                    "delta_pp": (
                        (metric_values.get("new") - metric_values.get("base")) * 100.0
                        if metric_values.get("base") is not None and metric_values.get("new") is not None
                        else None
                    ),
                }
                for metric_name, metric_values in (extra_accuracy_metrics or {}).items()
            },
        },
        "shape": {
            "base": {"batch": 1, "height": 224, "width": 224},
            "new": {"batch": 1, "height": 224, "width": 224} if shape_match else {"batch": 1, "height": 256, "width": 256},
        },
        "system_diff": {
            "os": {"base": "Linux", "new": "Linux"},
            "python": {"base": "3.11.0", "new": "3.11.0"},
            "machine": {"base": "x86_64", "new": "x86_64"},
            "cpu_count_logical": {"base": 8, "new": 8},
        },
        "precision": {
            "match": comparison_mode == "same_precision",
            "comparison_mode": comparison_mode,
            "pair": "fp32_vs_fp32" if comparison_mode == "same_precision" else "fp32_vs_fp16",
        },
    }


def test_judge_comparison_same_precision_improvement():
    judgement = judge_comparison(
        make_compare_result(
            comparison_mode="same_precision",
            mean_delta_pct=-10.0,
            p99_delta_pct=-4.0,
        )
    )

    assert judgement["overall"] == "improvement"
    assert judgement["mean_ms"] == "improvement"
    assert judgement["p99_ms"] == "improvement"


def test_judge_comparison_same_precision_regression():
    judgement = judge_comparison(
        make_compare_result(
            comparison_mode="same_precision",
            mean_delta_pct=5.0,
            p99_delta_pct=1.0,
        )
    )

    assert judgement["overall"] == "regression"
    assert judgement["mean_ms"] == "regression"


def test_judge_comparison_shape_mismatch_marks_overall_mismatch():
    judgement = judge_comparison(
        make_compare_result(
            comparison_mode="same_precision",
            mean_delta_pct=-10.0,
            p99_delta_pct=-10.0,
            shape_match=False,
        )
    )

    assert judgement["shape_match"] is False
    assert judgement["overall"] == "mismatch"
    assert "mismatch" in judgement["summary"].lower()


def test_judge_comparison_cross_precision_faster_without_accuracy_is_unknown_risk():
    judgement = judge_comparison(
        make_compare_result(
            comparison_mode="cross_precision",
            mean_delta_pct=-15.0,
            p99_delta_pct=-3.5,
            accuracy_present=False,
            accuracy_delta_pp=None,
        )
    )

    assert judgement["overall"] == "tradeoff_faster"
    assert judgement["tradeoff_risk"] == "unknown_risk"


def test_judge_comparison_cross_precision_severe_accuracy_drop_is_severe_tradeoff():
    judgement = judge_comparison(
        make_compare_result(
            comparison_mode="cross_precision",
            mean_delta_pct=-20.0,
            p99_delta_pct=-5.0,
            accuracy_present=True,
            accuracy_delta_pp=-3.0,
        )
    )

    assert judgement["overall"] == "tradeoff_faster"
    assert judgement["accuracy"] == "regression"
    assert judgement["tradeoff_risk"] == "severe_tradeoff"


def test_judge_comparison_cross_precision_detection_caution_tradeoff():
    judgement = judge_comparison(
        make_compare_result(
            comparison_mode="cross_precision",
            mean_delta_pct=-20.0,
            p99_delta_pct=-5.0,
            accuracy_present=True,
            accuracy_delta_pp=-0.90,
            accuracy_task="detection",
            primary_metric_name="map50",
        )
    )

    assert judgement["overall"] == "tradeoff_faster"
    assert judgement["accuracy"] == "regression"
    assert judgement["tradeoff_risk"] == "caution_tradeoff"
    assert "map50" in judgement["summary"]


def test_judge_comparison_cross_precision_detection_improvement_without_risk():
    judgement = judge_comparison(
        make_compare_result(
            comparison_mode="cross_precision",
            mean_delta_pct=-30.0,
            p99_delta_pct=None,
            accuracy_present=True,
            accuracy_delta_pp=1.86,
            accuracy_task="detection",
            primary_metric_name="map50",
            extra_accuracy_metrics={
                "f1_score": {"base": None, "new": 0.8129},
            },
        )
    )

    assert judgement["accuracy"] == "improvement"
    assert judgement["tradeoff_risk"] == "no_clear_tradeoff"
    assert "map50" in " ".join(judgement["notes"])