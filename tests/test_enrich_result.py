from __future__ import annotations

import json
import sys
import types

import pytest

from edgebench.compare.comparator import compare_results
from edgebench.result.loader import load_result


def import_enrich_result_module():
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

    from edgebench.commands import enrich_result

    return enrich_result


def write_result(tmp_path, name: str, *, accuracy: dict | None = None) -> str:
    path = tmp_path / name
    path.write_text(
        json.dumps(
            {
                "model": "yolov8n.onnx",
                "engine": "rknn",
                "device": "odroid_m2",
                "precision": "fp16",
                "batch": 1,
                "height": 640,
                "width": 640,
                "mean_ms": 14.2250,
                "p99_ms": 15.3181,
                "timestamp": "20260416-090000",
                "source_report_path": "reports/yolov8n.json",
                "system": {"os": "Linux"},
                "run_config": {"engine": "rknn", "runs": 50, "task": None},
                "accuracy": accuracy or {},
                "extra": {"runtime_artifact_path": "models/yolov8n.rknn"},
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


def test_enrich_result_successfully_attaches_detection_accuracy(tmp_path):
    enrich_result = import_enrich_result_module()
    result_path = write_result(tmp_path, "base.json")
    accuracy_json = write_accuracy_json(
        tmp_path,
        "accuracy.json",
        {
            "task": "detection",
            "sample_count": 500,
            "metrics": {
                "map50": 0.7791,
                "f1_score": 0.8129,
            },
        },
    )

    enrich_result.enrich_result_cmd(result_path=result_path, accuracy_json=accuracy_json, out_dir=str(tmp_path / "results"))

    saved_paths = sorted((tmp_path / "results").glob("*.json"))
    assert len(saved_paths) == 1

    enriched = load_result(str(saved_paths[0]))

    assert enriched["accuracy"]["task"] == "detection"
    assert enriched["accuracy"]["metrics"]["map50"] == 0.7791
    assert enriched["accuracy"]["metrics"]["f1_score"] == 0.8129
    assert enriched["extra"]["enrichment"]["source"] == "enrich_result_cmd"
    assert enriched["extra"]["enrichment"]["accuracy_json_path"] == accuracy_json
    assert enriched["extra"]["enrichment"]["replaces_existing_accuracy"] is False
    assert enriched["timestamp"] != "20260416-090000"


def test_enrich_result_preserves_runtime_fields(tmp_path):
    enrich_result = import_enrich_result_module()
    result_path = write_result(tmp_path, "base.json")
    accuracy_json = write_accuracy_json(
        tmp_path,
        "accuracy.json",
        {
            "task": "detection",
            "metrics": {
                "map50": 0.7791,
            },
        },
    )

    enrich_result.enrich_result_cmd(result_path=result_path, accuracy_json=accuracy_json, out_dir=str(tmp_path / "results"))
    enriched = load_result(str(next((tmp_path / "results").glob("*.json"))))

    assert enriched["mean_ms"] == 14.2250
    assert enriched["p99_ms"] == 15.3181
    assert enriched["engine"] == "rknn"
    assert enriched["device"] == "odroid_m2"
    assert enriched["precision"] == "fp16"
    assert enriched["source_report_path"] == "reports/yolov8n.json"
    assert enriched["run_config"]["engine"] == "rknn"
    assert enriched["extra"]["runtime_artifact_path"] == "models/yolov8n.rknn"


def test_enrich_result_prevents_overwrite_when_disabled(tmp_path):
    enrich_result = import_enrich_result_module()
    result_path = write_result(
        tmp_path,
        "base.json",
        accuracy={
            "task": "classification",
            "metrics": {
                "top1_accuracy": 0.90,
            },
        },
    )
    accuracy_json = write_accuracy_json(
        tmp_path,
        "accuracy.json",
        {
            "task": "detection",
            "metrics": {
                "map50": 0.7791,
            },
        },
    )

    with pytest.raises(sys.modules["typer"].Exit) as exc_info:
        enrich_result.enrich_result_cmd(
            result_path=result_path,
            accuracy_json=accuracy_json,
            out_dir=str(tmp_path / "results"),
            overwrite_accuracy=False,
        )

    assert exc_info.value.exit_code == 1
    assert not (tmp_path / "results").exists()


def test_enrich_result_fails_when_accuracy_payload_is_invalid(tmp_path):
    enrich_result = import_enrich_result_module()
    result_path = write_result(tmp_path, "base.json")
    accuracy_json = write_accuracy_json(
        tmp_path,
        "accuracy.json",
        {
            "task": "detection",
            "metrics": {
                "note": "missing numeric metric",
            },
        },
    )

    with pytest.raises(sys.modules["typer"].BadParameter):
        enrich_result.enrich_result_cmd(result_path=result_path, accuracy_json=accuracy_json, out_dir=str(tmp_path / "results"))


def test_enriched_results_compare_with_detection_map50(tmp_path):
    enrich_result = import_enrich_result_module()
    base_result_path = write_result(tmp_path, "base.json")
    new_result_path = write_result(tmp_path, "new.json")

    base_accuracy_json = write_accuracy_json(
        tmp_path,
        "base_accuracy.json",
        {
            "task": "detection",
            "metrics": {
                "map50": 0.7791,
                "f1_score": 0.8000,
            },
        },
    )
    new_accuracy_json = write_accuracy_json(
        tmp_path,
        "new_accuracy.json",
        {
            "task": "detection",
            "metrics": {
                "map50": 0.7977,
                "f1_score": 0.8129,
            },
        },
    )

    out_dir = tmp_path / "results"
    enrich_result.enrich_result_cmd(result_path=base_result_path, accuracy_json=base_accuracy_json, out_dir=str(out_dir))
    enrich_result.enrich_result_cmd(result_path=new_result_path, accuracy_json=new_accuracy_json, out_dir=str(out_dir))

    saved_paths = sorted(out_dir.glob("*.json"))
    assert len(saved_paths) == 2

    base = load_result(str(saved_paths[0]))
    new = load_result(str(saved_paths[1]))
    result = compare_results(base, new)

    assert result["accuracy"]["task"] == "detection"
    assert result["accuracy"]["metric_name"] == "map50"
    assert result["accuracy"]["present"] is True
    assert result["accuracy"]["metrics"]["map50"]["base"] == 0.7791
    assert result["accuracy"]["metrics"]["map50"]["new"] == 0.7977
