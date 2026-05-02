from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request
from fastapi import Body
from fastapi.responses import FileResponse
from fastapi.responses import RedirectResponse

from inferedgelab.compare.comparator import compare_results
from inferedgelab.compare.judgement import judge_comparison
from inferedgelab.result.loader import load_result
from inferedgelab.result.schema import normalize_result_schema
from inferedgelab.services.deployment_decision import build_deployment_decision

STATIC_DIR = Path(__file__).resolve().parent / "static"
DEMO_EVIDENCE_DIR = Path(__file__).resolve().parents[2] / "examples" / "studio_demo"
VALIDATION_DEMO_DIR = Path(__file__).resolve().parents[2] / "examples" / "validation_demo" / "subset"
VALIDATION_PROBLEM_DIR = Path(__file__).resolve().parents[2] / "examples" / "validation_demo" / "problem_cases"
DEMO_EVIDENCE_FILES = (
    "onnxruntime_cpu_result.json",
    "tensorrt_jetson_result.json",
)
DEMO_EVALUATION_REPORT = "yolov8_coco_subset_evaluation.json"
DEMO_PROBLEM_REPORTS = (
    "annotation_missing_report.json",
    "invalid_detection_structure_report.json",
    "contract_shape_mismatch_report.json",
)
LATENCY_REGRESSION_SUMMARY = "latency_regression_summary.json"
AIGUARD_PORTFOLIO_CASES = "aiguard_portfolio_cases.json"
DEMO_JOB_ID = "demo_yolov8n_trt_vs_onnx"
STATIC_ASSETS = {
    "app.js": "application/javascript",
    "style.css": "text/css",
}

router = APIRouter()


@router.get("/studio", include_in_schema=False)
def studio_index() -> FileResponse:
    return FileResponse(
        STATIC_DIR / "index.html",
        media_type="text/html",
        headers={"Cache-Control": "no-store"},
    )


@router.get("/studio로", include_in_schema=False)
def studio_korean_particle_redirect() -> RedirectResponse:
    return RedirectResponse(url="/studio", status_code=307)


@router.get("/studio/static/{asset_name}", include_in_schema=False)
def studio_static(asset_name: str) -> FileResponse:
    media_type = STATIC_ASSETS.get(asset_name)
    if media_type is None:
        raise HTTPException(status_code=404, detail="studio asset not found")
    return FileResponse(
        STATIC_DIR / asset_name,
        media_type=media_type,
        headers={"Cache-Control": "no-store"},
    )


@router.get("/studio/api/jobs", include_in_schema=False)
def studio_jobs(request: Request) -> dict[str, Any]:
    store = _get_studio_job_store(request)
    jobs = []
    if store is not None:
        jobs.extend(getattr(store, "_jobs", {}).values())
    jobs.extend(_get_demo_jobs(request).values())
    jobs = sorted(
        jobs,
        key=lambda job: str(job.get("updated_at") or job.get("created_at") or ""),
        reverse=True,
    )
    return {
        "source": "/api/jobs",
        "count": len(jobs),
        "jobs": jobs,
    }


@router.get("/studio/api/job/{job_id}", include_in_schema=False)
def studio_job_detail(request: Request, job_id: str) -> dict[str, Any]:
    demo_job = _get_demo_jobs(request).get(job_id)
    if demo_job is not None:
        return demo_job

    endpoint = _get_api_endpoint(request.app, "/api/jobs/{job_id}")
    return endpoint(job_id=job_id)


@router.get("/studio/api/compare/latest", include_in_schema=False)
def studio_compare_latest(request: Request) -> dict[str, Any]:
    imported_results = _get_imported_results(request)
    if len(imported_results) >= 2:
        return _build_imported_compare_response(
            imported_results[-2],
            imported_results[-1],
            guard_analysis=_get_studio_guard_analysis(request),
        )

    endpoint = _get_api_endpoint(request.app, "/api/compare-latest")
    try:
        return endpoint()
    except HTTPException as exc:
        if exc.status_code != 400:
            raise
        return {
            "status": "empty",
            "source": "/api/compare-latest",
            "error": exc.detail,
            "data": None,
            "deployment_decision": {
                "decision": "unknown",
                "reason": "No compare-ready result data is available yet.",
                "notes": "Run the CLI workflow or create result artifacts, then reload Local Studio.",
            },
        }


@router.post("/studio/api/run", include_in_schema=False)
def studio_run(request: Request, payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    model_path = payload.get("model_path")
    if not isinstance(model_path, str) or not model_path.strip():
        raise HTTPException(status_code=400, detail="model_path is required")

    endpoint = _get_api_endpoint(request.app, "/api/analyze")
    analyze_payload: dict[str, Any] = {
        "model_path": model_path.strip(),
        "notes": "Created from Local Studio Run",
    }
    options = payload.get("options")
    if isinstance(options, dict):
        analyze_payload["options"] = dict(options)
    job = endpoint(payload=analyze_payload)
    job["display_name"] = _build_analyze_display_name(job)
    return {
        "status": "created",
        "source": "/api/analyze",
        "job_id": job["job_id"],
        "job": job,
    }


@router.post("/studio/api/import", include_in_schema=False)
def studio_import(request: Request, payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    result = _load_import_payload(payload)
    result = _apply_backend_override(result, payload.get("backend_override"))
    imported_results = _get_imported_results(request)
    imported_results.append(result)
    request.app.state.studio_guard_analysis = None
    return {
        "status": "imported",
        "source": "studio-memory",
        "count": len(imported_results),
        "result": result,
        "compare_ready": len(imported_results) >= 2,
    }


@router.get("/studio/api/demo-evidence", include_in_schema=False)
def studio_demo_evidence(request: Request) -> dict[str, Any]:
    results = [_load_demo_result(file_name) for file_name in DEMO_EVIDENCE_FILES]
    evaluation_report = _load_demo_evaluation_report()
    problem_cases = _load_demo_problem_cases()
    guard_demo_cases = _load_aiguard_portfolio_cases()
    imported_results = _get_imported_results(request)
    imported_results.extend(results)
    guard_analysis = _build_demo_guard_analysis(results, evaluation_report)
    request.app.state.studio_guard_analysis = guard_analysis
    compare = _build_imported_compare_response(
        results[0],
        results[1],
        guard_analysis=guard_analysis,
    )
    demo_job = _build_demo_job(results, compare, evaluation_report, problem_cases, guard_demo_cases)
    _get_demo_jobs(request)[DEMO_JOB_ID] = demo_job
    return {
        "status": "loaded",
        "source": "examples/studio_demo",
        "job_id": DEMO_JOB_ID,
        "job": demo_job,
        "count": len(results),
        "results": results,
        "compare_ready": True,
        "compare": compare,
        "evaluation_report": evaluation_report,
        "problem_cases": problem_cases,
        "guard_demo_cases": guard_demo_cases,
        "guard_analysis": guard_analysis,
        "deployment_decision": compare["deployment_decision"],
    }


@router.get("/studio/api/jetson-command", include_in_schema=False)
def studio_jetson_command() -> dict[str, str]:
    command = "\n".join(
        [
            "./inferedge-runtime \\",
            "  --manifest ~/InferEdgeForge/builds/yolov8n__jetson__tensorrt__jetson_fp16/manifest.json \\",
            "  --model ~/InferEdgeForge/builds/yolov8n__jetson__tensorrt__jetson_fp16/model.engine \\",
            "  --engine tensorrt \\",
            "  --device jetson \\",
            "  --runs 5 \\",
            "  --warmup 1 \\",
            "  --output results/jetson/yolov8n_jetson_tensorrt_manifest_smoke.json",
        ]
    )
    return {"command": command}


@router.get("/studio{suffix:path}", include_in_schema=False)
def studio_path_fallback(suffix: str) -> RedirectResponse:
    if suffix.startswith("/api") or suffix.startswith("/static"):
        raise HTTPException(status_code=404, detail="studio route not found")
    if suffix:
        return RedirectResponse(url="/studio", status_code=307)
    return RedirectResponse(url="/studio", status_code=307)


def register_studio(app: FastAPI, job_store: Any | None = None) -> None:
    app.state.studio_job_store = job_store
    app.state.studio_imported_results = []
    app.state.studio_demo_jobs = {}
    app.state.studio_guard_analysis = None
    app.include_router(router)


def _get_studio_job_store(request: Request) -> Any | None:
    return getattr(request.app.state, "studio_job_store", None)


def _get_imported_results(request: Request) -> list[dict[str, Any]]:
    imported_results = getattr(request.app.state, "studio_imported_results", None)
    if imported_results is None:
        imported_results = []
        request.app.state.studio_imported_results = imported_results
    return imported_results


def _get_demo_jobs(request: Request) -> dict[str, dict[str, Any]]:
    demo_jobs = getattr(request.app.state, "studio_demo_jobs", None)
    if demo_jobs is None:
        demo_jobs = {}
        request.app.state.studio_demo_jobs = demo_jobs
    return demo_jobs


def _get_studio_guard_analysis(request: Request) -> dict[str, Any] | None:
    guard_analysis = getattr(request.app.state, "studio_guard_analysis", None)
    return guard_analysis if isinstance(guard_analysis, dict) else None


def _get_api_endpoint(app: FastAPI, path: str) -> Any:
    for route in app.routes:
        if getattr(route, "path", None) == path:
            return route.endpoint
    raise HTTPException(status_code=404, detail=f"API route not found: {path}")


def _load_import_payload(payload: dict[str, Any]) -> dict[str, Any]:
    path = payload.get("path") or payload.get("json_path")
    if isinstance(path, str) and path.strip():
        try:
            return _with_compare_keys(load_result(path.strip()))
        except (OSError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    raw_result = payload.get("result") or payload.get("payload") or payload.get("json")
    if raw_result is None:
        raw_result = payload
    if not isinstance(raw_result, dict):
        raise HTTPException(status_code=400, detail="import payload must be a JSON object")

    try:
        result = normalize_result_schema(dict(raw_result))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    result.setdefault("legacy_result", False)
    return _with_compare_keys(result)


def _build_imported_compare_response(
    base: dict[str, Any],
    new: dict[str, Any],
    guard_analysis: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result = compare_results(base, new)
    judgement = judge_comparison(result)
    deployment_decision = build_deployment_decision(judgement, guard_analysis=guard_analysis)
    data = {
        "base": base,
        "new": new,
        "result": result,
        "judgement": judgement,
        "deployment_decision": deployment_decision,
    }
    if guard_analysis is not None:
        data["guard_analysis"] = guard_analysis
    return {
        "status": "ok",
        "source": "studio-memory",
        "data": data,
        "base": base,
        "new": new,
        "result": result,
        "judgement": judgement,
        "deployment_decision": deployment_decision,
        **({"guard_analysis": guard_analysis} if guard_analysis is not None else {}),
    }


def _load_demo_result(file_name: str) -> dict[str, Any]:
    path = DEMO_EVIDENCE_DIR / file_name
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"demo evidence not found: {file_name}") from exc
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"demo evidence is invalid JSON: {file_name}") from exc

    try:
        result = normalize_result_schema(raw)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=500, detail=f"demo evidence schema error: {file_name}") from exc
    result.setdefault("legacy_result", False)
    result["_source_path"] = str(path.relative_to(DEMO_EVIDENCE_DIR.parents[1]))
    return _with_compare_keys(result)


def _load_demo_evaluation_report() -> dict[str, Any]:
    path = VALIDATION_DEMO_DIR / DEMO_EVALUATION_REPORT
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"demo evaluation report not found: {DEMO_EVALUATION_REPORT}") from exc
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"demo evaluation report is invalid JSON: {DEMO_EVALUATION_REPORT}") from exc

    accuracy = report.get("accuracy") if isinstance(report, dict) else None
    structural = report.get("structural_validation") if isinstance(report, dict) else None
    contract = report.get("contract_validation") if isinstance(report, dict) else None
    if not isinstance(accuracy, dict) or not isinstance(structural, dict) or not isinstance(contract, dict):
        raise HTTPException(status_code=500, detail=f"demo evaluation report schema error: {DEMO_EVALUATION_REPORT}")

    return {
        "report_role": report.get("report_role"),
        "source": f"examples/validation_demo/subset/{DEMO_EVALUATION_REPORT}",
        "preset": (report.get("preset") or {}).get("name"),
        "runtime_result": report.get("runtime_result") or {},
        "accuracy": accuracy,
        "structural_validation": structural,
        "contract_validation": contract,
        "deployment_signal": report.get("deployment_signal") or {},
    }


def _load_demo_problem_cases() -> list[dict[str, Any]]:
    cases = [_load_problem_report(file_name) for file_name in DEMO_PROBLEM_REPORTS]
    cases.append(_load_latency_regression_summary())
    return cases


def _load_latency_regression_summary() -> dict[str, Any]:
    path = DEMO_EVIDENCE_DIR / LATENCY_REGRESSION_SUMMARY
    try:
        summary = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"latency regression summary not found: {LATENCY_REGRESSION_SUMMARY}") from exc
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"latency regression summary is invalid JSON: {LATENCY_REGRESSION_SUMMARY}") from exc

    problem_case = summary.get("problem_case") if isinstance(summary, dict) else None
    deployment_signal = summary.get("deployment_signal") if isinstance(summary, dict) else None
    latency_checks = summary.get("latency_checks") if isinstance(summary, dict) else None
    if not isinstance(problem_case, str) or not isinstance(deployment_signal, dict) or not isinstance(latency_checks, dict):
        raise HTTPException(status_code=500, detail=f"latency regression summary schema error: {LATENCY_REGRESSION_SUMMARY}")

    return {
        "problem_case": problem_case,
        "problem_case_type": summary.get("problem_case_type") or "runtime_latency",
        "source": f"examples/studio_demo/{LATENCY_REGRESSION_SUMMARY}",
        "baseline_source": summary.get("baseline_source"),
        "new_source": summary.get("new_source"),
        "policy": summary.get("policy") or {},
        "baseline": summary.get("baseline") or {},
        "new": summary.get("new") or {},
        "latency_checks": latency_checks,
        "deployment_signal": deployment_signal,
    }


def _load_aiguard_portfolio_cases() -> dict[str, Any]:
    path = DEMO_EVIDENCE_DIR / AIGUARD_PORTFOLIO_CASES
    try:
        bundle = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"AIGuard portfolio cases not found: {AIGUARD_PORTFOLIO_CASES}") from exc
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"AIGuard portfolio cases are invalid JSON: {AIGUARD_PORTFOLIO_CASES}") from exc

    cases = bundle.get("cases") if isinstance(bundle, dict) else None
    if not isinstance(cases, list):
        raise HTTPException(status_code=500, detail=f"AIGuard portfolio cases schema error: {AIGUARD_PORTFOLIO_CASES}")

    return {
        "schema_version": bundle.get("schema_version"),
        "source": f"examples/studio_demo/{AIGUARD_PORTFOLIO_CASES}",
        "scope": bundle.get("scope"),
        "case_count": bundle.get("case_count", len(cases)),
        "cases": cases,
    }


def _load_problem_report(file_name: str) -> dict[str, Any]:
    path = VALIDATION_PROBLEM_DIR / file_name
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"demo problem report not found: {file_name}") from exc
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"demo problem report is invalid JSON: {file_name}") from exc

    problem_case = report.get("problem_case") if isinstance(report, dict) else None
    deployment_signal = report.get("deployment_signal") if isinstance(report, dict) else None
    structural = report.get("structural_validation") if isinstance(report, dict) else None
    contract = report.get("contract_validation") if isinstance(report, dict) else None
    accuracy = report.get("accuracy") if isinstance(report, dict) else None
    if not isinstance(problem_case, str) or not isinstance(deployment_signal, dict):
        raise HTTPException(status_code=500, detail=f"demo problem report schema error: {file_name}")

    return {
        "problem_case": problem_case,
        "source": f"examples/validation_demo/problem_cases/{file_name}",
        "deployment_signal": deployment_signal,
        "accuracy": accuracy if isinstance(accuracy, dict) else {},
        "structural_validation": structural if isinstance(structural, dict) else {},
        "contract_validation": contract if isinstance(contract, dict) else {},
    }


def _build_demo_job(
    results: list[dict[str, Any]],
    compare: dict[str, Any],
    evaluation_report: dict[str, Any],
    problem_cases: list[dict[str, Any]],
    guard_demo_cases: dict[str, Any],
) -> dict[str, Any]:
    now = _utc_now_iso()
    runtime_result = results[-1] if results else {}
    return {
        "job_id": DEMO_JOB_ID,
        "display_name": "Demo: TensorRT vs ONNX Runtime",
        "status": "completed",
        "created_at": now,
        "updated_at": now,
        "input_summary": {
            "workflow": "studio_demo_evidence",
            "model_path": "examples/studio_demo/*.json",
            "notes": "Bundled Local Studio demo evidence",
        },
        "result": {
            "runtime_result": runtime_result,
            "comparison": compare,
            "deployment_decision": compare["deployment_decision"],
            "guard_analysis": compare.get("guard_analysis"),
            "evaluation_report": evaluation_report,
            "problem_cases": problem_cases,
            "guard_demo_cases": guard_demo_cases,
            "summary": compare["judgement"]["summary"],
        },
        "error": None,
        "links": {
            "self": f"/studio/api/job/{DEMO_JOB_ID}",
            "compare": "/studio/api/compare/latest",
        },
        "next_actions": ["review_compare"],
    }


def _build_demo_guard_analysis(
    results: list[dict[str, Any]],
    evaluation_report: dict[str, Any],
) -> dict[str, Any]:
    baseline = results[0] if results else {}
    candidate = results[-1] if results else {}
    accuracy_metrics = evaluation_report.get("accuracy", {}).get("metrics", {})
    structural = evaluation_report.get("structural_validation") or {}
    contract = evaluation_report.get("contract_validation", {}).get("input_shape") or {}
    map50 = accuracy_metrics.get("map50")
    precision = accuracy_metrics.get("precision")
    recall = accuracy_metrics.get("recall")
    verdict = "review_required" if isinstance(map50, (int, float)) and map50 < 0.2 else "pass"
    severity = "medium" if verdict == "review_required" else "low"
    source = {
        "runtime_result_path": candidate.get("_source_path") or "examples/studio_demo/tensorrt_jetson_result.json",
        "baseline_profile_path": baseline.get("_source_path") or "examples/studio_demo/onnxruntime_cpu_result.json",
        "evaluation_report_path": evaluation_report.get("source"),
        "model_contract_path": "examples/validation_demo/subset/model_contract.json",
        "lab_result_path": "studio.demo_evidence",
    }
    evidence = [
        {
            "type": "accuracy_signal",
            "metric_name": "map50",
            "observed_value": map50,
            "baseline_value": None,
            "threshold": 0.2,
            "severity": severity,
            "status": "warning" if verdict == "review_required" else "passed",
            "explanation": (
                "Demo mAP50 is below the review threshold, so Lab should keep this as validation evidence "
                "instead of treating latency speedup alone as deployment-ready."
            ),
            "why_it_matters": "Latency improvement does not prove detection quality is deployment-ready.",
            "suspected_causes": [
                "Small validation subset",
                "Model/preset calibration gap",
                "Postprocess or threshold tuning needed",
            ],
            "recommendation": "Review accuracy evidence with a larger validation subset before deployment.",
            "raw_context": {
                "precision": precision,
                "recall": recall,
                "structural_status": structural.get("status"),
                "contract_status": contract.get("status"),
            },
        },
        {
            "type": "contract_validation",
            "metric_name": "input_shape_status",
            "observed_value": contract.get("status"),
            "baseline_value": "passed",
            "threshold": "passed",
            "severity": "low" if contract.get("status") == "passed" else "high",
            "status": "passed" if contract.get("status") == "passed" else "failed",
            "explanation": "The demo model contract input shape check is recorded as structured evidence.",
            "why_it_matters": "Contract mismatch can make accuracy metrics unreliable.",
            "suspected_causes": [],
            "recommendation": "Keep model_contract evidence attached to the Lab report.",
            "raw_context": contract,
        },
    ]
    return {
        "schema_version": "inferedge-aiguard-diagnosis-v1",
        "source": source,
        "guard_verdict": verdict,
        "severity": severity,
        "confidence": 0.82,
        "primary_reason": (
            "Latency improved, but demo accuracy evidence still requires review."
            if verdict == "review_required"
            else "Demo validation evidence is within configured Guard thresholds."
        ),
        "evidence": evidence,
        "suspected_causes": [
            "Small validation subset",
            "Detection threshold tuning needed",
        ]
        if verdict == "review_required"
        else [],
        "recommendations": [
            "Use this demo as portfolio evidence, then validate with a larger representative dataset before deployment.",
            "Keep AIGuard evidence optional and let Lab own the final deployment decision.",
        ],
        "thresholds": {"map50_review": 0.2},
        "baseline_summary": {
            "backend_key": baseline.get("backend_key"),
            "mean_ms": baseline.get("mean_ms"),
            "p99_ms": baseline.get("p99_ms"),
        },
        "candidate_summary": {
            "backend_key": candidate.get("backend_key"),
            "mean_ms": candidate.get("mean_ms"),
            "p99_ms": candidate.get("p99_ms"),
            "map50": map50,
        },
        "created_at": _utc_now_iso(),
    }


def _build_analyze_display_name(job: dict[str, Any]) -> str:
    input_summary = job.get("input_summary") or {}
    model_path = _first_display_value(input_summary.get("model_path"), input_summary.get("artifact_path"))
    model_name = Path(model_path).name if model_path else "analyze job"
    options = input_summary.get("options") if isinstance(input_summary.get("options"), dict) else {}
    backend = _first_display_value(options.get("backend"))
    device = _first_display_value(options.get("device"))
    suffix = f" ({backend}/{device})" if backend or device else ""
    return f"Analyze {model_name}{suffix}"


def _utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _with_compare_keys(result: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(result)
    if not enriched.get("backend_key"):
        engine = _first_display_value(
            enriched.get("engine_backend"),
            enriched.get("engine"),
            enriched.get("backend"),
        )
        device = _first_display_value(enriched.get("device_name"), enriched.get("device"))
        if engine and device:
            enriched["backend_key"] = f"{engine}__{device}"
    if not enriched.get("compare_key"):
        model = _first_display_value(enriched.get("model_name"), enriched.get("model"))
        batch = enriched.get("batch")
        height = enriched.get("height")
        width = enriched.get("width")
        precision = enriched.get("precision")
        if model and batch and height and width and precision:
            enriched["compare_key"] = f"{model}__b{batch}__h{height}w{width}__{precision}"
    return enriched


def _apply_backend_override(result: dict[str, Any], override: Any) -> dict[str, Any]:
    if not isinstance(override, str) or not override.strip():
        return result

    override = override.strip()
    if override == "onnxruntime__cpu":
        engine = "onnxruntime"
        device = "cpu"
    elif override == "tensorrt__jetson":
        engine = "tensorrt"
        device = "jetson"
    else:
        raise HTTPException(status_code=400, detail="unsupported backend_override")

    enriched = dict(result)
    enriched["engine"] = engine
    enriched["engine_backend"] = engine
    enriched["device"] = device
    enriched["device_name"] = device
    enriched["backend_key"] = override
    return _with_compare_keys(enriched)


def _first_display_value(*values: Any) -> str:
    for value in values:
        display_value = _display_value(value)
        if display_value:
            return display_value
    return ""


def _display_value(value: Any) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, dict):
        return _first_display_value(
            value.get("name"),
            value.get("backend"),
            value.get("path"),
            value.get("status"),
            value.get("id"),
        )
    return str(value)
