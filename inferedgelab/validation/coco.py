from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CocoGroundTruth:
    image_id: int
    file_name: str
    class_id: int
    box: tuple[float, float, float, float]


def load_coco_ground_truths(path: str) -> dict[str, list[CocoGroundTruth]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("COCO annotations must be a JSON object.")

    images = payload.get("images")
    annotations = payload.get("annotations")
    categories = payload.get("categories", [])
    if not isinstance(images, list) or not isinstance(annotations, list):
        raise ValueError("COCO annotations require images and annotations arrays.")

    image_by_id: dict[int, str] = {}
    for image in images:
        if not isinstance(image, dict):
            continue
        image_id = int(image["id"])
        image_by_id[image_id] = str(image["file_name"])

    category_to_class = _category_to_zero_based_class(categories)
    result: dict[str, list[CocoGroundTruth]] = {}
    for annotation in annotations:
        item = _parse_annotation(annotation, image_by_id=image_by_id, category_to_class=category_to_class)
        if item is None:
            continue
        result.setdefault(Path(item.file_name).name, []).append(item)
    return result


def _category_to_zero_based_class(categories: Any) -> dict[int, int]:
    if not isinstance(categories, list) or not categories:
        return {}
    ids = sorted(int(category["id"]) for category in categories if isinstance(category, dict) and "id" in category)
    return {category_id: index for index, category_id in enumerate(ids)}


def _parse_annotation(
    annotation: Any,
    *,
    image_by_id: dict[int, str],
    category_to_class: dict[int, int],
) -> CocoGroundTruth | None:
    if not isinstance(annotation, dict):
        return None
    if annotation.get("iscrowd", 0):
        return None

    image_id = int(annotation["image_id"])
    file_name = image_by_id.get(image_id)
    if not file_name:
        return None

    bbox = annotation.get("bbox")
    if not isinstance(bbox, list) or len(bbox) != 4:
        return None
    x, y, width, height = (float(value) for value in bbox)
    category_id = int(annotation["category_id"])
    class_id = category_to_class.get(category_id, category_id - 1)
    return CocoGroundTruth(
        image_id=image_id,
        file_name=file_name,
        class_id=class_id,
        box=(x + width / 2.0, y + height / 2.0, width, height),
    )
