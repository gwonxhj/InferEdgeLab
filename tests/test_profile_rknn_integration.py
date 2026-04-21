from __future__ import annotations

import importlib.util
import sys
import types

import numpy as np
import pytest
import typer


def _install_optional_dependency_stubs() -> None:
    if importlib.util.find_spec("onnx") is None:
        onnx_stub = types.ModuleType("onnx")
        onnx_stub.TensorProto = types.SimpleNamespace(
            FLOAT=1,
            FLOAT16=10,
            DOUBLE=11,
            INT64=7,
            INT32=6,
            UINT8=2,
            INT8=3,
        )
        sys.modules["onnx"] = onnx_stub

    if importlib.util.find_spec("onnxruntime") is None:
        sys.modules["onnxruntime"] = types.ModuleType("onnxruntime")


_install_optional_dependency_stubs()

from inferedgelab.commands.profile import profile_cmd
from inferedgelab.core.profiler import ProfileResult, profile_model


class FakeRknnProfilerEngine:
    def __init__(self) -> None:
        self.name = "rknn"
        self.device = "odroid_m2"
        self.runtime_paths = types.SimpleNamespace(runtime_artifact_path="model.rknn")
        self.load_calls: list[tuple[str, dict[str, object]]] = []

    def load(self, model_path: str, **kwargs) -> None:
        self.load_calls.append((model_path, dict(kwargs)))
        self.device = str(kwargs.get("device_name") or self.device)
        self.runtime_paths.runtime_artifact_path = str(kwargs.get("engine_path") or "model.rknn")

    def make_dummy_inputs(
        self,
        batch_override: int | None = None,
        height_override: int | None = None,
        width_override: int | None = None,
    ) -> dict[str, np.ndarray]:
        batch = batch_override or 1
        height = height_override or 224
        width = width_override or 224
        return {"images": np.zeros((batch, 3, height, width), dtype=np.float32)}

    def run(self, feeds):
        batch = next(iter(feeds.values())).shape[0]
        return [np.zeros((batch, 1), dtype=np.float32)]

    def close(self) -> None:
        return None


def test_profile_model_passes_rknn_specific_load_kwargs(monkeypatch):
    fake_engine = FakeRknnProfilerEngine()

    monkeypatch.setattr(
        "inferedgelab.core.profiler.create_engine",
        lambda engine_name: fake_engine,
    )

    result = profile_model(
        model_path="models/yolov8n.onnx",
        engine="rknn",
        engine_path="models/yolov8n.rknn",
        warmup=0,
        runs=1,
        batch=1,
        height=224,
        width=224,
        rknn_target="rk3588",
        device_name="odroid_m2",
    )

    assert fake_engine.load_calls == [
        (
            "models/yolov8n.onnx",
            {
                "intra_threads": 1,
                "inter_threads": 1,
                "engine_path": "models/yolov8n.rknn",
                "rknn_target": "rk3588",
                "device_name": "odroid_m2",
            },
        )
    ]
    assert result.engine == "rknn"
    assert result.device == "odroid_m2"
    assert result.extra["runtime_artifact_path"] == "models/yolov8n.rknn"
    assert result.extra["load_kwargs"]["rknn_target"] == "rk3588"
    assert result.extra["load_kwargs"]["device_name"] == "odroid_m2"


def test_profile_cmd_saves_rknn_runtime_metadata(monkeypatch, tmp_path):
    model_path = tmp_path / "model.onnx"
    model_path.write_bytes(b"fake-onnx")

    saved = {}

    def fake_save_result(result):
        saved["result"] = result
        return "results/fake.json"

    monkeypatch.setattr(
        "inferedgelab.commands.profile.analyze_onnx",
        lambda *args, **kwargs: types.SimpleNamespace(
            file_size_bytes=123,
            sha256="abc",
            parameters=0,
            inputs=[],
            outputs=[],
            flops_estimate=None,
            flops_breakdown=None,
            flops_hotspots=None,
            flops_assumptions=None,
        ),
    )
    monkeypatch.setattr(
        "inferedgelab.commands.profile.collect_system_info",
        lambda: {"os": "linux", "python": "3.11", "machine": "rk3588"},
    )
    monkeypatch.setattr(
        "inferedgelab.commands.profile.collect_package_versions",
        lambda: {"numpy": "1.0"},
    )
    monkeypatch.setattr(
        "inferedgelab.commands.profile.collect_system_snapshot",
        lambda: {"cpu": "rk3588"},
    )
    monkeypatch.setattr(
        "inferedgelab.commands.profile.profile_model",
        lambda **kwargs: ProfileResult(
            engine="rknn",
            device="odroid_m2",
            warmup=kwargs["warmup"],
            runs=kwargs["runs"],
            latency_ms={"mean": 12.3, "p99": 15.6},
            extra={
                "input_names": ["images"],
                "runtime_artifact_path": kwargs["engine_path"],
                "primary_input_name": "images",
                "resolved_input_shapes": {"images": [1, 3, 640, 640]},
                "effective_batch": 1,
                "effective_height": 640,
                "effective_width": 640,
            },
        ),
    )
    monkeypatch.setattr(
        "inferedgelab.commands.profile.save_result",
        fake_save_result,
    )
    monkeypatch.setattr(
        "inferedgelab.commands.profile.EdgeBenchReport.write_json",
        lambda self, output_path, indent=2: None,
    )

    profile_cmd(
        model_path=str(model_path),
        precision="fp32",
        engine="rknn",
        engine_path="models/yolov8n.rknn",
        rknn_target="rk3588",
        device_name="odroid_m2",
        warmup=1,
        runs=2,
        batch=1,
        height=640,
        width=640,
        intra_threads=1,
        inter_threads=1,
        no_hash=True,
        output=str(tmp_path / "report.json"),
    )

    structured = saved["result"]
    assert structured.engine == "rknn"
    assert structured.device == "odroid_m2"
    assert structured.run_config["engine_path"] == "models/yolov8n.rknn"
    assert structured.run_config["rknn_target"] == "rk3588"
    assert structured.run_config["device_name"] == "odroid_m2"
    assert structured.extra["runtime_artifact_path"] == "models/yolov8n.rknn"
    assert structured.extra["rknn_target"] == "rk3588"
    assert structured.extra["device_name"] == "odroid_m2"
    assert structured.extra["effective_batch"] == 1
    assert structured.extra["effective_height"] == 640
    assert structured.extra["effective_width"] == 640


def test_profile_cmd_rknn_requires_engine_path(tmp_path):
    model_path = tmp_path / "model.onnx"
    model_path.write_bytes(b"fake-onnx")

    with pytest.raises(typer.BadParameter, match="--engine-path is required"):
        profile_cmd(
            model_path=str(model_path),
            warmup=10,
            runs=100,
            batch=1,
            height=0,
            width=0,
            intra_threads=1,
            inter_threads=1,
            engine="rknn",
            precision="fp32",
            engine_path="",
            rknn_target="",
            device_name="",
            no_hash=True,
            output=str(tmp_path / "report.json"),
        )
