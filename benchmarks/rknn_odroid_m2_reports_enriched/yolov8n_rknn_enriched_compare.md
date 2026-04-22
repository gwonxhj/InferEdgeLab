# EdgeBench Compare Report

## Compared Results

- Base: `yolov8n.onnx` / `rknn` / `odroid_m2` / `20260422-084651-661456`
- New: `yolov8n.onnx` / `rknn` / `odroid_m2` / `20260422-084651-662668`

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
- Accuracy judgement: **improvement**
- Accuracy present: **True**
- Primary accuracy metric: **`map50`**
- Trade-off risk: **acceptable_tradeoff**
- Summary: Cross-precision comparison (fp16_vs_int8) shows faster latency in the new result. Primary accuracy metric (map50) delta: +1.86pp. Trade-off risk: acceptable_tradeoff.

## Notes

- This is a cross-precision comparison: fp16_vs_int8. Latency differences can be caused by precision changes as well as runtime behavior.
- Cross-precision overall status uses trade-off semantics instead of same-condition regression semantics.
- Trade-off risk classification: acceptable_tradeoff.
- Trade-off thresholds: caution<=-0.30pp, risky<=-1.00pp, severe<=-2.00pp.
- Accuracy data is available and is compared using map50 as the primary metric with percentage-point deltas.
- Primary accuracy delta (new - base, map50): +1.86pp.
- The new result shows a primary accuracy improvement on map50.

## Runtime Provenance Summary

| Field | Base | New |
|---|---|---|
| runtime_artifact_path | /home/odroid/edgebench/runtime_models/yolov8n_fp16.rknn | /home/odroid/edgebench/runtime_models/yolov8n_hybrid_int8_presetB.rknn |
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
| mean_ms | 70.4860 | 35.1338 | -35.3523 | -50.15% |
| p99_ms | 71.8033 | 35.9663 | -35.8370 | -49.91% |

## Accuracy Comparison

- Task: **`detection`**
- Primary metric: **`map50`**

| Metric | Base | New | Delta | Delta % | Delta pp |
|---|---:|---:|---:|---:|---:|
| map50 (primary) | 0.7791 | 0.7977 | 0.0186 | +2.39% | +1.86pp |
| f1_score | 0.8180 | 0.8129 | -0.0051 | -0.62% | -0.51pp |
| precision | 0.7950 | 0.7866 | -0.0084 | -1.06% | -0.84pp |
| recall | 0.8424 | 0.8410 | -0.0014 | -0.17% | -0.14pp |

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

