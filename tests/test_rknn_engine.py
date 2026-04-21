from __future__ import annotations

import builtins
import importlib
import importlib.util
import sys
import types

import numpy as np
import pytest


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

from inferedgelab.engines.registry import create_engine, normalize_engine_name, supported_engines
from inferedgelab.engines.rknn import RknnEngine


class FakeTensorInfo:
    def __init__(self, name: str, dtype: str, shape: list[int | None]) -> None:
        self.name = name
        self.dtype = dtype
        self.shape = shape


class FakeRKNNLite:
    def __init__(self) -> None:
        self.loaded_path = ""
        self.released = False

    def load_rknn(self, path: str) -> int:
        self.loaded_path = path
        return 0

    def init_runtime(self) -> int:
        return 0

    def inference(self, inputs):
        return [np.asarray(inputs[0]).sum(axis=(1, 2, 3))]

    def release(self) -> None:
        self.released = True


class FakeDim:
    def __init__(self, dim_value: int | None) -> None:
        self.dim_value = dim_value

    def HasField(self, name: str) -> bool:
        return name == "dim_value" and self.dim_value is not None


class FakeTensorShape:
    def __init__(self, dims: list[int | None]) -> None:
        self.dim = [FakeDim(dim) for dim in dims]


class FakeTensorType:
    def __init__(self, elem_type: int, dims: list[int | None]) -> None:
        self.elem_type = elem_type
        self.shape = FakeTensorShape(dims)

    def HasField(self, name: str) -> bool:
        return name == "shape"


class FakeType:
    def __init__(self, elem_type: int, dims: list[int | None]) -> None:
        self.tensor_type = FakeTensorType(elem_type, dims)

    def HasField(self, name: str) -> bool:
        return name == "tensor_type"


class FakeValueInfo:
    def __init__(self, name: str, elem_type: int, dims: list[int | None]) -> None:
        self.name = name
        self.type = FakeType(elem_type, dims)


class FakeGraph:
    def __init__(self) -> None:
        onnx_module = sys.modules["onnx"]
        self.input = [
            FakeValueInfo("images", onnx_module.TensorProto.FLOAT, [None, 3, None, None]),
        ]
        self.output = [
            FakeValueInfo("output0", onnx_module.TensorProto.FLOAT, [1, 1000]),
        ]


class FakeOnnxModel:
    def __init__(self) -> None:
        self.graph = FakeGraph()


def test_rknn_alias_normalize():
    assert normalize_engine_name("rknn") == "rknn"
    assert normalize_engine_name("rknnlite") == "rknn"
    assert normalize_engine_name("rknn_lite") == "rknn"
    assert "rknn" in supported_engines()


def test_create_engine_rknn():
    engine = create_engine("rknn")

    assert isinstance(engine, RknnEngine)
    assert engine.name == "rknn"
    assert engine.device == "npu"


def test_registry_import_does_not_require_onnxruntime_backend_import(monkeypatch):
    original_import_module = importlib.import_module

    def fake_import_module(name: str, package: str | None = None):
        if name == "inferedgelab.engines.onnxruntime_cpu":
            raise AssertionError("onnxruntime backend should not be imported during registry import")
        return original_import_module(name, package)

    monkeypatch.setattr(importlib, "import_module", fake_import_module)
    sys.modules.pop("inferedgelab.engines.registry", None)

    registry = importlib.import_module("inferedgelab.engines.registry")

    assert registry.normalize_engine_name("rknn") == "rknn"
    assert "rknn" in registry.supported_engines()


def test_create_engine_rknn_succeeds_without_onnxruntime_dependency(monkeypatch):
    original_import_module = importlib.import_module

    def fake_import_module(name: str, package: str | None = None):
        if name == "inferedgelab.engines.onnxruntime_cpu":
            raise ImportError("onnxruntime is unavailable")
        return original_import_module(name, package)

    monkeypatch.setattr(importlib, "import_module", fake_import_module)
    sys.modules.pop("inferedgelab.engines.registry", None)
    registry = importlib.import_module("inferedgelab.engines.registry")

    engine = registry.create_engine("rknn")

    assert isinstance(engine, RknnEngine)
    assert engine.name == "rknn"
    assert engine.device == "npu"


def test_rknn_load_requires_engine_path():
    engine = RknnEngine()

    with pytest.raises(RuntimeError, match="--engine-path"):
        engine.load("models/yolov8n.onnx")


def test_rknn_missing_runtime_binding_raises_clear_runtime_error(tmp_path, monkeypatch):
    artifact = tmp_path / "model.rknn"
    artifact.write_bytes(b"fake-rknn")
    engine = RknnEngine()
    original_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "rknnlite.api" or name == "rknnlite":
            raise ImportError("rknnlite is not installed")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(RuntimeError, match="RKNN runtime bindings are unavailable"):
        engine.load("models/yolov8n.onnx", engine_path=str(artifact))


def test_rknn_engine_smoke_shape_and_inference(tmp_path, monkeypatch):
    model_path = tmp_path / "model.onnx"
    artifact = tmp_path / "model.rknn"
    model_path.write_bytes(b"fake-onnx")
    artifact.write_bytes(b"fake-rknn")

    rknnlite_module = types.ModuleType("rknnlite")
    rknnlite_api_module = types.ModuleType("rknnlite.api")
    rknnlite_api_module.RKNNLite = FakeRKNNLite
    rknnlite_module.api = rknnlite_api_module

    monkeypatch.setitem(sys.modules, "rknnlite", rknnlite_module)
    monkeypatch.setitem(sys.modules, "rknnlite.api", rknnlite_api_module)
    monkeypatch.setattr(sys.modules["onnx"], "load", lambda path: FakeOnnxModel(), raising=False)

    engine = RknnEngine()
    engine.load(str(model_path), engine_path=str(artifact))

    feeds = engine.make_dummy_inputs(batch_override=2, height_override=320, width_override=320)
    outputs = engine.run(feeds)

    assert engine.runtime_paths.model_path == str(model_path)
    assert engine.runtime_paths.runtime_artifact_path == str(artifact)
    assert engine.outputs == ["output0"]
    assert list(feeds.keys()) == ["images"]
    assert feeds["images"].shape == (2, 3, 320, 320)
    assert feeds["images"].dtype == np.float32
    assert len(outputs) == 1
