# InferEdge Evaluation Report

- preset: `yolov8_coco`
- engine: `onnxruntime`
- device: `cpu`
- samples: `10`
- accuracy status: `evaluated`
- contract input shape: `passed`
- structural validation: `passed`
- deployment signal: `review`

## Metrics
- backend: `simplified`
- map50: `0.14097840361885305`
- map50_95: `0.08728567780534073`
- f1_score: `0.21428571428571427`
- precision: `0.29411764705882354`
- recall: `0.16853932584269662`
- note: `lightweight simplified mAP50 implementation`

## Notes
- Detection evaluation uses image directory traversal.
- YOLOv8 postprocessing supports single-output and split boxes/scores output layouts.
- Accuracy uses YOLO txt labels or COCO annotations when provided.
- When annotations are missing, InferEdge records accuracy_skipped and structural validation only.
- Accuracy metrics backend: simplified lightweight mAP50.
