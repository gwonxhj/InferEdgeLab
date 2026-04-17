# EdgeBench Compare Report

## Compared Results

- Base: `resnet18.onnx` / `tensorrt` / `gpu` / `20260417-064935`
- New: `resnet18.onnx` / `tensorrt` / `gpu` / `20260417-064937`

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
| runtime_artifact_path | models/resnet18.engine | models/resnet18.engine |
| primary_input_name | input | input |
| requested_shape_summary | b1 / h224 / w224 | b1 / h224 / w224 |
| effective_shape_summary | b1 / h224 / w224 | b1 / h224 / w224 |

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
| mean_ms | 2.8647 | 2.8265 | -0.0382 | -1.33% |
| p99_ms | 3.1388 | 3.0620 | -0.0769 | -2.45% |

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
| height | 224 | 224 |
| width | 224 | 224 |

## Input Shape Provenance

| Field | Base | New |
|---|---:|---:|
| requested_batch | 1 | 1 |
| requested_height | 224 | 224 |
| requested_width | 224 | 224 |
| effective_batch | 1 | 1 |
| effective_height | 224 | 224 |
| effective_width | 224 | 224 |
| primary_input_name | input | input |

### Resolved Input Shapes

- Base: `{'input': [1, 3, 224, 224]}`
- New: `{'input': [1, 3, 224, 224]}`

## System Info

| Field | Base | New |
|---|---|---|
| os | Linux 5.15.148-tegra | Linux 5.15.148-tegra |
| python | 3.10.12 | 3.10.12 |
| machine | aarch64 | aarch64 |
| cpu_count_logical | 6 | 6 |

## Run Config

| Field | Base | New |
|---|---:|---:|
| warmup | 10 | 10 |
| runs | 100 | 100 |
| intra_threads | 1 | 1 |
| inter_threads | 1 | 1 |
| mode | - | - |
| task | - | - |

