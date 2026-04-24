from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import numpy as np

from inferedgelab.engines.base import EngineModelIO
from inferedgelab.engines.registry import create_engine, normalize_engine_name


@dataclass
class Detection:
    class_id: int
    confidence: float
    box: tuple[float, float, float, float]


@dataclass
class GroundTruth:
    class_id: int
    box: tuple[float, float, float, float]


@dataclass
class DetectionEvalResult:
    task: str
    engine: str
    device: str
    sample_count: int
    metrics: Dict[str, float]
    notes: List[str]
    model_input: Dict[str, Any]
    actual_input_shape: List[int]
    dataset: Dict[str, Any]
    evaluation_config: Dict[str, Any]
    extra: Dict[str, Any]


def _require_cv2():
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError(
            "OpenCV (cv2) is required for detection evaluation but is not available in this environment. "
            "Install OpenCV in the runtime environment before using evaluate-detection."
        ) from exc
    return cv2


def _xywh_to_xyxy(box: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    x_center, y_center, width, height = box
    half_w = width / 2.0
    half_h = height / 2.0
    return (
        x_center - half_w,
        y_center - half_h,
        x_center + half_w,
        y_center + half_h,
    )


def _xyxy_to_xywh(box: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    x1, y1, x2, y2 = box
    width = max(0.0, x2 - x1)
    height = max(0.0, y2 - y1)
    return (
        x1 + width / 2.0,
        y1 + height / 2.0,
        width,
        height,
    )


def _clip_xyxy(
    box: tuple[float, float, float, float],
    original_width: int,
    original_height: int,
) -> tuple[float, float, float, float]:
    x1, y1, x2, y2 = box
    return (
        min(max(x1, 0.0), float(original_width)),
        min(max(y1, 0.0), float(original_height)),
        min(max(x2, 0.0), float(original_width)),
        min(max(y2, 0.0), float(original_height)),
    )


def letterbox(image: np.ndarray, target_size: int = 640, use_rgb: bool = True) -> tuple[np.ndarray, float, float, float]:
    cv2 = _require_cv2()

    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("letterbox expects a BGR image with shape HxWx3.")

    original_height, original_width = image.shape[:2]
    scale = min(target_size / float(original_width), target_size / float(original_height))
    resized_width = max(1, int(round(original_width * scale)))
    resized_height = max(1, int(round(original_height * scale)))

    resized = cv2.resize(image, (resized_width, resized_height), interpolation=cv2.INTER_LINEAR)
    if use_rgb:
        resized = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

    canvas = np.full((target_size, target_size, 3), 114, dtype=resized.dtype)
    pad_w = (target_size - resized_width) / 2.0
    pad_h = (target_size - resized_height) / 2.0
    left = int(round(pad_w))
    top = int(round(pad_h))
    canvas[top : top + resized_height, left : left + resized_width] = resized
    return canvas, scale, float(left), float(top)


def scale_coords(
    box: tuple[float, float, float, float],
    scale: float,
    pad_w: float,
    pad_h: float,
    original_width: int,
    original_height: int,
) -> tuple[float, float, float, float]:
    if scale <= 0:
        raise ValueError("scale must be positive.")

    x1, y1, x2, y2 = _xywh_to_xyxy(box)
    scaled_box = (
        (x1 - pad_w) / scale,
        (y1 - pad_h) / scale,
        (x2 - pad_w) / scale,
        (y2 - pad_h) / scale,
    )
    clipped = _clip_xyxy(scaled_box, original_width=original_width, original_height=original_height)
    return _xyxy_to_xywh(clipped)


def calculate_iou(
    box_a: tuple[float, float, float, float],
    box_b: tuple[float, float, float, float],
) -> float:
    ax1, ay1, ax2, ay2 = _xywh_to_xyxy(box_a)
    bx1, by1, bx2, by2 = _xywh_to_xyxy(box_b)

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h

    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union_area = area_a + area_b - inter_area
    if union_area <= 0.0:
        return 0.0
    return inter_area / union_area


def nms(detections: Sequence[Detection], iou_threshold: float) -> list[Detection]:
    kept: list[Detection] = []

    for class_id in sorted({det.class_id for det in detections}):
        class_detections = sorted(
            (det for det in detections if det.class_id == class_id),
            key=lambda det: det.confidence,
            reverse=True,
        )

        while class_detections:
            current = class_detections.pop(0)
            kept.append(current)
            class_detections = [
                candidate
                for candidate in class_detections
                if calculate_iou(current.box, candidate.box) < iou_threshold
            ]

    return kept


def load_ground_truth(label_path: str, image_width: int, image_height: int) -> list[GroundTruth]:
    label_file = Path(label_path)
    if not label_file.exists():
        return []

    ground_truths: list[GroundTruth] = []
    with open(label_file, "r", encoding="utf-8") as handle:
        for line in handle:
            parts = line.strip().split()
            if not parts:
                continue
            if len(parts) != 5:
                raise ValueError(f"Invalid YOLO label line: {line.strip()}")

            class_id = int(parts[0])
            x_center = float(parts[1]) * image_width
            y_center = float(parts[2]) * image_height
            width = float(parts[3]) * image_width
            height = float(parts[4]) * image_height
            ground_truths.append(
                GroundTruth(
                    class_id=class_id,
                    box=(x_center, y_center, width, height),
                )
            )

    return ground_truths


def get_image_files(image_dir: str) -> list[str]:
    directory = Path(image_dir)
    if not directory.is_dir():
        raise FileNotFoundError(f"Image directory was not found: {image_dir}")

    files = [
        str(path)
        for path in sorted(directory.iterdir())
        if path.suffix.lower() in {".jpg", ".jpeg", ".png"}
    ]
    if not files:
        raise ValueError(f"No image files were found in: {image_dir}")
    return files


def _normalize_single_output(output: Any, num_classes: int) -> tuple[np.ndarray, np.ndarray]:
    arr = np.asarray(output)
    if arr.ndim == 3 and arr.shape[0] == 1:
        arr = arr[0]
    if arr.ndim != 2:
        raise ValueError(f"Unsupported YOLOv8 single-output rank: {arr.shape}")

    expected_channels = 4 + num_classes
    if arr.shape[0] == expected_channels:
        preds = arr.T
    elif arr.shape[1] == expected_channels:
        preds = arr
    elif arr.shape[0] < arr.shape[1] and arr.shape[0] >= expected_channels:
        preds = arr.T
    elif arr.shape[1] < arr.shape[0] and arr.shape[1] >= expected_channels:
        preds = arr
    else:
        raise ValueError(f"Could not infer YOLOv8 single-output layout from shape: {arr.shape}")

    return preds[:, :4], preds[:, 4 : 4 + num_classes]


def _normalize_boxes_output(output: Any) -> np.ndarray:
    arr = np.asarray(output)
    if arr.ndim == 3 and arr.shape[0] == 1:
        arr = arr[0]
    if arr.ndim != 2:
        raise ValueError(f"Unsupported boxes output rank: {arr.shape}")

    if arr.shape[0] == 4:
        return arr.T
    if arr.shape[1] == 4:
        return arr
    raise ValueError(f"Could not infer boxes layout from shape: {arr.shape}")


def _normalize_scores_output(output: Any, num_classes: int) -> np.ndarray:
    arr = np.asarray(output)
    if arr.ndim == 3 and arr.shape[0] == 1:
        arr = arr[0]
    if arr.ndim != 2:
        raise ValueError(f"Unsupported scores output rank: {arr.shape}")

    if arr.shape[0] == num_classes:
        return arr.T
    if arr.shape[1] == num_classes:
        return arr
    if arr.shape[0] < arr.shape[1] and arr.shape[0] >= num_classes:
        return arr.T[:, :num_classes]
    if arr.shape[1] < arr.shape[0] and arr.shape[1] >= num_classes:
        return arr[:, :num_classes]
    raise ValueError(f"Could not infer scores layout from shape: {arr.shape}")


def _split_yolov8_outputs(outputs: Sequence[Any], num_classes: int) -> tuple[np.ndarray, np.ndarray]:
    if len(outputs) == 1:
        return _normalize_single_output(outputs[0], num_classes=num_classes)

    if len(outputs) != 2:
        raise ValueError(f"Unsupported YOLOv8 output count: {len(outputs)}")

    first = np.asarray(outputs[0])
    second = np.asarray(outputs[1])
    first_feature_shape = tuple(dim for dim in first.shape if dim not in (1,))
    second_feature_shape = tuple(dim for dim in second.shape if dim not in (1,))

    if 4 in first_feature_shape:
        boxes = _normalize_boxes_output(first)
        scores = _normalize_scores_output(second, num_classes=num_classes)
    elif 4 in second_feature_shape:
        boxes = _normalize_boxes_output(second)
        scores = _normalize_scores_output(first, num_classes=num_classes)
    else:
        raise ValueError("Could not infer boxes/scores outputs from TensorRT output shapes.")

    if boxes.shape[0] != scores.shape[0]:
        raise ValueError(
            f"YOLOv8 output candidate count mismatch: boxes={boxes.shape}, scores={scores.shape}"
        )
    return boxes, scores


def postprocess_yolov8(
    outputs: Sequence[Any],
    *,
    original_shape: tuple[int, int],
    scale: float,
    pad_w: float,
    pad_h: float,
    num_classes: int,
    conf_threshold: float,
    nms_threshold: float,
) -> list[Detection]:
    boxes, scores = _split_yolov8_outputs(outputs, num_classes=num_classes)
    original_height, original_width = original_shape

    detections: list[Detection] = []
    for box, class_scores in zip(boxes, scores):
        class_scores = np.asarray(class_scores).reshape(-1)
        if class_scores.size == 0:
            continue

        class_id = int(np.argmax(class_scores))
        confidence = float(class_scores[class_id])
        if confidence < conf_threshold:
            continue

        scaled_box = scale_coords(
            (float(box[0]), float(box[1]), float(box[2]), float(box[3])),
            scale=scale,
            pad_w=pad_w,
            pad_h=pad_h,
            original_width=original_width,
            original_height=original_height,
        )

        if scaled_box[2] <= 0.0 or scaled_box[3] <= 0.0:
            continue

        detections.append(
            Detection(
                class_id=class_id,
                confidence=confidence,
                box=scaled_box,
            )
        )

    return nms(detections, iou_threshold=nms_threshold)


def _average_precision(recalls: np.ndarray, precisions: np.ndarray) -> float:
    if recalls.size == 0 or precisions.size == 0:
        return 0.0

    mrec = np.concatenate(([0.0], recalls, [1.0]))
    mpre = np.concatenate(([0.0], precisions, [0.0]))

    for idx in range(mpre.size - 1, 0, -1):
        mpre[idx - 1] = max(mpre[idx - 1], mpre[idx])

    changing_points = np.where(mrec[1:] != mrec[:-1])[0]
    return float(np.sum((mrec[changing_points + 1] - mrec[changing_points]) * mpre[changing_points + 1]))


def _iter_class_predictions(
    predictions_by_image: Sequence[Sequence[Detection]],
    class_id: int,
) -> list[tuple[int, Detection]]:
    items: list[tuple[int, Detection]] = []
    for image_idx, detections in enumerate(predictions_by_image):
        for detection in detections:
            if detection.class_id == class_id:
                items.append((image_idx, detection))
    items.sort(key=lambda item: item[1].confidence, reverse=True)
    return items


def _class_ground_truths(
    ground_truths_by_image: Sequence[Sequence[GroundTruth]],
    class_id: int,
) -> tuple[dict[int, list[GroundTruth]], int]:
    grouped: dict[int, list[GroundTruth]] = {}
    total = 0
    for image_idx, ground_truths in enumerate(ground_truths_by_image):
        class_ground_truths = [item for item in ground_truths if item.class_id == class_id]
        if class_ground_truths:
            grouped[image_idx] = class_ground_truths
            total += len(class_ground_truths)
    return grouped, total


def compute_average_precision(
    predictions_by_image: Sequence[Sequence[Detection]],
    ground_truths_by_image: Sequence[Sequence[GroundTruth]],
    *,
    num_classes: int,
    iou_threshold: float,
) -> float:
    ap_values: list[float] = []

    for class_id in range(num_classes):
        predictions = _iter_class_predictions(predictions_by_image, class_id)
        ground_truths, total_ground_truths = _class_ground_truths(ground_truths_by_image, class_id)
        if total_ground_truths == 0:
            continue

        matched: dict[int, set[int]] = {image_idx: set() for image_idx in ground_truths}
        true_positives = np.zeros(len(predictions), dtype=np.float64)
        false_positives = np.zeros(len(predictions), dtype=np.float64)

        for idx, (image_idx, prediction) in enumerate(predictions):
            candidates = ground_truths.get(image_idx, [])
            best_iou = 0.0
            best_gt_index = -1

            for gt_index, gt in enumerate(candidates):
                if gt_index in matched[image_idx]:
                    continue
                iou = calculate_iou(prediction.box, gt.box)
                if iou > best_iou:
                    best_iou = iou
                    best_gt_index = gt_index

            if best_iou >= iou_threshold and best_gt_index >= 0:
                true_positives[idx] = 1.0
                matched[image_idx].add(best_gt_index)
            else:
                false_positives[idx] = 1.0

        cumulative_tp = np.cumsum(true_positives)
        cumulative_fp = np.cumsum(false_positives)
        recalls = cumulative_tp / max(float(total_ground_truths), 1.0)
        precisions = cumulative_tp / np.maximum(cumulative_tp + cumulative_fp, 1e-12)
        ap_values.append(_average_precision(recalls, precisions))

    if not ap_values:
        return 0.0
    return float(sum(ap_values) / len(ap_values))


def compute_precision_recall_f1(
    predictions_by_image: Sequence[Sequence[Detection]],
    ground_truths_by_image: Sequence[Sequence[GroundTruth]],
    *,
    num_classes: int,
    iou_threshold: float,
) -> tuple[float, float, float]:
    true_positives = 0
    false_positives = 0
    false_negatives = 0

    for class_id in range(num_classes):
        for image_idx, predictions in enumerate(predictions_by_image):
            class_predictions = sorted(
                (prediction for prediction in predictions if prediction.class_id == class_id),
                key=lambda prediction: prediction.confidence,
                reverse=True,
            )
            class_ground_truths = [
                ground_truth
                for ground_truth in ground_truths_by_image[image_idx]
                if ground_truth.class_id == class_id
            ]
            matched_gt: set[int] = set()

            for prediction in class_predictions:
                best_iou = 0.0
                best_gt_index = -1
                for gt_index, ground_truth in enumerate(class_ground_truths):
                    if gt_index in matched_gt:
                        continue
                    iou = calculate_iou(prediction.box, ground_truth.box)
                    if iou > best_iou:
                        best_iou = iou
                        best_gt_index = gt_index

                if best_iou >= iou_threshold and best_gt_index >= 0:
                    true_positives += 1
                    matched_gt.add(best_gt_index)
                else:
                    false_positives += 1

            false_negatives += len(class_ground_truths) - len(matched_gt)

    precision = true_positives / max(true_positives + false_positives, 1)
    recall = true_positives / max(true_positives + false_negatives, 1)
    f1_score = 0.0
    if precision + recall > 0:
        f1_score = 2.0 * precision * recall / (precision + recall)
    return float(precision), float(recall), float(f1_score)


def build_accuracy_payload(eval_result: DetectionEvalResult) -> dict[str, Any]:
    return {
        "task": "detection",
        "metrics": dict(eval_result.metrics),
        "dataset": dict(eval_result.dataset),
        "evaluation_config": dict(eval_result.evaluation_config),
    }


def save_accuracy_payload(payload: dict[str, Any], out_json: str) -> None:
    with open(out_json, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _prepare_input_tensor(image: np.ndarray, model_input: EngineModelIO) -> np.ndarray:
    expected_shape = list(model_input.shape)
    if len(expected_shape) != 4:
        raise ValueError(
            f"evaluate-detection currently supports 4D image inputs only. Got shape: {expected_shape}"
        )

    channels_last = expected_shape[-1] == 3
    channels_first = expected_shape[1] == 3
    if channels_first:
        arr = np.transpose(image, (2, 0, 1))[None, ...]
    elif channels_last:
        arr = image[None, ...]
    else:
        raise ValueError(
            f"Could not infer image tensor layout from model input shape: {expected_shape}"
        )

    if np.issubdtype(model_input.dtype, np.floating):
        arr = arr.astype(np.float32, copy=False) / 255.0
        arr = arr.astype(model_input.dtype, copy=False)
    elif np.issubdtype(model_input.dtype, np.uint8):
        arr = arr.astype(np.uint8, copy=False)
    else:
        arr = arr.astype(model_input.dtype, copy=False)

    return arr


def evaluate_detection_engine(
    *,
    model_path: str,
    engine_name: str,
    engine_path: str | None,
    image_dir: str,
    label_dir: str,
    num_classes: int = 1,
    conf_threshold: float = 0.2,
    nms_threshold: float = 0.45,
    iou_threshold: float = 0.5,
    use_rgb: bool = True,
    input_size: int = 640,
) -> DetectionEvalResult:
    engine_name = normalize_engine_name(engine_name)
    engine = create_engine(engine_name)

    load_kwargs: dict[str, Any] = {}
    if engine_path:
        load_kwargs["engine_path"] = engine_path

    try:
        engine.load(model_path, **load_kwargs)

        if not engine.inputs:
            raise ValueError("The engine does not expose any inputs.")

        model_input = engine.inputs[0]
        image_files = get_image_files(image_dir)

        predictions_by_image: list[list[Detection]] = []
        ground_truths_by_image: list[list[GroundTruth]] = []
        actual_input_shape: list[int] = []

        cv2 = _require_cv2()

        for image_path in image_files:
            image = cv2.imread(image_path)
            if image is None:
                raise RuntimeError(f"Failed to read image: {image_path}")

            original_height, original_width = image.shape[:2]
            letterboxed, scale, pad_w, pad_h = letterbox(
                image,
                target_size=input_size,
                use_rgb=use_rgb,
            )
            input_array = _prepare_input_tensor(letterboxed, model_input)
            if not actual_input_shape:
                actual_input_shape = [int(dim) for dim in input_array.shape]

            feeds = {model_input.name: input_array}
            outputs = engine.run(feeds)
            detections = postprocess_yolov8(
                outputs,
                original_shape=(original_height, original_width),
                scale=scale,
                pad_w=pad_w,
                pad_h=pad_h,
                num_classes=num_classes,
                conf_threshold=conf_threshold,
                nms_threshold=nms_threshold,
            )

            label_path = os.path.join(label_dir, f"{Path(image_path).stem}.txt")
            ground_truths = load_ground_truth(
                label_path,
                image_width=original_width,
                image_height=original_height,
            )

            predictions_by_image.append(detections)
            ground_truths_by_image.append(ground_truths)

        precision, recall, f1_score = compute_precision_recall_f1(
            predictions_by_image,
            ground_truths_by_image,
            num_classes=num_classes,
            iou_threshold=iou_threshold,
        )
        map50 = compute_average_precision(
            predictions_by_image,
            ground_truths_by_image,
            num_classes=num_classes,
            iou_threshold=0.5,
        )
        map_thresholds = np.arange(0.5, 1.0, 0.05)
        map50_95 = float(
            np.mean(
                [
                    compute_average_precision(
                        predictions_by_image,
                        ground_truths_by_image,
                        num_classes=num_classes,
                        iou_threshold=float(threshold),
                    )
                    for threshold in map_thresholds
                ]
            )
        )

        return DetectionEvalResult(
            task="detection",
            engine=engine.name,
            device=engine.device,
            sample_count=len(image_files),
            metrics={
                "map50": map50,
                "map50_95": map50_95,
                "f1_score": f1_score,
                "precision": precision,
                "recall": recall,
            },
            notes=[
                "Detection evaluation uses YOLO txt labels and image directory traversal.",
                "YOLOv8 postprocessing supports single-output and split boxes/scores output layouts.",
                "Primary detection accuracy metric for compare/enrich reuse is map50.",
            ],
            model_input={
                "name": model_input.name,
                "dtype": str(model_input.dtype),
                "shape": model_input.shape,
            },
            actual_input_shape=actual_input_shape,
            dataset={
                "image_dir": image_dir,
                "label_dir": label_dir,
                "sample_count": len(image_files),
            },
            evaluation_config={
                "conf_threshold": conf_threshold,
                "nms_threshold": nms_threshold,
                "iou_threshold": iou_threshold,
                "input_size": input_size,
                "rgb": use_rgb,
                "num_classes": num_classes,
            },
            extra={
                "engine_path": engine_path,
                "runtime_artifact_path": getattr(engine.runtime_paths, "runtime_artifact_path", None),
                "image_files": image_files,
            },
        )
    finally:
        engine.close()
