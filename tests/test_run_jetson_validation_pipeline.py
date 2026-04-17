from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def import_run_jetson_validation_pipeline_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "run_jetson_validation_pipeline.py"
    spec = importlib.util.spec_from_file_location("test_run_jetson_validation_pipeline_module", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_parse_args_accepts_new_passthrough_options(tmp_path, monkeypatch):
    module = import_run_jetson_validation_pipeline_module()

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_jetson_validation_pipeline.py",
            "--model-path",
            str(tmp_path / "models" / "yolov8n.onnx"),
            "--engine-path",
            str(tmp_path / "models" / "yolov8n.engine"),
            "--label",
            "Jetson Validation",
            "--precision",
            "fp16",
            "--warmup",
            "5",
            "--runs",
            "50",
            "--batch",
            "2",
            "--height",
            "640",
            "--width",
            "640",
            "--repeat",
            "3",
            "--skip-preflight",
            "--dry-run",
        ],
    )

    args = module._parse_args()

    assert args.model_path.endswith("yolov8n.onnx")
    assert args.engine_path.endswith("yolov8n.engine")
    assert args.label == "Jetson Validation"
    assert args.precision == "fp16"
    assert args.warmup == 5
    assert args.runs == 50
    assert args.batch == 2
    assert args.height == 640
    assert args.width == 640
    assert args.repeat == 3
    assert args.skip_preflight is True
    assert args.dry_run is True


def test_main_passes_new_validation_args_and_keeps_export_step(tmp_path, monkeypatch, capsys):
    module = import_run_jetson_validation_pipeline_module()
    model_path = tmp_path / "models" / "yolov8n.onnx"
    engine_path = tmp_path / "models" / "yolov8n.engine"
    report_dir = tmp_path / "reports" / "validation"
    evidence_out = tmp_path / "evidence" / "yolov8n.md"
    commands: list[list[str]] = []

    def fake_run_command(command):
        commands.append(list(command))

    monkeypatch.setattr(module, "_run_command", fake_run_command)
    monkeypatch.setattr(
        module,
        "latest_comparable_result_paths",
        lambda pattern: [str(tmp_path / "results" / "base.json"), str(tmp_path / "results" / "new.json")],
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_jetson_validation_pipeline.py",
            "--model-path",
            str(model_path),
            "--engine-path",
            str(engine_path),
            "--label",
            "Jetson Validation",
            "--precision",
            "fp16",
            "--warmup",
            "7",
            "--runs",
            "50",
            "--batch",
            "1",
            "--height",
            "640",
            "--width",
            "640",
            "--repeat",
            "2",
            "--report-dir",
            str(report_dir),
            "--evidence-out",
            str(evidence_out),
            "--skip-preflight",
            "--dry-run",
        ],
    )

    result = module.main()
    out = capsys.readouterr().out

    assert result == 0
    assert len(commands) == 2

    validation_command = commands[0]
    export_command = commands[1]

    assert validation_command == [
        sys.executable,
        "scripts/run_jetson_tensorrt_validation.py",
        "--model-path",
        str(model_path),
        "--engine-path",
        str(engine_path),
        "--precision",
        "fp16",
        "--warmup",
        "7",
        "--runs",
        "50",
        "--batch",
        "1",
        "--height",
        "640",
        "--width",
        "640",
        "--repeat",
        "2",
        "--report-dir",
        str(report_dir),
        "--skip-preflight",
        "--dry-run",
    ]

    assert export_command == [
        sys.executable,
        "scripts/export_validation_evidence.py",
        "--base-result",
        str(tmp_path / "results" / "base.json"),
        "--new-result",
        str(tmp_path / "results" / "new.json"),
        "--label",
        "Jetson Validation",
        "--markdown-out",
        str(evidence_out),
        "--report-markdown-path",
        str(report_dir / "yolov8n_tensorrt_latest.md"),
        "--report-html-path",
        str(report_dir / "yolov8n_tensorrt_latest.html"),
    ]

    assert "Profile runs done." in out
    assert f"Compare report path : {report_dir / 'yolov8n_tensorrt_latest.md'}" in out
    assert f"Evidence path       : {evidence_out}" in out
