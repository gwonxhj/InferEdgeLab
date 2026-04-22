# Odroid RKNN Validation Runbook

InferEdgeLab is designed to validate deployment trade-offs on real edge hardware.

This runbook demonstrates that RKNN-based inference on Odroid M2 can be profiled, compared, and interpreted as structured validation evidence rather than treated as raw benchmark output.

## 1. Purpose

This document is a validation runbook for the InferEdgeLab RKNN execution path on Odroid M2.
The goal is not only to confirm successful profiling, but also to verify Odroid M2 + RKNN runtime validation, FP16 vs INT8 cross-precision validation, and end-to-end reuse of the structured result → compare → report workflow.

## 2. Environment

- Device: `Odroid M2 (RK3588)`
- Engine: `RKNN (librknnrt 2.3.2)`
- Models:
  - `yolov8n`
  - `yolov8s`
  - `yolov8m`

## 3. Profiling Procedure

Validation is performed through `python -m inferedgelab.cli`.
For each model, confirm FP16 RKNN profiling, INT8 RKNN profiling, and structured result generation.

### 3-1. FP16 RKNN Profiling

```bash
python -m inferedgelab.cli profile models/yolov8n.onnx \
  --engine rknn \
  --engine-path models/yolov8n_fp16.rknn \
  --rknn-target rk3588 \
  --device-name odroid_m2 \
  --precision fp16 \
  --warmup 10 \
  --runs 50 \
  --batch 1 \
  --height 640 \
  --width 640
```

### 3-2. INT8 RKNN Profiling

```bash
python -m inferedgelab.cli profile models/yolov8n.onnx \
  --engine rknn \
  --engine-path models/yolov8n_int8.rknn \
  --rknn-target rk3588 \
  --device-name odroid_m2 \
  --precision int8 \
  --warmup 10 \
  --runs 50 \
  --batch 1 \
  --height 640 \
  --width 640
```

### 3-3. Structured Result Validation

After each profiling run, verify that the following fields are persisted in the structured result:

- `engine = rknn`
- `device = odroid_m2`
- `run_config.engine_path`
- `run_config.rknn_target`
- `run_config.device_name`
- `extra.runtime_artifact_path`
- `extra.rknn_target`
- `extra.device_name`

## 3-4. End-to-End Validation Flow (Reproducible)

The following commands reproduce the full RKNN validation workflow,
from profiling to accuracy-aware trade-off interpretation.

### Step 1. FP16 Profiling

```bash
python -m inferedgelab.cli profile models/yolov8n.onnx \
  --engine rknn \
  --engine-path models/yolov8n_fp16.rknn \
  --rknn-target rk3588 \
  --device-name odroid_m2 \
  --precision fp16 \
  --warmup 5 \
  --runs 10 \
  --batch 1 \
  --height 640 \
  --width 640
```

### Step 2. INT8 Profiling

```bash
python -m inferedgelab.cli profile models/yolov8n.onnx \
  --engine rknn \
  --engine-path models/yolov8n_int8.rknn \
  --rknn-target rk3588 \
  --device-name odroid_m2 \
  --precision int8 \
  --warmup 5 \
  --runs 10 \
  --batch 1 \
  --height 640 \
  --width 640
```

### Step 3. Cross-Precision Compare (Latency-only)

```bash
python -m inferedgelab.cli compare-latest \
  --model yolov8n.onnx \
  --engine rknn \
  --device odroid_m2 \
  --selection-mode cross_precision
```

### Step 4. Attach Accuracy (Enrich Pair)

```bash
python -m inferedgelab.cli enrich-pair \
  --base-result <fp16_result.json> \
  --base-accuracy-json validation_payloads/yolov8n_fp16_detection_accuracy.json \
  --new-result <int8_result.json> \
  --new-accuracy-json validation_payloads/yolov8n_int8_detection_accuracy.json \
  --out-dir results_enriched
```

### Step 5. Accuracy-aware Compare

```bash
python -m inferedgelab.cli compare \
  <enriched_fp16.json> \
  <enriched_int8.json>
```

### Result

- Step 3 produces a latency-only interpretation (tradeoff_faster, unknown_risk)
- Step 5 produces an accuracy-aware interpretation (acceptable_tradeoff)

> This demonstrates that the same runtime pair can evolve from raw benchmark output into a deployment decision without re-running profiling.

## 4. Running Compare-Latest

### 4-1. same-precision (fp16 vs fp16)

```bash
python -m inferedgelab.cli compare-latest \
  --model yolov8n.onnx \
  --engine rknn \
  --device odroid_m2 \
  --precision fp16 \
  --selection-mode same_precision
```

### 4-2. cross-precision (fp16 vs int8)

```bash
python -m inferedgelab.cli compare-latest \
  --model yolov8n.onnx \
  --engine rknn \
  --device odroid_m2 \
  --selection-mode cross_precision \
  --markdown-out reports/validation/yolov8n_rknn_cross_precision.md \
  --html-out reports/validation/yolov8n_rknn_cross_precision.html
```

Apply the same latest-pair comparison flow to `yolov8s` and `yolov8m` to confirm that both same-precision and cross-precision workflows are reusable across models.

## 5. Summary of Observed Results

The values below summarize representative observations from Odroid M2 + RKNN runtime validation.

| Model | FP16 mean latency | INT8 mean latency | Summary |
|---|---:|---:|---|
| `yolov8n` | 70.4860 ms | 35.1338 ms | INT8 reduces latency by about 50% |
| `yolov8s` | 86.4330 ms | 49.0504 ms | INT8 shows clear latency improvement |
| `yolov8m` | 171.5369 ms | 84.6368 ms | INT8 improvement remains clear on the larger model |

## 6. What This Validation Confirms

- INT8 latency improvement is consistently observed at roughly `40–50%`.
- Cross-precision comparison is interpreted as `tradeoff_faster` from a latency perspective.
- Without attached accuracy, the same runtime pair remains classified as `unknown_risk`.
- After attaching detection accuracy payloads through `enrich-pair`, the same `yolov8n` runtime pair is reclassified as `acceptable_tradeoff`.
- The enriched comparison uses `map50` as the primary metric and records a `+1.86pp` improvement (`0.7791 → 0.7977`).

In practice, the Odroid RKNN environment shows a clear speed advantage for INT8.
More importantly, InferEdgeLab can convert that observation into a structured and interpretable deployment decision workflow.

This confirms that InferEdgeLab does not treat quantization as a raw speed optimization,
but as a measurable and accuracy-aware deployment trade-off.

## 7. Generated Artifacts

The primary reusable artifacts produced in this validation track are:

- `results/*.json`
- `results_enriched/*.json`
- `reports/*.md`
- `reports/*.html`
- external accuracy payload JSON files used by `enrich-pair`

These artifacts can be reused later in `compare`, `compare-latest`, `history-report`, API adapter, and CI gate workflows.

The enriched validation path is especially important because it proves that a runtime pair can evolve from latency-only evidence to accuracy-aware trade-off evidence without rerunning the full profiling flow.

## 8. Validation Completion Criteria

Odroid RKNN validation is considered complete when all of the following conditions are satisfied:

- profile succeeds
- structured result is generated
- compare-latest succeeds
- report is generated
- enriched results are generated through `enrich-pair`
- enriched compare report is generated
- cross-precision trade-off risk is no longer `unknown_risk` after valid accuracy attachment

## 9. Notes and Limitations

- Without accuracy data, risk interpretation remains limited.
- `rknn` artifacts are strongly device-dependent and should not be assumed to be reusable across different boards or runtime environments.
