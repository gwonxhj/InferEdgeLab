# Jetson TensorRT Validation Runbook

This runbook validates the InferEdgeLab TensorRT execution path on a Jetson environment through a reproducible procedure.
The goal is not only to confirm successful execution, but also to verify that TensorRT profiling results are persisted as structured results and then reused through `compare-latest` and Markdown / HTML report generation.

## 1. Purpose

This document provides a production-style validation runbook for the InferEdgeLab TensorRT path on Jetson.
It verifies end-to-end reuse across TensorRT execution, structured result persistence, compare-latest execution, and report generation.

## 2. Validation Scope

- Environment
  - Jetson
  - TensorRT
  - ONNX source model + compiled engine artifact
- Models
  - `resnet18`
  - `yolov8n`
- Validation targets
  - preflight
  - profiling success
  - structured result persistence
  - `compare-latest` reuse
  - Markdown / HTML report generation

## 3. Prerequisites

Example model and engine files used in validation:

- `models/resnet18.onnx`
- `models/resnet18.engine`
- `models/yolov8n.onnx`
- `models/yolov8n.engine`

`scripts/check_jetson_tensorrt_env.py` is used to verify the minimum environment requirements for TensorRT execution on Jetson before profiling begins.
It is intended to check the validity of the Jetson / TensorRT / `cuda-python` environment and the model / engine artifact combination before running actual profiling commands.

## 4. Preflight Check

Validation command:

```bash
python scripts/check_jetson_tensorrt_env.py \
  --model-path models/resnet18.onnx \
  --engine-path models/resnet18.engine
```

PASS criteria:

- The script exits without error.
- Validation checks for the Jetson marker (`/etc/nv_tegra_release`), `tensorrt` / `onnxruntime` / `numpy`, CUDA Python binding availability, `model_path`, and `engine_path` all report success.
- On failure, the result should allow quick triage between Jetson environment issues, TensorRT / Python module issues, CUDA Python binding issues, and model / engine artifact path issues.
- A successful preflight indicates that `python -m inferedgelab.cli profile --engine tensorrt ...` can be executed on valid assumptions.

## 5. ResNet18 Validation

### 5-1. Run Profiling Twice

Validation was executed through `python -m inferedgelab.cli`.
The same command was run twice to create the latest comparable pair.

```bash
python -m inferedgelab.cli profile models/resnet18.onnx \
  --engine tensorrt \
  --engine-path models/resnet18.engine \
  --precision fp16 \
  --warmup 10 \
  --runs 100 \
  --batch 1 \
  --height 224 \
  --width 224
```

```bash
python -m inferedgelab.cli profile models/resnet18.onnx \
  --engine tensorrt \
  --engine-path models/resnet18.engine \
  --precision fp16 \
  --warmup 10 \
  --runs 100 \
  --batch 1 \
  --height 224 \
  --width 224
```

### 5-2. Compare Latest

```bash
python -m inferedgelab.cli compare-latest \
  --model resnet18.onnx \
  --engine tensorrt \
  --device gpu \
  --precision fp16 \
  --selection-mode same_precision
```

### 5-3. Expected Validation Points

- two structured results are generated
- `engine` / `device` / `precision` metadata is stored
- `runtime_artifact_path` is stored
- `primary_input_name` and `resolved_input_shapes` are stored
- same-precision `compare-latest` executes successfully
- regression interpretation is available

### 5-4. Example Observed Result

| Metric | Base | New | Interpretation |
|---|---:|---:|---|
| mean_ms | 2.8647 | 2.8265 | slight decrease |
| p99_ms | 3.1388 | 3.0620 | slight decrease |
| overall | - | neutral | same-precision neutral under the configured threshold |

Validation also confirmed that `reports/validation/resnet18_tensorrt_latest.md` and `reports/validation/resnet18_tensorrt_latest.html` were generated.
The following fields were also verified directly in the structured result JSON:

- `run_config.engine_path = models/resnet18.engine`
- `extra.runtime_artifact_path = models/resnet18.engine`
- `extra.primary_input_name = input`
- `extra.resolved_input_shapes.input = [1, 3, 224, 224]`
- `extra.effective_batch / effective_height / effective_width = 1 / 224 / 224`

## 6. YOLOv8n Validation

### 6-1. Repeat Profiling

YOLOv8n was profiled repeatedly under the same conditions to create the latest comparable pair.

```bash
python -m inferedgelab.cli profile models/yolov8n.onnx \
  --engine tensorrt \
  --engine-path models/yolov8n.engine \
  --precision fp16 \
  --warmup 10 \
  --runs 50 \
  --batch 1 \
  --height 640 \
  --width 640
```

```bash
python -m inferedgelab.cli profile models/yolov8n.onnx \
  --engine tensorrt \
  --engine-path models/yolov8n.engine \
  --precision fp16 \
  --warmup 10 \
  --runs 50 \
  --batch 1 \
  --height 640 \
  --width 640
```

### 6-2. Compare Latest

```bash
python -m inferedgelab.cli compare-latest \
  --model yolov8n.onnx \
  --engine tensorrt \
  --device gpu \
  --precision fp16 \
  --selection-mode same_precision
```

### 6-3. Save Markdown / HTML Reports

```bash
python -m inferedgelab.cli compare-latest \
  --model yolov8n.onnx \
  --engine tensorrt \
  --device gpu \
  --precision fp16 \
  --selection-mode same_precision \
  --markdown-out reports/validation/yolov8n_tensorrt_latest.md \
  --html-out reports/validation/yolov8n_tensorrt_latest.html
```

Validation also confirmed that `reports/validation/yolov8n_tensorrt_latest.md` and `reports/validation/yolov8n_tensorrt_latest.html` were generated.

### 6-4. Example Observed Result

| Metric | Base | New | Interpretation |
|---|---:|---:|---|
| mean_ms | 14.4592 | 14.1108 | slight decrease |
| p99_ms | 15.4154 | 15.2565 | slight decrease |
| overall | - | neutral | same-precision neutral |

Validation also confirmed that `reports/validation/yolov8n_tensorrt_latest.md` and `reports/validation/yolov8n_tensorrt_latest.html` were generated.
The following fields were also verified directly in the structured result JSON:

- `run_config.engine_path = models/yolov8n.engine`
- `extra.runtime_artifact_path = models/yolov8n.engine`
- `extra.primary_input_name = images`
- `extra.resolved_input_shapes.images = [1, 3, 640, 640]`
- `extra.effective_batch / effective_height / effective_width = 1 / 640 / 640`

## 7. Haeundae YOLOv8n TensorRT Accuracy-Aware Validation

This validation pass is separate from the earlier COCO YOLOv8n TensorRT latency-only records.
It documents only the InferEdgeLab responsibilities in the Haeundae YOLOv8n TensorRT validation workflow: detection accuracy evaluation, accuracy payload enrichment, and accuracy-aware comparison.
TensorRT engine builds, engine artifact hashing, raw benchmark execution, and benchmark metadata management are owned by the external Forge workflow.

### 7-1. Validation Context

- Source model: `models/onnx/yolov8n_haeundae.onnx`
- Dataset image directory: `/home/risenano01/DeepStream-Yolo/datasets/images/val`
- Dataset label directory: `/home/risenano01/DeepStream-Yolo/datasets/labels/val`
- Samples: `1657`
- Task: detection
- Classes: `1`
- Input: RGB, `640x640`
- Confidence threshold: `0.2`
- NMS threshold: `0.45`

### 7-2. Lab Workflow Summary

The Lab-side validation flow was:

1. Accept externally produced TensorRT engine artifacts and structured latency results.
2. Run `evaluate-detection` against the Haeundae validation images and YOLO labels to create detection accuracy payloads.
3. Attach detection accuracy payloads to the existing latency results through `enrich-pair`.
4. Run `compare` on the enriched FP16 and FP32 results to produce an accuracy-aware comparison.

Representative commands:

```bash
python -m inferedgelab.cli evaluate-detection \
  models/onnx/yolov8n_haeundae.onnx \
  --engine tensorrt \
  --engine-path <external-forge-tensorrt-engine> \
  --image-dir /home/risenano01/DeepStream-Yolo/datasets/images/val \
  --label-dir /home/risenano01/DeepStream-Yolo/datasets/labels/val \
  --num-classes 1 \
  --precision fp16 \
  --conf-threshold 0.2 \
  --nms-threshold 0.45 \
  --rgb \
  --out-json accuracy/yolov8n_haeundae_tensorrt_fp16_detection_accuracy.json
```

```bash
python -m inferedgelab.cli enrich-pair \
  --base-result results/yolov8n_haeundae.onnx__tensorrt__gpu__fp16__b1__h640w640__20260425-151440.json \
  --new-result results/yolov8n_haeundae.onnx__tensorrt__gpu__fp32__b1__h640w640__20260425-152321.json \
  --base-accuracy-json accuracy/yolov8n_haeundae_tensorrt_fp16_detection_accuracy.json \
  --new-accuracy-json accuracy/yolov8n_haeundae_tensorrt_fp32_detection_accuracy.json
```

```bash
python -m inferedgelab.cli compare \
  results/yolov8n_haeundae.onnx__tensorrt__gpu__fp16__b1__h640w640__20260425-153017-751881.json \
  results/yolov8n_haeundae.onnx__tensorrt__gpu__fp32__b1__h640w640__20260425-153017-753457.json
```

### 7-3. Lab-Consumed and Lab-Produced Files

| Precision | External Latency Result | Lab Accuracy JSON | Lab Enriched Result |
|---|---|---|---|
| FP16 | `results/yolov8n_haeundae.onnx__tensorrt__gpu__fp16__b1__h640w640__20260425-151440.json` | `accuracy/yolov8n_haeundae_tensorrt_fp16_detection_accuracy.json` | `results/yolov8n_haeundae.onnx__tensorrt__gpu__fp16__b1__h640w640__20260425-153017-751881.json` |
| FP32 | `results/yolov8n_haeundae.onnx__tensorrt__gpu__fp32__b1__h640w640__20260425-152321.json` | `accuracy/yolov8n_haeundae_tensorrt_fp32_detection_accuracy.json` | `results/yolov8n_haeundae.onnx__tensorrt__gpu__fp32__b1__h640w640__20260425-153017-753457.json` |

### 7-4. Accuracy-Aware Compare Output

| Metric | FP16 | FP32 | Delta | Delta % | Judgement |
|---|---:|---:|---:|---:|---|
| mean_ms | 8.8819 | 10.2869 | +1.4049 | +15.82% | regression |
| p99_ms | 13.7437 | 18.1921 | +4.4484 | +32.37% | regression |

| Metric | FP16 | FP32 | Delta |
|---|---:|---:|---:|
| mAP@50 | 0.8037 | 0.8041 | +0.04pp |
| mAP@50-95 | 0.5519 | 0.5520 | +0.01pp |
| F1 score | 0.8195 | 0.8197 | +0.02pp |
| Precision | 0.7983 | 0.7983 | +0.00pp |
| Recall | 0.8419 | 0.8423 | +0.04pp |

### 7-5. Compare Judgement

| Field | Value |
|---|---|
| comparison_mode | `cross_precision` |
| precision_pair | `fp16_vs_fp32` |
| overall_judgement | `tradeoff_slower` |
| mean_judgement | `regression` |
| p99_judgement | `regression` |
| accuracy_judge | `neutral` |
| trade_off_risk | `not_beneficial` |

### 7-6. Conclusion

For this Jetson Orin environment, this Haeundae validation dataset, and this custom YOLOv8n detection model, the Lab-side enriched comparison shows that FP32 provides almost no accuracy benefit while substantially worsening latency.
The downstream Lab judgement is `tradeoff_slower` with `not_beneficial` trade-off risk.

## 8. Generated Artifacts

The artifact types confirmed during this Jetson TensorRT validation are listed below.

### Auto-Synced Validation Evidence

<!-- EDGE_BENCH_JETSON_RUNBOOK_EVIDENCE:START -->

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

## Jetson TensorRT Validation Evidence - YOLOv8n

- Model: `yolov8n.onnx`
- Engine: `tensorrt`
- Device: `gpu`
- Precision pair: `fp16_vs_fp16`
- Overall: **neutral**

| Metric | Base | New |
|---|---:|---:|
| mean_ms | 14.4592 | 14.1108 |
| p99_ms | 15.4154 | 15.2565 |

### Runtime Provenance
- Base runtime_artifact_path: `models/yolov8n.engine`
- New runtime_artifact_path: `models/yolov8n.engine`
- Base primary_input_name: `images`
- New primary_input_name: `images`
- Base resolved_input_shapes: `{'images': [1, 3, 640, 640]}`
- New resolved_input_shapes: `{'images': [1, 3, 640, 640]}`

### Reports
- Markdown: `reports/validation/yolov8n_tensorrt_latest.md`
- HTML: `reports/validation/yolov8n_tensorrt_latest.html`

**Summary**: Same-precision comparison indicates no significant overall change. Accuracy trade-offs are not available in these results.

<!-- EDGE_BENCH_JETSON_RUNBOOK_EVIDENCE:END -->

### ResNet18

- structured runtime result
  - `results/resnet18.onnx__tensorrt__gpu__fp16__b1__h224w224__20260417-064935.json`
  - `results/resnet18.onnx__tensorrt__gpu__fp16__b1__h224w224__20260417-064937.json`
- compare report
  - `reports/validation/resnet18_tensorrt_latest.md`
  - `reports/validation/resnet18_tensorrt_latest.html`

### YOLOv8n

- structured runtime result
  - `results/yolov8n.onnx__tensorrt__gpu__fp16__b1__h640w640__20260417-065012.json`
  - `results/yolov8n.onnx__tensorrt__gpu__fp16__b1__h640w640__20260417-065014.json`
- compare report
  - `reports/validation/yolov8n_tensorrt_latest.md`
  - `reports/validation/yolov8n_tensorrt_latest.html`

In summary, the Jetson validation evidence is composed of two layers:

1. structured results generated through repeated profiling
2. Markdown / HTML compare reports generated from the latest comparable pair

These artifacts are produced on the Jetson validation machine itself, while the README and BENCHMARKS documents serve as summarized references.

## 9. Validation Completion Criteria

- [x] preflight PASS
- [x] TensorRT profiling succeeded
- [x] structured result generated
- [x] `compare-latest` succeeded
- [x] Markdown / HTML reports generated
- [x] runtime provenance fields verified
- [x] Haeundae YOLOv8n TensorRT FP16 vs FP32 accuracy-aware comparison completed

At minimum, the following fields should be checked when validating runtime provenance:

- `runtime_artifact_path`
- `primary_input_name`
- `resolved_input_shapes`

This validation run satisfied all of the above conditions, and the runtime provenance fields were verified directly from the structured result JSON files.

## 10. Interpretation Notes

- same-precision compare should be interpreted primarily for regression tracking
- if `run_config` differs, comparison results should be interpreted with caution
- TensorRT profiling results collected without accuracy should be interpreted primarily from a latency perspective
- Haeundae YOLOv8n TensorRT FP16 vs FP32 results should be interpreted only for the recorded Jetson Orin environment, Haeundae validation dataset, and custom YOLOv8n model
- production-grade robustness validation remains a later phase
- TensorRT `.engine` artifacts are device- and environment-dependent, so plan files generated on the target Jetson are preferred whenever possible
- during validation, TensorRT emitted the warning `Using an engine plan file across different models of devices is not recommended`
- ONNX Runtime may emit a `device_discovery.cc` warning during real-device validation, but in this validation run it did not break the profiling / compare / report workflow

## 11. Related Documents

- [README.md](../../README.md)
- [BENCHMARKS.md](../../BENCHMARKS.md)
- [docs/portfolio/edgebench_portfolio.md](../portfolio/edgebench_portfolio.md)
