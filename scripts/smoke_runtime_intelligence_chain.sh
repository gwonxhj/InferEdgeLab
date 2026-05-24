#!/usr/bin/env bash
set -euo pipefail

LAB_DIR="${LAB_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
OUTPUT_DIR="${OUTPUT_DIR:-$LAB_DIR/reports/runtime_intelligence_chain}"

usage() {
  cat <<'EOF'
InferEdge Runtime Intelligence local artifact smoke

Usage:
  bash scripts/smoke_runtime_intelligence_chain.sh [--output-dir <path>]
  bash scripts/smoke_runtime_intelligence_chain.sh --help

This smoke reproduces the local-first Runtime Intelligence artifact chain:
  bundle manifest gate
  -> EdgeEnv regression report
  -> Runtime Intelligence report with precomputed AIGuard evidence
  -> report artifact gate
  -> CI artifact gate

It uses committed lightweight fixtures and does not start device workers,
remote execution, cloud telemetry storage, or a production control plane.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --help|-h)
      usage
      exit 0
      ;;
    --output-dir)
      if [[ $# -lt 2 ]]; then
        echo "--output-dir requires a value" >&2
        exit 2
      fi
      OUTPUT_DIR="$2"
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

cd "$LAB_DIR"
mkdir -p "$OUTPUT_DIR"

if command -v poetry >/dev/null 2>&1; then
  PYTHON_CMD=(poetry run python)
  LAB_CMD=(poetry run inferedgelab)
else
  PYTHON_CMD=(python)
  LAB_CMD=(inferedgelab)
fi

echo "== Runtime Intelligence artifact smoke =="
echo "Output: $OUTPUT_DIR"

"${PYTHON_CMD[@]}" scripts/check_runtime_intelligence_bundle_manifest.py \
  --manifest examples/runtime_intelligence_chain/bundle_manifest.json \
  --edgeenv-handoff examples/runtime_intelligence_chain/edgeenv_lab_handoff_manifest.json \
  --summary-out "$OUTPUT_DIR/runtime_intelligence_bundle_manifest_gate_summary.md"

"${LAB_CMD[@]}" compare \
  examples/edgeenv_regression/lab_baseline_result.json \
  examples/edgeenv_regression/lab_candidate_result.json \
  --edgeenv-regression examples/edgeenv_regression/edgeenv_runtime_regression.json \
  --markdown-out "$OUTPUT_DIR/edgeenv_runtime_regression.md" \
  --html-out "$OUTPUT_DIR/edgeenv_runtime_regression.html"

"${LAB_CMD[@]}" compare \
  examples/edgeenv_regression/lab_baseline_result.json \
  examples/edgeenv_regression/lab_candidate_result.json \
  --edgeenv-regression examples/runtime_intelligence_chain/edgeenv_regression_with_orchestrator_context.json \
  --guard-analysis examples/runtime_intelligence_chain/aiguard_runtime_operation_guard_analysis.json \
  --markdown-out "$OUTPUT_DIR/runtime_anomaly_summary.md" \
  --html-out "$OUTPUT_DIR/runtime_anomaly_summary.html"

"${PYTHON_CMD[@]}" scripts/check_runtime_intelligence_artifact_bundle.py \
  --markdown "$OUTPUT_DIR/runtime_anomaly_summary.md" \
  --html "$OUTPUT_DIR/runtime_anomaly_summary.html" \
  --summary-out "$OUTPUT_DIR/runtime_anomaly_gate_summary.md"

"${LAB_CMD[@]}" portfolio-demo-check --format json > "$OUTPUT_DIR/portfolio_demo_check.json"
"${LAB_CMD[@]}" portfolio-demo-check > "$OUTPUT_DIR/portfolio_demo_check.md"
"${LAB_CMD[@]}" portfolio-demo-check --format json > "$OUTPUT_DIR/deployment_risk_summary.json"

"${PYTHON_CMD[@]}" scripts/check_runtime_intelligence_ci_artifacts.py \
  --report-dir "$OUTPUT_DIR" \
  --summary-out "$OUTPUT_DIR/runtime_intelligence_ci_artifact_gate_summary.md"

echo "Runtime Intelligence artifact smoke passed."
