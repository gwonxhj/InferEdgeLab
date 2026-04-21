# EdgeBench Compare Report

## Compared Results

- Base: `yolov8m.onnx` / `rknn` / `odroid_m2` / `20260421-090818`
- New: `yolov8m.onnx` / `rknn` / `odroid_m2` / `20260421-092216`

## Precision Context

- Base precision: **`fp16`**
- New precision: **`int8`**
- Precision match: **False**
- Comparison mode: **`cross_precision`**
- Precision pair: **`fp16_vs_int8`**

> [!WARNING]
> This is a cross-precision comparison.
> Interpret latency deltas as a precision trade-off signal, not a strict same-condition regression result.

## Judgement

- Overall: **tradeoff_faster**
- Overall semantics: **trade-off status, not same-condition regression status**
- Shape match: **True**
- System match: **True**
- Mean judgement: **improvement**
- P99 judgement: **improvement**
- Accuracy judgement: **unknown**
- Accuracy present: **False**
- Primary accuracy metric: **`top1_accuracy`**
- Trade-off risk: **unknown_risk**
- Summary: Cross-precision comparison (fp16_vs_int8) shows faster latency in the new result. Accuracy trade-offs are not available in these results. Trade-off risk: unknown_risk.

## Notes

- This is a cross-precision comparison: fp16_vs_int8. Latency differences can be caused by precision changes as well as runtime behavior.
- Cross-precision overall status uses trade-off semantics instead of same-condition regression semantics.
- Trade-off risk classification: unknown_risk.
- Trade-off thresholds: caution<=-0.30pp, risky<=-1.00pp, severe<=-2.00pp.
- Accuracy data is not available for one or both results, so trade-off interpretation is latency-only.

## Runtime Provenance Summary

| Field | Base | New |
|---|---|---|
| runtime_artifact_path | /home/odroid/edgebench/runtime_models/yolov8m_fp16.rknn | /home/odroid/edgebench/runtime_models/yolov8m_hybrid_int8_presetB.rknn |
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
| mean_ms | 171.5369 | 84.6368 | -86.9001 | -50.66% |
| p99_ms | 199.2491 | 86.1068 | -113.1422 | -56.78% |

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

