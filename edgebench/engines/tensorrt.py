from __future__ import annotations

from typing import Any, Dict, List, Optional

from edgebench.engines.base import EngineModelIO, EngineRuntimePaths, InferenceEngine


class TensorRtEngine(InferenceEngine):
    name = "tensorrt"
    device = "gpu"

    def __init__(self) -> None:
        self.inputs: List[EngineModelIO] = []
        self.outputs: List[str] = []
        self.runtime_paths = EngineRuntimePaths()

        # Jetson implementation placeholders:
        # - runtime: TensorRT runtime object
        # - engine: deserialized TensorRT engine
        # - context: execution context created from the engine
        # - stream: CUDA stream used for enqueue/execute
        # - binding_index_map: tensor/binding name to binding index mapping
        # - host_buffers/device_buffers: staged buffers for inputs/outputs
        self.runtime: Any = None
        self.engine: Any = None
        self.context: Any = None
        self.stream: Any = None
        self.binding_index_map: Dict[str, int] = {}
        self.host_buffers: Dict[str, Any] = {}
        self.device_buffers: Dict[str, Any] = {}

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
        self.runtime_paths.model_path = model_path
        self.runtime_paths.runtime_artifact_path = kwargs.get("engine_path")

        if not self.runtime_paths.runtime_artifact_path:
            raise self._missing_engine_path_error()

        # TODO(jetson): Replace this placeholder with Jetson-specific TensorRT runtime setup.
        # Expected future flow:
        # 1. Import TensorRT runtime bindings in the Jetson environment.
        # 2. Open engine_path and deserialize the compiled engine artifact.
        # 3. Create self.runtime, self.engine, and self.context.
        # 4. Build binding_index_map and allocate/reuse host/device buffers as needed.
        # 5. Inspect TensorRT bindings / tensor metadata and populate self.inputs/self.outputs.
        # 6. Create or attach a CUDA stream for repeated profile runs.
        # 7. Warmup and timed runs should reuse the same context/buffers where possible.
        # 8. Preserve model_path for provenance/reporting and engine_path for runtime execution.
        # 9. Keep the current profile command contract unchanged:
        #    - model_path: ONNX source path
        #    - engine_path: compiled TensorRT runtime artifact
        raise self._unsupported_environment_error(self.runtime_paths.runtime_artifact_path)

    def make_dummy_inputs(
        self,
        batch_override: Optional[int] = None,
        height_override: Optional[int] = None,
        width_override: Optional[int] = None,
    ) -> Dict[str, Any]:
        if not self.runtime_paths.runtime_artifact_path:
            raise self._missing_engine_path_error()
        # TODO(jetson): Generate placeholder host input buffers that match TensorRT binding specs.
        # This helper should continue to support the existing profile flow, even if actual device
        # buffers are allocated later during runtime execution. Dynamic shape handling should be
        # derived from binding metadata plus batch/height/width overrides from the profile command.
        raise self._unsupported_environment_error(self.runtime_paths.runtime_artifact_path)

    def run(self, feeds: Dict[str, Any]) -> List[Any]:
        if not self.runtime_paths.runtime_artifact_path:
            raise self._missing_engine_path_error()
        # TODO(jetson): Map feeds to TensorRT bindings, copy host->device as needed,
        # execute the TensorRT context on the configured stream, synchronize, collect outputs,
        # and return them in EdgeBench format.
        raise self._unsupported_environment_error(self.runtime_paths.runtime_artifact_path)
