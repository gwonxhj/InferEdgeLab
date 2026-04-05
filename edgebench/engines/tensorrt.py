from __future__ import annotations

from typing import Any, Dict, List, Optional

from edgebench.engines.base import EngineModelIO, InferenceEngine


class TensorRtEngine(InferenceEngine):
    name = "tensorrt"
    device = "gpu"

    def __init__(self) -> None:
        self.inputs: List[EngineModelIO] = []
        self.outputs: List[str] = []

    @staticmethod
    def _unsupported_environment_error() -> RuntimeError:
        return RuntimeError(
            "TensorRT backend requires a Jetson environment with the TensorRT runtime. "
            "The TensorRT runtime is not implemented for this EdgeBench environment yet."
        )

    def load(self, model_path: str, **kwargs) -> None:
        raise self._unsupported_environment_error()

    def make_dummy_inputs(
        self,
        batch_override: Optional[int] = None,
        height_override: Optional[int] = None,
        width_override: Optional[int] = None,
    ) -> Dict[str, Any]:
        raise self._unsupported_environment_error()

    def run(self, feeds: Dict[str, Any]) -> List[Any]:
        raise self._unsupported_environment_error()
