from __future__ import annotations

import json

from inferedgelab.result.loader import load_result, load_results_grouped_by_compare_key


def test_load_result_normalizes_legacy_fields_and_defaults(tmp_path):
    path = tmp_path / "result.json"
    path.write_text(
        json.dumps(
            {
                "model": "resnet18",
                "engine": "onnxruntime",
                "device": "cpu",
                "batch": 4,
                "height": 224,
                "width": 224,
                "mean_ms": 10.0,
                "p99_ms": 12.0,
                "timestamp": "2026-04-13T10:00:00Z",
                "extra": {
                    "requested_batch": 8,
                    "requested_height": 256,
                    "requested_width": 256,
                    "load_kwargs": {
                        "engine_path": "/tmp/model.engine",
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    result = load_result(str(path))

    assert result["legacy_result"] is True
    assert result["precision"] == "fp32"
    assert result["system"] == {}
    assert result["run_config"]["requested_batch"] == 8
    assert result["run_config"]["requested_height"] == 256
    assert result["run_config"]["requested_width"] == 256
    assert result["accuracy"] == {}
    assert result["extra"]["effective_batch"] == 4
    assert result["extra"]["effective_height"] == 224
    assert result["extra"]["effective_width"] == 224
    assert result["extra"]["runtime_artifact_path"] == "/tmp/model.engine"


def test_load_results_grouped_by_compare_key_filters_runtime_results(tmp_path):
    runtime_a = tmp_path / "runtime-a.json"
    runtime_a.write_text(
        json.dumps(
            {
                "runtime_role": "runtime-result",
                "compare_key": "toy224__b1__h224w224__fp32",
                "backend_key": "onnxruntime__cpu",
                "mean_ms": 1.4,
            }
        ),
        encoding="utf-8",
    )
    runtime_b = tmp_path / "runtime-b.json"
    runtime_b.write_text(
        json.dumps(
            {
                "runtime_role": "runtime-result",
                "compare_key": "toy224__b1__h224w224__fp32",
                "backend_key": "tensorrt__jetson",
                "mean_ms": 5.2,
            }
        ),
        encoding="utf-8",
    )
    non_runtime = tmp_path / "structured-result.json"
    non_runtime.write_text(json.dumps({"compare_key": "ignored", "mean_ms": 9.9}), encoding="utf-8")

    grouped = load_results_grouped_by_compare_key(str(tmp_path))

    assert list(grouped) == ["toy224__b1__h224w224__fp32"]
    assert [item["backend_key"] for item in grouped["toy224__b1__h224w224__fp32"]] == [
        "onnxruntime__cpu",
        "tensorrt__jetson",
    ]
    assert grouped["toy224__b1__h224w224__fp32"][0]["_source_path"] == str(runtime_a)
