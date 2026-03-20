from __future__ import annotations

import os
import platform
import sys
from typing import Any, Dict

def collect_system_snapshot() -> Dict[str, Any]:
    """
    현재 실행 환경의 기본 시스템 정보를 수집한다.

    용어:
    - os: 운영체제 이름 + 버전
    - python: 현재 파이썬 버전
    - machine: CPU 아키텍처 (예: arm64, x86_64)
    - cpu_count_logical: 논리 코어 수
    """
    return {
        "os": f"{platform.system()} {platform.release()}",
        "python": sys.version.split()[0],
        "machine": platform.machine(),
        "processor": platform.processor() or "unknown",
        "cpu_count_logical": os.cpu_count(),
    }