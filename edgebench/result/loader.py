from __future__ import annotations

import glob
import json
from typing import Any, Dict, List

def load_result(path: str) -> Dict[str, Any]:
    """
    구조화된 benchmark result JSON 하나를 읽는다.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
    
def load_results(pattern: str = "results/*.json") -> List[Dict[str, Any]]:
    """
    glob 패턴에 맞는 result JSON 여러 개를 읽는다.
    """
    paths = sorted(glob.glob(pattern))
    results: List[Dict[str, Any]] = []

    for path in paths:
        results.append(load_result(path))

    return results