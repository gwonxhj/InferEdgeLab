# YOLOv8 COCO Subset Evaluation Demo

This document records a small local-first accuracy evaluation demo for InferEdgeLab.
It is not a full COCO benchmark and should not be presented as production model validation.

## Scope

- Preset: `yolov8_coco`
- Model: YOLOv8n ONNX Runtime CPU
- Demo input: 10 local person-detection images
- Annotation source: local YOLO txt labels converted into a compact COCO-style annotation fixture
- Raw images: intentionally not committed
- Annotation fixture: `examples/validation_demo/subset/yolov8_coco_subset_annotations.json`
- Evaluation report: `examples/validation_demo/subset/yolov8_coco_subset_evaluation.json`

## Result

| Metric | Value |
|---|---:|
| Samples | 10 |
| Ground-truth boxes | 89 |
| Post-NMS detections checked | 51 |
| mAP@50 | 0.1410 |
| mAP@50-95 | 0.0873 |
| Precision | 0.2941 |
| Recall | 0.1685 |
| F1 score | 0.2143 |
| Structural validation | passed |
| Contract input shape | passed |

## Interpretation

This demo proves that InferEdgeLab can load COCO-style annotations, run the YOLOv8 detection evaluator, compute simplified accuracy metrics, validate detection output structure, and emit JSON/Markdown/HTML reports.
The numbers are intentionally documented as a small subset result only.
They are useful as portfolio workflow evidence, not as a claim of full COCO accuracy.

The relatively low recall is expected for this tiny local subset because the images are night beach/crowd scenes with many small person boxes.
That is useful for the portfolio: it shows that the validation pipeline records uncomfortable evidence instead of hiding it.

## Local Studio Link

Local Studio's `Load Demo Evidence` flow now returns this evaluation report summary together with the existing ONNX Runtime CPU vs TensorRT Jetson latency pair.
The Studio path remains local-first and does not upload raw images or add database, queue, auth, or production SaaS features.
