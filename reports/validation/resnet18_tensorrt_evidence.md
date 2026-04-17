## Jetson TensorRT Validation Evidence - ResNet18

- Model: `resnet18.onnx`
- Engine: `tensorrt`
- Device: `gpu`
- Precision pair: `fp16_vs_fp16`
- Overall: **neutral**

| Metric | Base | New |
|---|---:|---:|
| mean_ms | 2.8647 | 2.8265 |
| p99_ms | 3.1388 | 3.0620 |

### Runtime Provenance
- Base runtime_artifact_path: `models/resnet18.engine`
- New runtime_artifact_path: `models/resnet18.engine`
- Base primary_input_name: `input`
- New primary_input_name: `input`
- Base resolved_input_shapes: `{'input': [1, 3, 224, 224]}`
- New resolved_input_shapes: `{'input': [1, 3, 224, 224]}`

### Reports
- Markdown: `reports/validation/resnet18_tensorrt_latest.md`
- HTML: `reports/validation/resnet18_tensorrt_latest.html`

**Summary**: Same-precision comparison indicates no significant overall change. Accuracy trade-offs are not available in these results.
