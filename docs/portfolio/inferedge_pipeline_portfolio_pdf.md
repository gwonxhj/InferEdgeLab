# InferEdge Pipeline Portfolio PDF Draft

## Page 1. Project Overview

### One-Line Summary

InferEdge is an end-to-end edge AI inference validation pipeline that connects model artifact preparation, runtime benchmarking, and automated result comparison.

### Problem

Edge AI deployment is not finished when a model is converted or a single inference command runs.
A practical deployment workflow needs to answer:

- Which backend is actually faster under the same model, shape, and precision?
- Is the benchmark based on dummy input or real image input?
- Can the result be reproduced as structured evidence instead of a one-off terminal log?
- Can hardware acceleration results be explained clearly to engineers, reviewers, and hiring interviewers?

### Pipeline Overview

InferEdge separates the workflow into three responsibilities:

- InferEdgeForge prepares model artifacts, manifests, and metadata.
- InferEdgeRuntime runs inference on target backends and exports benchmark JSON.
- InferEdgeLab groups Runtime JSON by `compare_key`, compares by `backend_key`, and exports reports.

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

## Page 3. Real Benchmark Result & Contribution

### Real Image Input Benchmark

- Model: YOLOv8n
- Input Mode: image
- Input Shape: `1x3x640x640`
- `compare_key`: `yolov8n__b1__h640w640__fp32`
- `input_preprocess`: `opencv_bgr_to_rgb_resize_float32_nchw`

| Backend | Input Mode | Mean ms | P99 ms | FPS | Status |
|---|---|---:|---:|---:|---|
| TensorRT Jetson | image | 9.9375 | 15.5231 | 100.6293 | success |
| ONNX Runtime CPU | image | 45.4299 | 49.2128 | 22.0119 | success |

TensorRT Jetson was 4.6x faster than ONNX Runtime CPU in this real image input benchmark.

Runtime latency is measured as end-to-end wall-clock latency and should not be directly compared with trtexec GPU-only latency.

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
