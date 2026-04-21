from __future__ import annotations

import glob
import os
import re
import subprocess
import sys
from pathlib import Path


README_MARK_START = "<!-- EDGE_BENCH:START -->"
README_MARK_END = "<!-- EDGE_BENCH:END -->"
BENCHMARKS_MARK_START = "<!-- EDGE_BENCH_BENCHMARKS:START -->"
BENCHMARKS_MARK_END = "<!-- EDGE_BENCH_BENCHMARKS:END -->"
NO_AUTO_SUMMARY_MESSAGE = "> No auto-generated report summaries are available yet."


def run(cmd: list[str]) -> str:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        sys.stderr.write(p.stderr)
        raise SystemExit(p.returncode)
    return p.stdout


def replace_named_marker_block(text: str, start_marker: str, end_marker: str, block: str) -> str:
    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker),
        flags=re.DOTALL,
    )
    replacement = start_marker + "\n\n" + block.strip() + "\n\n" + end_marker
    if not pattern.search(text):
        raise RuntimeError(f"Marker block is missing: {start_marker} ... {end_marker}")
    return pattern.sub(replacement, text)


def _has_glob_matches(pattern: str) -> bool:
    return bool(glob.glob(pattern))


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def main() -> None:
    reports_pattern = "reports/*.json"
    readme_path = Path("README.md")
    benchmarks_path = Path("BENCHMARKS.md")

    has_reports = _has_glob_matches(reports_pattern)

    if has_reports:
        md_both = run(
            [
                "poetry",
                "run",
                "inferedgelab",
                "summarize",
                reports_pattern,
                "--mode",
                "both",
                "--recent",
                os.environ.get("EDGE_BENCH_RECENT", "5"),
                "--sort",
                "p99",
            ]
        )

        md_history = run(
            [
                "poetry",
                "run",
                "inferedgelab",
                "summarize",
                reports_pattern,
                "--mode",
                "history",
                "--sort",
                "p99",
            ]
        )
    else:
        md_both = ""
        md_history = NO_AUTO_SUMMARY_MESSAGE

    benchmarks_text = benchmarks_path.read_text(encoding="utf-8")
    updated_benchmarks = replace_named_marker_block(
        benchmarks_text,
        BENCHMARKS_MARK_START,
        BENCHMARKS_MARK_END,
        md_history,
    )
    _write_text(benchmarks_path, updated_benchmarks)

    if md_both:
        readme_text = readme_path.read_text(encoding="utf-8")
        updated_readme = replace_named_marker_block(
            readme_text,
            README_MARK_START,
            README_MARK_END,
            md_both,
        )
        _write_text(readme_path, updated_readme)
        print("✅ Updated README.md marker block + BENCHMARKS.md auto marker block")
    else:
        print("✅ Updated BENCHMARKS.md auto marker block (README marker skipped because no reports matched)")


if __name__ == "__main__":
    main()
