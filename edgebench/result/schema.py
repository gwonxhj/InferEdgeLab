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