from __future__ import annotations

from typing import Any, Dict, List, Optional

from edgebench.engines.base import EngineModelIO, InferenceEngine


class TensorRtEngine(InferenceEngine):
    name = "tensorrt"
    device = "gpu"

    def __init__(self) -> None:
        self.inputs: List[EngineModelIO] = []
        self.outputs: List[str] = []
        self.engine_path: Optional[str] = None
        self.model_path: Optional[str] = None

    @staticmethod
    def _missing_engine_path_error() -> RuntimeError:
        return RuntimeError(
            "TensorRT profiling requires --engine-path to point to a compiled TensorRT engine file."
        )

    @staticmethod
    def _unsupported_environment_error(engine_path: str) -> RuntimeError:
        return RuntimeError(
            "TensorRT backend requires a Jetson environment with the TensorRT runtime. "
            f"Received engine artifact: {engine_path}. "
            "The TensorRT runtime is not implemented for this EdgeBench environment yet."
        )

    def load(self, model_path: str, **kwargs) -> None:
        self.model_path = model_path
        self.engine_path = kwargs.get("engine_path")

        if not self.engine_path:
            raise self._missing_engine_path_error()

        raise self._unsupported_environment_error(self.engine_path)

    def make_dummy_inputs(
        self,
        batch_override: Optional[int] = None,
        height_override: Optional[int] = None,
        width_override: Optional[int] = None,
    ) -> Dict[str, Any]:
        if not self.engine_path:
            raise self._missing_engine_path_error()
        raise self._unsupported_environment_error(self.engine_path)

    def run(self, feeds: Dict[str, Any]) -> List[Any]:
        if not self.engine_path:
            raise self._missing_engine_path_error()
        raise self._unsupported_environment_error(self.engine_path)
