# EdgeBench Compare Report

## Compared Results

- Base: `yolov8n.onnx` / `rknn` / `odroid_m2` / `20260421-085655`
- New: `yolov8n.onnx` / `rknn` / `odroid_m2` / `20260421-090813`

## Precision Context

- Base precision: **`fp16`**
- New precision: **`fp16`**
- Precision match: **True**
- Comparison mode: **`same_precision`**
- Precision pair: **`fp16_vs_fp16`**

## Judgement

- Overall: **neutral**
- Shape match: **True**
- System match: **True**
- Mean judgement: **neutral**
- P99 judgement: **neutral**
- Accuracy judgement: **unknown**
- Accuracy present: **False**
- Primary accuracy metric: **`top1_accuracy`**
- Trade-off risk: **not_applicable**
- Summary: Same-precision comparison indicates no significant overall change. Accuracy trade-offs are not available in these results.

## Notes

- This is a same-precision comparison, so latency deltas are more suitable for regression tracking.
- Accuracy data is not available for one or both results, so trade-off interpretation is latency-only.

## Runtime Provenance Summary

| Field | Base | New |
|---|---|---|
| runtime_artifact_path | /home/odroid/edgebench/runtime_models/yolov8n_fp16.rknn | /home/odroid/edgebench/runtime_models/yolov8n_fp16.rknn |
| primary_input_name | images | images |
| requested_shape_summary | b1 / h640 / w640 | b1 / h640 / w640 |
| effective_shape_summary | b1 / h640 / w640 | b1 / h640 / w640 |

## Threshold Policy

| Threshold | Value |
|---|---:|
| latency_improve_threshold | -3.00% |
| latency_regress_threshold | +3.00% |
| accuracy_improve_threshold | +0.20pp |
| accuracy_regress_threshold | -0.20pp |
| tradeoff_caution_threshold | -0.30pp |
| tradeoff_risky_threshold | -1.00pp |
| tradeoff_severe_threshold | -2.00pp |

## Latency Comparison

| Metric | Base | New | Delta | Delta % |
|---|---:|---:|---:|---:|
| mean_ms | 70.4464 | 70.4860 | 0.0396 | +0.06% |
| p99_ms | 71.3739 | 71.8033 | 0.4293 | +0.60% |

## Accuracy Comparison

- Task: **`unknown`**
- Primary metric: **`top1_accuracy`**

| Metric | Base | New | Delta | Delta % | Delta pp |
|---|---:|---:|---:|---:|---:|

| Field | Base | New |
|---|---:|---:|
| sample_count | - | - |

## Input Shape

| Field | Base | New |
|---|---:|---:|
| batch | 1 | 1 |
| height | 640 | 640 |
| width | 640 | 640 |

## Input Shape Provenance

| Field | Base | New |
|---|---:|---:|
| requested_batch | 1 | 1 |
| requested_height | 640 | 640 |
| requested_width | 640 | 640 |
| effective_batch | 1 | 1 |
| effective_height | 640 | 640 |
| effective_width | 640 | 640 |
| primary_input_name | images | images |

### Resolved Input Shapes

- Base: `{'images': [1, 3, 640, 640]}`
- New: `{'images': [1, 3, 640, 640]}`

## System Info

| Field | Base | New |
|---|---|---|
| os | Linux 5.10.0-odroid-arm64 | Linux 5.10.0-odroid-arm64 |
| python | 3.10.20 | 3.10.20 |
| machine | aarch64 | aarch64 |
| cpu_count_logical | 8 | 8 |

## Run Config

| Field | Base | New |
|---|---:|---:|
| warmup | 5 | 5 |
| runs | 10 | 10 |
| intra_threads | 1 | 1 |
| inter_threads | 1 | 1 |
| mode | - | - |
| task | - | - |

