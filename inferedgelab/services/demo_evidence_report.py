from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from inferedgelab.studio.routes import (
    DEMO_EVIDENCE_FILES,
    VALIDATION_DEMO_DIR,
    _build_demo_guard_analysis,
    _build_imported_compare_response,
    _build_jetson_evidence_track,
    _load_aiguard_portfolio_cases,
    _load_demo_evaluation_report,
    _load_demo_problem_cases,
    _load_demo_result,
    _load_jetson_power_mode_summary,
)

IN_MEMORY_NOTE = "Local Studio demo evidence is in-memory and resets when the server restarts."
DEMO_ANNOTATIONS_FILE = "yolov8_coco_subset_annotations.json"


def build_demo_evidence_summary() -> dict[str, Any]:
    """Build the same bundled evidence summary used by Local Studio."""

    results = [_load_demo_result(file_name) for file_name in DEMO_EVIDENCE_FILES]
    onnx_result = results[0]
    tensorrt_result = results[1]
    tensorrt_15w_result = _load_demo_result("tensorrt_jetson_15w_result.json")
    evaluation_report = _load_demo_evaluation_report()
    problem_cases = _load_demo_problem_cases()
    guard_demo_cases = _load_aiguard_portfolio_cases()
    jetson_power_mode_summary = _load_jetson_power_mode_summary()
    guard_analysis = _build_demo_guard_analysis(results, evaluation_report)
    compare = _build_imported_compare_response(
        onnx_result,
        tensorrt_result,
        guard_analysis=guard_analysis,
    )
    comparison = _comparison_summary(onnx_result, tensorrt_result, compare)

    return {
        "schema_version": "inferedgelab-demo-evidence-summary-v1",
        "source": "examples/studio_demo",
        "scope": "local-first Local Studio demo evidence",
        "generated_at": _utc_now_iso(),
        "in_memory_note": IN_MEMORY_NOTE,
        "runtime_evidence": {
            "onnxruntime_cpu": _runtime_result_summary(
                "ONNX Runtime CPU baseline",
                onnx_result,
            ),
            "tensorrt_jetson_fp16_25w": _runtime_result_summary(
                "TensorRT Jetson FP16 25W candidate",
                tensorrt_result,
            ),
            "tensorrt_jetson_fp16_15w": _runtime_result_summary(
                "TensorRT Jetson FP16 15W power-mode evidence",
                tensorrt_15w_result,
            ),
        },
        "comparison": comparison,
        "deployment_decision": compare["deployment_decision"],
        "evaluation_report": _evaluation_summary(evaluation_report),
        "problem_cases": [_problem_case_summary(case) for case in problem_cases],
        "aiguard_cases": _aiguard_case_summaries(guard_demo_cases),
        "jetson_evidence_track": _build_jetson_evidence_track(results),
        "jetson_power_mode_summary": _power_mode_summary(jetson_power_mode_summary),
        "notes": [
            IN_MEMORY_NOTE,
            "This report is a local-first evidence replay, not a production SaaS dashboard export.",
            "Lab remains the deployment decision owner; AIGuard evidence is optional diagnosis context.",
        ],
    }


def build_demo_evidence_markdown(summary: dict[str, Any] | None = None) -> str:
    summary = summary or build_demo_evidence_summary()
    runtime = summary["runtime_evidence"]
    comparison = summary["comparison"]
    evaluation = summary["evaluation_report"]
    decision = summary["deployment_decision"]
    power_mode = summary["jetson_power_mode_summary"]

    lines: list[str] = [
        "# InferEdge Local Studio Demo Evidence Report",
        "",
        "## Scope",
        "",
        f"- source: `{summary['source']}`",
        f"- generated_at: `{summary['generated_at']}`",
        f"- note: {summary['in_memory_note']}",
        "- This is a local-first validation evidence export, not a production SaaS dashboard.",
        "",
        "## Runtime Evidence",
        "",
        "| Evidence | Backend | Device | Precision | Power Mode | Mean ms | P95 ms | P99 ms | FPS | Source |",
        "|---|---|---|---|---|---:|---:|---:|---:|---|",
    ]
    for item in runtime.values():
        lines.append(
            "| "
            f"{item['label']} | "
            f"{item['backend_key']} | "
            f"{item['device']} | "
            f"{item['precision']} | "
            f"{item['power_mode']} | "
            f"{_fmt_number(item['mean_ms'])} | "
            f"{_fmt_number(item['p95_ms'])} | "
            f"{_fmt_number(item['p99_ms'])} | "
            f"{_fmt_number(item['fps'])} | "
            f"`{item['source']}` |"
        )

    lines.extend(
        [
            "",
            "## Compare Summary",
            "",
            f"- baseline: `{comparison['baseline_backend_key']}`",
            f"- candidate: `{comparison['candidate_backend_key']}`",
            f"- speedup: **{_fmt_number(comparison['speedup'])}x faster**",
            f"- mean latency diff: `{_fmt_signed(comparison['mean_delta_ms'])} ms` / `{_fmt_signed(comparison['mean_delta_pct'])}%`",
            f"- p99 latency diff: `{_fmt_signed(comparison['p99_delta_ms'])} ms` / `{_fmt_signed(comparison['p99_delta_pct'])}%`",
            f"- FPS ratio: `{_fmt_number(comparison['fps_ratio'])}x`",
            f"- Lab judgement: `{comparison['lab_overall']}`",
            "",
            "## Deployment Decision",
            "",
            f"- decision: `{decision.get('decision')}`",
            f"- reason: {decision.get('reason')}",
            f"- guard_status: `{decision.get('guard_status')}`",
            f"- guard_verdict: `{decision.get('guard_verdict')}`",
            f"- recommended_action: {decision.get('recommended_action')}",
            "",
            "## YOLOv8 COCO Subset Evaluation",
            "",
            f"- preset: `{evaluation['preset']}`",
            f"- sample_count: `{evaluation['sample_count']}`",
            f"- ground_truth_boxes: `{evaluation['ground_truth_boxes']}`",
            f"- metric_backend: `{evaluation['metric_backend']}`",
            f"- mAP@50: `{_fmt_number(evaluation['map50'])}`",
            f"- precision: `{_fmt_number(evaluation['precision'])}`",
            f"- recall: `{_fmt_number(evaluation['recall'])}`",
            f"- structural_validation: `{evaluation['structural_status']}`",
            f"- contract_validation: `{evaluation['contract_status']}`",
            "",
            "## Problem Cases",
            "",
            "| Case | Decision | Reason | Source |",
            "|---|---|---|---|",
        ]
    )
    for case in summary["problem_cases"]:
        lines.append(
            f"| {case['problem_case']} | {case['decision']} | {case['reason']} | `{case['source']}` |"
        )

    lines.extend(
        [
            "",
            "## AIGuard Portfolio Cases",
            "",
            "| Case | Guard Verdict | Severity | Primary Reason |",
            "|---|---|---|---|",
        ]
    )
    for case in summary["aiguard_cases"]:
        lines.append(
            f"| {case['title']} | {case['guard_verdict']} | {case['severity']} | {case['primary_reason']} |"
        )

    lines.extend(
        [
            "",
            "## Jetson Power Mode Evidence",
            "",
            f"- scope: {power_mode['comparison_scope']}",
            f"- run_config_status: `{power_mode['run_config_status']}`",
            "",
            "| Metric | 25W | 15W | Delta | Delta % |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for metric_name, values in power_mode["metrics"].items():
        lines.append(
            "| "
            f"{metric_name} | "
            f"{_fmt_number(values['baseline_25w'])} | "
            f"{_fmt_number(values['candidate_15w'])} | "
            f"{_fmt_number(values['delta'])} | "
            f"{_fmt_number(values['delta_pct'])}% |"
        )

    lines.extend(
        [
            "",
            "## Notes",
            "",
        ]
    )
    for note in summary["notes"]:
        lines.append(f"- {note}")

    return "\n".join(lines) + "\n"


def write_demo_evidence_markdown(output: str | Path) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_demo_evidence_markdown(), encoding="utf-8")
    return path


def demo_evidence_summary_json(summary: dict[str, Any] | None = None) -> str:
    return json.dumps(summary or build_demo_evidence_summary(), ensure_ascii=False, indent=2) + "\n"


def build_demo_evidence_summary_text(summary: dict[str, Any] | None = None) -> str:
    summary = summary or build_demo_evidence_summary()
    comparison = summary["comparison"]
    runtime = summary["runtime_evidence"]
    decision = summary["deployment_decision"]
    evaluation = summary["evaluation_report"]
    return "\n".join(
        [
            "InferEdge Local Studio Demo Evidence",
            f"- TensorRT Jetson FP16 25W mean_ms: {_fmt_number(runtime['tensorrt_jetson_fp16_25w']['mean_ms'])}",
            f"- ONNX Runtime CPU mean_ms: {_fmt_number(runtime['onnxruntime_cpu']['mean_ms'])}",
            f"- speedup: {_fmt_number(comparison['speedup'])}x faster",
            f"- TensorRT FPS: {_fmt_number(runtime['tensorrt_jetson_fp16_25w']['fps'])}",
            f"- ONNX Runtime FPS: {_fmt_number(runtime['onnxruntime_cpu']['fps'])}",
            f"- deployment_decision: {decision.get('decision')}",
            f"- evaluation map50: {_fmt_number(evaluation['map50'])}",
            f"- in_memory_note: {summary['in_memory_note']}",
            "",
        ]
    )


def _runtime_result_summary(label: str, result: dict[str, Any]) -> dict[str, Any]:
    run_config = result.get("run_config") if isinstance(result.get("run_config"), dict) else {}
    jetson_evidence = result.get("jetson_evidence") if isinstance(result.get("jetson_evidence"), dict) else {}
    latency_ms = result.get("latency_ms") if isinstance(result.get("latency_ms"), dict) else {}
    return {
        "label": label,
        "model": _display(result.get("model_name") or result.get("model")),
        "backend_key": result.get("backend_key"),
        "compare_key": result.get("compare_key"),
        "backend": _display(result.get("engine_backend") or result.get("engine_name") or result.get("engine")),
        "device": _display(result.get("device_name") or result.get("device")),
        "precision": result.get("precision"),
        "power_mode": jetson_evidence.get("power_mode") or run_config.get("power_mode") or "-",
        "mean_ms": _number(result.get("mean_ms")),
        "p50_ms": _number(result.get("p50_ms") or latency_ms.get("p50")),
        "p95_ms": _number(result.get("p95_ms") or latency_ms.get("p95")),
        "p99_ms": _number(result.get("p99_ms")),
        "fps": _number(result.get("fps_value") or result.get("fps")),
        "source": result.get("_source_path") or "-",
    }


def _comparison_summary(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    compare: dict[str, Any],
) -> dict[str, Any]:
    result = compare["result"]
    metrics = result["metrics"]
    baseline_mean = _number(baseline.get("mean_ms"))
    candidate_mean = _number(candidate.get("mean_ms"))
    baseline_fps = _number(baseline.get("fps_value") or baseline.get("fps"))
    candidate_fps = _number(candidate.get("fps_value") or candidate.get("fps"))
    return {
        "baseline_backend_key": baseline.get("backend_key"),
        "candidate_backend_key": candidate.get("backend_key"),
        "baseline_compare_key": baseline.get("compare_key"),
        "candidate_compare_key": candidate.get("compare_key"),
        "speedup": _safe_div(baseline_mean, candidate_mean),
        "fps_ratio": _safe_div(candidate_fps, baseline_fps),
        "mean_delta_ms": metrics["mean_ms"]["delta"],
        "mean_delta_pct": metrics["mean_ms"]["delta_pct"],
        "p99_delta_ms": metrics["p99_ms"]["delta"],
        "p99_delta_pct": metrics["p99_ms"]["delta_pct"],
        "lab_overall": compare["judgement"].get("overall"),
        "comparison_mode": compare["judgement"].get("comparison_mode"),
        "precision_pair": compare["judgement"].get("precision_pair"),
        "summary": compare["judgement"].get("summary"),
    }


def _evaluation_summary(report: dict[str, Any]) -> dict[str, Any]:
    accuracy = report.get("accuracy") if isinstance(report.get("accuracy"), dict) else {}
    metrics = accuracy.get("metrics") if isinstance(accuracy.get("metrics"), dict) else {}
    runtime_result = report.get("runtime_result") if isinstance(report.get("runtime_result"), dict) else {}
    structural = report.get("structural_validation") if isinstance(report.get("structural_validation"), dict) else {}
    contract = report.get("contract_validation") if isinstance(report.get("contract_validation"), dict) else {}
    input_shape = contract.get("input_shape") if isinstance(contract.get("input_shape"), dict) else {}
    return {
        "source": report.get("source"),
        "preset": report.get("preset"),
        "sample_count": runtime_result.get("sample_count"),
        "ground_truth_boxes": runtime_result.get("ground_truth_boxes") or _demo_ground_truth_box_count(),
        "metric_backend": metrics.get("backend"),
        "map50": _number(metrics.get("map50")),
        "precision": _number(metrics.get("precision")),
        "recall": _number(metrics.get("recall")),
        "structural_status": structural.get("status"),
        "contract_status": input_shape.get("status"),
        "deployment_signal": report.get("deployment_signal") or {},
    }


def _problem_case_summary(case: dict[str, Any]) -> dict[str, Any]:
    signal = case.get("deployment_signal") if isinstance(case.get("deployment_signal"), dict) else {}
    return {
        "problem_case": case.get("problem_case"),
        "source": case.get("source"),
        "decision": signal.get("decision"),
        "reason": signal.get("reason"),
        "recommended_action": signal.get("recommended_action"),
    }


def _aiguard_case_summaries(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    cases = bundle.get("cases") if isinstance(bundle.get("cases"), list) else []
    summaries: list[dict[str, Any]] = []
    for case in cases:
        if not isinstance(case, dict):
            continue
        guard = case.get("guard_analysis") if isinstance(case.get("guard_analysis"), dict) else {}
        summaries.append(
            {
                "case_id": case.get("case_id"),
                "title": case.get("title"),
                "category": case.get("category"),
                "guard_verdict": guard.get("guard_verdict"),
                "severity": guard.get("severity"),
                "primary_reason": guard.get("primary_reason"),
                "evidence_count": len(guard.get("evidence") or []),
            }
        )
    return summaries


def _power_mode_summary(summary: dict[str, Any]) -> dict[str, Any]:
    metrics = {}
    for metric_name, values in (summary.get("metrics") or {}).items():
        metrics[metric_name] = {
            "baseline_25w": _number(values.get("baseline_25w")),
            "candidate_15w": _number(values.get("candidate_15w")),
            "delta": _number(values.get("delta_ms", values.get("delta"))),
            "delta_pct": _number(values.get("delta_pct")),
        }
    return {
        "source": summary.get("source"),
        "comparison_scope": summary.get("comparison_scope"),
        "run_config_status": summary.get("run_config_status"),
        "run_config_note": summary.get("run_config_note"),
        "metrics": metrics,
        "tegrastats": summary.get("tegrastats") or {},
        "deployment_signal": summary.get("deployment_signal") or {},
    }


def _demo_ground_truth_box_count() -> int | None:
    path = VALIDATION_DEMO_DIR / DEMO_ANNOTATIONS_FILE
    try:
        annotations = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    info = annotations.get("info") if isinstance(annotations, dict) else {}
    if not isinstance(info, dict):
        return None
    value = info.get("annotation_count")
    return int(value) if isinstance(value, int) else None


def _display(value: Any) -> str:
    if value is None or value == "":
        return "-"
    if isinstance(value, dict):
        return _display(value.get("name") or value.get("backend") or value.get("path"))
    return str(value)


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _safe_div(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in {None, 0}:
        return None
    return numerator / denominator


def _fmt_number(value: Any) -> str:
    number = _number(value)
    if number is None:
        return "-"
    return f"{number:.4f}".rstrip("0").rstrip(".")


def _fmt_signed(value: Any) -> str:
    number = _number(value)
    if number is None:
        return "-"
    return f"{number:+.4f}".rstrip("0").rstrip(".")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
