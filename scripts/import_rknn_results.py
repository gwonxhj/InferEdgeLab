from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from inferedgelab.result.saver import save_result
from inferedgelab.result.schema import BenchmarkResult


CURATED_RESULTS_PATH = Path("benchmarks/rknn_curated_results.json")

REQUIRED_KEYS = {
    "model",
    "engine",
    "device",
    "precision",
    "batch",
    "height",
    "width",
    "mean_ms",
    "timestamp",
}


def load_curated_results(path: Path | None = None) -> list[dict[str, Any]]:
    if path is None:
        path = CURATED_RESULTS_PATH

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise SystemExit(f"Expected a JSON array in {path}")

    items: list[dict[str, Any]] = []
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            raise SystemExit(f"Each curated result must be an object: {path} (index={index})")

        missing = REQUIRED_KEYS - set(item.keys())
        if missing:
            raise SystemExit(
                f"Missing required keys in curated result at index {index}: {sorted(missing)}"
            )

        if str(item.get("engine")) != "rknn":
            raise SystemExit(f"Curated result at index {index} must use engine='rknn'")

        items.append(item)

    return items


def _to_optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def to_benchmark_result(item: dict[str, Any]) -> BenchmarkResult:
    return BenchmarkResult(
        model=str(item["model"]),
        engine=str(item["engine"]),
        device=str(item["device"]),
        precision=str(item["precision"]),
        batch=int(item["batch"]),
        height=int(item["height"]),
        width=int(item["width"]),
        mean_ms=_to_optional_float(item.get("mean_ms")),
        p99_ms=_to_optional_float(item.get("p99_ms")),
        timestamp=str(item["timestamp"]),
        source_report_path=item.get("source_report_path"),
        system=item.get("system"),
        run_config=item.get("run_config"),
        accuracy=item.get("accuracy"),
        extra=item.get("extra"),
    )


def main() -> None:
    items = load_curated_results()

    for item in items:
        result = to_benchmark_result(item)
        path = save_result(result)
        print(
            f"saved: {path} "
            f"({result.model} / {result.device} / {result.precision})"
        )


if __name__ == "__main__":
    main()