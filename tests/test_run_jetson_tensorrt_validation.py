from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


def import_run_jetson_tensorrt_validation_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "run_jetson_tensorrt_validation.py"
    spec = importlib.util.spec_from_file_location("test_run_jetson_tensorrt_validation_module", module_path)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_main_returns_2_when_repeat_is_less_than_two(tmp_path, monkeypatch):
    module = import_run_jetson_tensorrt_validation_module()

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_jetson_tensorrt_validation.py",
            "--model-path",
            str(tmp_path / "models" / "resnet18.onnx"),
            "--engine-path",
            str(tmp_path / "models" / "resnet18.engine"),
            "--repeat",
            "1",
        ],
    )

    assert module.main() == 2


def test_main_runs_preflight_profiles_and_compare_and_creates_report_dir(tmp_path, monkeypatch):
    module = import_run_jetson_tensorrt_validation_module()

    report_dir = tmp_path / "reports" / "validation"
    model_path = tmp_path / "models" / "resnet18.onnx"
    engine_path = tmp_path / "models" / "resnet18.engine"
    commands: list[list[str]] = []

    def fake_run(command, check):
        commands.append(list(command))
        assert check is True
        return None

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_jetson_tensorrt_validation.py",
            "--model-path",
            str(model_path),
            "--engine-path",
            str(engine_path),
            "--report-dir",
            str(report_dir),
            "--repeat",
            "3",
        ],
    )

    result = module.main()

    assert result == 0
    assert report_dir.exists()
    assert len(commands) == 5

    preflight_command = commands[0]
    profile_commands = commands[1:4]
    compare_command = commands[4]

    assert preflight_command == [
        sys.executable,
        "scripts/check_jetson_tensorrt_env.py",
        "--model-path",
        str(model_path),
        "--engine-path",
        str(engine_path),
    ]

    for command in profile_commands:
        assert command == [
            sys.executable,
            "-m",
            "edgebench.cli",
            "profile",
            str(model_path),
            "--engine",
            "tensorrt",
            "--engine-path",
            str(engine_path),
            "--precision",
            "fp16",
            "--warmup",
            "10",
            "--runs",
            "100",
            "--batch",
            "1",
            "--height",
            "0",
            "--width",
            "0",
        ]

    assert compare_command == [
        sys.executable,
        "-m",
        "edgebench.cli",
        "compare-latest",
        "--model",
        "resnet18.onnx",
        "--engine",
        "tensorrt",
        "--device",
        "gpu",
        "--precision",
        "fp16",
        "--selection-mode",
        "same_precision",
        "--markdown-out",
        str(report_dir / "resnet18_tensorrt_latest.md"),
        "--html-out",
        str(report_dir / "resnet18_tensorrt_latest.html"),
    ]


def test_main_skip_preflight_does_not_call_preflight_command(tmp_path, monkeypatch):
    module = import_run_jetson_tensorrt_validation_module()

    model_path = tmp_path / "models" / "yolov8n.onnx"
    engine_path = tmp_path / "models" / "yolov8n.engine"
    commands: list[list[str]] = []

    def fake_run(command, check):
        commands.append(list(command))
        assert check is True
        return None

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_jetson_tensorrt_validation.py",
            "--model-path",
            str(model_path),
            "--engine-path",
            str(engine_path),
            "--skip-preflight",
        ],
    )

    result = module.main()

    assert result == 0
    assert len(commands) == 3
    assert all("scripts/check_jetson_tensorrt_env.py" not in command for command in commands)


def test_main_returns_called_process_error_returncode(tmp_path, monkeypatch):
    module = import_run_jetson_tensorrt_validation_module()

    model_path = tmp_path / "models" / "resnet18.onnx"
    engine_path = tmp_path / "models" / "resnet18.engine"

    def fake_run(command, check):
        raise subprocess.CalledProcessError(returncode=7, cmd=command)

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_jetson_tensorrt_validation.py",
            "--model-path",
            str(model_path),
            "--engine-path",
            str(engine_path),
        ],
    )

    assert module.main() == 7


def test_main_uses_model_stem_for_report_paths(tmp_path, monkeypatch, capsys):
    module = import_run_jetson_tensorrt_validation_module()

    report_dir = tmp_path / "custom-reports"
    model_path = tmp_path / "models" / "my_model.onnx"
    engine_path = tmp_path / "models" / "my_model.engine"
    commands: list[list[str]] = []

    def fake_run(command, check):
        commands.append(list(command))
        assert check is True
        return None

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_jetson_tensorrt_validation.py",
            "--model-path",
            str(model_path),
            "--engine-path",
            str(engine_path),
            "--report-dir",
            str(report_dir),
            "--repeat",
            "2",
        ],
    )

    result = module.main()
    out = capsys.readouterr().out

    assert result == 0
    assert str(report_dir / "my_model_tensorrt_latest.md") in out
    assert str(report_dir / "my_model_tensorrt_latest.html") in out
    assert commands[-1][-4:] == [
        "--markdown-out",
        str(report_dir / "my_model_tensorrt_latest.md"),
        "--html-out",
        str(report_dir / "my_model_tensorrt_latest.html"),
    ]
