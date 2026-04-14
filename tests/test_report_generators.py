from __future__ import annotations

from edgebench.report.markdown_generator import generate_compare_markdown
from edgebench.report.html_generator import generate_compare_html


def make_compare_result(
    *,
    comparison_mode: str = "same_precision",
    base_precision: str = "fp32",
    new_precision: str = "fp32",
    accuracy_task: str = "classification",
    primary_metric_name: str = "top1_accuracy",
    accuracy_metrics: dict | None = None,
) -> dict:
    if accuracy_metrics is None:
        accuracy_metrics = {
            "top1_accuracy": {
                "base": 0.90,
                "new": 0.92,
                "delta": 0.02,
                "delta_pct": 2.2222,
                "delta_pp": 2.0,
            }
        }

    return {
        "base_id": {
            "model": "base_model.onnx",
            "engine": "onnxruntime",
            "device": "cpu",
            "timestamp": "2026-04-14T00:00:00Z",
            "precision": base_precision,
        },
        "new_id": {
            "model": "new_model.onnx",
            "engine": "onnxruntime",
            "device": "cpu",
            "timestamp": "2026-04-14T01:00:00Z",
            "precision": new_precision,
        },
        "precision": {
            "base": base_precision,
            "new": new_precision,
            "match": comparison_mode == "same_precision",
            "comparison_mode": comparison_mode,
            "pair": f"{base_precision}_vs_{new_precision}",
        },
        "metrics": {
            "mean_ms": {
                "base": 10.0,
                "new": 8.0,
                "delta": -2.0,
                "delta_pct": -20.0,
            },
            "p99_ms": {
                "base": 12.0,
                "new": 10.0,
                "delta": -2.0,
                "delta_pct": -16.6667,
            },
        },
        "accuracy": {
            "present": True,
            "task": accuracy_task,
            "metric_name": primary_metric_name,
            "sample_count": {
                "base": 100,
                "new": 100,
            },
            "metrics": accuracy_metrics,
        },
        "shape": {
            "base": {"batch": 1, "height": 224, "width": 224},
            "new": {"batch": 1, "height": 224, "width": 224},
        },
        "shape_context": {
            "base": {
                "requested_batch": 1,
                "requested_height": 224,
                "requested_width": 224,
                "effective_batch": 1,
                "effective_height": 224,
                "effective_width": 224,
                "primary_input_name": "input",
                "resolved_input_shapes": {"input": [1, 3, 224, 224]},
            },
            "new": {
                "requested_batch": 1,
                "requested_height": 224,
                "requested_width": 224,
                "effective_batch": 1,
                "effective_height": 224,
                "effective_width": 224,
                "primary_input_name": "input",
                "resolved_input_shapes": {"input": [1, 3, 224, 224]},
            },
        },
        "runtime_provenance": {
            "base": {
                "runtime_artifact_path": "/tmp/base.engine",
                "primary_input_name": "input",
                "requested_shape_summary": "b1 / h224 / w224",
                "effective_shape_summary": "b1 / h224 / w224",
            },
            "new": {
                "runtime_artifact_path": "/tmp/new.engine",
                "primary_input_name": "input",
                "requested_shape_summary": "b1 / h224 / w224",
                "effective_shape_summary": "b1 / h224 / w224",
            },
        },
        "system_diff": {
            "os": {"base": "Linux", "new": "Linux"},
            "python": {"base": "3.11.0", "new": "3.11.0"},
            "machine": {"base": "x86_64", "new": "x86_64"},
            "cpu_count_logical": {"base": 8, "new": 8},
        },
        "run_config_diff": {
            "warmup": {"base": 10, "new": 10},
            "runs": {"base": 100, "new": 100},
            "intra_threads": {"base": 1, "new": 1},
            "inter_threads": {"base": 1, "new": 1},
            "mode": {"base": "profile", "new": "profile"},
            "task": {"base": accuracy_task, "new": accuracy_task},
        },
    }


def make_judgement(
    *,
    comparison_mode: str = "same_precision",
    precision_match: bool = True,
    overall: str = "improvement",
    accuracy: str = "improvement",
    tradeoff_risk: str = "not_applicable",
) -> dict:
    return {
        "overall": overall,
        "shape_match": True,
        "system_match": True,
        "precision_match": precision_match,
        "comparison_mode": comparison_mode,
        "precision_pair": "fp32_vs_fp32" if precision_match else "fp16_vs_int8",
        "mean_ms": "improvement",
        "p99_ms": "improvement",
        "accuracy": accuracy,
        "accuracy_present": True,
        "tradeoff_risk": tradeoff_risk,
        "thresholds": {
            "latency_improve_threshold": -3.0,
            "latency_regress_threshold": 3.0,
            "accuracy_improve_threshold": 0.2,
            "accuracy_regress_threshold": -0.2,
            "tradeoff_caution_threshold": -0.3,
            "tradeoff_risky_threshold": -1.0,
            "tradeoff_severe_threshold": -2.0,
        },
        "summary": "Synthetic summary for report generator testing.",
        "notes": [
            "Synthetic note 1",
            "Synthetic note 2",
        ],
    }


def test_generate_compare_markdown_includes_classification_primary_metric_and_summary():
    compare_result = make_compare_result()
    judgement = make_judgement()

    text = generate_compare_markdown(compare_result, judgement)

    assert "# EdgeBench Compare Report" in text
    assert "## Judgement" in text
    assert "- Primary accuracy metric: **`top1_accuracy`**" in text
    assert "- Summary: Synthetic summary for report generator testing." in text
    assert "| top1_accuracy (primary) |" in text
    assert "| runtime_artifact_path | /tmp/base.engine | /tmp/new.engine |" in text


def test_generate_compare_markdown_includes_cross_precision_warning_for_detection():
    compare_result = make_compare_result(
        comparison_mode="cross_precision",
        base_precision="fp16",
        new_precision="int8",
        accuracy_task="detection",
        primary_metric_name="map50",
        accuracy_metrics={
            "map50": {
                "base": 0.7791,
                "new": 0.7977,
                "delta": 0.0186,
                "delta_pct": 2.3874,
                "delta_pp": 1.86,
            },
            "f1_score": {
                "base": 0.8000,
                "new": 0.8129,
                "delta": 0.0129,
                "delta_pct": 1.6125,
                "delta_pp": 1.29,
            },
        },
    )
    judgement = make_judgement(
        comparison_mode="cross_precision",
        precision_match=False,
        overall="tradeoff_faster",
        accuracy="improvement",
        tradeoff_risk="acceptable_tradeoff",
    )

    text = generate_compare_markdown(compare_result, judgement)

    assert "> [!WARNING]" in text
    assert "This is a cross-precision comparison." in text
    assert "- Overall semantics: **trade-off status, not same-condition regression status**" in text
    assert "- Task: **`detection`**" in text
    assert "- Primary metric: **`map50`**" in text
    assert "| map50 (primary) |" in text
    assert "| f1_score |" in text


def test_generate_compare_markdown_orders_primary_accuracy_metric_first():
    compare_result = make_compare_result(
        accuracy_task="detection",
        primary_metric_name="map50",
        accuracy_metrics={
            "f1_score": {
                "base": 0.81,
                "new": 0.82,
                "delta": 0.01,
                "delta_pct": 1.2345,
                "delta_pp": 1.0,
            },
            "map50": {
                "base": 0.77,
                "new": 0.79,
                "delta": 0.02,
                "delta_pct": 2.5974,
                "delta_pp": 2.0,
            },
        },
    )
    judgement = make_judgement()

    text = generate_compare_markdown(compare_result, judgement)

    map50_idx = text.index("| map50 (primary) |")
    f1_idx = text.index("| f1_score |")
    assert map50_idx < f1_idx


def test_generate_compare_html_includes_primary_metric_summary_and_thresholds():
    compare_result = make_compare_result()
    judgement = make_judgement()

    html = generate_compare_html(compare_result, judgement)

    assert "<title>EdgeBench Compare Report</title>" in html
    assert "Primary metric" in html
    assert "top1_accuracy" in html
    assert "Synthetic summary for report generator testing." in html
    assert "latency_improve_threshold" in html
    assert "/tmp/base.engine" in html
    assert "/tmp/new.engine" in html


def test_generate_compare_html_includes_cross_precision_warning_and_detection_metric():
    compare_result = make_compare_result(
        comparison_mode="cross_precision",
        base_precision="fp16",
        new_precision="int8",
        accuracy_task="detection",
        primary_metric_name="map50",
        accuracy_metrics={
            "map50": {
                "base": 0.7791,
                "new": 0.7977,
                "delta": 0.0186,
                "delta_pct": 2.3874,
                "delta_pp": 1.86,
            },
            "f1_score": {
                "base": 0.8000,
                "new": 0.8129,
                "delta": 0.0129,
                "delta_pct": 1.6125,
                "delta_pp": 1.29,
            },
        },
    )
    judgement = make_judgement(
        comparison_mode="cross_precision",
        precision_match=False,
        overall="tradeoff_faster",
        accuracy="improvement",
        tradeoff_risk="acceptable_tradeoff",
    )

    html = generate_compare_html(compare_result, judgement)

    assert "Cross-precision comparison detected." in html
    assert "fp16_vs_int8" in html
    assert "map50" in html
    assert "f1_score" in html
    assert "acceptable_tradeoff" in html


def test_generate_compare_html_includes_notes_list_items():
    compare_result = make_compare_result()
    judgement = make_judgement()

    html = generate_compare_html(compare_result, judgement)

    assert "<li>Synthetic note 1</li>" in html
    assert "<li>Synthetic note 2</li>" in html