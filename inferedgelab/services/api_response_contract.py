from __future__ import annotations

from typing import Any

from inferedgelab.services.guard_analysis import guard_status, guard_verdict


def build_api_response_bundle(
    bundle: dict[str, Any],
    *,
    response_type: str = "compare",
) -> dict[str, Any]:
    """Wrap an internal Lab bundle into the stable SaaS API response shape.

    This helper does not recompute comparison, report, or deployment decision
    logic. It only projects the existing service bundle into an external
    contract that frontend/API clients can depend on.
    """

    data = bundle.get("data") if isinstance(bundle.get("data"), dict) else {}
    meta = bundle.get("meta") if isinstance(bundle.get("meta"), dict) else {}
    result = bundle.get("result") or data.get("result") or {}
    judgement = bundle.get("judgement") or data.get("judgement") or {}
    rendered = bundle.get("rendered") if isinstance(bundle.get("rendered"), dict) else {}
    deployment_decision = (
        bundle.get("deployment_decision")
        or data.get("deployment_decision")
        or {}
    )

    response = {
        "summary": _build_summary(
            response_type=response_type,
            result=result,
            judgement=judgement,
            deployment_decision=deployment_decision,
            guard_analysis=bundle.get("guard_analysis") or data.get("guard_analysis"),
        ),
        "comparison": {
            "result": result,
            "judgement": judgement,
            "rendered": {
                "markdown": bundle.get("markdown") or rendered.get("markdown"),
                "html": bundle.get("html") or rendered.get("html"),
            },
        },
        "deployment_decision": deployment_decision,
        "provenance": {
            "runtime": result.get("runtime_provenance"),
            "shape": result.get("shape_context"),
            "run_config_diff": result.get("run_config_diff"),
            "source_bundle": response_type,
        },
        "metadata": {
            **meta,
            "legacy_warning": bundle.get("legacy_warning", meta.get("legacy_warning")),
        },
        "timestamps": _build_timestamps(bundle, result),
        "execution_info": _build_execution_info(bundle, meta),
    }

    guard_analysis = bundle.get("guard_analysis") or data.get("guard_analysis")
    if guard_analysis is not None:
        response["guard_analysis"] = guard_analysis

    return response


def _build_summary(
    *,
    response_type: str,
    result: dict[str, Any],
    judgement: dict[str, Any],
    deployment_decision: dict[str, Any],
    guard_analysis: dict[str, Any] | None,
) -> dict[str, Any]:
    precision = result.get("precision") if isinstance(result.get("precision"), dict) else {}
    return {
        "response_type": response_type,
        "overall": judgement.get("overall"),
        "comparison_mode": judgement.get("comparison_mode")
        or precision.get("comparison_mode"),
        "precision_pair": judgement.get("precision_pair") or precision.get("pair"),
        "deployment_decision": deployment_decision.get("decision"),
        "guard_status": guard_status(guard_analysis),
        "guard_verdict": guard_verdict(guard_analysis),
    }


def _build_timestamps(bundle: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    base = bundle.get("base") if isinstance(bundle.get("base"), dict) else {}
    new = bundle.get("new") if isinstance(bundle.get("new"), dict) else {}
    base_id = result.get("base_id") if isinstance(result.get("base_id"), dict) else {}
    new_id = result.get("new_id") if isinstance(result.get("new_id"), dict) else {}
    return {
        "base": base.get("timestamp") or base_id.get("timestamp"),
        "new": new.get("timestamp") or new_id.get("timestamp"),
    }


def _build_execution_info(bundle: dict[str, Any], meta: dict[str, Any]) -> dict[str, Any]:
    return {
        "base_path": bundle.get("base_path") or meta.get("base_path"),
        "new_path": bundle.get("new_path") or meta.get("new_path"),
        "selection_mode": bundle.get("selection_mode") or meta.get("selection_mode"),
        "legacy_warning": bundle.get("legacy_warning", meta.get("legacy_warning")),
    }
