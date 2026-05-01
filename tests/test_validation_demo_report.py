from __future__ import annotations

import json
from pathlib import Path


def test_yolov8_coco_subset_demo_report_contains_evaluated_accuracy():
    repo_root = Path(__file__).resolve().parents[1]
    report_path = repo_root / "examples" / "validation_demo" / "subset" / "yolov8_coco_subset_evaluation.json"
    annotation_path = repo_root / "examples" / "validation_demo" / "subset" / "yolov8_coco_subset_annotations.json"

    report = json.loads(report_path.read_text(encoding="utf-8"))
    annotations = json.loads(annotation_path.read_text(encoding="utf-8"))

    assert annotations["info"]["image_count"] == 10
    assert annotations["info"]["annotation_count"] == 89
    assert report["preset"]["name"] == "yolov8_coco"
    assert report["runtime_result"]["sample_count"] == 10
    assert report["accuracy"]["status"] == "evaluated"
    assert report["accuracy"]["metrics"]["backend"] == "simplified"
    assert report["accuracy"]["metrics"]["note"] == "lightweight simplified mAP50 implementation"
    assert round(report["accuracy"]["metrics"]["map50"], 4) == 0.141
    assert round(report["accuracy"]["metrics"]["precision"], 4) == 0.2941
    assert round(report["accuracy"]["metrics"]["recall"], 4) == 0.1685
    assert report["structural_validation"]["status"] == "passed"
    assert report["contract_validation"]["input_shape"]["status"] == "passed"


def test_validation_problem_case_reports_cover_review_and_blocked_paths():
    repo_root = Path(__file__).resolve().parents[1]
    problem_dir = repo_root / "examples" / "validation_demo" / "problem_cases"

    reports = {
        path.name: json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(problem_dir.glob("*_report.json"))
    }

    assert set(reports) == {
        "annotation_missing_report.json",
        "contract_shape_mismatch_report.json",
        "invalid_detection_structure_report.json",
    }
    assert reports["annotation_missing_report.json"]["accuracy"]["status"] == "skipped"
    assert reports["annotation_missing_report.json"]["deployment_signal"]["decision"] == "review"
    assert reports["invalid_detection_structure_report.json"]["structural_validation"]["status"] == "failed"
    assert reports["invalid_detection_structure_report.json"]["deployment_signal"]["decision"] == "blocked"
    assert reports["contract_shape_mismatch_report.json"]["contract_validation"]["input_shape"]["status"] == "mismatch"
    assert reports["contract_shape_mismatch_report.json"]["deployment_signal"]["decision"] == "blocked"


def test_latency_regression_problem_case_records_review_signal():
    repo_root = Path(__file__).resolve().parents[1]
    summary_path = repo_root / "examples" / "studio_demo" / "latency_regression_summary.json"
    baseline_path = repo_root / "examples" / "studio_demo" / "normal_baseline_result.json"
    regression_path = repo_root / "examples" / "studio_demo" / "latency_regression_result.json"

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    regression = json.loads(regression_path.read_text(encoding="utf-8"))

    assert summary["problem_case"] == "latency_regression"
    assert summary["deployment_signal"]["decision"] == "review_required"
    assert summary["deployment_signal"]["reason"] == "p99 latency regression detected"
    assert summary["latency_checks"]["mean_latency"]["delta_pct"] >= 10.0
    assert summary["latency_checks"]["p99_latency"]["delta_pct"] >= 20.0
    assert summary["latency_checks"]["run_config"]["status"] == "passed"
    assert baseline["backend_key"] == regression["backend_key"] == "tensorrt__jetson"
    assert baseline["compare_key"] == regression["compare_key"]
    assert baseline["run_config"] == regression["run_config"]
