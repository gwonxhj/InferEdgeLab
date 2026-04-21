from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Sequence


def _print_step(title: str) -> None:
    print(f"\n== {title} ==")


def _run_command(command: Sequence[str], dry_run: bool = False) -> None:
    print("+", " ".join(shlex.quote(part) for part in command))
    if dry_run:
        return
    subprocess.run(command, check=True)


def _build_preflight_command(model_path: Path, engine_path: Path) -> list[str]:
    return [
        sys.executable,
        "scripts/check_jetson_tensorrt_env.py",
        "--model-path",
        str(model_path),
        "--engine-path",
        str(engine_path),
    ]


def _build_profile_command(args: argparse.Namespace, model_path: Path, engine_path: Path) -> list[str]:
    return [
        sys.executable,
        "-m",
        "inferedgelab.cli",
        "profile",
        str(model_path),
        "--engine",
        "tensorrt",
        "--engine-path",
        str(engine_path),
        "--precision",
        str(args.precision),
        "--warmup",
        str(args.warmup),
        "--runs",
        str(args.runs),
        "--batch",
        str(args.batch),
        "--height",
        str(args.height),
        "--width",
        str(args.width),
    ]


def _build_compare_latest_command(
    model_path: Path,
    precision: str,
    markdown_out: Path,
    html_out: Path,
) -> list[str]:
    return [
        sys.executable,
        "-m",
        "inferedgelab.cli",
        "compare-latest",
        "--model",
        model_path.name,
        "--engine",
        "tensorrt",
        "--device",
        "gpu",
        "--precision",
        precision,
        "--selection-mode",
        "same_precision",
        "--markdown-out",
        str(markdown_out),
        "--html-out",
        str(html_out),
    ]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the verified Jetson TensorRT validation flow for EdgeBench."
    )
    parser.add_argument("--model-path", required=True, help="ONNX source model path.")
    parser.add_argument("--engine-path", required=True, help="Compiled TensorRT engine path.")
    parser.add_argument("--precision", default="fp16", help="TensorRT precision filter.")
    parser.add_argument("--warmup", type=int, default=10, help="Warmup iterations per profiling run.")
    parser.add_argument("--runs", type=int, default=100, help="Measured iterations per profiling run.")
    parser.add_argument("--batch", type=int, default=1, help="Batch size for profiling.")
    parser.add_argument("--height", type=int, default=0, help="Input height passed to profile.")
    parser.add_argument("--width", type=int, default=0, help="Input width passed to profile.")
    parser.add_argument(
        "--repeat",
        type=int,
        default=2,
        help="Number of profile runs to generate the latest comparable pair. Minimum: 2.",
    )
    parser.add_argument(
        "--report-dir",
        default="reports/validation",
        help="Directory where compare-latest Markdown/HTML reports are stored.",
    )
    parser.add_argument(
        "--skip-preflight",
        action="store_true",
        help="Skip scripts/check_jetson_tensorrt_env.py before profiling.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without executing subprocesses.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    if args.repeat < 2:
        print("Error: --repeat must be at least 2 to generate a latest pair for same-precision compare.")
        return 2

    model_path = Path(args.model_path)
    engine_path = Path(args.engine_path)
    report_dir = Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)

    report_base = f"{model_path.stem}_tensorrt_latest"
    markdown_out = report_dir / f"{report_base}.md"
    html_out = report_dir / f"{report_base}.html"

    try:
        if args.skip_preflight:
            _print_step("Skipping Preflight Check")
            print("Preflight check was skipped by request.")
        else:
            _print_step("Preflight Check")
            _run_command(_build_preflight_command(model_path, engine_path), dry_run=args.dry_run)

        for index in range(args.repeat):
            _print_step(f"Profile Run {index + 1}/{args.repeat}")
            _run_command(_build_profile_command(args, model_path, engine_path), dry_run=args.dry_run)

        _print_step("Compare Latest")
        _run_command(
            _build_compare_latest_command(
                model_path=model_path,
                precision=str(args.precision),
                markdown_out=markdown_out,
                html_out=html_out,
            ),
            dry_run=args.dry_run,
        )
    except subprocess.CalledProcessError as exc:
        print(f"Validation flow failed with exit code {exc.returncode}.")
        return exc.returncode or 1

    _print_step("Validation Complete")
    print(f"Markdown report: {markdown_out}")
    print(f"HTML report    : {html_out}")
    if args.dry_run:
        print("Dry-run mode: commands were not executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
