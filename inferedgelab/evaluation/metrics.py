from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol, Sequence

import numpy as np

from inferedgelab.evaluation.coco_eval import build_metric_payload
from inferedgelab.evaluation.pycocotools_backend import PycocotoolsUnavailableError
from inferedgelab.evaluation.pycocotools_backend import require_pycocotools


class MetricBackendError(RuntimeError):
    """Raised when a metric backend cannot evaluate the requested payload."""


class AveragePrecisionFn(Protocol):
    def __call__(
        self,
        predictions_by_image: Sequence[Any],
        ground_truths_by_image: Sequence[Any],
        *,
        num_classes: int,
        iou_threshold: float,
    ) -> float: ...


class PrecisionRecallFn(Protocol):
    def __call__(
        self,
        predictions_by_image: Sequence[Any],
        ground_truths_by_image: Sequence[Any],
        *,
        num_classes: int,
        iou_threshold: float,
    ) -> tuple[float, float, float]: ...


@dataclass(frozen=True)
class MetricBackendResult:
    metrics: dict[str, Any]
    notes: list[str]
    warnings: list[str]


class MetricBackend(Protocol):
    name: str

    def ensure_available(self) -> None: ...

    def evaluate(
        self,
        *,
        predictions_by_image: Sequence[Any],
        ground_truths_by_image: Sequence[Any],
        num_classes: int,
        iou_threshold: float,
        average_precision_fn: AveragePrecisionFn,
        precision_recall_fn: PrecisionRecallFn,
        mean_fn: Callable[[list[float]], float],
    ) -> MetricBackendResult: ...


class SimplifiedMap50Backend:
    name = "simplified"

    def ensure_available(self) -> None:
        return None

    def evaluate(
        self,
        *,
        predictions_by_image: Sequence[Any],
        ground_truths_by_image: Sequence[Any],
        num_classes: int,
        iou_threshold: float,
        average_precision_fn: AveragePrecisionFn,
        precision_recall_fn: PrecisionRecallFn,
        mean_fn: Callable[[list[float]], float],
    ) -> MetricBackendResult:
        precision, recall, f1_score = precision_recall_fn(
            predictions_by_image,
            ground_truths_by_image,
            num_classes=num_classes,
            iou_threshold=iou_threshold,
        )
        map50 = average_precision_fn(
            predictions_by_image,
            ground_truths_by_image,
            num_classes=num_classes,
            iou_threshold=0.5,
        )
        thresholds = [round(0.5 + 0.05 * index, 2) for index in range(10)]
        map50_95 = float(
            mean_fn(
                [
                    average_precision_fn(
                        predictions_by_image,
                        ground_truths_by_image,
                        num_classes=num_classes,
                        iou_threshold=float(threshold),
                    )
                    for threshold in thresholds
                ]
            )
        )
        return MetricBackendResult(
            metrics=build_metric_payload(
                backend=self.name,
                metrics={
                    "map50": float(map50),
                    "map50_95": map50_95,
                    "f1_score": float(f1_score),
                    "precision": float(precision),
                    "recall": float(recall),
                },
                note="lightweight simplified mAP50 implementation",
            ),
            notes=["Accuracy metrics backend: simplified lightweight mAP50."],
            warnings=[],
        )


class PycocotoolsBackend:
    name = "pycocotools"

    def ensure_available(self) -> None:
        try:
            require_pycocotools()
        except PycocotoolsUnavailableError as exc:
            raise MetricBackendError(str(exc)) from exc

    def evaluate(
        self,
        *,
        predictions_by_image: Sequence[Any],
        ground_truths_by_image: Sequence[Any],
        num_classes: int,
        iou_threshold: float,
        average_precision_fn: AveragePrecisionFn,
        precision_recall_fn: PrecisionRecallFn,
        mean_fn: Callable[[list[float]], float],
    ) -> MetricBackendResult:
        modules = require_pycocotools()
        coco_cls = modules["COCO"]
        cocoeval_cls = modules["COCOeval"]

        images = [{"id": index + 1} for index, _ in enumerate(ground_truths_by_image)]
        categories = [{"id": class_id, "name": str(class_id)} for class_id in range(num_classes)]
        annotations: list[dict[str, Any]] = []
        detections: list[dict[str, Any]] = []

        annotation_id = 1
        for image_index, ground_truths in enumerate(ground_truths_by_image, start=1):
            for ground_truth in ground_truths:
                box = _xyxy_to_xywh(getattr(ground_truth, "box"))
                annotations.append(
                    {
                        "id": annotation_id,
                        "image_id": image_index,
                        "category_id": int(getattr(ground_truth, "class_id")),
                        "bbox": box,
                        "area": box[2] * box[3],
                        "iscrowd": 0,
                    }
                )
                annotation_id += 1

        for image_index, predictions in enumerate(predictions_by_image, start=1):
            for prediction in predictions:
                detections.append(
                    {
                        "image_id": image_index,
                        "category_id": int(getattr(prediction, "class_id")),
                        "bbox": _xyxy_to_xywh(getattr(prediction, "box")),
                        "score": float(getattr(prediction, "confidence")),
                    }
                )

        if not annotations:
            return MetricBackendResult(
                metrics=build_metric_payload(
                    backend=self.name,
                    metrics={
                        "map50": 0.0,
                        "map50_95": 0.0,
                        "f1_score": 0.0,
                        "precision": 0.0,
                        "recall": 0.0,
                    },
                    warnings=["No COCO annotations were available for pycocotools evaluation."],
                ),
                notes=["Accuracy metrics backend: pycocotools."],
                warnings=["No COCO annotations were available for pycocotools evaluation."],
            )

        coco_gt = coco_cls()
        coco_gt.dataset = {
            "images": images,
            "annotations": annotations,
            "categories": categories,
            "info": {},
            "licenses": [],
        }
        coco_gt.createIndex()

        coco_dt = coco_gt.loadRes(detections) if detections else coco_gt.loadRes([])
        coco_eval = cocoeval_cls(coco_gt, coco_dt, "bbox")
        coco_eval.params.catIds = [item["id"] for item in categories]
        coco_eval.params.imgIds = [item["id"] for item in images]
        coco_eval.evaluate()
        coco_eval.accumulate()

        precision_values = coco_eval.eval["precision"]
        recall_values = coco_eval.eval["recall"]
        valid_precision = precision_values[precision_values > -1]
        valid_recall = recall_values[recall_values > -1]
        map50_95 = float(np.mean(valid_precision)) if valid_precision.size else 0.0
        map50_precision = precision_values[0]
        valid_map50_precision = map50_precision[map50_precision > -1]
        map50 = float(np.mean(valid_map50_precision)) if valid_map50_precision.size else 0.0
        recall = float(np.mean(valid_recall)) if valid_recall.size else 0.0
        precision = map50
        f1_score = 0.0
        if precision + recall > 0:
            f1_score = 2.0 * precision * recall / (precision + recall)

        return MetricBackendResult(
            metrics=build_metric_payload(
                backend=self.name,
                metrics={
                    "map50": map50,
                    "map50_95": map50_95,
                    "f1_score": float(f1_score),
                    "precision": precision,
                    "recall": recall,
                },
            ),
            notes=["Accuracy metrics backend: pycocotools official COCO evaluator."],
            warnings=[],
        )


def supported_metric_backends() -> tuple[str, ...]:
    return ("simplified", "pycocotools")


def get_metric_backend(name: str) -> MetricBackend:
    normalized = name.strip().lower()
    if normalized == "simplified":
        return SimplifiedMap50Backend()
    if normalized == "pycocotools":
        return PycocotoolsBackend()
    supported = ", ".join(supported_metric_backends())
    raise MetricBackendError(f"unsupported metric backend: {name}. Supported backends: {supported}")


def _xyxy_to_xywh(box: Sequence[float]) -> list[float]:
    x1, y1, x2, y2 = [float(value) for value in box]
    return [x1, y1, max(0.0, x2 - x1), max(0.0, y2 - y1)]
