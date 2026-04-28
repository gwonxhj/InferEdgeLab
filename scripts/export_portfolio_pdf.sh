#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INPUT="${ROOT_DIR}/docs/portfolio/inferedge_portfolio_submission.md"
OUTPUT="${ROOT_DIR}/artifacts/portfolio/inferedge_portfolio_submission.pdf"

if ! command -v pandoc >/dev/null 2>&1; then
  echo "error: pandoc is required to export the InferEdge portfolio PDF." >&2
  echo "Install pandoc locally, then rerun: bash scripts/export_portfolio_pdf.sh" >&2
  exit 127
fi

if [[ ! -f "${INPUT}" ]]; then
  echo "error: input Markdown not found: ${INPUT}" >&2
  exit 1
fi

mkdir -p "$(dirname "${OUTPUT}")"

pandoc "${INPUT}" \
  --from markdown \
  --standalone \
  --metadata title="InferEdge Portfolio Submission" \
  --output "${OUTPUT}"

echo "Exported portfolio PDF: ${OUTPUT}"
