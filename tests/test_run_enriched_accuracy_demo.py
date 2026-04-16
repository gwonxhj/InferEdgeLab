from __future__ import annotations

import importlib.util
import json
import sys
import types

import pytest


def import_run_enriched_accuracy_demo_module():
    if "typer" not in sys.modules:
        typer_stub = types.ModuleType("typer")

        class Exit(Exception):
            def __init__(self, code: int = 0):
                super().__init__(code)
                self.exit_code = code

        class BadParameter(Exception):
            pass

        def argument(default=None, *args, **kwargs):
            return default

        def option(default=None, *args, **kwargs):
            return default

        typer_stub.Exit = Exit
        typer_stub.BadParameter = BadParameter
        typer_stub.Argument = argument
        typer_stub.Option = option
        sys.modules["typer"] = typer_stub

    if "rich" not in sys.modules:
        rich_stub = types.ModuleType("rich")
        rich_stub.print = print
        sys.modules["rich"] = rich_stub

    module_path = importlib.util.spec_from_file_location(
        "test_run_enriched_accuracy_demo_module",
        str(
            (
                __import__("pathlib").Path(__file__).resolve().parents[1]
                / "scripts"
                / "run_enriched_accuracy_demo.py"
            )
        ),
    )
    assert module_path is not None
    assert module_path.loader is not None
    module = importlib.util.module_from_spec(module_path)
    module_path.loader.exec_module(module)
    return module


def write_result(tmp_path, name: str, *, precision: str, mean_ms: float, p99_ms: float) -> str:
    path = tmp_path / name
    path.write_text(
        json.dumps(
            {
                "model": "yolov8n.onnx",
                "engine": "rknn",
                "device": "npu",
                "precision": precision,
                "batch": 1,
                "height": 640,
                "width": 640,
                "mean_ms": mean_ms,
                "p99_ms": p99_ms,
                "timestamp": "20260416-100000" if precision == "fp16" else "20260416-101000",
                "source_report_path": f"reports/{precision}.json",
                "system": {"os": "Linux"},
                "run_config": {"engine": "rknn", "runs": 5},
                "accuracy": {},
                "extra": {"runtime_artifact_path": f"models/{precision}.rknn"},
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return str(path)


def write_accuracy_json(tmp_path, name: str, map50: float, f1_score: float) -> str:
    path = tmp_path / name
    path.write_text(
        json.dumps(
            {
                "task": "detection",
                "metrics": {
                    "map50": map50,
                    "f1_score": f1_score,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return str(path)


def test_run_enriched_accuracy_demo_creates_two_enriched_results_and_expected_judgement(tmp_path):
    demo = import_run_enriched_accuracy_demo_module()
    base_result = write_result(tmp_path, "base.json", precision="fp16", mean_ms=71.8846, p99_ms=73.7026)
    new_result = write_result(tmp_path, "new.json", precision="int8", mean_ms=35.0657, p99_ms=35.6140)
    base_accuracy = write_accuracy_json(tmp_path, "base_accuracy.json", map50=0.7791, f1_score=0.8000)
    new_accuracy = write_accuracy_json(tmp_path, "new_accuracy.json", map50=0.7977, f1_score=0.8129)

    result = demo.run_enriched_accuracy_demo(
        base_result=base_result,
        base_accuracy_json=base_accuracy,
        new_result=new_result,
        new_accuracy_json=new_accuracy,
        out_dir=str(tmp_path / "results_enriched"),
    )

    assert result["saved_base_path"]
    assert result["saved_new_path"]
    assert len(list((tmp_path / "results_enriched").glob("*.json"))) == 2
    assert result["compare_result"]["accuracy"]["metric_name"] == "map50"
    assert result["judgement"]["overall"] == "tradeoff_faster"
    assert result["judgement"]["tradeoff_risk"] == "acceptable_tradeoff"


def test_run_enriched_accuracy_demo_compare_result_uses_detection_map50_primary_metric(tmp_path):
    demo = import_run_enriched_accuracy_demo_module()
    base_result = write_result(tmp_path, "base.json", precision="fp16", mean_ms=71.8846, p99_ms=73.7026)
    new_result = write_result(tmp_path, "new.json", precision="int8", mean_ms=35.0657, p99_ms=35.6140)
    base_accuracy = write_accuracy_json(tmp_path, "base_accuracy.json", map50=0.7791, f1_score=0.8000)
    new_accuracy = write_accuracy_json(tmp_path, "new_accuracy.json", map50=0.7977, f1_score=0.8129)

    result = demo.run_enriched_accuracy_demo(
        base_result=base_result,
        base_accuracy_json=base_accuracy,
        new_result=new_result,
        new_accuracy_json=new_accuracy,
        out_dir=str(tmp_path / "results_enriched"),
    )

    assert result["compare_result"]["accuracy"]["task"] == "detection"
    assert result["compare_result"]["accuracy"]["metric_name"] == "map50"


def test_main_returns_1_when_expectation_mismatches(tmp_path, monkeypatch):
    demo = import_run_enriched_accuracy_demo_module()
    base_result = write_result(tmp_path, "base.json", precision="fp16", mean_ms=71.8846, p99_ms=73.7026)
    new_result = write_result(tmp_path, "new.json", precision="int8", mean_ms=35.0657, p99_ms=35.6140)
    base_accuracy = write_accuracy_json(tmp_path, "base_accuracy.json", map50=0.7791, f1_score=0.8000)
    new_accuracy = write_accuracy_json(tmp_path, "new_accuracy.json", map50=0.7977, f1_score=0.8129)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_enriched_accuracy_demo.py",
            "--base-result",
            base_result,
            "--base-accuracy-json",
            base_accuracy,
            "--new-result",
            new_result,
            "--new-accuracy-json",
            new_accuracy,
            "--out-dir",
            str(tmp_path / "results_enriched"),
            "--expect-overall",
            "neutral",
        ],
    )

    assert demo.main() == 1
