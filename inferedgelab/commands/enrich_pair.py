from __future__ import annotations

import typer
from rich import print as rprint

from inferedgelab.commands.enrich_result import enrich_result_to_path


def enrich_pair_cmd(
    base_result: str = typer.Option(..., "--base-result", help="Base structured benchmark result JSON path"),
    base_accuracy_json: str = typer.Option(..., "--base-accuracy-json", help="Base accuracy JSON path"),
    new_result: str = typer.Option(..., "--new-result", help="New structured benchmark result JSON path"),
    new_accuracy_json: str = typer.Option(..., "--new-accuracy-json", help="New accuracy JSON path"),
    out_dir: str = typer.Option("results", "--out-dir", help="Directory where the enriched results are saved"),
    overwrite_accuracy: bool = typer.Option(
        True,
        "--overwrite-accuracy/--no-overwrite-accuracy",
        help="Whether to replace an existing accuracy field in the source results",
    ),
):
    base_saved_path = enrich_result_to_path(
        result_path=base_result,
        accuracy_json=base_accuracy_json,
        out_dir=out_dir,
        overwrite_accuracy=overwrite_accuracy,
    )
    new_saved_path = enrich_result_to_path(
        result_path=new_result,
        accuracy_json=new_accuracy_json,
        out_dir=out_dir,
        overwrite_accuracy=overwrite_accuracy,
    )

    rprint(f"[cyan]Saved enriched base structured result[/cyan]: {base_saved_path}")
    rprint(f"[cyan]Saved enriched new structured result[/cyan]: {new_saved_path}")
