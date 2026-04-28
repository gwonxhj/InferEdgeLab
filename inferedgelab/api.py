from __future__ import annotations

from typing import Any

from fastapi import Body, FastAPI, HTTPException

from inferedgelab import __version__
from inferedgelab.compare.comparator import compare_results
from inferedgelab.compare.judgement import judge_comparison
from inferedgelab.config import resolve_compare_thresholds
from inferedgelab.report.html_generator import generate_compare_html
from inferedgelab.report.markdown_generator import generate_compare_markdown
from inferedgelab.services.api_job_store import InMemoryApiJobStore
from inferedgelab.services.api_response_contract import build_api_response_bundle
from inferedgelab.services.compare_service import build_compare_bundle
from inferedgelab.services.compare_service import build_compare_latest_bundle
from inferedgelab.services.deployment_decision import build_deployment_decision
from inferedgelab.services.history_report_service import build_history_report_outputs
from inferedgelab.services.list_results_service import build_list_results_bundle
from inferedgelab.services.summarize_service import build_summary_bundle


def create_app() -> FastAPI:
    app = FastAPI(title="InferEdgeLab API")
    job_store = InMemoryApiJobStore()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "inferedgelab-api", "version": __version__}

    @app.get("/api/list-results")
    def list_results(
        pattern: str = "results/*.json",
        limit: int = 10,
        model: str = "",
        engine: str = "",
        device: str = "",
        precision: str = "",
        batch: int | None = None,
        height: int | None = None,
        width: int | None = None,
        legacy_only: bool = False,
    ) -> dict[str, Any]:
        try:
            return build_list_results_bundle(
                pattern=pattern,
                limit=limit,
                model=model,
                engine=engine,
                device=device,
                precision=precision,
                batch=batch,
                height=height,
                width=width,
                legacy_only=legacy_only,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/summarize")
    def summarize(
        pattern: str,
        format: str = "md",
        mode: str = "latest",
        sort: str = "p99",
        recent: int = 0,
        top: int = 0,
    ) -> dict[str, Any]:
        try:
            return build_summary_bundle(
                pattern=pattern,
                format=format,
                mode=mode,
                sort=sort,
                recent=recent,
                top=top,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/history-report")
    def history_report(
        pattern: str = "results/*.json",
        model: str = "",
        engine: str = "",
        device: str = "",
        precision: str = "",
        batch: int | None = None,
        height: int | None = None,
        width: int | None = None,
        include_markdown: bool = False,
    ) -> dict[str, Any]:
        try:
            return build_history_report_outputs(
                pattern=pattern,
                model=model,
                engine=engine,
                device=device,
                precision=precision,
                batch=batch,
                height=height,
                width=width,
                include_markdown=include_markdown,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/compare")
    def compare(
        base_path: str,
        new_path: str,
    ) -> dict[str, Any]:
        try:
            bundle = build_compare_bundle(
                base_path=base_path,
                new_path=new_path,
            )
            return build_api_response_bundle(bundle, response_type="compare")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/compare")
    def compare_json(
        payload: dict[str, Any] = Body(...),
    ) -> dict[str, Any]:
        try:
            return _build_compare_response_from_payload(payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/analyze")
    def analyze(
        payload: dict[str, Any] = Body(...),
    ) -> dict[str, Any]:
        try:
            return job_store.create_analyze_job(payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/jobs/{job_id}")
    def get_job(job_id: str) -> dict[str, Any]:
        job = job_store.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="job not found")
        return job

    @app.get("/api/compare-latest")
    def compare_latest(
        pattern: str = "results/*.json",
        model: str = "",
        engine: str = "",
        device: str = "",
        precision: str = "",
        selection_mode: str = "same_precision",
        latency_improve_threshold: float | None = None,
        latency_regress_threshold: float | None = None,
        accuracy_improve_threshold: float | None = None,
        accuracy_regress_threshold: float | None = None,
        tradeoff_caution_threshold: float | None = None,
        tradeoff_risky_threshold: float | None = None,
        tradeoff_severe_threshold: float | None = None,
        pyproject_path: str = "pyproject.toml",
    ) -> dict[str, Any]:
        try:
            return build_compare_latest_bundle(
                pattern=pattern,
                model=model,
                engine=engine,
                device=device,
                precision=precision,
                selection_mode=selection_mode,
                latency_improve_threshold=latency_improve_threshold,
                latency_regress_threshold=latency_regress_threshold,
                accuracy_improve_threshold=accuracy_improve_threshold,
                accuracy_regress_threshold=accuracy_regress_threshold,
                tradeoff_caution_threshold=tradeoff_caution_threshold,
                tradeoff_risky_threshold=tradeoff_risky_threshold,
                tradeoff_severe_threshold=tradeoff_severe_threshold,
                pyproject_path=pyproject_path,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return app


app = create_app()


def _build_compare_response_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    base = _required_dict(payload, "base_result", "base")
    new = _required_dict(payload, "new_result", "new")
    guard_analysis = payload.get("guard_analysis")
    if guard_analysis is not None and not isinstance(guard_analysis, dict):
        raise ValueError("guard_analysis must be a JSON object when provided")

    thresholds = resolve_compare_thresholds(
        latency_improve_threshold=_optional_float(payload, "latency_improve_threshold"),
        latency_regress_threshold=_optional_float(payload, "latency_regress_threshold"),
        accuracy_improve_threshold=_optional_float(payload, "accuracy_improve_threshold"),
        accuracy_regress_threshold=_optional_float(payload, "accuracy_regress_threshold"),
        tradeoff_caution_threshold=_optional_float(payload, "tradeoff_caution_threshold"),
        tradeoff_risky_threshold=_optional_float(payload, "tradeoff_risky_threshold"),
        tradeoff_severe_threshold=_optional_float(payload, "tradeoff_severe_threshold"),
        pyproject_path=str(payload.get("pyproject_path") or "pyproject.toml"),
    )

    result = compare_results(base, new)
    judgement = judge_comparison(
        result,
        latency_improve_threshold=thresholds["latency_improve_threshold"],
        latency_regress_threshold=thresholds["latency_regress_threshold"],
        accuracy_improve_threshold=thresholds["accuracy_improve_threshold"],
        accuracy_regress_threshold=thresholds["accuracy_regress_threshold"],
        tradeoff_caution_threshold=thresholds["tradeoff_caution_threshold"],
        tradeoff_risky_threshold=thresholds["tradeoff_risky_threshold"],
        tradeoff_severe_threshold=thresholds["tradeoff_severe_threshold"],
    )
    deployment_decision = build_deployment_decision(
        judgement,
        guard_analysis=guard_analysis,
    )
    markdown = generate_compare_markdown(
        result,
        judgement,
        guard_analysis=guard_analysis,
        deployment_decision=deployment_decision,
    )
    html = generate_compare_html(
        result,
        judgement,
        guard_analysis=guard_analysis,
        deployment_decision=deployment_decision,
    )

    meta = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    bundle = {
        "meta": {
            "base_path": meta.get("base_path") or "request.base_result",
            "new_path": meta.get("new_path") or "request.new_result",
            "legacy_warning": bool(base.get("legacy_result") or new.get("legacy_result")),
        },
        "data": {
            "base": base,
            "new": new,
            "result": result,
            "judgement": judgement,
            "deployment_decision": deployment_decision,
        },
        "rendered": {
            "markdown": markdown,
            "html": html,
        },
        "base": base,
        "new": new,
        "base_path": meta.get("base_path") or "request.base_result",
        "new_path": meta.get("new_path") or "request.new_result",
        "result": result,
        "judgement": judgement,
        "markdown": markdown,
        "html": html,
        "legacy_warning": bool(base.get("legacy_result") or new.get("legacy_result")),
        "deployment_decision": deployment_decision,
    }
    if guard_analysis is not None:
        bundle["guard_analysis"] = guard_analysis
        bundle["data"]["guard_analysis"] = guard_analysis

    return build_api_response_bundle(bundle, response_type="compare")


def _required_dict(payload: dict[str, Any], *keys: str) -> dict[str, Any]:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, dict):
            return value
    names = " or ".join(keys)
    raise ValueError(f"{names} must be provided as a JSON object")


def _optional_float(payload: dict[str, Any], key: str) -> float | None:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be a number when provided")
    return float(value)
