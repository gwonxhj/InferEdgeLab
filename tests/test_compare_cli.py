from __future__ import annotations

import json

from inferedgelab.commands.compare import compare_cmd


def write_result(tmp_path, name: str, *, timestamp: str, precision: str, mean_ms: float) -> str:
    path = tmp_path / name
    path.write_text(
        json.dumps(
            {
                "model": "resnet18",
                "engine": "onnxruntime",
                "device": "cpu",
                "precision": precision,
                "batch": 1,
                "height": 224,
                "width": 224,
                "mean_ms": mean_ms,
                "p99_ms": mean_ms + 2.0,
                "timestamp": timestamp,
                "run_config": {},
                "system": {"os": "Linux", "python": "3.11.0", "machine": "x86_64", "cpu_count_logical": 8},
                "accuracy": {
                    "task": "classification",
                    "sample_count": 100,
                    "metrics": {"top1_accuracy": 0.9},
                },
            }
        ),
        encoding="utf-8",
    )
    return str(path)


def test_compare_cmd_outputs_deployment_decision(tmp_path, capsys):
    base_path = write_result(
        tmp_path,
        "base.json",
        timestamp="2026-04-13T09:00:00Z",
        precision="fp32",
        mean_ms=10.0,
    )
    new_path = write_result(
        tmp_path,
        "new.json",
        timestamp="2026-04-13T10:00:00Z",
        precision="fp32",
        mean_ms=9.0,
    )

    compare_cmd(base_path=base_path, new_path=new_path, markdown_out="", html_out="", with_guard=False)
    out = capsys.readouterr().out

    assert "Deployment Decision" in out
    assert "decision:" in out
