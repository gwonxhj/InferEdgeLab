#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
InferEdge guided pipeline smoke

This script documents and optionally runs reproducible manual smoke paths.
It does not start a production worker daemon, queue, database, or SaaS worker.

Usage:
  bash scripts/demo_pipeline_smoke.sh --help
  bash scripts/demo_pipeline_smoke.sh
  bash scripts/demo_pipeline_smoke.sh --run-jetson

Modes:
  default       Print the macOS Lab -> Runtime ONNX Runtime smoke and Jetson TensorRT smoke commands.
  --run-jetson  Execute the Jetson TensorRT Runtime command in the current shell.

Environment overrides:
  JETSON_RUNTIME_DIR      Default: /home/risenano01/InferEdge-Runtime
  JETSON_FORGE_BUILD_DIR  Default: /home/risenano01/InferEdgeForge/builds/yolov8n__jetson__tensorrt__jetson_fp16
  RUNTIME_BIN             Default: ./build-trt-opencv/inferedge-runtime
  MODEL_ENGINE            Default: $JETSON_FORGE_BUILD_DIR/model.engine
  MANIFEST_PATH           Default: $JETSON_FORGE_BUILD_DIR/manifest.json
  JETSON_RESULT_PATH      Default: results/jetson/yolov8n_jetson_tensorrt_manifest_smoke.json

Validated evidence captured in portfolio docs:
  1. macOS ONNX Runtime CPU smoke through Lab's dev-only Runtime execution path using yolov8n.onnx.
  2. Jetson Orin Nano TensorRT smoke using a Forge-generated manifest and TensorRT engine artifact.
EOF
}

RUN_JETSON=0
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
elif [[ "${1:-}" == "--run-jetson" ]]; then
  RUN_JETSON=1
elif [[ $# -gt 0 ]]; then
  echo "Unknown argument: $1" >&2
  usage >&2
  exit 2
fi

JETSON_RUNTIME_DIR="${JETSON_RUNTIME_DIR:-/home/risenano01/InferEdge-Runtime}"
JETSON_FORGE_BUILD_DIR="${JETSON_FORGE_BUILD_DIR:-/home/risenano01/InferEdgeForge/builds/yolov8n__jetson__tensorrt__jetson_fp16}"
RUNTIME_BIN="${RUNTIME_BIN:-./build-trt-opencv/inferedge-runtime}"
MODEL_ENGINE="${MODEL_ENGINE:-$JETSON_FORGE_BUILD_DIR/model.engine}"
MANIFEST_PATH="${MANIFEST_PATH:-$JETSON_FORGE_BUILD_DIR/manifest.json}"
JETSON_RESULT_PATH="${JETSON_RESULT_PATH:-results/jetson/yolov8n_jetson_tensorrt_manifest_smoke.json}"

cat <<EOF
== InferEdge manual smoke guide ==

Path 1: macOS Lab -> Runtime ONNX Runtime CPU smoke
  Flow:
    /api/analyze
    -> /api/jobs/{job_id}/run-runtime-dev
    -> /api/jobs/{job_id}

  Evidence:
    model: yolov8n.onnx
    Runtime: C++ CLI via Lab dev-only subprocess path
    backend: ONNX Runtime CPU
    result: Lab job completed and Runtime JSON ingested

Path 2: Jetson TensorRT Runtime smoke
  Device:
    Jetson Orin Nano, Linux 5.15.148-tegra, aarch64

  Runtime repo:
    $JETSON_RUNTIME_DIR

  Forge manifest:
    $MANIFEST_PATH

  TensorRT engine artifact:
    $MODEL_ENGINE

  Result JSON:
    $JETSON_RESULT_PATH

  Runtime command:
    cd "$JETSON_RUNTIME_DIR"
    "$RUNTIME_BIN" \\
      --manifest "$MANIFEST_PATH" \\
      --model "$MODEL_ENGINE" \\
      --engine tensorrt \\
      --device jetson \\
      --height 640 \\
      --width 640 \\
      --runs 5 \\
      --warmup 1 \\
      --output "$JETSON_RESULT_PATH"

  Expected evidence:
    success: true
    status: success
    engine_backend: tensorrt
    device_name: jetson
    manifest_applied: true
    compare_model_name: yolov8n
    compare_key: yolov8n__b1__h640w640__fp32
    input shape: [1, 3, 640, 640]
    output shape: [1, 84, 8400]
    mean_ms: 13.997197
    p99_ms: 15.499456
    fps_value: 71.442877

Note:
  This is a guided/manual smoke script, not production worker orchestration.
  Runtime now preserves Forge manifest source_model identity for compare naming
  when a manifest is applied, so explicit model.engine artifact paths can still
  produce yolov8n compare keys.
EOF

if [[ "$RUN_JETSON" -eq 1 ]]; then
  echo
  echo "== Running Jetson TensorRT smoke =="
  cd "$JETSON_RUNTIME_DIR"
  mkdir -p "$(dirname "$JETSON_RESULT_PATH")"
  "$RUNTIME_BIN" \
    --manifest "$MANIFEST_PATH" \
    --model "$MODEL_ENGINE" \
    --engine tensorrt \
    --device jetson \
    --height 640 \
    --width 640 \
    --runs 5 \
    --warmup 1 \
    --output "$JETSON_RESULT_PATH"
fi
