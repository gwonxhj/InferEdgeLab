from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import glob
from pathlib import Path


MARK_START = "<!-- EDGE_BENCH:START -->"
MARK_END = "<!-- EDGE_BENCH:END -->"
CURATED_RESULTS_PATH = Path("benchmarks/rknn_curated_results.json")


def run(cmd: list[str]) -> str:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        sys.stderr.write(p.stderr)
        raise SystemExit(p.returncode)
    # edgebench가 rich 출력/경고 섞을 수 있으니, stdout만 사용
    return p.stdout


def replace_marked_block(readme_text: str, block: str) -> str:
    pat = re.compile(
        re.escape(MARK_START) + r".*?" + re.escape(MARK_END),
        flags=re.DOTALL,
    )
    repl = MARK_START + "\n\n" + block.strip() + "\n\n" + MARK_END
    if not pat.search(readme_text):
        raise SystemExit("README.md marker not found. Add markers first.")
    return pat.sub(repl, readme_text)


def _fmt_metric(value):
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _load_curated_results(path: Path) -> list[dict]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise SystemExit(f"Expected a JSON array in {path}")

    return [item for item in data if isinstance(item, dict)]


def _has_glob_matches(pattern: str) -> bool:
    return bool(glob.glob(pattern))


def _build_curated_hardware_validation_markdown(path: Path) -> str:
    items = _load_curated_results(path)
    if not items:
        return ""

    lines: list[str] = []
    lines.append("## Curated Hardware Validation")
    lines.append("")
    lines.append("### Odroid RKNN Benchmarks")
    lines.append("")
    lines.append(
        "These entries are curated hardware validation results imported from documented "
        "Odroid RKNN experiments, separate from the CI-generated CPU benchmark tables above."
    )
    lines.append("")
    lines.append("")
    lines.append("| Model | Engine | Device | Precision | Batch | Input(HxW) | Mean (ms) | P99 (ms) | mAP50 | F1 | Precision | Recall | Quantization | Preset | Source | Timestamp (UTC) |")
    lines.append("|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|")

    for item in items:
        accuracy = item.get("accuracy") or {}
        metrics = accuracy.get("metrics") or {}
        extra = item.get("extra") or {}
        quantization = extra.get("quantization_mode") or "-"
        preset = extra.get("quantization_preset") or "-"
        source = extra.get("source") or "-"

        lines.append(
            "| "
            + " | ".join(
                [
                    str(item.get("model", "-")),
                    str(item.get("engine", "-")),
                    str(item.get("device", "-")),
                    str(item.get("precision", "-")),
                    str(item.get("batch", "-")),
                    f"{item.get('height', '-')}x{item.get('width', '-')}",
                    _fmt_metric(item.get("mean_ms")),
                    _fmt_metric(item.get("p99_ms")),
                    _fmt_metric(metrics.get("map50")),
                    _fmt_metric(metrics.get("f1_score")),
                    _fmt_metric(metrics.get("precision")),
                    _fmt_metric(metrics.get("recall")),
                    str(quantization),
                    str(preset),
                    str(source),
                    str(item.get("timestamp", "-")),
                ]
            )
            + " |"
        )

    lines.append("")
    return "\n".join(lines)


def main():
    reports_pattern = "reports/*.json"
    has_reports = _has_glob_matches(reports_pattern)

    if has_reports:
        md_both = run(
            [
                "poetry",
                "run",
                "edgebench",
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
                "edgebench",
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
        md_history = (
            "# Benchmarks\n\n"
            "> No auto-generated report summaries are available yet.\n"
        )

    curated_section = _build_curated_hardware_validation_markdown(CURATED_RESULTS_PATH)
    benchmarks_body = md_history.rstrip() + "\n"
    if curated_section:
        benchmarks_body += "\n" + curated_section

    with open("BENCHMARKS.md", "w", encoding="utf-8") as f:
        f.write(benchmarks_body)

    if md_both:
        with open("README.md", "r", encoding="utf-8") as f:
            readme = f.read()

        readme2 = replace_marked_block(readme, md_both)

        with open("README.md", "w", encoding="utf-8") as f:
            f.write(readme2)

        print("✅ Updated README.md (marker block) + BENCHMARKS.md")
    else:
        print("✅ Updated BENCHMARKS.md (curated section only; README marker skipped because no reports matched)")


if __name__ == "__main__":
    main()
