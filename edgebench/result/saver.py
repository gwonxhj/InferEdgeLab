from __future__ import annotations

import json
import os

from .schema import BenchmarkResult


def save_result(result: BenchmarkResult, out_dir: str = "results") -> str:
    os.makedirs(out_dir, exist_ok=True)

    filename = (
        f"{result.model}__{result.engine}__{result.device}__{result.precision}"
        f"__b{result.batch}__h{result.height}w{result.width}"
        f"__{result.timestamp}.json"
    )
    path = os.path.join(out_dir, filename)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
        f.write("\n")

    return path