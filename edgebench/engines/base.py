from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np


@dataclass
class EngineModelIO:
    name: str
    dtype: np.dtype
    shape: List[Optional[int]]


@dataclass
class EngineRuntimePaths:
    model_path: Optional[str] = None
    runtime_artifact_path: Optional[str] = None


def resolve_engine_io_shape(
    io_spec: EngineModelIO,
    batch_override: Optional[int] = None,
    height_override: Optional[int] = None,
    width_override: Optional[int] = None,
) -> List[int]:
    """
    EngineModelIO.shape와 override 값을 바탕으로 실제 입력 shape를 계산한다.

    규칙:
    - None 차원은 override가 있으면 override 사용
    - batch axis(0)는 batch_override 우선
    - image-like shape 기준 axis 2/3에는 height/width override 반영
    - 나머지 unknown dim은 1로 채움
    - 고정된 dim_value는 그대로 사용
    """
    resolved: List[int] = []

    for i, dim in enumerate(io_spec.shape):
        if dim is None:
            if i == 0:
                resolved.append(int(batch_override) if batch_override is not None else 1)
            elif i == 2 and height_override is not None:
                resolved.append(int(height_override))
            elif i == 3 and width_override is not None:
                resolved.append(int(width_override))
            else:
                resolved.append(1)
        else:
            resolved.append(int(dim))

    return resolved


class InferenceEngine(ABC):
    """
    EdgeBench inference engine 공통 인터페이스.

    - model_path: 분석/리포팅에 사용하는 원본 모델 경로
    - runtime_artifact_path: 실제 runtime execution에 사용하는 artifact 경로
      (예: TensorRT .engine)
    """

    name: str
    device: str
    inputs: List[EngineModelIO]
    outputs: List[str]
    runtime_paths: Optional[EngineRuntimePaths]

    @abstractmethod
    def load(self, model_path: str, **kwargs) -> None:
        raise NotImplementedError

    def _resolve_input_shape(
        self,
        io_spec: EngineModelIO,
        batch_override: Optional[int] = None,
        height_override: Optional[int] = None,
        width_override: Optional[int] = None,
    ) -> List[int]:
        return resolve_engine_io_shape(
            io_spec,
            batch_override=batch_override,
            height_override=height_override,
            width_override=width_override,
        )

    @abstractmethod
    def make_dummy_inputs(
        self,
        batch_override: Optional[int] = None,
        height_override: Optional[int] = None,
        width_override: Optional[int] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def run(self, feeds: Dict[str, Any]) -> List[Any]:
        raise NotImplementedError
