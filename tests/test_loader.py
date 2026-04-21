from __future__ import annotations

import json

from inferedgelab.result.loader import load_result


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
