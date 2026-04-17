## Jetson TensorRT Validation Evidence - YOLOv8n

- Model: `yolov8n.onnx`
- Engine: `tensorrt`
- Device: `gpu`
- Precision pair: `fp16_vs_fp16`
- Overall: **neutral**

| Metric | Base | New |
|---|---:|---:|
| mean_ms | 14.4592 | 14.1108 |
| p99_ms | 15.4154 | 15.2565 |

### Runtime Provenance
- Base runtime_artifact_path: `models/yolov8n.engine`
- New runtime_artifact_path: `models/yolov8n.engine`
- Base primary_input_name: `images`
- New primary_input_name: `images`
- Base resolved_input_shapes: `{'images': [1, 3, 640, 640]}`
- New resolved_input_shapes: `{'images': [1, 3, 640, 640]}`

### Reports
- Markdown: `reports/validation/yolov8n_tensorrt_latest.md`
- HTML: `reports/validation/yolov8n_tensorrt_latest.html`

**Summary**: Same-precision comparison indicates no significant overall change. Accuracy trade-offs are not available in these results.
