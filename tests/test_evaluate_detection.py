from __future__ import annotations

import importlib.util
import json
import sys
import types
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pytest
from typer.testing import CliRunner

from inferedgelab.core.detection_evaluator import (
    Detection,
    DetectionEvalResult,
    GroundTruth,
    build_accuracy_payload,
    calculate_iou,
    compute_average_precision,
    compute_precision_recall_f1,
    evaluate_detection_engine,
    load_ground_truth,
    nms,
    save_accuracy_payload,
    scale_coords,
)
from inferedgelab.engines.base import EngineModelIO


@contextmanager
def _temporary_sys_modules(module_names: list[str]):
    saved = {name: sys.modules.get(name) for name in module_names}
    try:
        yield
    finally:
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


def _import_cli_module():
    repo_root = Path(__file__).resolve().parents[1]
    command_specs = {
        "inferedgelab.commands.analyze": "analyze_cmd",
        "inferedgelab.commands.profile": "profile_cmd",
        "inferedgelab.commands.evaluate": "evaluate_cmd",
        "inferedgelab.commands.evaluate_detection": "evaluate_detection_cmd",
        "inferedgelab.commands.summarize": "summarize",
        "inferedgelab.commands.compare": "compare_cmd",
        "inferedgelab.commands.compare_latest": "compare_latest_cmd",
        "inferedgelab.commands.enrich_pair": "enrich_pair_cmd",
        "inferedgelab.commands.enrich_result": "enrich_result_cmd",
        "inferedgelab.commands.list_results": "list_results_cmd",
        "inferedgelab.commands.history_report": "history_report_cmd",
        "inferedgelab.commands.serve": "serve_cmd",
    }

    with _temporary_sys_modules(["typer", "test_cli_module", *command_specs.keys()]):
        typer_stub = types.ModuleType("typer")

        class Typer:
            def __init__(self, *args, **kwargs):
                self.registered_commands = []

            def command(self, name=None, **kwargs):
                def decorator(fn):
                    self.registered_commands.append((name, fn))
                    return fn
                return decorator

        typer_stub.Typer = Typer
        typer_stub.echo = lambda value: value
        typer_stub.Option = lambda default=None, *args, **kwargs: default
        typer_stub.Argument = lambda default=None, *args, **kwargs: default
        typer_stub.BadParameter = type("BadParameter", (Exception,), {})
        typer_stub.Exit = type("Exit", (Exception,), {})
        sys.modules["typer"] = typer_stub

        for module_name, attr_name in command_specs.items():
            stub = types.ModuleType(module_name)
            setattr(stub, attr_name, lambda *args, **kwargs: None)
            sys.modules[module_name] = stub

        module_path = repo_root / "inferedgelab" / "cli.py"
        spec = importlib.util.spec_from_file_location("test_cli_module", module_path)
        assert spec is not None
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module


def test_load_ground_truth_converts_yolo_txt_to_absolute_xywh(tmp_path):
    label_path = tmp_path / "sample.txt"
    label_path.write_text("0 0.5 0.25 0.4 0.2\n", encoding="utf-8")

    ground_truths = load_ground_truth(str(label_path), image_width=1000, image_height=500)

    assert len(ground_truths) == 1
    assert ground_truths[0].class_id == 0
    assert ground_truths[0].box == (500.0, 125.0, 400.0, 100.0)


def test_calculate_iou_returns_expected_overlap():
    iou = calculate_iou((50.0, 50.0, 40.0, 40.0), (60.0, 50.0, 40.0, 40.0))

    assert round(iou, 4) == 0.6


def test_nms_keeps_highest_confidence_box_for_overlapping_predictions():
    detections = [
        Detection(class_id=0, confidence=0.95, box=(50.0, 50.0, 40.0, 40.0)),
        Detection(class_id=0, confidence=0.75, box=(52.0, 50.0, 40.0, 40.0)),
        Detection(class_id=0, confidence=0.60, box=(150.0, 150.0, 20.0, 20.0)),
    ]

    kept = nms(detections, iou_threshold=0.5)

    assert len(kept) == 2
    assert kept[0].confidence == 0.95
    assert kept[1].confidence == 0.60


def test_scale_coords_clips_xyxy_and_returns_original_image_xywh():
    scaled = scale_coords(
        box=(350.0, 300.0, 300.0, 200.0),
        scale=0.5,
        pad_w=100.0,
        pad_h=50.0,
        original_width=800,
        original_height=600,
    )

    assert scaled == pytest.approx((500.0, 450.0, 600.0, 300.0))


def test_map50_and_f1_are_one_for_perfect_prediction():
    predictions_by_image = [[Detection(class_id=0, confidence=0.99, box=(50.0, 50.0, 20.0, 20.0))]]
    ground_truths_by_image = [[GroundTruth(class_id=0, box=(50.0, 50.0, 20.0, 20.0))]]

    precision, recall, f1_score = compute_precision_recall_f1(
        predictions_by_image,
        ground_truths_by_image,
        num_classes=1,
        iou_threshold=0.5,
    )
    map50 = compute_average_precision(
        predictions_by_image,
        ground_truths_by_image,
        num_classes=1,
        iou_threshold=0.5,
    )

    assert precision == pytest.approx(1.0)
    assert recall == pytest.approx(1.0)
    assert f1_score == pytest.approx(1.0)
    assert map50 == pytest.approx(1.0)


def test_accuracy_payload_save_keeps_task_and_metrics_structure(tmp_path):
    payload = build_accuracy_payload(
        DetectionEvalResult(
            task="detection",
            engine="tensorrt",
            device="gpu",
            sample_count=2,
            metrics={
                "map50": 0.9,
                "map50_95": 0.7,
                "f1_score": 0.8,
                "precision": 0.85,
                "recall": 0.75,
            },
            notes=[],
            model_input={"name": "images", "dtype": "float32", "shape": [1, 3, 640, 640]},
            actual_input_shape=[1, 3, 640, 640],
            dataset={"image_dir": "images", "label_dir": "labels", "sample_count": 2},
            evaluation_config={
                "conf_threshold": 0.2,
                "nms_threshold": 0.45,
                "iou_threshold": 0.5,
                "input_size": 640,
                "rgb": True,
            },
            extra={},
        )
    )
    out_json = tmp_path / "accuracy.json"

    save_accuracy_payload(payload, str(out_json))

    saved = json.loads(out_json.read_text(encoding="utf-8"))
    assert saved["task"] == "detection"
    assert saved["metrics"]["map50"] == pytest.approx(0.9)
    assert saved["metrics"]["f1_score"] == pytest.approx(0.8)
    assert saved["dataset"]["sample_count"] == 2


def test_evaluate_detection_command_writes_accuracy_payload(tmp_path, monkeypatch):
    from inferedgelab.commands import evaluate_detection

    captured = {}

    def fake_evaluate_detection_engine(**kwargs):
        captured["engine_kwargs"] = kwargs
        return DetectionEvalResult(
            task="detection",
            engine="tensorrt",
            device="gpu",
            sample_count=3,
            metrics={
                "map50": 0.7791,
                "map50_95": 0.5512,
                "f1_score": 0.8180,
                "precision": 0.7950,
                "recall": 0.8424,
            },
            notes=[],
            model_input={"name": "images", "dtype": "float16", "shape": [1, 3, 640, 640]},
            actual_input_shape=[1, 3, 640, 640],
            dataset={"image_dir": "images", "label_dir": "labels", "sample_count": 3},
            evaluation_config={
                "conf_threshold": 0.2,
                "nms_threshold": 0.45,
                "iou_threshold": 0.5,
                "input_size": 640,
                "rgb": True,
            },
            extra={"runtime_artifact_path": "engine.plan"},
        )

    def fake_save_result(result, out_dir="results"):
        captured["result"] = result
        captured["out_dir"] = out_dir
        return str(Path(out_dir) / "saved.json")

    monkeypatch.setattr(evaluate_detection, "evaluate_detection_engine", fake_evaluate_detection_engine)
    monkeypatch.setattr(evaluate_detection, "save_result", fake_save_result)
    monkeypatch.setattr(
        evaluate_detection,
        "collect_system_snapshot",
        lambda: {"os": "Linux"},
    )

    out_json = tmp_path / "accuracy.json"
    evaluate_detection.evaluate_detection_cmd(
        model_path="models/onnx/yolov8n.onnx",
        engine="tensorrt",
        engine_path="builds/model.engine",
        image_dir="images",
        label_dir="labels",
        num_classes=1,
        precision="fp16",
        conf_threshold=0.2,
        nms_threshold=0.45,
        iou_threshold=0.5,
        rgb=True,
        out_json=str(out_json),
        out_dir=str(tmp_path / "results"),
        save_structured_result=True,
    )

    payload = json.loads(out_json.read_text(encoding="utf-8"))
    assert payload["task"] == "detection"
    assert payload["metrics"]["map50"] == pytest.approx(0.7791)
    assert captured["result"].accuracy["task"] == "detection"
    assert captured["result"].accuracy["metrics"]["map50"] == pytest.approx(0.7791)
    assert captured["result"].run_config["mode"] == "evaluate-detection"
    assert captured["engine_kwargs"]["debug_samples"] == 0


def test_evaluate_detection_engine_debug_path_prints_sample_diagnostics(tmp_path, monkeypatch, capsys):
    image_dir = tmp_path / "images"
    label_dir = tmp_path / "labels"
    image_dir.mkdir()
    label_dir.mkdir()
    (image_dir / "sample.jpg").write_bytes(b"fake-image")
    (label_dir / "sample.txt").write_text("0 0.5 0.5 0.15625 0.15625\n", encoding="utf-8")

    class FakeCv2:
        INTER_LINEAR = 1
        COLOR_BGR2RGB = 2

        @staticmethod
        def imread(path):
            return np.zeros((640, 640, 3), dtype=np.uint8)

        @staticmethod
        def resize(image, size, interpolation=None):
            width, height = size
            return np.zeros((height, width, 3), dtype=image.dtype)

        @staticmethod
        def cvtColor(image, code):
            return image

    class FakeEngine:
        def __init__(self):
            self.name = "tensorrt"
            self.device = "gpu"
            self.inputs = [EngineModelIO(name="images", dtype=np.dtype(np.float32), shape=[1, 3, 640, 640])]
            self.runtime_paths = types.SimpleNamespace(runtime_artifact_path="engine.plan")

        def load(self, model_path, **kwargs):
            return None

        def run(self, feeds):
            return [
                np.array(
                    [[[320.0], [320.0], [100.0], [100.0], [0.95]]],
                    dtype=np.float32,
                )
            ]

        def close(self):
            return None

    monkeypatch.setattr(
        "inferedgelab.core.detection_evaluator._require_cv2",
        lambda: FakeCv2,
    )
    monkeypatch.setattr(
        "inferedgelab.core.detection_evaluator.create_engine",
        lambda engine_name: FakeEngine(),
    )

    result = evaluate_detection_engine(
        model_path="models/onnx/yolov8n.onnx",
        engine_name="tensorrt",
        engine_path="builds/model.engine",
        image_dir=str(image_dir),
        label_dir=str(label_dir),
        num_classes=1,
        conf_threshold=0.2,
        nms_threshold=0.45,
        iou_threshold=0.5,
        use_rgb=True,
        input_size=640,
        debug_samples=1,
    )

    stdout = capsys.readouterr().out
    assert result.metrics["map50"] == pytest.approx(1.0)
    assert "sample_index=0" in stdout
    assert "raw_output_count            : 1" in stdout
    assert "single_output_layout" in stdout
    assert "top_score_samples" in stdout
    assert "gt_count                    : 1" in stdout


def test_evaluate_detection_help_shows_debug_samples_option():
    with _temporary_sys_modules(["typer", "inferedgelab.cli"]):
        sys.modules.pop("typer", None)
        sys.modules.pop("inferedgelab.cli", None)

        import importlib

        cli_module = importlib.import_module("inferedgelab.cli")
        runner = CliRunner()
        result = runner.invoke(cli_module.app, ["evaluate-detection", "--help"])

        assert result.exit_code == 0
        assert "--debug-samples" in result.stdout


def test_cli_help_registers_evaluate_detection_command():
    cli_module = _import_cli_module()
    command_names = [name for name, _ in cli_module.app.registered_commands]

    assert "evaluate-detection" in command_names
