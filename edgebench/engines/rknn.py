from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from edgebench.engines.base import EngineModelIO, EngineRuntimePaths, InferenceEngine


def _rknn_dim_to_optional_int(dim: Any) -> Optional[int]:
    if dim is None:
        return None
    try:
        value = int(dim)
    except (TypeError, ValueError):
        return None
    return value if value >= 0 else None


def _rknn_shape_to_model_shape(shape: Any) -> List[Optional[int]]:
    if shape is None:
        return []
    return [_rknn_dim_to_optional_int(dim) for dim in list(shape)]


def _rknn_dtype_to_numpy_dtype(dtype: Any) -> np.dtype:
    if isinstance(dtype, np.dtype):
        return dtype

    dtype_name = str(dtype).lower()
    if "float16" in dtype_name:
        return np.dtype(np.float16)
    if "float32" in dtype_name or dtype_name == "float":
        return np.dtype(np.float32)
    if "int8" in dtype_name:
        return np.dtype(np.int8)
    if "uint8" in dtype_name:
        return np.dtype(np.uint8)
    if "int32" in dtype_name:
        return np.dtype(np.int32)
    if "bool" in dtype_name:
        return np.dtype(np.bool_)

    try:
        return np.dtype(dtype)
    except (TypeError, ValueError):
        return np.dtype(np.float32)


class RknnEngine(InferenceEngine):
    name = "rknn"
    device = "npu"

    def __init__(self) -> None:
        self.inputs: List[EngineModelIO] = []
        self.outputs: List[str] = []
        self.runtime_paths = EngineRuntimePaths()

        self.rknn_module: Any = None
        self.runtime: Any = None
        self.runtime_target: Optional[str] = None

    @staticmethod
    def _missing_engine_path_error() -> RuntimeError:
        return RuntimeError(
            "RKNN profiling requires --engine-path to point to a compiled .rknn file."
        )

    @staticmethod
    def _unsupported_environment_error() -> RuntimeError:
        return RuntimeError(
            "RKNN runtime bindings are unavailable in this environment. "
            "Install rknn-toolkit-lite2 on the target Odroid/RK3588 environment to use the RKNN backend."
        )

    @staticmethod
    def _artifact_not_found_error(engine_path: str) -> RuntimeError:
        return RuntimeError(f"RKNN artifact was not found: {engine_path}")

    @staticmethod
    def _artifact_load_error(engine_path: str) -> RuntimeError:
        return RuntimeError(
            f"RKNN artifact load failed: {engine_path}. "
            "Check that the .rknn file is valid for the target RKNN runtime."
        )

    @staticmethod
    def _runtime_init_error(target: Optional[str]) -> RuntimeError:
        target_note = f" target={target}." if target else ""
        return RuntimeError(
            "RKNN runtime initialization failed."
            f"{target_note} Check that the runtime environment matches the target device."
        )

    @staticmethod
    def _metadata_error(engine_path: str) -> RuntimeError:
        return RuntimeError(
            f"RKNN IO metadata extraction failed: {engine_path}. "
            "Check that the RKNN model exposes valid input/output metadata."
        )

    @staticmethod
    def _execution_error(engine_path: str) -> RuntimeError:
        return RuntimeError(
            f"RKNN execution failed: {engine_path}. "
            "Check that the runtime is initialized and the dummy input shape matches the model."
        )

    def _load_runtime_bindings(self) -> None:
        try:
            from rknnlite.api import RKNNLite
        except ImportError as exc:
            raise self._unsupported_environment_error() from exc

        self.rknn_module = RKNNLite
        self.runtime = RKNNLite()

    def _load_rknn_artifact(self) -> None:
        engine_path = self.runtime_paths.runtime_artifact_path
        if not engine_path:
            raise self._missing_engine_path_error()

        artifact = Path(engine_path)
        if not artifact.is_file():
            raise self._artifact_not_found_error(engine_path)

        ret = self.runtime.load_rknn(str(artifact))
        if ret != 0:
            raise self._artifact_load_error(engine_path)

    def _init_runtime(self, target: Optional[str] = None) -> None:
        self.runtime_target = target
        ret = self.runtime.init_runtime(target=target) if target else self.runtime.init_runtime()
        if ret != 0:
            raise self._runtime_init_error(target)

    def _build_io_metadata(self) -> None:
        engine_path = self.runtime_paths.runtime_artifact_path or "unknown"

        try:
            raw_inputs = getattr(self.runtime, "get_inputs", lambda: None)()
            raw_outputs = getattr(self.runtime, "get_outputs", lambda: None)()
        except Exception as exc:
            raise self._metadata_error(engine_path) from exc

        if not raw_inputs:
            raise self._metadata_error(engine_path)

        inputs: List[EngineModelIO] = []
        for index, item in enumerate(raw_inputs):
            name = getattr(item, "name", None) or f"input_{index}"
            dtype = getattr(item, "dtype", "float32")
            shape = getattr(item, "shape", None)
            inputs.append(
                EngineModelIO(
                    name=name,
                    dtype=_rknn_dtype_to_numpy_dtype(dtype),
                    shape=_rknn_shape_to_model_shape(shape),
                )
            )

        outputs: List[str] = []
        if raw_outputs:
            for index, item in enumerate(raw_outputs):
                name = getattr(item, "name", None) or f"output_{index}"
                outputs.append(name)

        self.inputs = inputs
        self.outputs = outputs

    def load(self, model_path: str, **kwargs) -> None:
        self.runtime_paths.model_path = model_path
        self.runtime_paths.runtime_artifact_path = kwargs.get("engine_path")

        if not self.runtime_paths.runtime_artifact_path:
            raise self._missing_engine_path_error()

        target = kwargs.get("rknn_target")
        self.device = kwargs.get("device_name") or "npu"

        self._load_runtime_bindings()
        self._load_rknn_artifact()
        self._init_runtime(target=target)
        self._build_io_metadata()

    def make_dummy_inputs(
        self,
        batch_override: Optional[int] = None,
        height_override: Optional[int] = None,
        width_override: Optional[int] = None,
    ) -> Dict[str, Any]:
        if self.runtime is None or not self.inputs:
            raise RuntimeError("RKNN runtime is not ready. Call load() first.")

        feeds: Dict[str, Any] = {}
        for inp in self.inputs:
            shape = self._resolve_input_shape(
                inp,
                batch_override=batch_override,
                height_override=height_override,
                width_override=width_override,
            )
            if np.issubdtype(inp.dtype, np.floating):
                arr = np.random.random_sample(shape).astype(inp.dtype, copy=False)
            elif np.issubdtype(inp.dtype, np.integer):
                arr = np.random.randint(0, 10, size=shape, dtype=inp.dtype)
            elif np.issubdtype(inp.dtype, np.bool_):
                arr = np.random.randint(0, 2, size=shape).astype(inp.dtype, copy=False)
            else:
                arr = np.zeros(shape, dtype=inp.dtype)
            feeds[inp.name] = arr
        return feeds

    def run(self, feeds: Dict[str, Any]) -> List[Any]:
        engine_path = self.runtime_paths.runtime_artifact_path or "unknown"
        if self.runtime is None:
            raise RuntimeError("RKNN runtime is not ready. Call load() first.")

        if not self.inputs:
            raise RuntimeError("RKNN input metadata is empty. Call load() first.")

        ordered_inputs: List[np.ndarray] = []
        for inp in self.inputs:
            if inp.name not in feeds:
                raise RuntimeError(f"RKNN input feed is missing required input: {inp.name}")
            ordered_inputs.append(np.asarray(feeds[inp.name]))

        try:
            outputs = self.runtime.inference(inputs=ordered_inputs)
        except Exception as exc:
            raise self._execution_error(engine_path) from exc

        if outputs is None:
            raise self._execution_error(engine_path)

        return list(outputs)

    def close(self) -> None:
        if self.runtime is not None:
            try:
                self.runtime.release()
            except Exception:
                pass

        self.inputs = []
        self.outputs = []
        self.runtime = None
        self.rknn_module = None
        self.runtime_target = None
