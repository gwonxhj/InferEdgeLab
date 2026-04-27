# YOLOv8n Runtime Backend Comparison

For a broader project-level summary, see [InferEdge Pipeline Portfolio Summary](inferedge_pipeline_portfolio.md).

## Overview

This report summarizes a real InferEdgeRuntime to InferEdgeLab comparison workflow.
InferEdgeRuntime generated compare-ready JSON results, and InferEdgeLab grouped and compared them automatically by `compare_key`.

The comparison group used here is:

- `compare_key`: `yolov8n__b1__h640w640__fp32`

## Test Setup

| Item | Value |
|---|---|
| Model | YOLOv8n |
| Input Shape | 1x3x640x640 |
| Compare Key | yolov8n__b1__h640w640__fp32 |
| ONNX Runtime Backend | onnxruntime__cpu |
| TensorRT Backend | tensorrt__jetson |
| Report Tool | edgebench compare-runtime-dir |

## Result Summary

| Backend | Mean ms | P99 ms | FPS | Status |
|---|---:|---:|---:|---|
| onnxruntime__cpu | 84.288435 | 192.162 | 11.864024 | success |
| tensorrt__jetson | 24.809266 | 26.226712 | 40.30752 | success |

- Fastest backend: `tensorrt__jetson`
- Slowest backend: `onnxruntime__cpu`
- Speedup ratio: `3.4x`
- ONNX Runtime is 3.4x slower than TensorRT.

## Real Image Input Validation

The following validation is based on a real JPEG image input, not dummy input.
InferEdgeRuntime loaded the image with OpenCV, preprocessed it, and then benchmarked the Runtime backend path end to end.

The image preprocessing path was:

- OpenCV `imread`
- BGR to RGB
- resize to `640x640`
- `float32`
- normalize to `0.0` to `1.0`
- NCHW layout

The Runtime JSON recorded `extra.input_mode` as `image` and used `input_preprocess = opencv_bgr_to_rgb_resize_float32_nchw`.
Both backend results used the same `compare_key`, so InferEdgeLab grouped them together for backend comparison:

- `compare_key`: `yolov8n__b1__h640w640__fp32`
- `input_mode`: `image`
- `input_preprocess`: `opencv_bgr_to_rgb_resize_float32_nchw`

| Backend | Input Mode | Mean ms | P99 ms | FPS | Status |
|---|---|---:|---:|---:|---|
| tensorrt__jetson | image | 9.9375 | 15.5231 | 100.6293 | success |
| onnxruntime__cpu | image | 45.4299 | 49.2128 | 22.0119 | success |

- Fastest backend: `tensorrt__jetson`
- Slowest backend: `onnxruntime__cpu`
- Speedup ratio: `4.6x`
- ONNX Runtime is 4.6x slower than TensorRT.

### Result Reproducibility Note

Raw Runtime JSON artifacts are not committed to keep the repository clean.
The benchmark numbers in this document are recorded from validated InferEdgeRuntime and InferEdgeLab runs.
When equivalent local artifacts are available, `compare_key` and `backend_key` make the comparison reproducible through `compare-runtime-dir`.

## Interpretation

The TensorRT Jetson backend showed lower end-to-end runtime latency under this condition.
This result should not be interpreted as absolute hardware superiority because the two measurements use different hardware and backend stacks: ONNX Runtime on Mac CPU and TensorRT on Jetson.

The value of this report is that it validates the full comparison workflow:
Forge/Runtime artifacts can produce structured Runtime JSON, and InferEdgeLab can group, compare, and report multi-backend results through `compare_key` and `backend_key`.

The real image input result is an end-to-end Runtime latency comparison using actual image input.
The TensorRT Jetson measurement includes OpenCV preprocessing followed by TensorRT Runtime execution.
The ONNX Runtime CPU measurement used the same image input and the same `compare_key`.
This confirms that the Forge/Runtime/Lab pipeline is connected not only for dummy benchmarks, but also for real-input validation.

## Benchmark Policy Notes

InferEdgeRuntime latency is end-to-end wall-clock latency.
It may include host-to-device copy, device-to-host copy, enqueue or launch overhead, compute time, and synchronization overhead.

TensorRT Runtime latency should not be directly compared with `trtexec` GPU latency.
`trtexec` exposes lower-level timing metrics, while Runtime JSON is designed to reflect deployment-oriented end-to-end cost.

Real image input results should also not be compared directly with `trtexec` GPU latency.
Before interpreting a Runtime comparison, check whether `input_mode` is `dummy` or `image`.
Even when results share the same `compare_key`, different `input_mode` values should be interpreted as separate benchmark contexts.

InferEdgeLab compares only results with the same `compare_key`.
In this validation, both Runtime results used `yolov8n__b1__h640w640__fp32`, so Lab placed them into the same comparison group.

## Reproduction Commands

Generate the ONNX Runtime JSON from InferEdgeRuntime on Mac:

    cd "/Users/GwonHyeokJun/Documents/New project/InferEdge-Runtime"
    cmake -S . -B build-ort -DINFEREDGE_ENABLE_ORT=ON -DINFEREDGE_ORT_ROOT=$HOME/onnxruntime/onnxruntime-osx-arm64-1.25.0
    cmake --build build-ort
    ./build-ort/inferedge-runtime \
      --manifest examples/manifest.sample.json \
      --model /Users/GwonHyeokJun/Documents/GitHub/edgebench/models/yolov8n.onnx \
      --engine onnxruntime \
      --device cpu \
      --batch 1 \
      --height 640 \
      --width 640 \
      --warmup 10 \
      --runs 50 \
      --output results/onnxruntime_yolov8n_compare.json

Generate the TensorRT JSON from InferEdgeRuntime on Jetson:

    cd ~/InferEdge-Runtime
    cmake -S . -B build-trt -DINFEREDGE_ENABLE_TENSORRT=ON
    cmake --build build-trt
    ./build-trt/inferedge-runtime \
      --manifest /tmp/yolov8n_runtime_manifest.json \
      --warmup 10 \
      --runs 50 \
      --output results/tensorrt_yolov8n_manifest_compare.json

Copy both Runtime JSON files into InferEdgeLab:

    mkdir -p "/Users/GwonHyeokJun/Documents/GitHub/edgebench/results/runtime_compare_real"
    scp nano01:~/InferEdge-Runtime/results/tensorrt_yolov8n_manifest_compare.json \
      "/Users/GwonHyeokJun/Documents/GitHub/edgebench/results/runtime_compare_real/tensorrt_jetson_yolov8n.json"
    cp "/Users/GwonHyeokJun/Documents/New project/InferEdge-Runtime/results/onnxruntime_yolov8n_compare.json" \
      "/Users/GwonHyeokJun/Documents/GitHub/edgebench/results/runtime_compare_real/onnxruntime_cpu_yolov8n.json"

Generate the InferEdgeLab report:

    cd "/Users/GwonHyeokJun/Documents/GitHub/edgebench"
    poetry run edgebench compare-runtime-dir results/runtime_compare_real --report reports/runtime_compare_real.md

## Portfolio Takeaway

This validation is more than a single inference run.
It demonstrates an edge AI validation workflow that connects artifact preparation, runtime benchmarking, structured JSON export, Lab comparison, and Markdown reporting.

InferEdgeRuntime owns measurement and result export.
InferEdgeLab owns comparison, interpretation, and reporting.

The `compare_key` and `backend_key` fields make multi-backend Runtime results automatically comparable without moving comparison logic into Runtime.
