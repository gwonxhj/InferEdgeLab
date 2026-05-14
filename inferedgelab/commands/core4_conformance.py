from __future__ import annotations

import typer

from inferedgelab.services.core4_conformance import (
    build_core4_conformance_report,
    build_core4_conformance_text,
    core4_conformance_json,
)


def core4_conformance_check_cmd(
    format: str = typer.Option("text", "--format", "-f", help="text/json"),
    repo_root: str = typer.Option(".", "--repo-root", help="Repository root to check"),
) -> None:
    report = build_core4_conformance_report(repo_root=repo_root)
    normalized_format = format.strip().lower()
    if normalized_format == "text":
        print(build_core4_conformance_text(report), end="")
    elif normalized_format == "json":
        print(core4_conformance_json(report), end="")
    else:
        raise typer.BadParameter("--format must be one of: text, json")

    if report["status"] != "pass":
        raise typer.Exit(code=1)
