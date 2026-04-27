# InferEdge Pipeline Portfolio Summary

## 1. Project Summary

InferEdge is a portfolio project that splits the edge AI inference workflow into three focused stages:

- InferEdgeForge: prepares model artifacts, conversion outputs, manifests, and metadata.
- InferEdgeRuntime: runs inference on the target device, measures benchmark latency and FPS, and exports JSON results.
- InferEdgeLab: loads Runtime JSON results, groups them by `compare_key`, compares them by `backend_key`, and generates comparison reports.

This project demonstrates an end-to-end edge AI inference validation workflow from artifact preparation to runtime benchmarking and result comparison.

## How to Read This Portfolio

Use this document as the project-level overview.
For the detailed real-input benchmark evidence, read [runtime_compare_yolov8n.md](runtime_compare_yolov8n.md).
For a compact submission draft, use [inferedge_pipeline_portfolio_pdf.md](inferedge_pipeline_portfolio_pdf.md).
For measurement interpretation and limitations, read [benchmark_policy.md](../benchmark_policy.md).

## 2. Problem Definition

In edge AI deployment, converting a model or running one inference command is not enough.
A deployment workflow also needs to answer whether the result is reproducible, comparable, and explainable.

The key problems are:

- Different backends can show very different latency characteristics.
- Different devices have different performance profiles and runtime overheads.
- Dummy benchmarks and real image input benchmarks must be interpreted separately.
- Results should be saved as reproducible JSON and reports, not only terminal logs.
- Hardware acceleration results need to be explained in a way that is understandable to reviewers and deployment stakeholders.

## 3. System Architecture

```text
InferEdgeForge
  -> build / convert / manifest
InferEdgeRuntime
  -> load model or engine
  -> run dummy or real image input inference
  -> measure latency / FPS
  -> export compare-ready JSON
InferEdgeLab
  -> load Runtime JSON
  -> group by compare_key
  -> compare by backend_key
  -> export Markdown report
```

```mermaid
graph LR
    A["InferEdgeForge<br/>Build / Convert / Manifest"] --> B["InferEdgeRuntime<br/>Run Inference / Benchmark / JSON Export"]
    B --> C["InferEdgeLab<br/>Group / Compare / Report"]
    C --> D["Portfolio Report<br/>Markdown / PDF Draft"]
```

Runtime measures. Lab compares. Portfolio documents explain the evidence.

The responsibility boundary is intentional.
Runtime focuses on measurement, while Lab focuses on analysis, comparison, and reporting.
This keeps target-device execution code separate from portfolio/reporting logic.

## 4. Runtime Benchmark Workflow

The benchmark workflow is:

1. Prepare the model artifact through Forge or a local model artifact flow.
2. Select an InferEdgeRuntime backend such as ONNX Runtime CPU or TensorRT.
3. Select dummy input or real image input.
4. Measure latency mean, p99, and FPS in Runtime.
5. Export compare-ready JSON with `compare_key` and `backend_key`.
6. Load the JSON files in InferEdgeLab and generate a backend comparison report.

`compare_key` identifies the comparison group for the same model, input shape, and precision.
`backend_key` identifies the actual backend and device combination, such as `onnxruntime__cpu` or `tensorrt__jetson`.

## 5. Real Image Input Validation Result

This validation used YOLOv8n with real image input:

- Model: YOLOv8n
- Input Mode: image
- Input Shape: `1x3x640x640`
- `compare_key`: `yolov8n__b1__h640w640__fp32`
- `input_preprocess`: `opencv_bgr_to_rgb_resize_float32_nchw`

| Backend | Input Mode | Mean ms | P99 ms | FPS | Status |
|---|---|---:|---:|---:|---|
| TensorRT Jetson | image | 9.9375 | 15.5231 | 100.6293 | success |
| ONNX Runtime CPU | image | 45.4299 | 49.2128 | 22.0119 | success |

- Total compare groups: 1
- Comparable groups count: 1
- Skipped groups count: 0
- Fastest backend: `tensorrt__jetson`
- Slowest backend: `onnxruntime__cpu`
- Speedup ratio: `4.6x`
- ONNX Runtime is 4.6x slower than TensorRT.

The Runtime latency is end-to-end wall-clock latency and should not be directly compared with trtexec GPU-only latency.

## 6. Technical Contribution

The project demonstrates the following technical work:

- C++ Runtime CLI design for repeatable inference benchmarking.
- ONNX Runtime CPU backend benchmarking.
- TensorRT Jetson backend benchmarking.
- OpenCV real image input preprocessing.
- Structured JSON result schema for benchmark outputs.
- `compare_key` and `backend_key` metadata design for automatic grouping.
- InferEdgeLab automatic grouping and backend comparison.
- Markdown report export for portfolio-ready result summaries.
- Benchmark policy documentation for dummy input, real image input, Runtime latency, and trtexec latency interpretation.

## 7. What This Proves

From a hiring perspective, this project shows that I can:

- Validate real TensorRT execution on an edge device.
- Store inference latency as structured data instead of one-off terminal logs.
- Design comparable backend metadata and automate comparison.
- Separate Runtime measurement responsibilities from Lab analysis and reporting responsibilities.
- Verify results using real image input, not only dummy tensors.

## 8. Interview Talking Points

- "I did not only run YOLOv8n; I built a validation pipeline that goes from Runtime JSON to Lab comparison reports."
- "Using the same `compare_key`, I compared ONNX Runtime CPU and TensorRT Jetson, and TensorRT was 4.6x faster with real image input."
- "Runtime latency is measured end to end, so I separated the benchmark policy from trtexec GPU latency."
- "Runtime focuses on measurement, while Lab focuses on comparison and reporting. That separation keeps the system easier to extend."

## 9. Related Documents

- [YOLOv8n Runtime backend comparison](runtime_compare_yolov8n.md)
- [Benchmark policy](../benchmark_policy.md)
- [README](../../README.md)
