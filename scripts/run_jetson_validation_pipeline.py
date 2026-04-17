from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from edgebench.result.loader import latest_comparable_result_paths


def _print_step(title: str) -> None:
    print(f"\n== {title} ==")


def _run_command(command: Sequence[str]) -> None:
    print("+", " ".join(shlex.quote(part) for part in command))
    subprocess.run(command, check=True)


def _build_validation_command(
    *,
    model_path: Path,
    engine_path: Path,
    precision: str,
    repeat: int,
    report_dir: Path,
) -> list[str]:
    return [
        sys.executable,
        "scripts/run_jetson_tensorrt_validation.py",
        "--model-path",
        str(model_path),
        "--engine-path",
        str(engine_path),
        "--precision",
        precision,
        "--repeat",
        str(repeat),
        "--report-dir",
        str(report_dir),
    ]


def _build_export_command(
    *,
    base_result: str,
    new_result: str,
    label: str,
    markdown_out: Path,
    report_markdown_path: Path,
    report_html_path: Path,
) -> list[str]:
    return [
        sys.executable,
        "scripts/export_validation_evidence.py",
        "--base-result",
        base_result,
        "--new-result",
        new_result,
        "--label",
        label,
        "--markdown-out",
        str(markdown_out),
        "--report-markdown-path",
        str(report_markdown_path),
        "--report-html-path",
        str(report_html_path),
    ]


def _default_evidence_out(model_path: Path, report_dir: Path) -> Path:
    return report_dir / f"{model_path.stem}_validation_evidence.md"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the full Jetson TensorRT validation pipeline and export markdown evidence."
    )
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--engine-path", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--precision", default="fp16")
    parser.add_argument("--repeat", type=int, default=2)
    parser.add_argument("--report-dir", default="reports/validation")
    parser.add_argument("--evidence-out", default="auto-generated")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    model_path = Path(args.model_path)
    engine_path = Path(args.engine_path)
    report_dir = Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)

    report_base = f"{model_path.stem}_tensorrt_latest"
    report_markdown_path = report_dir / f"{report_base}.md"
    report_html_path = report_dir / f"{report_base}.html"

    if args.evidence_out == "auto-generated":
        evidence_out = _default_evidence_out(model_path, report_dir)
    else:
        evidence_out = Path(args.evidence_out)

    _print_step("Jetson TensorRT Validation")
    _run_command(
        _build_validation_command(
            model_path=model_path,
            engine_path=engine_path,
            precision=str(args.precision),
            repeat=int(args.repeat),
            report_dir=report_dir,
        )
    )
    print("Profile runs done.")

    _print_step("Locate Latest Pair")
    base_result, new_result = latest_comparable_result_paths("results/*.json")
    print(f"Base result    : {base_result}")
    print(f"New result     : {new_result}")

    _print_step("Export Validation Evidence")
    _run_command(
        _build_export_command(
            base_result=base_result,
            new_result=new_result,
            label=str(args.label),
            markdown_out=evidence_out,
            report_markdown_path=report_markdown_path,
            report_html_path=report_html_path,
        )
    )

    print(f"Compare report path : {report_markdown_path}")
    print(f"Evidence path       : {evidence_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
