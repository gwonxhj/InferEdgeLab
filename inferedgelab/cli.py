from __future__ import annotations

import typer

from inferedgelab import __version__
from inferedgelab.commands.analyze import analyze_cmd
from inferedgelab.commands.profile import profile_cmd
from inferedgelab.commands.evaluate import evaluate_cmd
from inferedgelab.commands.summarize import summarize
from inferedgelab.commands.compare import compare_cmd
from inferedgelab.commands.compare_latest import compare_latest_cmd
from inferedgelab.commands.enrich_pair import enrich_pair_cmd
from inferedgelab.commands.enrich_result import enrich_result_cmd
from inferedgelab.commands.list_results import list_results_cmd
from inferedgelab.commands.history_report import history_report_cmd
from inferedgelab.commands.serve import serve_cmd

app = typer.Typer(help="InferEdgeLab CLI - Edge AI Inference Validation Tool")


def version_cmd() -> None:
    typer.echo(__version__)

app.command("analyze", help="Static analysis (params/IO/FLOPs)")(analyze_cmd)
app.command("profile", help="Runtime profiling with selectable engine backend")(profile_cmd)
app.command("evaluate", help="Accuracy evaluation for classification manifest inputs")(evaluate_cmd)
app.command("summarize", help="Summarize InferEdgeLab JSON reports")(summarize)
app.command("compare", help="Compare two structured benchmark result JSON files")(compare_cmd)
app.command("compare-latest", help="Compare the two most recent structured benchmark results")(compare_latest_cmd)
app.command("enrich-pair", help="Attach accuracy metadata to a base/new structured result pair")(enrich_pair_cmd)
app.command("enrich-result", help="Attach accuracy metadata to an existing structured benchmark result")(enrich_result_cmd)
app.command("list-results", help="List recent structured benchmark results")(list_results_cmd)
app.command("history-report", help="Generate HTML history report from structured benchmark results")(history_report_cmd)
app.command("serve", help="Run InferEdgeLab FastAPI server")(serve_cmd)
app.command("version", help="Show InferEdgeLab version")(version_cmd)

if __name__ == "__main__":
    app()
