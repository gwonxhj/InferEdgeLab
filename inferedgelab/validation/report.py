from __future__ import annotations

from datetime import datetime
import html
import json
from pathlib import Path
from typing import Any

from inferedgelab.validation.model_contract import ModelContract
from inferedgelab.validation.structural import validate_shape


def build_evaluation_report(
    *,
    eval_result: Any,
    model_contract: ModelContract,
    preset: dict[str, Any],
    latency_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    accuracy_status = str(eval_result.extra.get("accuracy_status") or "evaluated")
    structural_validation = dict(eval_result.extra.get("structural_validation") or {})
    contract_validation = {
        "input_shape": validate_shape(eval_result.actual_input_shape, model_contract.input.shape)
        if eval_result.actual_input_shape and model_contract.input.shape
        else {"status": "not_checked"},
        "preset": model_contract.preset,
        "task": model_contract.task,
    }
    return {
        "report_role": "inferedge-evaluation-report",
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "preset": preset,
        "model_contract": model_contract.to_dict(),
        "runtime_result": {
            "engine": eval_result.engine,
            "device": eval_result.device,
            "sample_count": eval_result.sample_count,
            "model_input": eval_result.model_input,
            "actual_input_shape": eval_result.actual_input_shape,
        },
        "accuracy": {
            "status": accuracy_status,
            "metrics": dict(eval_result.metrics),
            "reason": eval_result.extra.get("accuracy_skip_reason") if accuracy_status == "skipped" else None,
        },
        "contract_validation": contract_validation,
        "structural_validation": structural_validation,
        "latency_summary": latency_summary or {"status": "not_provided"},
        "deployment_signal": _deployment_signal(accuracy_status, structural_validation, contract_validation),
        "notes": list(eval_result.notes),
    }


def save_evaluation_report(report: dict[str, Any], *, json_path: str = "", markdown_path: str = "", html_path: str = "") -> None:
    if json_path.strip():
        _write_text(json_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    if markdown_path.strip():
        _write_text(markdown_path, render_evaluation_markdown(report))
    if html_path.strip():
        _write_text(html_path, render_evaluation_html(report))


def render_evaluation_markdown(report: dict[str, Any]) -> str:
    accuracy = report["accuracy"]
    structural = report.get("structural_validation") or {}
    contract_validation = report.get("contract_validation") or {}
    input_shape = contract_validation.get("input_shape") or {}
    signal = report["deployment_signal"]
    lines = [
        "# InferEdge Evaluation Report",
        "",
        f"- preset: `{report['preset']['name']}`",
        f"- engine: `{report['runtime_result']['engine']}`",
        f"- device: `{report['runtime_result']['device']}`",
        f"- samples: `{report['runtime_result']['sample_count']}`",
        f"- accuracy status: `{accuracy['status']}`",
        f"- contract input shape: `{input_shape.get('status', 'unknown')}`",
        f"- structural validation: `{structural.get('status', 'unknown')}`",
        f"- deployment signal: `{signal['decision']}`",
        "",
        "## Metrics",
    ]
    if accuracy["status"] == "skipped":
        lines.append(f"- accuracy skipped reason: {accuracy.get('reason') or 'not provided'}")
    for key, value in accuracy.get("metrics", {}).items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Notes"])
    for note in report.get("notes", []):
        lines.append(f"- {note}")
    return "\n".join(lines) + "\n"


def render_evaluation_html(report: dict[str, Any]) -> str:
    markdown = render_evaluation_markdown(report)
    escaped = html.escape(markdown)
    return (
        "<!doctype html>\n"
        "<html><head><meta charset=\"utf-8\"><title>InferEdge Evaluation Report</title></head>"
        "<body><pre>"
        f"{escaped}"
        "</pre></body></html>\n"
    )


def _deployment_signal(
    accuracy_status: str,
    structural_validation: dict[str, Any],
    contract_validation: dict[str, Any],
) -> dict[str, str]:
    if (contract_validation.get("input_shape") or {}).get("status") == "mismatch":
        return {
            "decision": "blocked",
            "reason": "Actual runtime input shape does not match the model contract.",
        }
    if structural_validation.get("status") == "failed":
        return {
            "decision": "blocked",
            "reason": "Structural validation found invalid detection output.",
        }
    if accuracy_status == "skipped":
        return {
            "decision": "review",
            "reason": "Accuracy evaluation was skipped because annotations were not provided.",
        }
    return {
        "decision": "review",
        "reason": "Accuracy evidence is available; compare and deployment policy still decide release.",
    }


def _write_text(path: str, text: str) -> None:
    out_path = Path(path)
    if out_path.parent != Path("."):
        out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
