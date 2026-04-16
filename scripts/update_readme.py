from __future__ import annotations

import argparse
from pathlib import Path


README_MARK_START = "<!-- EDGE_BENCH:START -->"
README_MARK_END = "<!-- EDGE_BENCH:END -->"
BENCHMARKS_MARK_START = "<!-- EDGE_BENCH_BENCHMARKS:START -->"
BENCHMARKS_MARK_END = "<!-- EDGE_BENCH_BENCHMARKS:END -->"


def extract_marker_block(text: str, start_marker: str, end_marker: str) -> str:
    start = text.find(start_marker)
    end = text.find(end_marker)
    if start == -1 or end == -1 or end <= start:
        raise RuntimeError(f"Could not find marker block: {start_marker} ... {end_marker}")
    return text[start + len(start_marker) : end].strip("\n")


def replace_marker_block(text: str, start_marker: str, end_marker: str, block: str) -> str:
    start = text.find(start_marker)
    end = text.find(end_marker)
    if start == -1 or end == -1 or end <= start:
        raise RuntimeError(f"Could not find marker block: {start_marker} ... {end_marker}")
    replacement = f"{start_marker}\n\n{block.strip()}\n\n{end_marker}"
    return text[:start] + replacement + text[end + len(end_marker) :]


def update_readme(readme_path: Path, bench_path: Path) -> None:
    readme = readme_path.read_text(encoding="utf-8")
    bench = bench_path.read_text(encoding="utf-8")

    benchmark_block = extract_marker_block(bench, BENCHMARKS_MARK_START, BENCHMARKS_MARK_END)
    updated_readme = replace_marker_block(readme, README_MARK_START, README_MARK_END, benchmark_block)

    readme_path.write_text(updated_readme, encoding="utf-8")
    print(f"Updated {readme_path} from {bench_path}.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--readme", required=True)
    parser.add_argument("--bench", required=True)
    args = parser.parse_args()

    update_readme(Path(args.readme), Path(args.bench))


if __name__ == "__main__":
    main()
