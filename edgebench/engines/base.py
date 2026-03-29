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


class InferenceEngine(ABC):
    """
    EdgeBench inference engine 공통 인터페이스.
    """

    name: str
    device: str
    inputs: List[EngineModelIO]
    outputs: List[str]

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