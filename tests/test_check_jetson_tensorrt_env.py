from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def import_check_jetson_tensorrt_env_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "check_jetson_tensorrt_env.py"
    spec = importlib.util.spec_from_file_location("test_check_jetson_tensorrt_env_module", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_main_returns_1_when_jetson_marker_modules_and_paths_are_missing(tmp_path, monkeypatch):
    module = import_check_jetson_tensorrt_env_module()
    original_exists = Path.exists

    def fake_exists(path: Path) -> bool:
        if str(path) == "/etc/nv_tegra_release":
            return False
        return original_exists(path)

    monkeypatch.setattr(Path, "exists", fake_exists)
    monkeypatch.setattr(module.importlib.util, "find_spec", lambda name: None)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_jetson_tensorrt_env.py",
            "--model-path",
            str(tmp_path / "missing.onnx"),
            "--engine-path",
            str(tmp_path / "missing.engine"),
        ],
    )

    assert module.main() == 1


def test_main_returns_0_when_jetson_marker_modules_and_paths_exist(tmp_path, monkeypatch):
    module = import_check_jetson_tensorrt_env_module()
    model_path = tmp_path / "model.onnx"
    engine_path = tmp_path / "model.engine"
    model_path.write_text("onnx", encoding="utf-8")
    engine_path.write_text("engine", encoding="utf-8")
    original_exists = Path.exists

    def fake_exists(path: Path) -> bool:
        if str(path) == "/etc/nv_tegra_release":
            return True
        return original_exists(path)

    def fake_find_spec(name: str):
        if name in {"tensorrt", "onnxruntime", "numpy", "cuda"}:
            return object()
        return None

    monkeypatch.setattr(Path, "exists", fake_exists)
    monkeypatch.setattr(module.importlib.util, "find_spec", fake_find_spec)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_jetson_tensorrt_env.py",
            "--model-path",
            str(model_path),
            "--engine-path",
            str(engine_path),
        ],
    )

    assert module.main() == 0


def test_main_prints_skip_when_model_and_engine_paths_are_not_provided(tmp_path, monkeypatch, capsys):
    module = import_check_jetson_tensorrt_env_module()
    original_exists = Path.exists

    def fake_exists(path: Path) -> bool:
        if str(path) == "/etc/nv_tegra_release":
            return True
        return original_exists(path)

    def fake_find_spec(name: str):
        if name in {"tensorrt", "onnxruntime", "numpy", "cuda"}:
            return object()
        return None

    monkeypatch.setattr(Path, "exists", fake_exists)
    monkeypatch.setattr(module.importlib.util, "find_spec", fake_find_spec)
    monkeypatch.setattr(sys, "argv", ["check_jetson_tensorrt_env.py"])

    assert module.main() == 0
    out = capsys.readouterr().out

    assert "[SKIP] model_path: not provided" in out
    assert "[SKIP] engine_path: not provided" in out


def test_cuda_python_binding_check_affects_summary_result(tmp_path, monkeypatch, capsys):
    module = import_check_jetson_tensorrt_env_module()
    model_path = tmp_path / "model.onnx"
    engine_path = tmp_path / "model.engine"
    model_path.write_text("onnx", encoding="utf-8")
    engine_path.write_text("engine", encoding="utf-8")
    original_exists = Path.exists

    def fake_exists(path: Path) -> bool:
        if str(path) == "/etc/nv_tegra_release":
            return True
        return original_exists(path)

    def fake_find_spec(name: str):
        if name in {"tensorrt", "onnxruntime", "numpy"}:
            return object()
        return None

    monkeypatch.setattr(Path, "exists", fake_exists)
    monkeypatch.setattr(module.importlib.util, "find_spec", fake_find_spec)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "check_jetson_tensorrt_env.py",
            "--model-path",
            str(model_path),
            "--engine-path",
            str(engine_path),
        ],
    )

    assert module.main() == 1
    out = capsys.readouterr().out

    assert "[MISSING] cuda-python binding:" in out
    assert "FAIL:" in out
