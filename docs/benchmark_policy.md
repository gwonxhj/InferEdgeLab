# Benchmark Policy

InferEdgeLab compares structured benchmark results by grouping compatible measurements and reporting backend-level differences.

For Runtime-produced JSON, Lab groups results by `compare_key` and distinguishes backends by `backend_key`.
Runtime latency should be interpreted as end-to-end wall-clock latency, not as a pure accelerator kernel time.

See [docs/portfolio/runtime_compare_yolov8n.md](portfolio/runtime_compare_yolov8n.md) for a real YOLOv8n Runtime comparison example.
