from __future__ import annotations

from typing import Any, Dict, List, Optional

from edgebench.engines.base import EngineModelIO, InferenceEngine


class TensorRtEngine(InferenceEngine):
    name = "tensorrt"
    device = "gpu"

    def __init__(self) -> None:
        self.inputs: List[EngineModelIO] = []
        self.outputs: List[str] = []
        # model_path stays as the original ONNX source path for analysis/reporting.
        self.engine_path: Optional[str] = None
        # engine_path is the compiled TensorRT engine artifact used for runtime.
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

        # TODO(jetson): Replace this placeholder with Jetson-specific TensorRT runtime setup.
        # Expected future flow:
        # 1. Deserialize the compiled engine from engine_path.
        # 2. Create TensorRT execution context and CUDA bindings.
        # 3. Populate self.inputs/self.outputs from the runtime engine metadata.
        # 4. Keep model_path for provenance/reporting, not runtime execution.
        raise self._unsupported_environment_error(self.engine_path)

    def make_dummy_inputs(
        self,
        batch_override: Optional[int] = None,
        height_override: Optional[int] = None,
        width_override: Optional[int] = None,
    ) -> Dict[str, Any]:
        if not self.engine_path:
            raise self._missing_engine_path_error()
        # TODO(jetson): Generate host/device input buffers that match the TensorRT bindings.
        raise self._unsupported_environment_error(self.engine_path)

    def run(self, feeds: Dict[str, Any]) -> List[Any]:
        if not self.engine_path:
            raise self._missing_engine_path_error()
        # TODO(jetson): Copy feeds into bindings, execute the context, and return outputs.
        raise self._unsupported_environment_error(self.engine_path)
