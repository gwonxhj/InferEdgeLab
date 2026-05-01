from __future__ import annotations

import math
from typing import Any, Sequence


def validate_detection_structure(
    detections_by_image: Sequence[Sequence[Any]],
    *,
    num_classes: int | None = None,
) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    detection_count = 0

    for image_index, detections in enumerate(detections_by_image):
        for detection_index, detection in enumerate(detections):
            detection_count += 1
            class_id = int(getattr(detection, "class_id", -1))
            confidence = float(getattr(detection, "confidence", float("nan")))
            box = tuple(float(value) for value in getattr(detection, "box", ()))

            if num_classes is not None and not 0 <= class_id < num_classes:
                issues.append(
                    _issue(image_index, detection_index, "class_id_out_of_range", class_id)
                )
            if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
                issues.append(_issue(image_index, detection_index, "score_out_of_range", confidence))
            if len(box) != 4:
                issues.append(_issue(image_index, detection_index, "bbox_not_xywh", list(box)))
                continue
            if not all(math.isfinite(value) for value in box):
                issues.append(_issue(image_index, detection_index, "bbox_non_finite", list(box)))
            if box[2] <= 0.0 or box[3] <= 0.0:
                issues.append(_issue(image_index, detection_index, "bbox_non_positive_size", list(box)))

    return {
        "status": "passed" if not issues else "failed",
        "checked": {
            "image_count": len(detections_by_image),
            "detection_count": detection_count,
            "num_classes": num_classes,
        },
        "issues": issues,
    }


def validate_shape(actual_shape: Sequence[int], expected_shape: Sequence[int]) -> dict[str, Any]:
    actual = [int(value) for value in actual_shape]
    expected = [int(value) for value in expected_shape]
    return {
        "status": "passed" if actual == expected else "mismatch",
        "actual_shape": actual,
        "expected_shape": expected,
    }


def _issue(image_index: int, detection_index: int, code: str, value: Any) -> dict[str, Any]:
    return {
        "image_index": image_index,
        "detection_index": detection_index,
        "code": code,
        "value": value,
    }
