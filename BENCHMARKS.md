# Benchmarks

> This document combines the auto-generated benchmark summary with Jetson TensorRT / RKNN validation references.
> Manually maintained validation evidence remains in place, while only the auto-generated summary is updated inside the marker block.

This document serves two purposes:

1. Preserve the auto-generated CPU benchmark summary
2. Provide a table-oriented benchmark reference for real edge hardware validation evidence

The Jetson TensorRT validation evidence is described narratively in the README and portfolio document.
This file stays focused on quick, table-oriented reference data.

---

## What These Benchmarks Prove

These benchmarks are not isolated measurements.

They demonstrate that InferEdgeLab can:

- Reproduce hardware-level performance differences (FP16 → INT8)
- Persist results as structured validation evidence
- Reuse those results across comparison, reporting, and CI workflows
- Interpret cross-precision trade-offs instead of exposing raw numbers

On RKNN (Odroid M2), INT8 consistently reduces latency by ~40-50% compared to FP16.

This is not just observed - it is captured, compared, and reusable.

---

## Auto-Generated Benchmark Summary

This section is the auto-generated summary block used by `scripts/update_benchmarks.py` and `scripts/update_readme.py`.
The manually maintained validation evidence sections are kept outside the marker block below.

<!-- EDGE_BENCH_BENCHMARKS:START -->

> No auto-generated report summaries are available yet.

<!-- EDGE_BENCH_BENCHMARKS:END -->

---

## Curated Hardware Validation

This section presents representative results from real Odroid RKNN experiments, organized using the InferEdgeLab result schema.
These are not just report tables; they are reusable validation evidence that can flow into `compare`, `compare-latest`, and report generation.

These curated results are external benchmark references, while the RKNN runtime validation below demonstrates the same models executed through InferEdgeLab's profiling and comparison workflow.

This distinction shows that InferEdgeLab can both import benchmark references and reproduce them as structured validation evidence on real hardware.

---

## Jetson TensorRT Validation Reference

This section summarizes values taken from actual structured result and `compare-latest` outputs generated during Jetson validation.
These are validated execution records, not illustrative numbers: TensorRT execution, structured result persistence, and compare/report reuse were all confirmed.

| Model | Engine | Device | Precision | Batch | Input(HxW) | Warmup | Runs | Base Mean (ms) | New Mean (ms) | Base P99 (ms) | New P99 (ms) | Overall | Notes |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| resnet18.onnx | tensorrt | gpu | fp16 | 1 | 224x224 | 10 | 100 | 2.8647 | 2.8265 | 3.1388 | 3.0620 | neutral | same-precision compare, runtime provenance confirmed |
| yolov8n.onnx | tensorrt | gpu | fp16 | 1 | 640x640 | 10 | 50 | 14.4592 | 14.1108 | 15.4154 | 15.2565 | neutral | same-precision compare, runtime provenance confirmed |

> Notes:
> - The Jetson values above are based on actual `compare-latest` outputs and direct inspection of the structured result JSON files.
> - `runtime_artifact_path` was confirmed to be stored as `models/resnet18.engine` and `models/yolov8n.engine`, respectively.
> - Repeated profiling generates TensorRT structured results under `results/*.json` on the validation machine.
> - Latest-pair compare reports are generated under `reports/validation/*.md` and `reports/validation/*.html` on the validation machine.

---

## RKNN Runtime Validation Reference

Separate from the curated import results, this section captures validation references profiled directly through InferEdgeLab's RKNN runtime backend on an Odroid M2 device.

| Model | Engine | Device | Precision Pair | Batch | Input(HxW) | Warmup | Runs | Base Mean (ms) | New Mean (ms) | Base P99 (ms) | New P99 (ms) | Overall | Trade-off Risk | Notes |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| yolov8n.onnx | rknn | odroid_m2 | fp16_vs_fp16 | 1 | 640x640 | 5 | 10 | 70.4464 | 70.4860 | 71.3739 | 71.8033 | neutral | not_applicable | same-precision compare, runtime provenance confirmed |
| yolov8n.onnx | rknn | odroid_m2 | fp16_vs_int8 | 1 | 640x640 | 5 | 10 | 70.4860 | 35.1338 | 71.8033 | 35.9663 | tradeoff_faster | unknown_risk | cross-precision compare, latency-only runtime validation |
| yolov8n.onnx | rknn | odroid_m2 | fp16_vs_int8 (enriched) | 1 | 640x640 | 5 | 50 | 72.4430 | 35.5771 | 79.1559 | 45.3868 | tradeoff_faster | acceptable_tradeoff | enriched runtime pair with map50: 0.7791 -> 0.7977 |
| yolov8s.onnx | rknn | odroid_m2 | fp16_vs_int8 (enriched) | 1 | 640x640 | 5 | 50 | 85.8169 | 49.9623 | 109.4198 | 58.6213 | tradeoff_faster | acceptable_tradeoff | enriched runtime pair with map50: 0.7840 -> 0.8090 |
| yolov8m.onnx | rknn | odroid_m2 | fp16_vs_int8 (enriched) | 1 | 640x640 | 5 | 50 | 171.9906 | 87.8136 | 192.6720 | 111.5943 | tradeoff_faster | acceptable_tradeoff | enriched runtime pair with map50: 0.7856 -> 0.7975 |

> Notes:
> - The values above were confirmed through actual `profile` → structured result persistence → `compare` execution on Odroid M2.
> - The enriched pairs were generated through `enrich-pair` using external detection accuracy JSON payloads.
> - The default runtime cross-precision comparison does not include accuracy data, so trade-off risk initially appears as `unknown_risk`.
> - After attaching detection accuracy JSON via `enrich-pair`, the same runtime validation path is reinterpreted as `acceptable_tradeoff`.
> - This demonstrates that InferEdgeLab supports both latency-only runtime comparison and accuracy-aware deployment trade-off interpretation on the same hardware validation path.

### Quick Takeaway

- On Odroid M2, RKNN runtime validation confirmed stable same-precision comparison for `yolov8n.onnx` under FP16 with a **neutral** result
- Cross-precision enriched runtime comparison showed large latency reductions:
  - `yolov8n`: `72.4430 ms → 35.5771 ms` (**-50.89%**)
  - `yolov8s`: `85.8169 ms → 49.9623 ms` (**-41.78%**)
  - `yolov8m`: `171.9906 ms → 87.8136 ms` (**-48.94%**)
- After enrichment with detection accuracy payloads, all `yolov8n/s/m` runtime pairs were classified as `acceptable_tradeoff`
- The primary metric used in enriched comparison was `map50`, and it improved across all three models:
  - `yolov8n`: `0.7791 → 0.7977` (**+1.86pp**)
  - `yolov8s`: `0.7840 → 0.8090` (**+2.50pp**)
  - `yolov8m`: `0.7856 → 0.7975` (**+1.19pp**)
- This proves that InferEdgeLab does not stop at raw speed comparison; it can turn runtime benchmark evidence into an interpretable deployment trade-off decision across multiple model scales

### Odroid RKNN Benchmarks

These entries are curated hardware validation results imported from documented Odroid RKNN experiments, separate from the CI-generated CPU benchmark tables above.


| Model | Engine | Device | Precision | Batch | Input(HxW) | Mean (ms) | P99 (ms) | mAP50 | F1 | Precision | Recall | Quantization | Preset | Source | Timestamp (UTC) |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| YOLOv8n | rknn | odroid_m1 | fp16 | 1 | 640x640 | 151.07 | - | 0.7389 | 0.8066 | 0.8457 | 0.7710 | fp16 | default | odroid_report | 2026-04-13T00:00:00Z |
| YOLOv8n | rknn | odroid_m2 | fp16 | 1 | 640x640 | 51.82 | - | 0.7791 | 0.8180 | 0.7950 | 0.8424 | fp16 | default | odroid_report | 2026-04-13T00:05:00Z |
| YOLOv8n | rknn | odroid_m2 | int8 | 1 | 640x640 | 16.29 | - | 0.7977 | 0.8129 | 0.7866 | 0.8410 | hybrid_int8 | default | odroid_report | 2026-04-13T00:10:00Z |
| YOLOv8s | rknn | odroid_m2 | fp16 | 1 | 640x640 | 62.27 | - | 0.7840 | 0.8281 | 0.8027 | 0.8551 | fp16 | default | odroid_report | 2026-04-13T00:15:00Z |
| YOLOv8s | rknn | odroid_m2 | int8 | 1 | 640x640 | 29.16 | - | 0.8090 | 0.8206 | 0.7880 | 0.8561 | hybrid_int8 | default | odroid_report | 2026-04-13T00:20:00Z |
| YOLOv8m | rknn | odroid_m2 | fp16 | 1 | 640x640 | 141.70 | - | 0.7856 | 0.8317 | 0.8029 | 0.8626 | fp16 | default | odroid_report | 2026-04-13T00:25:00Z |
| YOLOv8m | rknn | odroid_m2 | int8 | 1 | 640x640 | 63.59 | - | 0.7975 | 0.8095 | 0.7728 | 0.8498 | hybrid_int8 | default | odroid_report | 2026-04-13T00:30:00Z |

> Notes: This table does not come from direct execution through the RKNN runtime backend. It is curated validation data linked from documented Odroid measurements.
> The values are based on measurements recorded on 2025-02-12, with some display rounding applied for readability.
