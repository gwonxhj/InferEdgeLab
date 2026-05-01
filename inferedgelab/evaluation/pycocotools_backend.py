from __future__ import annotations

import importlib
from typing import Any


class PycocotoolsUnavailableError(RuntimeError):
    """Raised when the optional pycocotools backend is requested but unavailable."""


def require_pycocotools() -> dict[str, Any]:
    try:
        coco_module = importlib.import_module("pycocotools.coco")
        cocoeval_module = importlib.import_module("pycocotools.cocoeval")
    except ImportError as exc:
        raise PycocotoolsUnavailableError(
            "pycocotools backend requested but pycocotools is not installed. "
            "Hint: pip install pycocotools"
        ) from exc

    return {
        "COCO": getattr(coco_module, "COCO"),
        "COCOeval": getattr(cocoeval_module, "COCOeval"),
    }
