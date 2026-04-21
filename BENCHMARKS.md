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
| yolov8n.onnx | rknn | npu | fp16_vs_fp16 | 1 | 640x640 | 1 | 5 | 72.4249 | 71.8846 | 73.6221 | 73.7026 | neutral | not_applicable | same-precision compare, runtime provenance confirmed |
| yolov8n.onnx | rknn | npu | fp16_vs_int8 | 1 | 640x640 | 1 | 5 | 71.8846 | 35.0657 | 73.7026 | 35.6140 | tradeoff_faster | unknown_risk | cross-precision compare, latency-only runtime validation |
| yolov8n.onnx | rknn | npu | fp16_vs_int8 (enriched) | 1 | 640x640 | 1 | 5 | 71.8846 | 35.0657 | 73.7026 | 35.6140 | tradeoff_faster | acceptable_tradeoff | enriched runtime pair with map50: 0.7791 -> 0.7977 |

> Notes:
> - The values above were confirmed through actual `profile` → structured result persistence → `compare-latest` execution on Odroid M2.
> - The FP16 runtime artifact is `/home/odroid/rise/fp16/yolov8n_fp16.rknn`.
> - The INT8 runtime artifact is `/home/odroid/rise/int8/yolov8n_hybrid_int8_boxdfl_scorefix.rknn`.
> - The default runtime cross-precision pair does not include accuracy data, so the trade-off risk is interpreted as `unknown_risk`.
> - After attaching detection accuracy JSON via `enrich-result` / `enrich-pair`, the same runtime pair can be reinterpreted through an accuracy-aware compare flow.

### Quick Takeaway

- In curated cross-precision validation on Odroid M2 + YOLOv8n, moving from FP16 to Hybrid INT8 reduces mean latency from `51.82 ms → 16.29 ms`
- In the same curated comparison, `map50` is maintained or improved from `0.7791 → 0.7977`
- Separately, direct RKNN runtime profiling on Odroid M2 also confirms successful execution of the `yolov8n.onnx` + `yolov8n_fp16.rknn` combination
- In same-precision RKNN runtime compare, mean latency `72.4249 ms → 71.8846 ms` and p99 `73.6221 ms → 73.7026 ms` are classified as **neutral**
- In cross-precision RKNN runtime compare, mean latency `71.8846 ms → 35.0657 ms` and p99 `73.7026 ms → 35.6140 ms` are classified as **tradeoff_faster**
- Because this runtime cross-precision pair is latency-only and does not store accuracy, the trade-off risk is interpreted as `unknown_risk`
- InferEdgeLab therefore connects both curated import and runtime profiling paths into the same RKNN validation evidence workflow
- `enrich-result` / `enrich-pair` can attach accuracy evidence later to runtime-only results
- As a result, a runtime cross-precision pair does not have to stop at `unknown_risk`; it can be extended to an accuracy-aware classification such as `acceptable_tradeoff`
- These results are not one-off measurements, but reproducible validation evidence generated via InferEdgeLab workflow (profile → structured result → compare → report)

### Odroid RKNN Benchmarks

These entries are curated hardware validation results imported from documented Odroid RKNN experiments, separate from the CI-generated CPU benchmark tables above.


| Model | Engine | Device | Precision | Batch | Input(HxW) | Mean (ms) | P99 (ms) | mAP50 | F1 | Precision | Recall | Quantization | Preset | Source | Timestamp (UTC) |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| YOLOv8n | rknn | odroid_m1 | fp16 | 1 | 640x640 | 151.07 | - | 0.7389 | 0.8066 | 0.8457 | 0.7710 | fp16 | default | odroid_report | 2026-04-13T00:00:00Z |
| YOLOv8n | rknn | odroid_m2 | fp16 | 1 | 640x640 | 51.82 | - | 0.7791 | 0.8180 | 0.7950 | 0.8424 | fp16 | default | odroid_report | 2026-04-13T00:05:00Z |
| YOLOv8n | rknn | odroid_m2 | int8 | 1 | 640x640 | 16.29 | - | 0.7977 | 0.8129 | 0.7866 | 0.8410 | hybrid_int8 | default | odroid_report | 2026-04-13T00:10:00Z |
| YOLOv8s | rknn | odroid_m2 | int8 | 1 | 640x640 | 29.16 | - | 0.8090 | 0.8206 | 0.7880 | 0.8561 | hybrid_int8 | default | odroid_report | 2026-04-13T00:15:00Z |

> Notes: This table does not come from direct execution through the RKNN runtime backend. It is curated validation data linked from documented Odroid measurements.
> The values are based on measurements recorded on 2025-02-12, with some display rounding applied for readability.
