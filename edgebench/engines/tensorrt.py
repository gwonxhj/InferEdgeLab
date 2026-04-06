from __future__ import annotations

from typing import Any, Dict, List, Optional
from pathlib import Path

import numpy as np

from edgebench.engines.base import EngineModelIO, EngineRuntimePaths, InferenceEngine


def _tensorrt_dim_to_optional_int(dim: Any) -> Optional[int]:
    if dim is None:
        return None

    try:
        dim_value = int(dim)
    except (TypeError, ValueError):
        return None

    return dim_value if dim_value >= 0 else None


def _tensorrt_shape_to_model_shape(shape: Any) -> List[Optional[int]]:
    return [_tensorrt_dim_to_optional_int(dim) for dim in shape]


def _tensorrt_dtype_to_numpy_dtype(dtype: Any) -> np.dtype:
    if isinstance(dtype, np.dtype):
        return dtype

    dtype_name = str(dtype).lower()
    if "float32" in dtype_name or dtype_name.endswith(".float") or dtype_name == "float":
        return np.dtype(np.float32)
    if "float16" in dtype_name or "half" in dtype_name:
        return np.dtype(np.float16)
    if dtype_name.endswith(".int8") or dtype_name == "int8":
        return np.dtype(np.int8)
    if dtype_name.endswith(".int32") or dtype_name == "int32":
        return np.dtype(np.int32)
    if dtype_name.endswith(".bool") or dtype_name == "bool":
        return np.dtype(np.bool_)

    try:
        return np.dtype(dtype)
    except (TypeError, ValueError):
        # Placeholder fallback until TensorRT dtype enum mapping is implemented.
        return np.dtype(np.float32)


def _make_engine_model_io(name: str, dtype: Any, shape: Any) -> EngineModelIO:
    return EngineModelIO(
        name=name,
        dtype=_tensorrt_dtype_to_numpy_dtype(dtype),
        shape=_tensorrt_shape_to_model_shape(shape),
    )


class TensorRtEngine(InferenceEngine):
    name = "tensorrt"
    device = "gpu"

    def __init__(self) -> None:
        self.inputs: List[EngineModelIO] = []
        self.outputs: List[str] = []
        self.runtime_paths = EngineRuntimePaths()

        # Jetson implementation placeholders:
        # - trt: lazily imported TensorRT Python module
        # - logger: TensorRT logger instance
        # - runtime: TensorRT runtime object
        # - engine: deserialized TensorRT engine
        # - context: execution context created from the engine
        # - stream: CUDA stream used for enqueue/execute
        # - binding_index_map: tensor/binding name to binding index mapping
        # - host_buffers/device_buffers: staged buffers for inputs/outputs
        self.trt: Any = None
        self.logger: Any = None
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
    

    @staticmethod
    def _engine_artifact_not_found_error(engine_path: str) -> RuntimeError:
        return RuntimeError(
            f"TensorRT engine artifact was not found: {engine_path}"
        )


    @staticmethod
    def _engine_artifact_read_error(engine_path: str) -> RuntimeError:
        return RuntimeError(
            f"TensorRT engine artifact could not be read: {engine_path}"
        )


    @staticmethod
    def _engine_deserialize_error(engine_path: str) -> RuntimeError:
        return RuntimeError(
            "TensorRT engine deserialization failed. "
            f"Received engine artifact: {engine_path}. "
            "Check that the .engine file matches the target Jetson/TensorRT environment."
        )

    @staticmethod
    def _execution_context_creation_error(engine_path: str) -> RuntimeError:
        return RuntimeError(
            "TensorRT execution context creation failed. "
            f"Received engine artifact: {engine_path}. "
            "Check that the deserialized engine is valid for the target Jetson/TensorRT environment."
        )

    @staticmethod
    def _metadata_extraction_error(engine_path: str) -> RuntimeError:
        return RuntimeError(
            "TensorRT metadata extraction failed. "
            f"Received engine artifact: {engine_path}. "
            "Check that the deserialized engine exposes valid IO metadata for this TensorRT environment."
        )


    def _load_runtime_bindings(self) -> None:
        """
        Jetson 환경에서 TensorRT Python runtime bindings를 import/prepare 한다.
        예:
        - import tensorrt as trt
        - logger/runtime 초기화
        """
        try:
            import tensorrt as trt
        except ImportError as exc:
            raise RuntimeError(
                "TensorRT Python bindings are unavailable in this environment. "
                "Install the Jetson-compatible TensorRT Python package to use the TensorRT backend."
            ) from exc

        try:
            logger = trt.Logger(trt.Logger.WARNING)
            runtime = trt.Runtime(logger)
        except Exception as exc:
            raise RuntimeError(
                "TensorRT runtime initialization failed after importing the Python bindings."
            ) from exc

        if runtime is None:
            raise RuntimeError(
                "TensorRT runtime initialization failed: trt.Runtime(...) returned None."
            )

        self.trt = trt
        self.logger = logger
        self.runtime = runtime

    def _deserialize_engine_artifact(self) -> None:
        """
        runtime_artifact_path(.engine)를 열고 TensorRT engine을 deserialize 한다.
        결과는 self.engine에 보관한다.
        """
        engine_path = self.runtime_paths.runtime_artifact_path
        if not engine_path:
            raise self._missing_engine_path_error()

        if self.runtime is None:
            raise RuntimeError(
                "TensorRT runtime is not initialized. "
                "Call _load_runtime_bindings() before deserializing the engine artifact."
            )

        engine_file = Path(engine_path)
        if not engine_file.is_file():
            raise self._engine_artifact_not_found_error(engine_path)

        try:
            engine_bytes = engine_file.read_bytes()
        except OSError as exc:
            raise self._engine_artifact_read_error(engine_path) from exc

        if not engine_bytes:
            raise self._engine_deserialize_error(engine_path)

        try:
            engine = self.runtime.deserialize_cuda_engine(engine_bytes)
        except Exception as exc:
            raise self._engine_deserialize_error(engine_path) from exc

        if engine is None:
            raise self._engine_deserialize_error(engine_path)

        self.engine = engine

    def _create_execution_context(self) -> None:
        """
        deserialized TensorRT engine에서 execution context를 생성하고
        필요 시 CUDA stream 준비를 연결한다.
        """
        if self.engine is None:
            raise RuntimeError(
                "TensorRT engine is not deserialized yet. "
                "Complete _deserialize_engine_artifact() before creating the execution context."
            )
        engine_path = self.runtime_paths.runtime_artifact_path or "unknown"

        try:
            context = self.engine.create_execution_context()
        except Exception as exc:
            raise self._execution_context_creation_error(engine_path) from exc

        if context is None:
            raise self._execution_context_creation_error(engine_path)

        self.context = context

    def _iter_engine_io_metadata(self):
        if self.engine is None:
            raise RuntimeError(
                "TensorRT engine is not deserialized yet. "
                "Complete _deserialize_engine_artifact() before extracting metadata."
            )

        trt = self.trt
        tensor_io_mode_input = getattr(getattr(trt, "TensorIOMode", None), "INPUT", None)

        if hasattr(self.engine, "num_io_tensors") and hasattr(self.engine, "get_tensor_name"):
            num_io_tensors = int(self.engine.num_io_tensors)
            for binding_index in range(num_io_tensors):
                name = self.engine.get_tensor_name(binding_index)
                dtype = self.engine.get_tensor_dtype(name)
                shape = self.engine.get_tensor_shape(name)
                tensor_mode = self.engine.get_tensor_mode(name)
                is_input = (
                    tensor_mode == tensor_io_mode_input
                    if tensor_io_mode_input is not None
                    else str(tensor_mode).upper().endswith("INPUT")
                )
                yield binding_index, name, dtype, shape, bool(is_input)
            return

        if hasattr(self.engine, "num_bindings") and hasattr(self.engine, "get_binding_name"):
            num_bindings = int(self.engine.num_bindings)
            for binding_index in range(num_bindings):
                name = self.engine.get_binding_name(binding_index)
                dtype = self.engine.get_binding_dtype(binding_index)
                shape = self.engine.get_binding_shape(binding_index)
                is_input = self.engine.binding_is_input(binding_index)
                yield binding_index, name, dtype, shape, bool(is_input)
            return

        raise RuntimeError(
            "TensorRT engine does not expose a supported IO metadata API. "
            "Expected either tensor-based or binding-based metadata accessors."
        )

    def _build_engine_io_metadata(self) -> None:
        """
        TensorRT binding/tensor metadata를 읽어 self.inputs / self.outputs를 구성한다.

        목표:
        - self.inputs: List[EngineModelIO]
        - self.outputs: List[str]
        - binding_index_map 채우기
        """
        if self.engine is None:
            raise RuntimeError(
                "TensorRT engine is not deserialized yet. "
                "Complete _deserialize_engine_artifact() before extracting metadata."
            )

        engine_path = self.runtime_paths.runtime_artifact_path or "unknown"

        try:
            binding_index_map: Dict[str, int] = {}
            inputs: List[EngineModelIO] = []
            outputs: List[str] = []
            entry_count = 0

            for binding_index, name, dtype, shape, is_input in self._iter_engine_io_metadata():
                entry_count += 1
                binding_index_map[name] = binding_index
                if is_input:
                    inputs.append(_make_engine_model_io(name, dtype, shape))
                else:
                    outputs.append(name)
        except RuntimeError as exc:
            message = str(exc)
            if "not deserialized yet" in message or "supported IO metadata API" in message:
                raise
            raise self._metadata_extraction_error(engine_path) from exc
        except Exception as exc:
            raise self._metadata_extraction_error(engine_path) from exc

        if entry_count == 0:
            raise RuntimeError(
                "TensorRT metadata extraction returned no IO entries. "
                f"Received engine artifact: {engine_path}."
            )
        if not inputs:
            raise RuntimeError(
                "TensorRT metadata extraction found no input tensors. "
                f"Received engine artifact: {engine_path}."
            )

        self.binding_index_map = binding_index_map
        self.inputs = inputs
        self.outputs = outputs

    def _allocate_runtime_buffers(self) -> None:
        """
        host/device buffer를 준비한다.
        초기 구현에서는 warmup/timed run 동안 재사용 가능한 구조를 목표로 한다.
        """
        raise self._unsupported_environment_error(self.runtime_paths.runtime_artifact_path or "unknown")

    def _make_dummy_inputs_impl(
        self,
        batch_override: Optional[int] = None,
        height_override: Optional[int] = None,
        width_override: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        self.inputs metadata를 기준으로 override 계약을 적용한
        host-side dummy input 생성을 담당한다.
        """
        # Future Jetson flow:
        # feeds: Dict[str, Any] = {}
        # for inp in self.inputs:
        #     shape = self._resolve_input_shape(
        #         inp,
        #         batch_override=batch_override,
        #         height_override=height_override,
        #         width_override=width_override,
        #     )
        #     # Allocate or populate a host-side buffer using inp.dtype and shape.
        #     feeds[inp.name] = ...
        # return feeds
        raise self._unsupported_environment_error(self.runtime_paths.runtime_artifact_path or "unknown")

    def _run_impl(self, feeds: Dict[str, Any]) -> List[Any]:
        """
        feeds를 TensorRT binding에 연결하고 실행한 뒤
        EdgeBench 공통 출력 형식(List[Any])으로 반환한다.
        """
        raise self._unsupported_environment_error(self.runtime_paths.runtime_artifact_path or "unknown")

    def _ensure_runtime_ready(self) -> None:
        """
        run() / make_dummy_inputs() 전에 runtime 필수 상태가 준비되었는지 확인한다.
        향후에는 self.engine, self.context, self.inputs 등을 검증하는 용도로 확장한다.
        """
        if not self.runtime_paths.runtime_artifact_path:
            raise self._missing_engine_path_error()
        if self.runtime is None:
            raise RuntimeError(
                "TensorRT runtime is not initialized. "
                "Call _load_runtime_bindings() before using the runtime."
            )
        if self.engine is None:
            raise RuntimeError(
                "TensorRT engine is not deserialized. "
                "Call _deserialize_engine_artifact() before using the runtime."
            )
        if self.context is None:
            raise RuntimeError(
                "TensorRT execution context is not created. "
                "Call _create_execution_context() before using the runtime."
            )


    def load(self, model_path: str, **kwargs) -> None:
        self.runtime_paths.model_path = model_path
        self.runtime_paths.runtime_artifact_path = kwargs.get("engine_path")

        if not self.runtime_paths.runtime_artifact_path:
            raise self._missing_engine_path_error()

        self._load_runtime_bindings()
        self._deserialize_engine_artifact()
        self._create_execution_context()
        self._build_engine_io_metadata()


    def make_dummy_inputs(
        self,
        batch_override: Optional[int] = None,
        height_override: Optional[int] = None,
        width_override: Optional[int] = None,
    ) -> Dict[str, Any]:
        self._ensure_runtime_ready()

        return self._make_dummy_inputs_impl(
            batch_override=batch_override,
            height_override=height_override,
            width_override=width_override,
        )


    def run(self, feeds: Dict[str, Any]) -> List[Any]:
        self._ensure_runtime_ready()

        return self._run_impl(feeds)
