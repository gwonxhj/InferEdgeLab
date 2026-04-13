# Benchmarks

> No auto-generated report summaries are available yet.

## Curated Hardware Validation

### Odroid RKNN Benchmarks

These entries are curated hardware validation results imported from documented Odroid RKNN experiments, separate from the CI-generated CPU benchmark tables above.


| Model | Engine | Device | Precision | Batch | Input(HxW) | Mean (ms) | P99 (ms) | mAP50 | F1 | Precision | Recall | Quantization | Preset | Source | Timestamp (UTC) |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| YOLOv8n | rknn | odroid_m1 | fp16 | 1 | 640x640 | 34.812 | 39.457 | 0.621 | 0.588 | 0.641 | 0.543 | fp16 | default | odroid_report | 2026-04-13T00:00:00Z |
| YOLOv8n | rknn | odroid_m2 | fp16 | 1 | 640x640 | 22.764 | 25.118 | 0.621 | 0.588 | 0.641 | 0.543 | fp16 | default | odroid_report | 2026-04-13T00:05:00Z |
| YOLOv8n | rknn | odroid_m2 | int8 | 1 | 640x640 | 15.403 | 17.086 | 0.612 | 0.581 | 0.635 | 0.537 | hybrid_int8 | default | odroid_report | 2026-04-13T00:10:00Z |
| YOLOv8s | rknn | odroid_m2 | int8 | 1 | 640x640 | 24.917 | 27.844 | 0.671 | 0.624 | 0.689 | 0.585 | hybrid_int8 | default | odroid_report | 2026-04-13T00:15:00Z |
