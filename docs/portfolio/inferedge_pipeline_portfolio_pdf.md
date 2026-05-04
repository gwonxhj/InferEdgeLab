# InferEdge Pipeline Portfolio PDF Draft

> Status note: this is an older compact PDF draft retained as reference.
> The current PDF source is [inferedge_portfolio_submission.md](inferedge_portfolio_submission.md),
> with final resume/interview wording in [inferedge_resume_interview_summary.md](inferedge_resume_interview_summary.md).

## Page 1. Project Overview

### One-Line Summary

InferEdge is an end-to-end edge AI inference validation pipeline that connects build provenance, runtime execution, Lab comparison/reporting, optional diagnosis evidence, and deployment decisions.

### Problem

Edge AI deployment is not finished when a model is converted or a single inference command runs.
A practical deployment workflow needs to answer:

- Which backend is actually faster under the same model, shape, and precision?
- Is the benchmark based on dummy input or real image input?
- Can the result be reproduced as structured evidence instead of a one-off terminal log?
- Can hardware acceleration results be explained clearly to engineers, reviewers, and hiring interviewers?

### Pipeline Overview

InferEdge separates the workflow into repository responsibilities:

- InferEdgeForge prepares model artifacts, manifests, and metadata.
- InferEdgeRuntime runs inference on target backends and exports benchmark JSON.
- InferEdgeLab groups Runtime JSON by `compare_key`, compares by `backend_key`, and exports reports.
- InferEdgeAIGuard optionally provides deterministic rule/evidence diagnosis.

This makes the project more than a YOLOv8n demo. It is a reproducible validation pipeline from artifact preparation to measurable backend comparison.

---

## Page 2. System Architecture & Workflow

### Architecture

```text
InferEdgeForge
  -> build / convert / manifest / metadata
InferEdgeRuntime
  -> load model or engine
  -> run dummy or real image input inference
  -> measure latency and FPS
  -> export compare-ready JSON
InferEdgeLab
  -> load Runtime JSON
  -> group by compare_key
  -> compare by backend_key
  -> export Markdown report
```

### Responsibility Split

- Runtime is responsible for measurement.
- Lab is responsible for comparison and reporting.
- `compare_key` defines the comparison group for the same model, shape, and precision.
- `backend_key` identifies the backend/device combination, such as `onnxruntime__cpu` or `tensorrt__jetson`.

### Workflow

1. Prepare a model or engine artifact through Forge or a local artifact flow.
2. Run InferEdgeRuntime with ONNX Runtime CPU or TensorRT Jetson.
3. Select dummy input or real OpenCV image input.
4. Measure mean latency, p99 latency, and FPS.
5. Export compare-ready JSON.
6. Use InferEdgeLab to generate a Markdown comparison report.

---

## Page 3. Current Demo Evidence & Contribution

### Local Studio Demo Evidence

- Model: YOLOv8n
- Input Shape: `1x3x640x640`
- ONNX baseline `compare_key`: `yolov8n__b1__h640w640__fp32`
- TensorRT candidate `compare_key`: `yolov8n__b1__h640w640__fp16`
- TensorRT power mode: `25W`

| Backend | Precision | Power Mode | Mean ms | P99 ms | FPS | Status |
|---|---|---|---:|---:|---:|---|
| TensorRT Jetson | FP16 | 25W | 10.066401 | 15.548438 | 99.340373 | success |
| ONNX Runtime CPU | FP32 | n/a | 45.4299 | 49.2128 | 22.0119 | success |

TensorRT Jetson FP16 25W was about 4.51x faster than ONNX Runtime CPU FP32 in the current Local Studio demo evidence.

Runtime latency is measured as end-to-end wall-clock latency and should not be directly compared with trtexec GPU-only latency.
The historical real-image input benchmark remains documented separately in `runtime_compare_yolov8n.md`.

### Technical Contribution

- C++ Runtime CLI design
- ONNX Runtime CPU benchmark
- TensorRT Jetson benchmark
- OpenCV real image input preprocessing
- Structured JSON result schema
- `compare_key` / `backend_key` based automatic comparison
- Markdown report export
- Benchmark policy documentation

### Interview Summary

I did not simply run YOLOv8n.
I implemented an end-to-end validation pipeline from real image input inference to JSON export, backend comparison, and Markdown reporting.

### Source Documents

- [Full pipeline summary](inferedge_pipeline_portfolio.md)
- [YOLOv8n Runtime comparison](runtime_compare_yolov8n.md)
- [Benchmark policy](../benchmark_policy.md)
