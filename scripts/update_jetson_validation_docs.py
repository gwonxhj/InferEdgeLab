from __future__ import annotations

import argparse
from pathlib import Path


README_MARK_START = "<!-- EDGE_BENCH_JETSON_EVIDENCE:START -->"
README_MARK_END = "<!-- EDGE_BENCH_JETSON_EVIDENCE:END -->"
RUNBOOK_MARK_START = "<!-- EDGE_BENCH_JETSON_RUNBOOK_EVIDENCE:START -->"
RUNBOOK_MARK_END = "<!-- EDGE_BENCH_JETSON_RUNBOOK_EVIDENCE:END -->"


def _read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Evidence source file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def _build_evidence_block(resnet18_evidence: Path, yolov8n_evidence: Path) -> str:
    parts = [
        _read_text(resnet18_evidence),
        _read_text(yolov8n_evidence),
    ]
    return "\n\n".join(parts).strip()


def replace_marker_block(text: str, start_marker: str, end_marker: str, block: str) -> str:
    start = text.find(start_marker)
    end = text.find(end_marker)
    if start == -1 or end == -1 or end <= start:
        raise RuntimeError(f"Could not find marker block: {start_marker} ... {end_marker}")
    replacement = f"{start_marker}\n\n{block.strip()}\n\n{end_marker}"
    return text[:start] + replacement + text[end + len(end_marker):]


def update_jetson_validation_docs(
    *,
    readme_path: Path,
    runbook_path: Path,
    resnet18_evidence_path: Path,
    yolov8n_evidence_path: Path,
) -> None:
    evidence_block = _build_evidence_block(resnet18_evidence_path, yolov8n_evidence_path)

    readme = readme_path.read_text(encoding="utf-8")
    updated_readme = replace_marker_block(readme, README_MARK_START, README_MARK_END, evidence_block)
    readme_path.write_text(updated_readme, encoding="utf-8")

    runbook = runbook_path.read_text(encoding="utf-8")
    updated_runbook = replace_marker_block(runbook, RUNBOOK_MARK_START, RUNBOOK_MARK_END, evidence_block)
    runbook_path.write_text(updated_runbook, encoding="utf-8")

    print(f"Updated {readme_path} and {runbook_path}.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--readme", required=True)
    parser.add_argument("--runbook", required=True)
    parser.add_argument("--resnet18-evidence", required=True)
    parser.add_argument("--yolov8n-evidence", required=True)
    args = parser.parse_args()

    update_jetson_validation_docs(
        readme_path=Path(args.readme),
        runbook_path=Path(args.runbook),
        resnet18_evidence_path=Path(args.resnet18_evidence),
        yolov8n_evidence_path=Path(args.yolov8n_evidence),
    )


if __name__ == "__main__":
    main()
