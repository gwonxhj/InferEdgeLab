from __future__ import annotations

from importlib import import_module
from typing import Dict, Set

from inferedgelab.engines.base import InferenceEngine


_ENGINE_ALIASES: Dict[str, str] = {
    "ort": "onnxruntime",
    "onnxruntime_cpu": "onnxruntime",
    "onnxruntime": "onnxruntime",
    "trt": "tensorrt",
    "tensor_rt": "tensorrt",
    "tensorrt": "tensorrt",
    "rknn": "rknn",
    "rknnlite": "rknn",
    "rknn_lite": "rknn",
}

_ENGINE_TARGETS: Dict[str, str] = {
    "onnxruntime": "inferedgelab.engines.onnxruntime_cpu:OnnxRuntimeCpuEngine",
    "tensorrt": "inferedgelab.engines.tensorrt:TensorRtEngine",
    "rknn": "inferedgelab.engines.rknn:RknnEngine",
}


def _load_engine_class(target: str) -> type[InferenceEngine]:
    module_path, class_name = target.split(":", 1)
    module = import_module(module_path)
    engine_class = getattr(module, class_name)
    return engine_class


def _create_engine_instance(normalized_engine: str) -> InferenceEngine:
    target = _ENGINE_TARGETS[normalized_engine]
    engine_class = _load_engine_class(target)
    return engine_class()


_ENGINE_FACTORIES = {
    engine_name: (lambda engine_name=engine_name: _create_engine_instance(engine_name))
    for engine_name in _ENGINE_TARGETS
}


def normalize_engine_name(engine: str) -> str:
    value = str(engine or "").strip().lower()
    return _ENGINE_ALIASES.get(value, value)


def supported_engines() -> Set[str]:
    return set(_ENGINE_TARGETS.keys())


def supported_engines_display() -> str:
    return ", ".join(sorted(supported_engines()))


def create_engine(engine: str) -> InferenceEngine:
    normalized = normalize_engine_name(engine)
    factory = _ENGINE_FACTORIES.get(normalized)
    if factory is None:
        raise ValueError(
            f"지원하지 않는 engine입니다: {engine}. 현재 지원: {supported_engines_display()}"
        )
    return factory()
