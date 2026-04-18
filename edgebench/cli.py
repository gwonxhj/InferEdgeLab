from __future__ import annotations

import typer

from edgebench.commands.analyze import analyze_cmd
from edgebench.commands.profile import profile_cmd
from edgebench.commands.evaluate import evaluate_cmd
from edgebench.commands.summarize import summarize
from edgebench.commands.compare import compare_cmd
from edgebench.commands.compare_latest import compare_latest_cmd
from edgebench.commands.enrich_pair import enrich_pair_cmd
from edgebench.commands.enrich_result import enrich_result_cmd
from edgebench.commands.list_results import list_results_cmd
from edgebench.commands.history_report import history_report_cmd
from edgebench.commands.serve import serve_cmd

app = typer.Typer(help="EdgeBench CLI - Edge AI Inference Validation Tool")

app.command("analyze", help="Static analysis (params/IO/FLOPs)")(analyze_cmd)
app.command("profile", help="Runtime profiling with selectable engine backend")(profile_cmd)
app.command("evaluate", help="Accuracy evaluation for classification manifest inputs")(evaluate_cmd)
app.command("summarize", help="Summarize EdgeBench JSON reports")(summarize)
app.command("compare", help="Compare two structured benchmark result JSON files")(compare_cmd)
app.command("compare-latest", help="Compare the two most recent structured benchmark results")(compare_latest_cmd)
app.command("enrich-pair", help="Attach accuracy metadata to a base/new structured result pair")(enrich_pair_cmd)
app.command("enrich-result", help="Attach accuracy metadata to an existing structured benchmark result")(enrich_result_cmd)
app.command("list-results", help="List recent structured benchmark results")(list_results_cmd)
app.command("history-report", help="Generate HTML history report from structured benchmark results")(history_report_cmd)
app.command("serve", help="Run EdgeBench FastAPI server")(serve_cmd)

if __name__ == "__main__":
    app()
