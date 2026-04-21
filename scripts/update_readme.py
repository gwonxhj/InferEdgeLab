from __future__ import annotations

import argparse
from pathlib import Path


README_MARK_START = "<!-- EDGE_BENCH:START -->"
README_MARK_END = "<!-- EDGE_BENCH:END -->"
BENCHMARKS_MARK_START = "<!-- EDGE_BENCH_BENCHMARKS:START -->"
BENCHMARKS_MARK_END = "<!-- EDGE_BENCH_BENCHMARKS:END -->"


def extract_marker_block(text: str, start_marker: str, end_marker: str) -> str:
    """Extract the content inside a marker block."""
    start = text.find(start_marker)
    end = text.find(end_marker)
    if start == -1 or end == -1 or end <= start:
        raise RuntimeError(
            f"Required marker block was not found: {start_marker} ... {end_marker}. "
            "README sync only updates the auto-generated marker block."
        )
    return text[start + len(start_marker) : end].strip("\n")


def replace_marker_block(text: str, start_marker: str, end_marker: str, block: str) -> str:
    """Replace the content inside a marker block and preserve surrounding manual content."""
    start = text.find(start_marker)
    end = text.find(end_marker)
    if start == -1 or end == -1 or end <= start:
        raise RuntimeError(
            f"Required marker block was not found: {start_marker} ... {end_marker}. "
            "README sync only updates the auto-generated marker block."
        )
    replacement = f"{start_marker}\n\n{block.strip()}\n\n{end_marker}"
    return text[:start] + replacement + text[end + len(end_marker) :]


def read_text(path: Path) -> str:
    """Read UTF-8 text from a file."""
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    """Write UTF-8 text to a file."""
    path.write_text(text, encoding="utf-8")


def update_readme(readme_path: Path, bench_path: Path) -> None:
    """Copy the BENCHMARKS auto-generated marker block into the README marker block."""
    readme_text = read_text(readme_path)
    benchmarks_text = read_text(bench_path)

    benchmark_block = extract_marker_block(
        benchmarks_text,
        BENCHMARKS_MARK_START,
        BENCHMARKS_MARK_END,
    )
    updated_readme = replace_marker_block(
        readme_text,
        README_MARK_START,
        README_MARK_END,
        benchmark_block,
    )

    write_text(readme_path, updated_readme)
    print(f"Updated README auto marker block: {readme_path} <- {bench_path}")


def main() -> None:
    """Parse CLI arguments and sync the BENCHMARKS auto block into README."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--readme", required=True)
    parser.add_argument("--bench", required=True)
    args = parser.parse_args()

    update_readme(Path(args.readme), Path(args.bench))


if __name__ == "__main__":
    main()
