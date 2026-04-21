from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict

import typer
from rich import print as rprint

from inferedgelab.result.loader import load_result
from inferedgelab.result.saver import save_result
from inferedgelab.result.schema import BenchmarkResult


def _load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise typer.BadParameter("JSON payload must be an object.")

    return data


def _validate_accuracy_payload(data: dict) -> dict:
    if not isinstance(data, dict):
        raise typer.BadParameter("Accuracy payload must be a JSON object.")

    task = data.get("task")
    metrics = data.get("metrics")

    if not isinstance(task, str) or not task.strip():
        raise typer.BadParameter("Accuracy payload must include a non-empty string field: task")

    if not isinstance(metrics, dict):
        raise typer.BadParameter("Accuracy payload must include a dict field: metrics")

    numeric_metric_found = any(isinstance(value, (int, float)) and not isinstance(value, bool) for value in metrics.values())
    if not numeric_metric_found:
        raise typer.BadParameter("Accuracy payload metrics must include at least one numeric metric value")

    return dict(data)


def _build_enriched_result(base_result: dict, accuracy_payload: dict, accuracy_json_path: str) -> BenchmarkResult:
    existing_extra = dict(base_result.get("extra") or {})
    existing_accuracy = base_result.get("accuracy") or {}
    replaces_existing_accuracy = bool(existing_accuracy)

    enrichment = {
        "source": "enrich_result_cmd",
        "accuracy_json_path": accuracy_json_path,
        "replaces_existing_accuracy": replaces_existing_accuracy,
    }

    existing_extra["enrichment"] = enrichment

    return BenchmarkResult(
        model=str(base_result.get("model")),
        engine=str(base_result.get("engine")),
        device=str(base_result.get("device")),
        precision=str(base_result.get("precision")),
        batch=int(base_result.get("batch")),
        height=int(base_result.get("height")),
        width=int(base_result.get("width")),
        mean_ms=base_result.get("mean_ms"),
        p99_ms=base_result.get("p99_ms"),
        timestamp=datetime.utcnow().strftime("%Y%m%d-%H%M%S-%f"),
        source_report_path=base_result.get("source_report_path"),
        system=dict(base_result.get("system") or {}),
        run_config=dict(base_result.get("run_config") or {}),
        accuracy=dict(accuracy_payload),
        extra=existing_extra,
    )


def enrich_result_to_path(
    result_path: str,
    accuracy_json: str,
    out_dir: str = "results",
    overwrite_accuracy: bool = True,
) -> str:
    base_result = load_result(result_path)
    accuracy_payload = _validate_accuracy_payload(_load_json(accuracy_json))

    existing_accuracy = base_result.get("accuracy") or {}
    if existing_accuracy and not overwrite_accuracy:
        rprint("[red]The source result already contains accuracy metadata. Use --overwrite-accuracy to replace it.[/red]")
        raise typer.Exit(code=1)

    enriched = _build_enriched_result(base_result, accuracy_payload, accuracy_json)
    return save_result(enriched, out_dir=out_dir)


def enrich_result_cmd(
    result_path: str = typer.Argument(..., help="Base structured benchmark result JSON path"),
    accuracy_json: str = typer.Option(..., "--accuracy-json", help="External accuracy JSON path"),
    out_dir: str = typer.Option("results", "--out-dir", help="Directory where the enriched result is saved"),
    overwrite_accuracy: bool = typer.Option(
        True,
        "--overwrite-accuracy/--no-overwrite-accuracy",
        help="Whether to replace an existing accuracy field in the source result",
    ),
):
    saved_path = enrich_result_to_path(
        result_path=result_path,
        accuracy_json=accuracy_json,
        out_dir=out_dir,
        overwrite_accuracy=overwrite_accuracy,
    )
    rprint(f"[cyan]Saved enriched structured result[/cyan]: {saved_path}")
