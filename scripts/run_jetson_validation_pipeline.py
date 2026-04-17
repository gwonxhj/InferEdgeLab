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
    warmup: int,
    runs: int,
    batch: int,
    height: int,
    width: int,
    repeat: int,
    report_dir: Path,
    skip_preflight: bool,
    dry_run: bool,
) -> list[str]:
    command = [
        sys.executable,
        "scripts/run_jetson_tensorrt_validation.py",
        "--model-path",
        str(model_path),
        "--engine-path",
        str(engine_path),
        "--precision",
        precision,
        "--warmup",
        str(warmup),
        "--runs",
        str(runs),
        "--batch",
        str(batch),
        "--height",
        str(height),
        "--width",
        str(width),
        "--repeat",
        str(repeat),
        "--report-dir",
        str(report_dir),
    ]

    if skip_preflight:
        command.append("--skip-preflight")
    if dry_run:
        command.append("--dry-run")

    return command


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
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument("--runs", type=int, default=100)
    parser.add_argument("--batch", type=int, default=1)
    parser.add_argument("--height", type=int, default=0)
    parser.add_argument("--width", type=int, default=0)
    parser.add_argument("--repeat", type=int, default=2)
    parser.add_argument("--report-dir", default="reports/validation")
    parser.add_argument("--evidence-out", default="auto-generated")
    parser.add_argument("--skip-preflight", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
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
            warmup=int(args.warmup),
            runs=int(args.runs),
            batch=int(args.batch),
            height=int(args.height),
            width=int(args.width),
            repeat=int(args.repeat),
            report_dir=report_dir,
            skip_preflight=bool(args.skip_preflight),
            dry_run=bool(args.dry_run),
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
