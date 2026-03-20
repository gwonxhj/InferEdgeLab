from __future__ import annotations

import typer

from edgebench.commands.analyze import analyze_cmd
from edgebench.commands.profile import profile_cmd
from edgebench.commands.summarize import summarize
from edgebench.commands.compare import compare_cmd
from edgebench.commands.compare_latest import compare_latest_cmd

app = typer.Typer(help="EdgeBench CLI - Edge AI Profiling Tool")

app.command("analyze", help="Static analysis (params/IO/FLOPs)")(analyze_cmd)
app.command("profile", help="Runtime profiling (onnxruntime cpu)")(profile_cmd)
app.command("summarize", help="Summarize EdgeBench JSON reports")(summarize)
app.command("compare", help="Compare two structured benchmark result JSON files")(compare_cmd)
app.command("compare-latest", help="Compare the two most recent structured benchmark results")(compare_latest_cmd)

if __name__ == "__main__":
    app()