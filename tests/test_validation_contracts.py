from __future__ import annotations

from pathlib import Path

import pytest

from inferedgelab.core.detection_evaluator import Detection, DetectionEvalResult
from inferedgelab.validation.coco import load_coco_ground_truths
from inferedgelab.validation.model_contract import (
    ModelContractError,
    build_default_contract,
    load_model_contract,
    parse_model_contract,
)
from inferedgelab.validation.presets import get_preset, supported_presets
from inferedgelab.validation.report import build_evaluation_report, render_evaluation_markdown
from inferedgelab.validation.structural import validate_detection_structure, validate_shape


def test_yolov8_coco_preset_builds_default_model_contract():
    preset = get_preset("yolov8_coco")
    contract = build_default_contract("yolov8_coco")

    assert "yolov8_coco" in supported_presets()
    assert preset.task == "object_detection"
    assert contract.preset == "yolov8_coco"
    assert contract.input.shape == [1, 3, 640, 640]
    assert contract.output.type == "yolov8_detection"
    assert len(contract.labels) == 80


def test_parse_model_contract_rejects_preset_task_mismatch():
    with pytest.raises(ModelContractError):
        parse_model_contract(
            {
                "preset": "yolov8_coco",
                "task": "classification",
                "input": {"shape": [1, 3, 640, 640]},
                "output": {"shape": [1, 84, 8400]},
            }
        )


def test_example_validation_demo_contracts_are_parseable():
    repo_root = Path(__file__).resolve().parents[1]

    normal = load_model_contract(str(repo_root / "examples" / "validation_demo" / "yolov8_coco_model_contract.json"))
    problem = load_model_contract(str(repo_root / "examples" / "validation_demo" / "problem_model_contract.json"))

    assert normal.metadata["demo_case"] == "normal"
    assert problem.metadata["demo_case"] == "problem"
    assert problem.input.shape == [1, 3, 320, 320]


def test_load_coco_ground_truths_maps_annotations_by_file_name():
    fixture = Path(__file__).parent / "fixtures" / "validation" / "coco_minimal.json"

    ground_truths = load_coco_ground_truths(str(fixture))

    assert list(ground_truths) == ["sample.jpg"]
    assert ground_truths["sample.jpg"][0].class_id == 0
    assert ground_truths["sample.jpg"][0].box == pytest.approx((140.0, 150.0, 80.0, 60.0))


def test_structural_validation_detects_invalid_detection_fields():
    result = validate_detection_structure(
        [[Detection(class_id=99, confidence=1.2, box=(10.0, 10.0, -5.0, 5.0))]],
        num_classes=3,
    )

    assert result["status"] == "failed"
    assert {issue["code"] for issue in result["issues"]} == {
        "class_id_out_of_range",
        "score_out_of_range",
        "bbox_non_positive_size",
    }


def test_shape_validation_reports_mismatch():
    result = validate_shape([1, 3, 320, 320], [1, 3, 640, 640])

    assert result["status"] == "mismatch"


def test_evaluation_report_marks_missing_annotations_as_accuracy_skipped():
    eval_result = DetectionEvalResult(
        task="detection",
        engine="onnxruntime",
        device="cpu",
        sample_count=1,
        metrics={
            "map50": 0.0,
            "map50_95": 0.0,
            "f1_score": 0.0,
            "precision": 0.0,
            "recall": 0.0,
        },
        notes=["structural validation only"],
        model_input={"name": "images", "dtype": "float32", "shape": [1, 3, 640, 640]},
        actual_input_shape=[1, 3, 640, 640],
        dataset={"image_dir": "images", "sample_count": 1, "accuracy_status": "skipped"},
        evaluation_config={"input_size": 640},
        extra={
            "accuracy_status": "skipped",
            "accuracy_skip_reason": "annotations missing",
            "structural_validation": {"status": "passed", "issues": []},
        },
    )

    report = build_evaluation_report(
        eval_result=eval_result,
        model_contract=build_default_contract("yolov8_coco"),
        preset=get_preset("yolov8_coco").to_dict(),
    )
    markdown = render_evaluation_markdown(report)

    assert report["accuracy"]["status"] == "skipped"
    assert report["contract_validation"]["input_shape"]["status"] == "passed"
    assert report["deployment_signal"]["decision"] == "review"
    assert "accuracy skipped reason" in markdown


def test_evaluation_report_blocks_contract_shape_mismatch():
    eval_result = DetectionEvalResult(
        task="detection",
        engine="onnxruntime",
        device="cpu",
        sample_count=1,
        metrics={
            "map50": 0.0,
            "map50_95": 0.0,
            "f1_score": 0.0,
            "precision": 0.0,
            "recall": 0.0,
        },
        notes=[],
        model_input={"name": "images", "dtype": "float32", "shape": [1, 3, 640, 640]},
        actual_input_shape=[1, 3, 640, 640],
        dataset={"image_dir": "images", "sample_count": 1},
        evaluation_config={"input_size": 640},
        extra={"accuracy_status": "skipped", "structural_validation": {"status": "passed", "issues": []}},
    )
    contract = parse_model_contract(
        {
            "preset": "yolov8_coco",
            "task": "object_detection",
            "input": {"shape": [1, 3, 320, 320]},
            "output": {"shape": [1, 84, 8400]},
        }
    )

    report = build_evaluation_report(
        eval_result=eval_result,
        model_contract=contract,
        preset=get_preset("yolov8_coco").to_dict(),
    )

    assert report["contract_validation"]["input_shape"]["status"] == "mismatch"
    assert report["deployment_signal"]["decision"] == "blocked"
