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
    assert round(report["accuracy"]["metrics"]["map50"], 4) == 0.141
    assert round(report["accuracy"]["metrics"]["precision"], 4) == 0.2941
    assert round(report["accuracy"]["metrics"]["recall"], 4) == 0.1685
    assert report["structural_validation"]["status"] == "passed"
    assert report["contract_validation"]["input_shape"]["status"] == "passed"
