from __future__ import annotations

from typing import Callable, Dict, Set

from edgebench.engines.base import InferenceEngine
from edgebench.engines.onnxruntime_cpu import OnnxRuntimeCpuEngine
from edgebench.engines.rknn import RknnEngine
from edgebench.engines.tensorrt import TensorRtEngine


EngineFactory = Callable[[], InferenceEngine]


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

_ENGINE_FACTORIES: Dict[str, EngineFactory] = {
    "onnxruntime": OnnxRuntimeCpuEngine,
    "tensorrt": TensorRtEngine,
    "rknn": RknnEngine,
}


def normalize_engine_name(engine: str) -> str:
    value = str(engine or "").strip().lower()
    return _ENGINE_ALIASES.get(value, value)


def supported_engines() -> Set[str]:
    return set(_ENGINE_FACTORIES.keys())


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
