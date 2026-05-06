from __future__ import annotations

from pathlib import Path

import typer
from rich import print as rprint

from inferedgelab.services.demo_evidence_report import (
    build_demo_evidence_markdown,
    build_demo_evidence_summary,
    build_demo_evidence_summary_text,
    build_portfolio_demo_check,
    build_portfolio_demo_check_text,
    demo_evidence_summary_json,
    write_demo_evidence_markdown,
)


def demo_evidence_summary_cmd(
    format: str = typer.Option("text", "--format", "-f", help="text/json/markdown"),
    output: str = typer.Option("", "--output", "-o", help="Optional output path"),
) -> None:
    summary = build_demo_evidence_summary()
    normalized_format = format.strip().lower()
    if normalized_format == "text":
        text = build_demo_evidence_summary_text(summary)
    elif normalized_format == "json":
        text = demo_evidence_summary_json(summary)
    elif normalized_format in {"markdown", "md"}:
        text = build_demo_evidence_markdown(summary)
    else:
        raise typer.BadParameter("--format must be one of: text, json, markdown")

    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        rprint(f"[green]Saved[/green]: {path}")
    else:
        print(text, end="")


def export_demo_evidence_cmd(
    output: str = typer.Option(
        "reports/studio_demo_evidence.md",
        "--output",
        "-o",
        help="Markdown output path",
    ),
) -> None:
    path = write_demo_evidence_markdown(output)
    rprint(f"[green]Saved[/green]: {path}")


def portfolio_demo_check_cmd(
    format: str = typer.Option("text", "--format", "-f", help="text/json"),
    repo_root: str = typer.Option(".", "--repo-root", help="Repository root to check"),
) -> None:
    report = build_portfolio_demo_check(repo_root=repo_root)
    normalized_format = format.strip().lower()
    if normalized_format == "text":
        print(build_portfolio_demo_check_text(report), end="")
    elif normalized_format == "json":
        print(demo_evidence_summary_json(report), end="")
    else:
        raise typer.BadParameter("--format must be one of: text, json")

    if report["status"] != "pass":
        raise typer.Exit(code=1)
