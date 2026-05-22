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


def test_compare_cmd_outputs_edgeenv_regression_evidence(tmp_path, capsys):
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
    edgeenv_path = tmp_path / "edgeenv_regression.json"
    edgeenv_path.write_text(
        json.dumps(
            {
                "regression_detected": True,
                "regression_type": "latency",
                "severity": "high",
                "comparable": True,
                "mode": "same-condition",
                "recommendation": "review_required",
                "evidence": {"mean_delta_pct": 18.4, "p99_delta_pct": 32.1},
                "runtime_telemetry_context": {
                    "role": "supplemental_runtime_telemetry_context",
                    "source": "result_artifacts+runtime_telemetry_history",
                    "baseline": {
                        "run_id": "baseline",
                        "result_telemetry_present": True,
                        "history_entry_present": True,
                        "execution_sequence_id": 1,
                        "history_execution_sequence_id": 1,
                        "telemetry_source": "synthetic_local_fixture",
                    },
                    "candidate": {
                        "run_id": "candidate",
                        "result_telemetry_present": True,
                        "history_entry_present": True,
                        "execution_sequence_id": 2,
                        "history_execution_sequence_id": 2,
                        "telemetry_source": "synthetic_local_fixture",
                    },
                    "history": {
                        "schema_version": "edgeenv.runtime-telemetry-history.v1",
                        "summary": {
                            "registered_runs": 2,
                            "telemetry_runs": 2,
                            "missing_telemetry_runs": 0,
                        },
                    },
                    "evidence_gaps": [],
                },
            }
        ),
        encoding="utf-8",
    )

    compare_cmd(
        base_path=base_path,
        new_path=new_path,
        markdown_out="",
        html_out="",
        with_guard=False,
        edgeenv_regression=str(edgeenv_path),
    )
    out = capsys.readouterr().out

    assert "Runtime Regression Evidence" in out
    assert "regression_detected: True" in out
    assert "Runtime Telemetry Context" in out
    assert "candidate: run_id=candidate" in out
    assert "history_sequence=2" in out
    assert "evidence_gaps: none" in out
    assert "decision: review_required" in out
