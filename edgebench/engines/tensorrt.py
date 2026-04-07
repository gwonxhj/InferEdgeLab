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


def _tensorrt_shape_to_runtime_shape(shape: Any) -> List[int]:
    concrete_shape: List[int] = []

    for dim in shape:
        resolved_dim = _tensorrt_dim_to_optional_int(dim)
        concrete_shape.append(resolved_dim if resolved_dim is not None and resolved_dim > 0 else 1)

    return concrete_shape


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
        self.cuda: Any = None
        self.cuda_context: Any = None
        self.cuda_stream: Any = None
        self.cuda_stream_handle: int = 0
        self.binding_index_map: Dict[str, int] = {}
        self.host_buffers: Dict[str, Any] = {}
        self.device_buffers: Dict[str, Any] = {}
        self.binding_device_ptrs: List[int] = []


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

    @staticmethod
    def _runtime_buffer_allocation_error(engine_path: str) -> RuntimeError:
        return RuntimeError(
            "TensorRT runtime buffer allocation failed. "
            f"Received engine artifact: {engine_path}."
        )

    @staticmethod
    def _device_allocation_error(engine_path: str) -> RuntimeError:
        return RuntimeError(
            "TensorRT device allocation failed. "
            f"Received engine artifact: {engine_path}."
        )

    @staticmethod
    def _host_to_device_copy_error(engine_path: str) -> RuntimeError:
        return RuntimeError(
            "TensorRT host to device copy failed. "
            f"Received engine artifact: {engine_path}."
        )

    @staticmethod
    def _device_to_host_copy_error(engine_path: str) -> RuntimeError:
        return RuntimeError(
            "TensorRT device to host copy failed. "
            f"Received engine artifact: {engine_path}."
        )

    @staticmethod
    def _execution_error(engine_path: str) -> RuntimeError:
        return RuntimeError(
            "TensorRT execution failed. "
            f"Received engine artifact: {engine_path}."
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

    def _load_cuda_driver(self) -> Any:
        if self.cuda is not None and self.cuda_context is not None:
            return self.cuda

        try:
            from cuda.bindings import driver as cuda
        except ImportError as exc:
            raise RuntimeError(
                "CUDA driver bindings are unavailable in this environment. "
                "Install the Jetson-compatible cuda-python package to use TensorRT device allocation."
            ) from exc

        try:
            init_result = cuda.cuInit(0)
        except Exception as exc:
            raise RuntimeError(
                "CUDA driver initialization failed while preparing a CUDA context for TensorRT device allocation."
            ) from exc

        if isinstance(init_result, tuple):
            init_status = init_result[0]
        else:
            init_status = init_result

        if int(init_status) != 0:
            raise RuntimeError(
                "CUDA driver initialization failed while preparing a CUDA context for TensorRT device allocation."
            )

        try:
            device_result = cuda.cuDeviceGet(0)
        except Exception as exc:
            raise RuntimeError(
                "CUDA device discovery failed while preparing a CUDA context for TensorRT device allocation."
            ) from exc

        if not isinstance(device_result, tuple) or len(device_result) < 2:
            raise RuntimeError(
                "CUDA device discovery failed while preparing a CUDA context for TensorRT device allocation."
            )

        device_status, device = device_result[0], device_result[1]
        if int(device_status) != 0:
            raise RuntimeError(
                "CUDA device discovery failed while preparing a CUDA context for TensorRT device allocation."
            )

        try:
            context_result = cuda.cuDevicePrimaryCtxRetain(device)
        except Exception as exc:
            raise RuntimeError(
                "CUDA primary context acquisition failed while preparing TensorRT device allocation."
            ) from exc

        if not isinstance(context_result, tuple) or len(context_result) < 2:
            raise RuntimeError(
                "CUDA primary context acquisition failed while preparing TensorRT device allocation."
            )

        context_status, cuda_context = context_result[0], context_result[1]
        if int(context_status) != 0 or cuda_context is None:
            raise RuntimeError(
                "CUDA primary context acquisition failed while preparing TensorRT device allocation."
            )

        try:
            set_current_result = cuda.cuCtxSetCurrent(cuda_context)
        except Exception as exc:
            raise RuntimeError(
                "CUDA context activation failed while preparing TensorRT device allocation."
            ) from exc

        if isinstance(set_current_result, tuple):
            set_current_status = set_current_result[0]
        else:
            set_current_status = set_current_result

        if int(set_current_status) != 0:
            raise RuntimeError(
                "CUDA context activation failed while preparing TensorRT device allocation."
            )

        self.cuda = cuda
        self.cuda_context = cuda_context
        self._create_cuda_stream()
        return self.cuda
    
    def _create_cuda_stream(self) -> None:
        if self.cuda is None:
            raise RuntimeError(
                "CUDA driver is not initialized. "
                "Call _load_cuda_driver() before creating a CUDA stream."
            )

        if self.cuda_stream is not None and self.cuda_stream_handle:
            return

        try:
            stream_result = self.cuda.cuStreamCreate(0)
        except Exception as exc:
            raise RuntimeError(
                "CUDA stream creation failed while preparing TensorRT execution."
            ) from exc

        if not isinstance(stream_result, tuple) or len(stream_result) < 2:
            raise RuntimeError(
                "CUDA stream creation failed while preparing TensorRT execution."
            )

        stream_status, cuda_stream = stream_result[0], stream_result[1]
        if int(stream_status) != 0 or cuda_stream is None:
            raise RuntimeError(
                "CUDA stream creation failed while preparing TensorRT execution."
            )

        self.cuda_stream = cuda_stream
        self.cuda_stream_handle = int(cuda_stream)

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

    def _allocate_device_buffer(
        self,
        name: str,
        host_buffer: np.ndarray,
        binding_index: int,
    ) -> Dict[str, Any]:
        engine_path = self.runtime_paths.runtime_artifact_path or "unknown"
        cuda = self._load_cuda_driver()

        try:
            allocation_result = cuda.cuMemAlloc(int(host_buffer.nbytes))
            if not isinstance(allocation_result, tuple) or len(allocation_result) < 2:
                raise RuntimeError(
                    f"CUDA device allocation did not return an allocation handle for binding: {name}"
                )

            status, device_allocation = allocation_result[0], allocation_result[1]
            if int(status) != 0:
                raise RuntimeError(
                    f"CUDA device allocation returned status {int(status)} for binding: {name}"
                )

            device_ptr = int(device_allocation)
        except RuntimeError as exc:
            message = str(exc)
            if "CUDA " in message:
                raise
            raise self._device_allocation_error(engine_path) from exc
        except Exception as exc:
            raise self._device_allocation_error(engine_path) from exc

        return {
            "name": name,
            "dtype": host_buffer.dtype,
            "shape": [int(dim) for dim in host_buffer.shape],
            "nbytes": int(host_buffer.nbytes),
            "binding_index": binding_index,
            "device_allocation": device_allocation,
            "device_ptr": device_ptr,
        }

    def _allocate_runtime_buffers(self) -> None:
        """
        host/device buffer를 준비한다.
        초기 구현에서는 warmup/timed run 동안 재사용 가능한 구조를 목표로 한다.
        """
        engine_path = self.runtime_paths.runtime_artifact_path or "unknown"

        if self.engine is None:
            raise RuntimeError(
                "TensorRT engine is not deserialized yet. "
                "Complete _deserialize_engine_artifact() before allocating runtime buffers."
            )
        if self.context is None:
            raise RuntimeError(
                "TensorRT execution context is not created yet. "
                "Complete _create_execution_context() before allocating runtime buffers."
            )
        if not self.inputs:
            raise RuntimeError(
                "TensorRT input metadata is empty. "
                "Complete _build_engine_io_metadata() before allocating runtime buffers."
            )
        if not self.binding_index_map:
            raise RuntimeError(
                "TensorRT binding index map is empty. "
                "Complete _build_engine_io_metadata() before allocating runtime buffers."
            )

        try:
            host_buffers: Dict[str, Any] = {}
            device_buffers: Dict[str, Any] = {}
            metadata_entries = list(self._iter_engine_io_metadata())

            for inp in self.inputs:
                input_shape = self._resolve_input_shape(inp)
                host_buffer = np.empty(input_shape, dtype=inp.dtype)
                host_buffers[inp.name] = host_buffer
                device_buffers[inp.name] = self._allocate_device_buffer(
                    name=inp.name,
                    host_buffer=host_buffer,
                    binding_index=self.binding_index_map[inp.name],
                )

            output_metadata: Dict[str, Dict[str, Any]] = {}
            for binding_index, name, dtype, shape, is_input in metadata_entries:
                if is_input:
                    continue
                output_metadata[name] = {
                    "binding_index": binding_index,
                    "dtype": _tensorrt_dtype_to_numpy_dtype(dtype),
                    "shape": _tensorrt_shape_to_runtime_shape(shape),
                }

            missing_outputs = [output_name for output_name in self.outputs if output_name not in output_metadata]
            if missing_outputs:
                raise RuntimeError(
                    "TensorRT output metadata could not be matched for declared outputs: "
                    + ", ".join(missing_outputs)
                )

            for output_name in self.outputs:
                metadata = output_metadata[output_name]
                output_shape = metadata["shape"]
                output_dtype = metadata["dtype"]
                host_buffer = np.empty(output_shape, dtype=output_dtype)
                host_buffers[output_name] = host_buffer
                device_buffers[output_name] = self._allocate_device_buffer(
                    name=output_name,
                    host_buffer=host_buffer,
                    binding_index=metadata["binding_index"],
                )

            binding_device_ptrs = [0] * len(metadata_entries)
            for name, binding_index in self.binding_index_map.items():
                if binding_index < 0 or binding_index >= len(binding_device_ptrs):
                    raise RuntimeError(
                        f"TensorRT binding index is out of range while preparing device pointers: {name}"
                    )

                device_ptr = device_buffers.get(name, {}).get("device_ptr")
                if not isinstance(device_ptr, int) or device_ptr <= 0:
                    raise RuntimeError(
                        f"TensorRT binding device pointer could not be prepared for binding: {name}"
                    )

                binding_device_ptrs[binding_index] = device_ptr

            if any(device_ptr <= 0 for device_ptr in binding_device_ptrs):
                raise RuntimeError(
                    "TensorRT binding device pointers are incomplete after runtime buffer allocation."
                )
        except RuntimeError as exc:
            message = str(exc)
            if (
                "not deserialized yet" in message
                or "not created yet" in message
                or "metadata is empty" in message
                or "index map is empty" in message
                or "could not be matched for declared outputs" in message
                or "CUDA driver bindings are unavailable" in message
                or "CUDA driver initialization failed" in message
                or "TensorRT device allocation failed" in message
                or "binding index is out of range" in message
                or "binding device pointer could not be prepared" in message
                or "binding device pointers are incomplete" in message
            ):
                raise
            raise self._runtime_buffer_allocation_error(engine_path) from exc
        except Exception as exc:
            raise self._runtime_buffer_allocation_error(engine_path) from exc

        self.host_buffers = host_buffers
        self.device_buffers = device_buffers
        self.binding_device_ptrs = binding_device_ptrs

    def _copy_host_to_device(self, name: str, host_array: np.ndarray, device_ptr: int) -> None:
        engine_path = self.runtime_paths.runtime_artifact_path or "unknown"

        if self.cuda is None or self.cuda_stream is None or not self.cuda_stream_handle:
            raise self._host_to_device_copy_error(engine_path)

        try:
            memcpy_result = self.cuda.cuMemcpyHtoDAsync(
                device_ptr,
                int(host_array.ctypes.data),
                int(host_array.nbytes),
                self.cuda_stream,
            )
        except Exception as exc:
            raise self._host_to_device_copy_error(engine_path) from exc

        memcpy_status = memcpy_result[0] if isinstance(memcpy_result, tuple) else memcpy_result
        if int(memcpy_status) != 0:
            raise self._host_to_device_copy_error(engine_path)

    def _copy_device_to_host(self, name: str, device_ptr: int, host_array: np.ndarray) -> None:
        engine_path = self.runtime_paths.runtime_artifact_path or "unknown"
        if self.cuda is None or self.cuda_stream is None or not self.cuda_stream_handle:
            raise self._device_to_host_copy_error(engine_path)

        try:
            memcpy_result = self.cuda.cuMemcpyDtoHAsync(
                int(host_array.ctypes.data),
                device_ptr,
                int(host_array.nbytes),
                self.cuda_stream,
            )
        except Exception as exc:
            raise self._device_to_host_copy_error(engine_path) from exc

        memcpy_status = memcpy_result[0] if isinstance(memcpy_result, tuple) else memcpy_result
        if int(memcpy_status) != 0:
            raise self._device_to_host_copy_error(engine_path)

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
        feeds: Dict[str, Any] = {}

        for inp in self.inputs:
            shape = self._resolve_input_shape(
                inp,
                batch_override=batch_override,
                height_override=height_override,
                width_override=width_override,
            )
            host_buffer = self.host_buffers[inp.name]

            if list(host_buffer.shape) != shape:
                raise RuntimeError(
                    "TensorRT dummy input shape does not match the preallocated host buffer. "
                    f"Input: {inp.name}, resolved shape: {shape}, allocated shape: {list(host_buffer.shape)}."
                )

            if np.issubdtype(inp.dtype, np.floating):
                dummy_data = np.random.random_sample(shape).astype(inp.dtype, copy=False)
            elif np.issubdtype(inp.dtype, np.integer):
                dummy_data = np.random.randint(0, 10, size=shape, dtype=inp.dtype)
            elif np.issubdtype(inp.dtype, np.bool_):
                dummy_data = np.random.randint(0, 2, size=shape).astype(inp.dtype, copy=False)
            else:
                dummy_data = np.zeros(shape, dtype=inp.dtype)
            np.copyto(host_buffer, dummy_data)
            feeds[inp.name] = host_buffer

        return feeds

    def _run_impl(self, feeds: Dict[str, Any]) -> List[Any]:
        """
        feeds를 TensorRT binding에 연결하고 실행한 뒤
        EdgeBench 공통 출력 형식(List[Any])으로 반환한다.
        """
        engine_path = self.runtime_paths.runtime_artifact_path or "unknown"
        if self.cuda is None or self.cuda_stream is None or not self.cuda_stream_handle:
            raise self._execution_error(engine_path)

        for inp in self.inputs:
            if inp.name not in feeds:
                raise RuntimeError(f"TensorRT input feed is missing required input: {inp.name}")

            feed_array = np.asarray(feeds[inp.name])
            host_buffer = self.host_buffers[inp.name]
            expected_shape = list(host_buffer.shape)

            if list(feed_array.shape) != expected_shape:
                raise RuntimeError(
                    "TensorRT input shape does not match the preallocated host buffer. "
                    f"Input: {inp.name}, feed shape: {list(feed_array.shape)}, allocated shape: {expected_shape}."
                )

            if feed_array.dtype != inp.dtype:
                feed_array = feed_array.astype(inp.dtype, copy=False)

            np.copyto(host_buffer, feed_array)
            self._copy_host_to_device(
                inp.name,
                host_buffer,
                int(self.device_buffers[inp.name]["device_ptr"]),
            )

        try:
            if hasattr(self.context, "set_tensor_address"):
                for name, buffer_info in self.device_buffers.items():
                    set_result = self.context.set_tensor_address(name, int(buffer_info["device_ptr"]))
                    if set_result is False:
                        raise self._execution_error(engine_path)

                if hasattr(self.context, "execute_async_v3"):
                    execute_result = self.context.execute_async_v3(self.cuda_stream_handle)
                elif hasattr(self.context, "execute_v3"):
                    execute_result = self.context.execute_v3()
                else:
                    raise self._execution_error(engine_path)
            elif hasattr(self.context, "execute_async_v2"):
                execute_result = self.context.execute_async_v2(
                    self.binding_device_ptrs,
                    self.cuda_stream_handle,
                )
            elif hasattr(self.context, "execute_v2"):
                execute_result = self.context.execute_v2(self.binding_device_ptrs)
            else:
                raise self._execution_error(engine_path)
        except RuntimeError:
            raise
        except Exception as exc:
            raise self._execution_error(engine_path) from exc

        if execute_result is False:
            raise self._execution_error(engine_path)

        try:
            sync_result = self.cuda.cuStreamSynchronize(self.cuda_stream)
        except Exception as exc:
            raise self._execution_error(engine_path) from exc

        sync_status = sync_result[0] if isinstance(sync_result, tuple) else sync_result
        if int(sync_status) != 0:
            raise self._execution_error(engine_path)

        outputs: List[Any] = []
        for output_name in self.outputs:
            host_buffer = self.host_buffers[output_name]
            self._copy_device_to_host(
                output_name,
                int(self.device_buffers[output_name]["device_ptr"]),
                host_buffer,
            )
            outputs.append(host_buffer.copy())

        return outputs

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
        if not self.host_buffers:
            raise RuntimeError(
                "TensorRT host buffers are not allocated. "
                "Call _allocate_runtime_buffers() before using the runtime."
            )
        if not self.device_buffers:
            raise RuntimeError(
                "TensorRT device buffers are not allocated. "
                "Call _allocate_runtime_buffers() before using the runtime."
            )
        if not self.binding_device_ptrs:
            raise RuntimeError(
                "TensorRT binding device pointers are not prepared. "
                "Call _allocate_runtime_buffers() before using the runtime."
            )
        if self.cuda_stream is None or not self.cuda_stream_handle:
            raise RuntimeError(
                "TensorRT CUDA stream is not prepared. "
                "Call _load_cuda_driver() before using the runtime."
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
        self._allocate_runtime_buffers()


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
