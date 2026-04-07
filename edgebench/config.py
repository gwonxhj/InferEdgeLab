from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 fallback
    import tomli as tomllib


DEFAULT_COMPARE_THRESHOLDS: Dict[str, float] = {
    "latency_improve_threshold": -3.0,
    "latency_regress_threshold": 3.0,
    "accuracy_improve_threshold": 0.20,
    "accuracy_regress_threshold": -0.20,
    "tradeoff_caution_threshold": -0.30,
    "tradeoff_risky_threshold": -1.00,
    "tradeoff_severe_threshold": -2.00,
}


def _project_root_from_here() -> Path:
    return Path(__file__).resolve().parent.parent


def load_pyproject_compare_config(pyproject_path: str = "pyproject.toml") -> Dict[str, float]:
    path = Path(pyproject_path)

    if not path.is_absolute():
        path = _project_root_from_here() / pyproject_path

    if not path.is_file():
        return dict(DEFAULT_COMPARE_THRESHOLDS)

    with open(path, "rb") as f:
        data = tomllib.load(f)

    compare_cfg = (
        data.get("tool", {})
        .get("edgebench", {})
        .get("compare", {})
    )

    resolved = dict(DEFAULT_COMPARE_THRESHOLDS)

    for key in DEFAULT_COMPARE_THRESHOLDS:
        value = compare_cfg.get(key)
        if value is None:
            continue
        resolved[key] = float(value)

    return resolved


def resolve_compare_thresholds(
    *,
    latency_improve_threshold: float | None = None,
    latency_regress_threshold: float | None = None,
    accuracy_improve_threshold: float | None = None,
    accuracy_regress_threshold: float | None = None,
    tradeoff_caution_threshold: float | None = None,
    tradeoff_risky_threshold: float | None = None,
    tradeoff_severe_threshold: float | None = None,
    pyproject_path: str = "pyproject.toml",
) -> Dict[str, float]:
    resolved = load_pyproject_compare_config(pyproject_path=pyproject_path)

    overrides = {
        "latency_improve_threshold": latency_improve_threshold,
        "latency_regress_threshold": latency_regress_threshold,
        "accuracy_improve_threshold": accuracy_improve_threshold,
        "accuracy_regress_threshold": accuracy_regress_threshold,
        "tradeoff_caution_threshold": tradeoff_caution_threshold,
        "tradeoff_risky_threshold": tradeoff_risky_threshold,
        "tradeoff_severe_threshold": tradeoff_severe_threshold,
    }

    for key, value in overrides.items():
        if value is not None:
            resolved[key] = float(value)

    return resolved