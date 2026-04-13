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
) -> dict:
    return {
        "metrics": {
            "mean_ms": {"delta_pct": mean_delta_pct},
            "p99_ms": {"delta_pct": p99_delta_pct},
        },
        "accuracy": {
            "present": accuracy_present,
            "metrics": {
                "top1_accuracy": {
                    "delta_pp": accuracy_delta_pp,
                }
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
