#!/usr/bin/env bash
set -euo pipefail

LAB_DIR="${LAB_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
RUNTIME_DIR="${RUNTIME_DIR:-$(cd "$LAB_DIR/.." && pwd)/InferEdge-Runtime}"
JETSON_RUNTIME_DIR="${JETSON_RUNTIME_DIR:-~/InferEdge-Runtime}"
JETSON_FORGE_BUILD_DIR="${JETSON_FORGE_BUILD_DIR:-~/InferEdgeForge/builds/yolov8n__jetson__tensorrt__jetson_fp16}"
RUNTIME_BIN="${RUNTIME_BIN:-./build-trt-opencv/inferedge-runtime}"
MANIFEST_PATH="${MANIFEST_PATH:-$JETSON_FORGE_BUILD_DIR/manifest.json}"
MODEL_ENGINE="${MODEL_ENGINE:-$JETSON_FORGE_BUILD_DIR/model.engine}"
JETSON_OUTPUT="${JETSON_OUTPUT:-results/jetson/yolov8n_jetson_tensorrt_manifest_identity_smoke.json}"

MODE="dry-run"

usage() {
  cat <<EOF
InferEdge end-to-end guided demo

Usage:
  bash scripts/demo_pipeline_full.sh [--dry-run]
  bash scripts/demo_pipeline_full.sh --run-local-lab
  bash scripts/demo_pipeline_full.sh --run-jetson-command-print
  bash scripts/demo_pipeline_full.sh --run-jetson-local
  bash scripts/demo_pipeline_full.sh --help

Modes:
  --dry-run                   Print the guided portfolio demo summary. This is the default.
  --run-local-lab             Run a lightweight local Lab validation command.
  --run-jetson-command-print  Print the Jetson TensorRT Runtime command without executing it.
  --run-jetson-local          Execute the Jetson TensorRT Runtime command on the current machine.

Environment overrides:
  LAB_DIR                  Default: current InferEdgeLab repository
  RUNTIME_DIR              Default: sibling InferEdge-Runtime repository
  JETSON_RUNTIME_DIR       Default: ~/InferEdge-Runtime
  JETSON_FORGE_BUILD_DIR   Default: ~/InferEdgeForge/builds/yolov8n__jetson__tensorrt__jetson_fp16
  RUNTIME_BIN              Default: ./build-trt-opencv/inferedge-runtime
  MANIFEST_PATH            Default: \$JETSON_FORGE_BUILD_DIR/manifest.json
  MODEL_ENGINE             Default: \$JETSON_FORGE_BUILD_DIR/model.engine
  JETSON_OUTPUT            Default: results/jetson/yolov8n_jetson_tensorrt_manifest_identity_smoke.json

This is a guided portfolio demo, not a production daemon, queue, database, or SaaS worker.
EOF
}

jetson_command() {
  cat <<EOF
cd $JETSON_RUNTIME_DIR
$RUNTIME_BIN \\
  --manifest $MANIFEST_PATH \\
  --model $MODEL_ENGINE \\
  --engine tensorrt \\
  --device jetson \\
  --height 640 \\
  --width 640 \\
  --runs 5 \\
  --warmup 1 \\
  --output $JETSON_OUTPUT
EOF
}

expand_path() {
  case "$1" in
    "~") printf '%s\n' "$HOME" ;;
    "~/"*) printf '%s\n' "$HOME/${1#"~/"}" ;;
    *) printf '%s\n' "$1" ;;
  esac
}

print_summary() {
  cat <<EOF
=== InferEdge End-to-End Demo ===
Pipeline: Forge -> Runtime -> Lab -> optional AIGuard
Scope: SaaS-ready validation foundation, not production SaaS

Evidence 1: macOS Lab -> Runtime ONNX Runtime CPU smoke
  Flow: /api/analyze -> /api/jobs/{job_id}/run-runtime-dev -> /api/jobs/{job_id}
  Result: Lab job completed, Runtime JSON ingested, deployment_decision present

Evidence 2: Jetson Orin Nano TensorRT manifest smoke
  Forge manifest + TensorRT model.engine -> C++ Runtime CLI -> Runtime JSON
  Jetson TensorRT: mean ~14.00 ms, p99 ~15.50 ms, FPS ~71.44

Evidence 3: YOLOv8n real image benchmark
  TensorRT Jetson: mean 9.9375 ms, p99 15.5231 ms, FPS 100.6293
  ONNX Runtime CPU: mean 45.4299 ms, p99 49.2128 ms, FPS 22.0119
  Real image speedup: 4.6x wall-clock Runtime latency

Compare readiness:
  Runtime preserves Forge manifest source_model identity for TensorRT engine artifacts.
  compare_model_name: yolov8n
  compare_key: yolov8n__b1__h640w640__fp32

Decision owner: Lab
AIGuard role: optional deterministic diagnosis evidence
Future work: production worker daemon, DB/queue, upload, frontend, auth/billing

Useful commands:
  bash scripts/demo_pipeline_full.sh --run-local-lab
  bash scripts/demo_pipeline_full.sh --run-jetson-command-print
  bash scripts/demo_pipeline_full.sh --run-jetson-local   # run only on Jetson
EOF
}

run_local_lab() {
  echo "=== Local Lab lightweight validation ==="
  echo "LAB_DIR=$LAB_DIR"
  cd "$LAB_DIR"
  if command -v poetry >/dev/null 2>&1; then
    poetry run python3 -m pytest tests/test_api_worker_workflow.py tests/test_runtime_execution_smoke.py -q
  else
    python3 -m pytest tests/test_api_worker_workflow.py tests/test_runtime_execution_smoke.py -q
  fi
}

run_jetson_local() {
  echo "=== Running Jetson TensorRT Runtime command locally ==="
  echo "This mode assumes the current machine is the Jetson device."
  local runtime_dir output_path
  runtime_dir="$(expand_path "$JETSON_RUNTIME_DIR")"
  output_path="$(expand_path "$JETSON_OUTPUT")"
  cd "$runtime_dir"
  mkdir -p "$(dirname "$output_path")"
  "$RUNTIME_BIN" \
    --manifest "$(expand_path "$MANIFEST_PATH")" \
    --model "$(expand_path "$MODEL_ENGINE")" \
    --engine tensorrt \
    --device jetson \
    --height 640 \
    --width 640 \
    --runs 5 \
    --warmup 1 \
    --output "$output_path"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --help|-h)
      usage
      exit 0
      ;;
    --dry-run)
      MODE="dry-run"
      ;;
    --run-local-lab)
      MODE="run-local-lab"
      ;;
    --run-jetson-command-print)
      MODE="run-jetson-command-print"
      ;;
    --run-jetson-local)
      MODE="run-jetson-local"
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

case "$MODE" in
  dry-run)
    print_summary
    ;;
  run-local-lab)
    print_summary
    echo
    run_local_lab
    ;;
  run-jetson-command-print)
    print_summary
    echo
    echo "=== Jetson TensorRT command ==="
    jetson_command
    ;;
  run-jetson-local)
    print_summary
    echo
    run_jetson_local
    ;;
esac
