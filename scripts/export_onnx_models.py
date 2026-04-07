from pathlib import Path

import torch
import torchvision.models as models
from ultralytics import YOLO


def export_resnet18():
    print("Exporting ResNet18...")
    model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    model.eval()

    dummy_input = torch.randn(1, 3, 224, 224)

    torch.onnx.export(
        model,
        dummy_input,
        "models/resnet18.onnx",
        input_names=["input"],
        output_names=["output"],
        opset_version=18,
        external_data=False,
    )

    print("models/resnet18.onnx 생성 완료")


def export_yolov8():
    print("Exporting YOLOv8...")
    models_dir = Path("models")
    models_dir.mkdir(parents=True, exist_ok=True)

    exported_path = Path("yolov8n.onnx")
    target_path = models_dir / "yolov8n.onnx"

    model = YOLO("yolov8n.pt")
    model.export(format="onnx", imgsz=640)

    if not exported_path.exists():
        raise FileNotFoundError("Expected exported file was not created: yolov8n.onnx")

    exported_path.replace(target_path)
    print("models/yolov8n.onnx 생성 완료")


if __name__ == "__main__":
    export_resnet18()
    export_yolov8()
