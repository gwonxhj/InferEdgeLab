from __future__ import annotations

import pytest

from inferedgelab.compare.comparator import compare_group, compare_results


def make_result(
    *,
    model: str = "resnet18.onnx",
    engine: str = "onnxruntime",
    device: str = "cpu",
    precision: str = "fp32",
    batch: int = 1,
    height: int = 224,
    width: int = 224,
    mean_ms: float | None = 10.0,
    p99_ms: float | None = 12.0,
    accuracy: dict | None = None,
    system: dict | None = None,
    run_config: dict | None = None,
    extra: dict | None = None,
    timestamp: str = "2026-04-14T00:00:00Z",
) -> dict:
    return {
        "model": model,
        "engine": engine,
        "device": device,
        "precision": precision,
        "batch": batch,
        "height": height,
        "width": width,
        "mean_ms": mean_ms,
        "p99_ms": p99_ms,
        "timestamp": timestamp,
        "accuracy": accuracy or {},
        "system": system or {},
        "run_config": run_config or {},
        "extra": extra or {},
    }


def test_compare_results_classification_selects_top1_accuracy_as_primary_metric():
    base = make_result(
        accuracy={
            "task": "classification",
            "sample_count": 100,
            "metrics": {
                "top1_accuracy": 0.90,
            },
        }
    )
    new = make_result(
        timestamp="2026-04-14T01:00:00Z",
        accuracy={
            "task": "classification",
            "sample_count": 100,
            "metrics": {
                "top1_accuracy": 0.92,
            },
        },
    )

    result = compare_results(base, new)

    assert result["accuracy"]["task"] == "classification"
    assert result["accuracy"]["metric_name"] == "top1_accuracy"
    assert result["accuracy"]["present"] is True
    assert round(result["accuracy"]["metrics"]["top1_accuracy"]["delta"], 4) == 0.02
    assert round(result["accuracy"]["metrics"]["top1_accuracy"]["delta_pp"], 4) == 2.0


def test_compare_results_detection_selects_map50_as_primary_metric():
    base = make_result(
        model="yolov8n",
        engine="rknn",
        device="odroid_m2",
        precision="fp16",
        height=640,
        width=640,
        accuracy={
            "task": "detection",
            "metrics": {
                "map50": 0.7791,
                "f1_score": 0.8000,
            },
        },
    )
    new = make_result(
        model="yolov8n",
        engine="rknn",
        device="odroid_m2",
        precision="int8",
        height=640,
        width=640,
        timestamp="2026-04-14T01:00:00Z",
        accuracy={
            "task": "detection",
            "metrics": {
                "map50": 0.7977,
                "f1_score": 0.8129,
            },
        },
    )

    result = compare_results(base, new)

    assert result["accuracy"]["task"] == "detection"
    assert result["accuracy"]["metric_name"] == "map50"
    assert result["accuracy"]["present"] is True
    assert result["accuracy"]["metrics"]["map50"]["base"] == 0.7791
    assert result["accuracy"]["metrics"]["map50"]["new"] == 0.7977
    assert round(result["accuracy"]["metrics"]["map50"]["delta"], 4) == 0.0186
    assert round(result["accuracy"]["metrics"]["map50"]["delta_pp"], 2) == 1.86


def test_compare_results_falls_back_to_first_numeric_metric_when_task_specific_metric_missing():
    base = make_result(
        accuracy={
            "task": "detection",
            "metrics": {
                "custom_score": 0.50,
            },
        }
    )
    new = make_result(
        timestamp="2026-04-14T01:00:00Z",
        accuracy={
            "task": "detection",
            "metrics": {
                "custom_score": 0.55,
            },
        },
    )

    result = compare_results(base, new)

    assert result["accuracy"]["metric_name"] == "custom_score"
    assert round(result["accuracy"]["metrics"]["custom_score"]["delta"], 4) == 0.05
    assert round(result["accuracy"]["metrics"]["custom_score"]["delta_pp"], 4) == 5.0


def test_compare_results_sets_cross_precision_mode_when_precision_differs():
    base = make_result(precision="fp16")
    new = make_result(precision="int8", timestamp="2026-04-14T01:00:00Z")

    result = compare_results(base, new)

    assert result["precision"]["match"] is False
    assert result["precision"]["comparison_mode"] == "cross_precision"
    assert result["precision"]["pair"] == "fp16_vs_int8"


def test_compare_results_sets_same_precision_mode_when_precision_matches():
    base = make_result(precision="fp32")
    new = make_result(precision="fp32", timestamp="2026-04-14T01:00:00Z")

    result = compare_results(base, new)

    assert result["precision"]["match"] is True
    assert result["precision"]["comparison_mode"] == "same_precision"
    assert result["precision"]["pair"] == "fp32_vs_fp32"


def test_compare_results_builds_runtime_provenance_from_extra_and_load_kwargs():
    base = make_result(
        run_config={
            "requested_batch": 1,
            "requested_height": 224,
            "requested_width": 224,
        },
        extra={
            "runtime_artifact_path": "/tmp/base.engine",
            "primary_input_name": "input",
            "effective_batch": 1,
            "effective_height": 224,
            "effective_width": 224,
        },
    )
    new = make_result(
        timestamp="2026-04-14T01:00:00Z",
        run_config={
            "requested_batch": 1,
            "requested_height": 320,
            "requested_width": 320,
        },
        extra={
            "load_kwargs": {
                "engine_path": "/tmp/new.engine",
            },
            "effective_batch": 1,
            "effective_height": 320,
            "effective_width": 320,
        },
        height=320,
        width=320,
    )

    result = compare_results(base, new)

    assert result["runtime_provenance"]["base"]["runtime_artifact_path"] == "/tmp/base.engine"
    assert result["runtime_provenance"]["new"]["runtime_artifact_path"] == "/tmp/new.engine"
    assert result["runtime_provenance"]["base"]["requested_shape_summary"] == "b1 / h224 / w224"
    assert result["runtime_provenance"]["new"]["requested_shape_summary"] == "b1 / h320 / w320"
    assert result["runtime_provenance"]["new"]["effective_shape_summary"] == "b1 / h320 / w320"


def test_compare_results_uses_batch_height_width_when_requested_values_are_missing():
    base = make_result(batch=1, height=224, width=224)
    new = make_result(
        batch=2,
        height=256,
        width=256,
        timestamp="2026-04-14T01:00:00Z",
    )

    result = compare_results(base, new)

    assert result["shape_context"]["base"]["requested_batch"] == 1
    assert result["shape_context"]["base"]["requested_height"] == 224
    assert result["shape_context"]["base"]["requested_width"] == 224
    assert result["shape_context"]["new"]["requested_batch"] == 2
    assert result["shape_context"]["new"]["requested_height"] == 256
    assert result["shape_context"]["new"]["requested_width"] == 256


def test_compare_results_marks_accuracy_absent_when_no_numeric_metrics_exist():
    base = make_result(
        accuracy={
            "task": "detection",
            "metrics": {
                "note": "n/a",
            },
        }
    )
    new = make_result(
        timestamp="2026-04-14T01:00:00Z",
        accuracy={
            "task": "detection",
            "metrics": {
                "note": "still n/a",
            },
        },
    )

    result = compare_results(base, new)

    assert result["accuracy"]["present"] is False
    assert result["accuracy"]["metrics"] == {}
    assert result["accuracy"]["metric_name"] == "map50"


def test_compare_results_handles_zero_base_for_pct_delta_as_none():
    base = make_result(mean_ms=0.0, p99_ms=0.0)
    new = make_result(
        mean_ms=5.0,
        p99_ms=7.0,
        timestamp="2026-04-14T01:00:00Z",
    )

    result = compare_results(base, new)

    assert result["metrics"]["mean_ms"]["delta"] == 5.0
    assert result["metrics"]["mean_ms"]["delta_pct"] is None
    assert result["metrics"]["p99_ms"]["delta"] == 7.0
    assert result["metrics"]["p99_ms"]["delta_pct"] is None


def test_compare_group_selects_fastest_backend_and_speedup():
    result = compare_group(
        [
            {
                "runtime_role": "runtime-result",
                "compare_key": "toy224__b1__h224w224__fp32",
                "backend_key": "onnxruntime__cpu",
                "mean_ms": 1.4,
            },
            {
                "runtime_role": "runtime-result",
                "compare_key": "toy224__b1__h224w224__fp32",
                "backend_key": "tensorrt__jetson",
                "mean_ms": 5.2,
            },
        ]
    )

    assert result is not None
    assert result["compare_key"] == "toy224__b1__h224w224__fp32"
    assert result["backends"] == ["onnxruntime__cpu", "tensorrt__jetson"]
    assert result["fastest"] == "onnxruntime__cpu"
    assert result["slowest"] == "tensorrt__jetson"
    assert result["speedup"] == pytest.approx(3.714285714)
    assert result["summary"] == "TensorRT is 3.7x slower than ONNX Runtime"


def test_compare_group_requires_two_backends():
    result = compare_group(
        [
            {
                "runtime_role": "runtime-result",
                "compare_key": "toy224__b1__h224w224__fp32",
                "backend_key": "onnxruntime__cpu",
                "mean_ms": 1.4,
            }
        ]
    )

    assert result is None
