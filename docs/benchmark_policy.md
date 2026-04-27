# Benchmark Policy

InferEdgeLab compares structured benchmark results by grouping compatible measurements and reporting backend-level differences.

For Runtime-produced JSON, Lab groups results by `compare_key` and distinguishes backends by `backend_key`.
Runtime latency should be interpreted as end-to-end wall-clock latency, not as a pure accelerator kernel time.
Real image input benchmarks should be interpreted separately from dummy input benchmarks.
Runtime JSON `extra.input_mode` distinguishes dummy and image input runs, so matching `compare_key` values still need input-mode context before drawing conclusions.

See [docs/portfolio/runtime_compare_yolov8n.md](portfolio/runtime_compare_yolov8n.md) for a real YOLOv8n Runtime comparison example, including a real image input comparison.

## Limitations / Future Work

- TensorRT INT8 optimization is planned but intentionally not included in the current Runtime comparison.
- Multi-stream execution and batching are future work.
- Accuracy validation can be added as a separate pipeline stage.
- Real image input and dummy input results must be interpreted separately.
