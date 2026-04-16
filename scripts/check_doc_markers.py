from __future__ import annotations

from pathlib import Path


README_MARK_START = "<!-- EDGE_BENCH:START -->"
README_MARK_END = "<!-- EDGE_BENCH:END -->"
BENCHMARKS_MARK_START = "<!-- EDGE_BENCH_BENCHMARKS:START -->"
BENCHMARKS_MARK_END = "<!-- EDGE_BENCH_BENCHMARKS:END -->"


def validate_marker_contract(text: str, start_marker: str, end_marker: str, label: str) -> None:
    if start_marker not in text or end_marker not in text:
        raise RuntimeError(
            f"{label} is missing required marker block: {start_marker} ... {end_marker}"
        )


def validate_default_docs(readme_path: Path, benchmarks_path: Path) -> None:
    validate_marker_contract(
        readme_path.read_text(encoding="utf-8"),
        README_MARK_START,
        README_MARK_END,
        str(readme_path),
    )
    validate_marker_contract(
        benchmarks_path.read_text(encoding="utf-8"),
        BENCHMARKS_MARK_START,
        BENCHMARKS_MARK_END,
        str(benchmarks_path),
    )


def main() -> None:
    validate_default_docs(Path("README.md"), Path("BENCHMARKS.md"))
    print("Document marker contract is valid.")


if __name__ == "__main__":
    main()
