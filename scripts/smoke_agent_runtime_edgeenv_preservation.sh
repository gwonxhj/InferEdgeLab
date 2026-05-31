#!/usr/bin/env bash
set -euo pipefail

LAB_DIR="${LAB_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
OUTPUT_DIR="${OUTPUT_DIR:-$LAB_DIR/reports/agent_runtime_edgeenv_preservation}"

usage() {
  cat <<'EOF'
InferEdge Agent Runtime EdgeEnv preservation smoke

Usage:
  bash scripts/smoke_agent_runtime_edgeenv_preservation.sh [--output-dir <path>]
  bash scripts/smoke_agent_runtime_edgeenv_preservation.sh --help

This smoke uses committed lightweight fixtures to verify that an EdgeEnv
runs-show artifact remains visible in the Lab-owned Agent Runtime report.
It does not require a live Jetson device and does not claim production
runtime operation.
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
  LAB_CMD=(poetry run inferedgelab)
else
  LAB_CMD=(inferedgelab)
fi

REPORT_JSON="$OUTPUT_DIR/agent_runtime_edgeenv_preservation.json"
REPORT_MD="$OUTPUT_DIR/agent_runtime_edgeenv_preservation.md"

echo "== Agent Runtime EdgeEnv preservation smoke =="
echo "Output: $OUTPUT_DIR"

"${LAB_CMD[@]}" agent-runtime-report \
  --orchestration-summary examples/agent_runtime/agent_3_orchestration_summary.json \
  --guard-analysis examples/agent_runtime/aiguard_runtime_guard_analysis.json \
  --edgeenv-run-show examples/agent_runtime/edgeenv_run_show_runtime_operation.json \
  --format json \
  --output "$REPORT_JSON"

"${LAB_CMD[@]}" agent-runtime-report \
  --orchestration-summary examples/agent_runtime/agent_3_orchestration_summary.json \
  --guard-analysis examples/agent_runtime/aiguard_runtime_guard_analysis.json \
  --edgeenv-run-show examples/agent_runtime/edgeenv_run_show_runtime_operation.json \
  --format markdown \
  --output "$REPORT_MD"

grep -q "edgeenv_preservation_context" "$REPORT_JSON"
grep -q "run-fixture-edgeenv-operation-0001" "$REPORT_JSON"
grep -q "inferedge-runtime-operation-summary-v1" "$REPORT_JSON"
grep -q "supplemental_evidence_not_gate" "$REPORT_JSON"
grep -q "preservation_identity_label" "$REPORT_JSON"
grep -q "preservation_details_label" "$REPORT_JSON"
grep -q "Runtime Intelligence EdgeEnv Preservation" "$REPORT_MD"
grep -q "preservation_identity" "$REPORT_MD"
grep -q "preservation_details" "$REPORT_MD"
grep -q "edgeenv_run_id" "$REPORT_MD"
grep -q "run-fixture-edgeenv-operation-0001" "$REPORT_MD"
grep -q "runtime_operation_health_reason" "$REPORT_MD"
grep -q "timeout_threshold_exceeded" "$REPORT_MD"
grep -q "review_latency_budget_or_degrade" "$REPORT_MD"
grep -q "supplemental_evidence_not_gate" "$REPORT_MD"
grep -q "Lab remains the final deployment decision owner" "$REPORT_MD"

echo "Agent Runtime EdgeEnv preservation smoke passed."
