from __future__ import annotations

import glob
import json
import os
from typing import Any, Dict, List


def load_result(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_results(pattern: str = "results/*.json") -> List[Dict[str, Any]]:
    paths = sorted(glob.glob(pattern))
    results: List[Dict[str, Any]] = []

    for path in paths:
        results.append(load_result(path))

    return results


def list_result_paths(pattern: str = "results/*.json") -> List[str]:
    """
    structured result 파일 경로들을 수정 시간 기준 오름차순으로 반환한다.
    """
    paths = glob.glob(pattern)
    return sorted(paths, key=os.path.getmtime)


def latest_result_paths(count: int = 2, pattern: str = "results/*.json") -> List[str]:
    """
    가장 최근 result 파일 N개 경로를 반환한다.
    """
    paths = list_result_paths(pattern)
    if len(paths) < count:
        raise ValueError(f"최소 {count}개의 result 파일이 필요합니다. 현재: {len(paths)}개")
    return paths[-count:]