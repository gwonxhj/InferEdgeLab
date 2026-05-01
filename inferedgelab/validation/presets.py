from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ValidationPreset:
    name: str
    task: str
    description: str
    input_shape: list[int]
    input_format: str
    output_type: str
    output_shape: list[int]
    labels: list[str]
    thresholds: dict[str, float]
    accuracy: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


COCO80_LABELS = [
    "person",
    "bicycle",
    "car",
    "motorcycle",
    "airplane",
    "bus",
    "train",
    "truck",
    "boat",
    "traffic light",
    "fire hydrant",
    "stop sign",
    "parking meter",
    "bench",
    "bird",
    "cat",
    "dog",
    "horse",
    "sheep",
    "cow",
    "elephant",
    "bear",
    "zebra",
    "giraffe",
    "backpack",
    "umbrella",
    "handbag",
    "tie",
    "suitcase",
    "frisbee",
    "skis",
    "snowboard",
    "sports ball",
    "kite",
    "baseball bat",
    "baseball glove",
    "skateboard",
    "surfboard",
    "tennis racket",
    "bottle",
    "wine glass",
    "cup",
    "fork",
    "knife",
    "spoon",
    "bowl",
    "banana",
    "apple",
    "sandwich",
    "orange",
    "broccoli",
    "carrot",
    "hot dog",
    "pizza",
    "donut",
    "cake",
    "chair",
    "couch",
    "potted plant",
    "bed",
    "dining table",
    "toilet",
    "tv",
    "laptop",
    "mouse",
    "remote",
    "keyboard",
    "cell phone",
    "microwave",
    "oven",
    "toaster",
    "sink",
    "refrigerator",
    "book",
    "clock",
    "vase",
    "scissors",
    "teddy bear",
    "hair drier",
    "toothbrush",
]


_PRESETS: dict[str, ValidationPreset] = {
    "yolov8_coco": ValidationPreset(
        name="yolov8_coco",
        task="object_detection",
        description="YOLOv8 object detection on COCO-style labels.",
        input_shape=[1, 3, 640, 640],
        input_format="NCHW_RGB_FLOAT32_0_1",
        output_type="yolov8_detection",
        output_shape=[1, 84, 8400],
        labels=COCO80_LABELS,
        thresholds={"score": 0.25, "iou": 0.5},
        accuracy={
            "primary_metric": "map50",
            "secondary_metrics": ["precision", "recall", "f1_score", "map50_95"],
            "annotation_formats": ["coco", "yolo_txt"],
        },
    ),
    "resnet_imagenet": ValidationPreset(
        name="resnet_imagenet",
        task="classification",
        description="ImageNet classification contract placeholder.",
        input_shape=[1, 3, 224, 224],
        input_format="NCHW_RGB_FLOAT32_0_1",
        output_type="classification_logits",
        output_shape=[1, 1000],
        labels=[],
        thresholds={"top1_min": 0.0, "top5_min": 0.0},
        accuracy={
            "primary_metric": "top1",
            "secondary_metrics": ["top5"],
            "annotation_formats": ["imagenet_folder", "custom_contract"],
        },
    ),
    "custom_contract": ValidationPreset(
        name="custom_contract",
        task="custom",
        description="Custom validation requires an explicit model_contract.json.",
        input_shape=[],
        input_format="custom",
        output_type="custom",
        output_shape=[],
        labels=[],
        thresholds={},
        accuracy={
            "primary_metric": "contract_defined",
            "secondary_metrics": [],
            "annotation_formats": ["custom_contract"],
        },
    ),
}


def supported_presets() -> list[str]:
    return sorted(_PRESETS)


def get_preset(name: str) -> ValidationPreset:
    key = name.strip().lower()
    if key not in _PRESETS:
        supported = ", ".join(supported_presets())
        raise ValueError(f"Unsupported validation preset: {name}. Supported presets: {supported}")
    return _PRESETS[key]
