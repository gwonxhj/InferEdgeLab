#!/usr/bin/env bash
set -euo pipefail

LAB_DIR="${LAB_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
OUTPUT_DIR="${OUTPUT_DIR:-$LAB_DIR/reports/agent_runtime_remote_paths}"

usage() {
  cat <<'EOF'
InferEdge Agent Runtime remote dispatch path smoke

Usage:
  bash scripts/smoke_agent_runtime_remote_paths.sh [--output-dir <path>]
  bash scripts/smoke_agent_runtime_remote_paths.sh --help

This smoke reproduces two local-first remote dispatch starter paths:
  plan-only worker selection
  fallback-recovered starter execution

It uses committed lightweight fixtures and does not start remote workers,
open SSH/HTTP connections, or claim production remote execution.
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

PLAN_ONLY_MD="$OUTPUT_DIR/remote_dispatch_plan_only.md"
FALLBACK_MD="$OUTPUT_DIR/remote_dispatch_fallback_recovered.md"

echo "== Agent Runtime remote dispatch path smoke =="
echo "Output: $OUTPUT_DIR"

"${LAB_CMD[@]}" agent-runtime-report \
  --orchestration-summary examples/agent_runtime/agent_3_orchestration_summary.json \
  --guard-analysis examples/agent_runtime/aiguard_runtime_guard_analysis.json \
  --remote-dispatch examples/agent_runtime/remote_dispatch_plan_only.json \
  --format markdown \
  --output "$PLAN_ONLY_MD"

"${LAB_CMD[@]}" agent-runtime-report \
  --orchestration-summary examples/agent_runtime/agent_3_orchestration_summary.json \
  --guard-analysis examples/runtime_intelligence_chain/aiguard_runtime_operation_guard_analysis.json \
  --remote-dispatch examples/agent_runtime/remote_dispatch_fallback_recovered.json \
  --format markdown \
  --output "$FALLBACK_MD"

grep -q "execution_plan_mode" "$PLAN_ONLY_MD"
grep -q "plan_only" "$PLAN_ONLY_MD"
grep -q "remote_runtime_summary_boundary" "$PLAN_ONLY_MD"
grep -q "remote dispatch starter evidence only" "$PLAN_ONLY_MD"
grep -q "remote_operation_final_status" "$FALLBACK_MD"
grep -q "succeeded" "$FALLBACK_MD"
grep -q "remote_runtime_event_count" "$FALLBACK_MD"
grep -q "remote_runtime_summary_boundary" "$FALLBACK_MD"
grep -q "remote dispatch starter evidence only" "$FALLBACK_MD"
grep -q "remote_execution_recovered_by_fallback" "$FALLBACK_MD"

echo "Agent Runtime remote dispatch path smoke passed."
