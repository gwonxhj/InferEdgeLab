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

if ! command -v xelatex >/dev/null 2>&1; then
  echo "error: xelatex is required to export the InferEdge portfolio PDF." >&2
  echo "Install a TeX distribution with xelatex, then rerun: bash scripts/export_portfolio_pdf.sh" >&2
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
  --pdf-engine=xelatex \
  --metadata title="InferEdge Portfolio Submission" \
  -V mainfont="Apple SD Gothic Neo" \
  -V sansfont="Apple SD Gothic Neo" \
  -V monofont="Menlo" \
  -V geometry:margin=0.8in \
  -V hyphenpenalty=10000 \
  -V exhyphenpenalty=10000 \
  --output "${OUTPUT}"

echo "Exported portfolio PDF: ${OUTPUT}"
