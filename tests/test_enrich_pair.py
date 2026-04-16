from __future__ import annotations

import json
import sys
import types

import pytest

from edgebench.compare.comparator import compare_results
from edgebench.result.loader import load_result


def import_enrich_pair_module():
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

    from edgebench.commands import enrich_pair

    return enrich_pair


def write_result(tmp_path, name: str, *, precision: str, accuracy: dict | None = None) -> str:
    path = tmp_path / name
    path.write_text(
        json.dumps(
            {
                "model": "yolov8n.onnx",
                "engine": "rknn",
                "device": "odroid_m2",
                "precision": precision,
                "batch": 1,
                "height": 640,
                "width": 640,
                "mean_ms": 14.2250 if precision == "fp16" else 14.1221,
                "p99_ms": 15.3181 if precision == "fp16" else 14.9191,
                "timestamp": "20260416-090000" if precision == "fp16" else "20260416-091000",
                "source_report_path": f"reports/{precision}.json",
                "system": {"os": "Linux"},
                "run_config": {"engine": "rknn", "runs": 50, "task": None},
                "accuracy": accuracy or {},
                "extra": {"runtime_artifact_path": f"models/{precision}.rknn"},
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return str(path)


def write_accuracy_json(tmp_path, name: str, payload: dict) -> str:
    path = tmp_path / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


def test_enrich_pair_creates_two_enriched_detection_results(tmp_path):
    enrich_pair = import_enrich_pair_module()
    base_result = write_result(tmp_path, "base.json", precision="fp16")
    new_result = write_result(tmp_path, "new.json", precision="int8")
    base_accuracy_json = write_accuracy_json(
        tmp_path,
        "base_accuracy.json",
        {"task": "detection", "metrics": {"map50": 0.7791, "f1_score": 0.8000}},
    )
    new_accuracy_json = write_accuracy_json(
        tmp_path,
        "new_accuracy.json",
        {"task": "detection", "metrics": {"map50": 0.7977, "f1_score": 0.8129}},
    )

    enrich_pair.enrich_pair_cmd(
        base_result=base_result,
        base_accuracy_json=base_accuracy_json,
        new_result=new_result,
        new_accuracy_json=new_accuracy_json,
        out_dir=str(tmp_path / "results"),
    )

    saved_paths = sorted((tmp_path / "results").glob("*.json"))
    assert len(saved_paths) == 2


def test_enrich_pair_fails_when_overwrite_is_disabled_and_accuracy_exists(tmp_path):
    enrich_pair = import_enrich_pair_module()
    base_result = write_result(
        tmp_path,
        "base.json",
        precision="fp16",
        accuracy={"task": "detection", "metrics": {"map50": 0.7700}},
    )
    new_result = write_result(tmp_path, "new.json", precision="int8")
    base_accuracy_json = write_accuracy_json(
        tmp_path,
        "base_accuracy.json",
        {"task": "detection", "metrics": {"map50": 0.7791}},
    )
    new_accuracy_json = write_accuracy_json(
        tmp_path,
        "new_accuracy.json",
        {"task": "detection", "metrics": {"map50": 0.7977}},
    )

    with pytest.raises(sys.modules["typer"].Exit) as exc_info:
        enrich_pair.enrich_pair_cmd(
            base_result=base_result,
            base_accuracy_json=base_accuracy_json,
            new_result=new_result,
            new_accuracy_json=new_accuracy_json,
            out_dir=str(tmp_path / "results"),
            overwrite_accuracy=False,
        )

    assert exc_info.value.exit_code == 1


def test_enrich_pair_saved_results_preserve_accuracy_task_and_metrics(tmp_path):
    enrich_pair = import_enrich_pair_module()
    base_result = write_result(tmp_path, "base.json", precision="fp16")
    new_result = write_result(tmp_path, "new.json", precision="int8")
    base_accuracy_json = write_accuracy_json(
        tmp_path,
        "base_accuracy.json",
        {"task": "detection", "metrics": {"map50": 0.7791, "f1_score": 0.8000}},
    )
    new_accuracy_json = write_accuracy_json(
        tmp_path,
        "new_accuracy.json",
        {"task": "detection", "metrics": {"map50": 0.7977, "f1_score": 0.8129}},
    )

    out_dir = tmp_path / "results"
    enrich_pair.enrich_pair_cmd(
        base_result=base_result,
        base_accuracy_json=base_accuracy_json,
        new_result=new_result,
        new_accuracy_json=new_accuracy_json,
        out_dir=str(out_dir),
    )

    saved_paths = sorted(out_dir.glob("*.json"))
    base = load_result(str(saved_paths[0]))
    new = load_result(str(saved_paths[1]))

    assert base["accuracy"]["task"] == "detection"
    assert new["accuracy"]["task"] == "detection"
    assert base["accuracy"]["metrics"]["map50"] == 0.7791
    assert new["accuracy"]["metrics"]["map50"] == 0.7977
    assert base["accuracy"]["metrics"]["f1_score"] == 0.8000
    assert new["accuracy"]["metrics"]["f1_score"] == 0.8129


def test_enriched_pair_compare_recognizes_detection_map50_as_primary_metric(tmp_path):
    enrich_pair = import_enrich_pair_module()
    base_result = write_result(tmp_path, "base.json", precision="fp16")
    new_result = write_result(tmp_path, "new.json", precision="int8")
    base_accuracy_json = write_accuracy_json(
        tmp_path,
        "base_accuracy.json",
        {"task": "detection", "metrics": {"map50": 0.7791, "f1_score": 0.8000}},
    )
    new_accuracy_json = write_accuracy_json(
        tmp_path,
        "new_accuracy.json",
        {"task": "detection", "metrics": {"map50": 0.7977, "f1_score": 0.8129}},
    )

    out_dir = tmp_path / "results"
    enrich_pair.enrich_pair_cmd(
        base_result=base_result,
        base_accuracy_json=base_accuracy_json,
        new_result=new_result,
        new_accuracy_json=new_accuracy_json,
        out_dir=str(out_dir),
    )

    saved_paths = sorted(out_dir.glob("*.json"))
    base = load_result(str(saved_paths[0]))
    new = load_result(str(saved_paths[1]))
    result = compare_results(base, new)

    assert result["accuracy"]["task"] == "detection"
    assert result["accuracy"]["metric_name"] == "map50"
    assert result["accuracy"]["present"] is True
    assert result["accuracy"]["metrics"]["map50"]["base"] == 0.7791
    assert result["accuracy"]["metrics"]["map50"]["new"] == 0.7977
