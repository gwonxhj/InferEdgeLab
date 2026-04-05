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
