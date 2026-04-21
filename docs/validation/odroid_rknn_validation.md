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
| `yolov8n` | ~70 ms | ~35 ms | INT8 is reduced to roughly half of FP16 latency |
| `yolov8s` | ~86 ms | ~49 ms | INT8 shows clear latency improvement |
| `yolov8m` | ~171 ms | ~84 ms | INT8 improvement remains visible on the larger model |

## 6. What This Validation Confirms

- INT8 latency improvement is consistently observed at roughly `40–50%`.
- Cross-precision comparison is interpreted as `tradeoff_faster` from a latency perspective.
- When accuracy is not attached, risk interpretation remains incomplete and is classified as `unknown_risk`.

In practice, the Odroid RKNN environment shows a clear speed advantage for INT8. However, without accuracy evidence, the workflow should not automatically treat that result as a complete deployment decision.

This validation confirms that InferEdgeLab can capture quantization-driven performance differences and represent them as structured comparison outputs rather than raw logs.

The same workflow can be extended later by attaching accuracy results, enabling full deployment decision validation.

This confirms that InferEdgeLab does not treat quantization as a raw speed optimization,
but as a measurable and interpretable deployment trade-off.

## 7. Generated Artifacts

The primary reusable artifacts produced in this validation track are:

- `results/*.json`
- `reports/*.md`
- `reports/*.html`

These artifacts can be reused later in `compare`, `compare-latest`, `history-report`, API adapter, and CI gate workflows.

## 8. Validation Completion Criteria

Odroid RKNN validation is considered complete when all of the following conditions are satisfied:

- profile succeeds
- structured result is generated
- compare-latest succeeds
- report is generated

## 9. Notes and Limitations

- Without accuracy data, risk interpretation remains limited.
- `rknn` artifacts are strongly device-dependent and should not be assumed to be reusable across different boards or runtime environments.
