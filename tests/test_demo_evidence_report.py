from __future__ import annotations

import json

import pytest

from inferedgelab.commands.demo_evidence import demo_evidence_summary_cmd
from inferedgelab.commands.demo_evidence import export_demo_evidence_cmd
from inferedgelab.commands.demo_evidence import portfolio_demo_check_cmd
from inferedgelab.services.demo_evidence_report import (
    IN_MEMORY_NOTE,
    build_demo_evidence_markdown,
    build_demo_evidence_summary,
    build_portfolio_demo_check,
)


def test_demo_evidence_summary_reproduces_portfolio_metrics():
    summary = build_demo_evidence_summary()

    runtime = summary["runtime_evidence"]
    comparison = summary["comparison"]
    evaluation = summary["evaluation_report"]

    assert summary["schema_version"] == "inferedgelab-demo-evidence-summary-v1"
    assert summary["in_memory_note"] == IN_MEMORY_NOTE
    assert runtime["onnxruntime_cpu"]["mean_ms"] == pytest.approx(45.4299)
    assert runtime["onnxruntime_cpu"]["p99_ms"] == pytest.approx(49.2128)
    assert runtime["onnxruntime_cpu"]["fps"] == pytest.approx(22.0119)
    assert runtime["tensorrt_jetson_fp16_25w"]["mean_ms"] == pytest.approx(10.066401)
    assert runtime["tensorrt_jetson_fp16_25w"]["p99_ms"] == pytest.approx(15.548438)
    assert runtime["tensorrt_jetson_fp16_25w"]["fps"] == pytest.approx(99.340373)
    assert runtime["tensorrt_jetson_fp16_15w"]["mean_ms"] == pytest.approx(10.799106)
    assert comparison["speedup"] == pytest.approx(4.512994, rel=1e-5)
    assert comparison["lab_overall"] == "tradeoff_faster"
    assert summary["deployment_decision"]["decision"] == "review_required"
    assert evaluation["metric_backend"] == "simplified"
    assert evaluation["ground_truth_boxes"] == 89
    assert evaluation["map50"] == pytest.approx(0.1409784036)
    assert evaluation["structural_status"] == "passed"
    assert {case["problem_case"] for case in summary["problem_cases"]} == {
        "annotation_missing",
        "invalid_detection_structure",
        "contract_shape_mismatch",
        "latency_regression",
    }
    assert {case["guard_verdict"] for case in summary["aiguard_cases"]} == {
        "pass",
        "blocked",
        "review_required",
    }


def test_demo_evidence_markdown_contains_report_sections():
    markdown = build_demo_evidence_markdown()

    assert "# InferEdge Local Studio Demo Evidence Report" in markdown
    assert IN_MEMORY_NOTE in markdown
    assert "TensorRT Jetson FP16 25W candidate" in markdown
    assert "ONNX Runtime CPU baseline" in markdown
    assert "4.513x faster" in markdown
    assert "YOLOv8 COCO Subset Evaluation" in markdown
    assert "latency_regression" in markdown
    assert "AIGuard Portfolio Cases" in markdown
    assert "Jetson Power Mode Evidence" in markdown
    assert "not a production SaaS dashboard" in markdown


def test_demo_evidence_summary_command_outputs_json(capsys):
    demo_evidence_summary_cmd(format="json", output="")
    out = capsys.readouterr().out
    summary = json.loads(out)

    assert summary["schema_version"] == "inferedgelab-demo-evidence-summary-v1"
    assert summary["comparison"]["speedup"] == pytest.approx(4.512994, rel=1e-5)
    assert summary["in_memory_note"] == IN_MEMORY_NOTE


def test_export_demo_evidence_command_writes_markdown(tmp_path, capsys):
    out_path = tmp_path / "studio_demo_evidence.md"

    export_demo_evidence_cmd(output=str(out_path))

    output = capsys.readouterr().out
    markdown = out_path.read_text(encoding="utf-8")
    assert "Saved" in output
    assert "# InferEdge Local Studio Demo Evidence Report" in markdown
    assert IN_MEMORY_NOTE in markdown


def test_portfolio_demo_check_passes_for_committed_evidence():
    report = build_portfolio_demo_check()

    assert report["schema_version"] == "inferedgelab-portfolio-demo-check-v1"
    assert report["status"] == "pass"
    assert report["failed_count"] == 0
    assert report["core_metrics"]["tensorrt_jetson_fp16_25w_mean_ms"] == pytest.approx(10.066401)
    assert report["core_metrics"]["onnxruntime_cpu_mean_ms"] == pytest.approx(45.4299)
    assert report["core_metrics"]["speedup"] == pytest.approx(4.513023, rel=1e-5)
    assert any(check["name"] == "aiguard:portfolio_case_count" for check in report["checks"])
    assert any(check["name"] == "problem_cases:portfolio_bundle" for check in report["checks"])


def test_portfolio_demo_check_command_outputs_json(capsys):
    portfolio_demo_check_cmd(format="json", repo_root=".")
    out = capsys.readouterr().out
    report = json.loads(out)

    assert report["schema_version"] == "inferedgelab-portfolio-demo-check-v1"
    assert report["status"] == "pass"
    assert report["failed_count"] == 0
