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
    """Run a command and return stdout, exiting with the original code on failure."""
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if process.returncode != 0:
        sys.stderr.write(process.stderr)
        raise SystemExit(process.returncode)
    return process.stdout


def replace_named_marker_block(text: str, start_marker: str, end_marker: str, block: str) -> str:
    """Replace only the content inside a named marker block."""
    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker),
        flags=re.DOTALL,
    )
    replacement = start_marker + "\n\n" + block.strip() + "\n\n" + end_marker
    if not pattern.search(text):
        raise RuntimeError(
            f"Required marker block was not found: {start_marker} ... {end_marker}. "
            "Only the auto-generated marker block can be updated."
        )
    return pattern.sub(replacement, text)


def discover_report_files(pattern: str) -> list[str]:
    """Discover report JSON files that feed the auto-generated benchmark summary."""
    return sorted(glob.glob(pattern))


def run_summarize_command(pattern: str, *, mode: str, sort: str = "p99", recent: str | None = None) -> str:
    """Run the summarize CLI and return markdown output for the requested mode."""
    cmd = [
        "poetry",
        "run",
        "inferedgelab",
        "summarize",
        pattern,
        "--mode",
        mode,
        "--sort",
        sort,
    ]
    if recent is not None:
        cmd.extend(["--recent", recent])
    return run(cmd)


def fallback_benchmarks_block() -> str:
    """Return the default auto-summary block when no reports are available."""
    return NO_AUTO_SUMMARY_MESSAGE


def build_auto_summary_outputs(reports_pattern: str) -> tuple[str, str]:
    """Build README and BENCHMARKS markdown blocks from the current report set."""
    report_files = discover_report_files(reports_pattern)
    if not report_files:
        return "", fallback_benchmarks_block()

    md_both = run_summarize_command(
        reports_pattern,
        mode="both",
        recent=os.environ.get("EDGE_BENCH_RECENT", "5"),
    )
    md_history = run_summarize_command(reports_pattern, mode="history")
    return md_both, md_history


def should_update_readme(md_both: str) -> bool:
    """Return whether README should be updated from summarize --mode both output."""
    return bool(md_both.strip())


def write_text(path: Path, text: str) -> None:
    """Write UTF-8 text to a file."""
    path.write_text(text, encoding="utf-8")


def update_file_marker_block(path: Path, start_marker: str, end_marker: str, block: str) -> None:
    """Update a marker block in a file while preserving all manual content outside it."""
    original_text = path.read_text(encoding="utf-8")
    updated_text = replace_named_marker_block(original_text, start_marker, end_marker, block)
    write_text(path, updated_text)


def main() -> None:
    """Sync auto-generated summary blocks into BENCHMARKS.md and README.md."""
    reports_pattern = "reports/*.json"
    readme_path = Path("README.md")
    benchmarks_path = Path("BENCHMARKS.md")

    md_both, md_history = build_auto_summary_outputs(reports_pattern)

    update_file_marker_block(
        benchmarks_path,
        BENCHMARKS_MARK_START,
        BENCHMARKS_MARK_END,
        md_history,
    )

    if should_update_readme(md_both):
        update_file_marker_block(
            readme_path,
            README_MARK_START,
            README_MARK_END,
            md_both,
        )
        print("Updated BENCHMARKS.md auto marker block and README.md auto marker block.")
    else:
        print("Updated BENCHMARKS.md auto marker block. Skipped README.md because no report summaries were generated.")


if __name__ == "__main__":
    main()
