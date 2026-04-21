from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional


@dataclass
class BenchmarkResult:
    model: str
    engine: str
    device: str
    precision: str

    batch: int
    height: int
    width: int

    mean_ms: Optional[float]
    p99_ms: Optional[float]

    timestamp: str
    source_report_path: Optional[str] = None

    system: Dict[str, Any] | None = None
    run_config: Dict[str, Any] | None = None
    accuracy: Dict[str, Any] | None = None
    extra: Dict[str, Any] | None = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def normalize_result_schema(data: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(data)

    system = normalized.get("system")
    if not isinstance(system, dict):
        system = {}
    normalized["system"] = dict(system)

    run_config = normalized.get("run_config")
    if not isinstance(run_config, dict):
        run_config = {}
    normalized["run_config"] = dict(run_config)

    accuracy = normalized.get("accuracy")
    if not isinstance(accuracy, dict):
        accuracy = {}
    normalized["accuracy"] = dict(accuracy)

    extra = normalized.get("extra")
    if not isinstance(extra, dict):
        extra = {}
    normalized["extra"] = dict(extra)

    precision = normalized.get("precision")
    if precision is None:
        precision = "fp32"
    normalized["precision"] = precision

    for key in ("requested_batch", "requested_height", "requested_width"):
        if normalized["run_config"].get(key) is None and normalized["extra"].get(key) is not None:
            normalized["run_config"][key] = normalized["extra"].get(key)

    if normalized["extra"].get("effective_batch") is None:
        normalized["extra"]["effective_batch"] = normalized.get("batch")
    if normalized["extra"].get("effective_height") is None:
        normalized["extra"]["effective_height"] = normalized.get("height")
    if normalized["extra"].get("effective_width") is None:
        normalized["extra"]["effective_width"] = normalized.get("width")

    if normalized["extra"].get("runtime_artifact_path") is None:
        load_kwargs = normalized["extra"].get("load_kwargs")
        if isinstance(load_kwargs, dict) and load_kwargs.get("engine_path") is not None:
            normalized["extra"]["runtime_artifact_path"] = load_kwargs.get("engine_path")

    return normalized
