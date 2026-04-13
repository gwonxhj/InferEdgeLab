from __future__ import annotations

import json
import sys
import types


def import_check_compare_policy_main():
    if "typer" not in sys.modules:
        typer_stub = types.ModuleType("typer")

        class Exit(Exception):
            def __init__(self, code: int = 0):
                super().__init__(code)
                self.exit_code = code

        class BadParameter(Exception):
            pass

        def option(default=None, *args, **kwargs):
            return default

        typer_stub.Exit = Exit
        typer_stub.BadParameter = BadParameter
        typer_stub.Option = option
        sys.modules["typer"] = typer_stub

    if "rich" not in sys.modules:
        rich_stub = types.ModuleType("rich")
        rich_stub.print = print
        sys.modules["rich"] = rich_stub

    from scripts.check_compare_policy import main

    return main


def write_result(
    tmp_path,
    name: str,
    *,
    timestamp: str,
    precision: str,
    mean_ms: float,
    p99_ms: float,
    accuracy: float | None = None,
    accuracy_task: str = "classification",
    accuracy_metric_name: str = "top1_accuracy",
    extra_accuracy_metrics: dict | None = None,
    model: str = "resnet18",
    engine: str = "onnxruntime",
    device: str = "cpu",
    batch: int = 1,
    height: int = 224,
    width: int = 224,
) -> str:
    data = {
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
        "system": {
            "os": "Linux",
            "python": "3.11.0",
            "machine": "x86_64",
            "cpu_count_logical": 8,
        },
    }
    if accuracy is not None or extra_accuracy_metrics:
        metrics = {}
        if accuracy is not None:
            metrics[accuracy_metric_name] = accuracy
        if extra_accuracy_metrics:
            metrics.update(extra_accuracy_metrics)

        data["accuracy"] = {
            "task": accuracy_task,
            "sample_count": 100,
            "metrics": metrics,
        }

    path = tmp_path / name
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


def test_compare_policy_same_precision_regression_returns_2(tmp_path):
    main = import_check_compare_policy_main()

    write_result(
        tmp_path,
        "base.json",
        timestamp="2026-04-13T09:00:00Z",
        precision="fp32",
        mean_ms=10.0,
        p99_ms=12.0,
        accuracy=0.90,
    )
    write_result(
        tmp_path,
        "new.json",
        timestamp="2026-04-13T10:00:00Z",
        precision="fp32",
        mean_ms=11.0,
        p99_ms=12.2,
        accuracy=0.90,
    )

    result = main(pattern=str(tmp_path / "*.json"), selection_mode="same_precision")

    assert result == 2


def test_compare_policy_cross_precision_severe_tradeoff_returns_2(tmp_path):
    main = import_check_compare_policy_main()

    write_result(
        tmp_path,
        "base.json",
        timestamp="2026-04-13T09:00:00Z",
        precision="fp32",
        mean_ms=10.0,
        p99_ms=12.0,
        accuracy=0.95,
    )
    write_result(
        tmp_path,
        "new.json",
        timestamp="2026-04-13T10:00:00Z",
        precision="fp16",
        mean_ms=8.0,
        p99_ms=10.0,
        accuracy=0.92,
    )

    result = main(pattern=str(tmp_path / "*.json"), selection_mode="cross_precision")

    assert result == 2


def test_compare_policy_allow_missing_pair_writes_skipped_summary_and_returns_0(tmp_path):
    main = import_check_compare_policy_main()

    write_result(
        tmp_path,
        "only.json",
        timestamp="2026-04-13T10:00:00Z",
        precision="fp32",
        mean_ms=10.0,
        p99_ms=12.0,
    )
    summary_out = tmp_path / "summary.md"

    result = main(
        pattern=str(tmp_path / "*.json"),
        selection_mode="same_precision",
        allow_missing_pair=True,
        summary_out=str(summary_out),
    )

    assert result == 0
    summary_text = summary_out.read_text(encoding="utf-8")
    assert "skipped" in summary_text
    assert "Failed to select compare pair" in summary_text


def test_compare_policy_normal_case_returns_0(tmp_path):
    main = import_check_compare_policy_main()

    write_result(
        tmp_path,
        "base.json",
        timestamp="2026-04-13T09:00:00Z",
        precision="fp32",
        mean_ms=10.0,
        p99_ms=12.0,
        accuracy=0.90,
    )
    write_result(
        tmp_path,
        "new.json",
        timestamp="2026-04-13T10:00:00Z",
        precision="fp32",
        mean_ms=9.5,
        p99_ms=11.8,
        accuracy=0.90,
    )

    result = main(pattern=str(tmp_path / "*.json"), selection_mode="same_precision")

    assert result == 0


def test_compare_policy_cross_precision_detection_caution_tradeoff_returns_0(tmp_path):
    main = import_check_compare_policy_main()

    write_result(
        tmp_path,
        "base.json",
        timestamp="2026-04-13T09:00:00Z",
        precision="fp16",
        mean_ms=51.813,
        p99_ms=52.0,
        accuracy=0.7791,
        accuracy_task="detection",
        accuracy_metric_name="map50",
        model="yolov8n",
        engine="rknn",
        device="odroid_m2",
        height=640,
        width=640,
    )
    write_result(
        tmp_path,
        "new.json",
        timestamp="2026-04-13T10:00:00Z",
        precision="int8",
        mean_ms=16.289,
        p99_ms=17.0,
        accuracy=0.7701,
        accuracy_task="detection",
        accuracy_metric_name="map50",
        extra_accuracy_metrics={"f1_score": 0.8129},
        model="yolov8n",
        engine="rknn",
        device="odroid_m2",
        height=640,
        width=640,
    )

    result = main(pattern=str(tmp_path / "*.json"), selection_mode="cross_precision")

    assert result == 0


def test_compare_policy_cross_precision_detection_severe_tradeoff_returns_2(tmp_path):
    main = import_check_compare_policy_main()

    write_result(
        tmp_path,
        "base.json",
        timestamp="2026-04-13T09:00:00Z",
        precision="fp16",
        mean_ms=51.813,
        p99_ms=52.0,
        accuracy=0.7791,
        accuracy_task="detection",
        accuracy_metric_name="map50",
        model="yolov8n",
        engine="rknn",
        device="odroid_m2",
        height=640,
        width=640,
    )
    write_result(
        tmp_path,
        "new.json",
        timestamp="2026-04-13T10:00:00Z",
        precision="int8",
        mean_ms=16.289,
        p99_ms=17.0,
        accuracy=0.7491,
        accuracy_task="detection",
        accuracy_metric_name="map50",
        model="yolov8n",
        engine="rknn",
        device="odroid_m2",
        height=640,
        width=640,
    )

    result = main(pattern=str(tmp_path / "*.json"), selection_mode="cross_precision")

    assert result == 2