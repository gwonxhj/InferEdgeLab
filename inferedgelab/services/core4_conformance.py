from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from inferedgelab.services.demo_evidence_report import build_demo_evidence_summary

SCHEMA_VERSION = "inferedgelab-core4-conformance-v1"
DEFAULT_FIXTURE_DIR = Path(__file__).resolve().parents[2] / "examples" / "core4_conformance"
DEFAULT_STUDIO_DEMO_DIR = Path(__file__).resolve().parents[2] / "examples" / "studio_demo"


def build_core4_conformance_report(repo_root: str | Path | None = None) -> dict[str, Any]:
    """Validate the Core 4 contract chain with committed lightweight fixtures.

    This check is intentionally local-first and fixture-based. It does not run
    workers or mutate existing result/compare schemas.
    """

    root = Path(repo_root) if repo_root is not None else Path.cwd()
    checks: list[dict[str, Any]] = []

    manifest_path = root / "examples" / "core4_conformance" / "forge_manifest.json"
    metadata_path = root / "examples" / "core4_conformance" / "forge_metadata.json"
    runtime_path = root / "examples" / "studio_demo" / "tensorrt_jetson_25w_result.json"
    guard_path = root / "examples" / "studio_demo" / "aiguard_portfolio_cases.json"

    manifest = _load_json(manifest_path, checks, "forge:manifest_file")
    metadata = _load_json(metadata_path, checks, "forge:metadata_file")
    runtime = _load_json(runtime_path, checks, "runtime:result_file")
    guard_bundle = _load_json(guard_path, checks, "aiguard:portfolio_cases_file")
    summary = build_demo_evidence_summary()

    _check_forge_contract(manifest, metadata, checks)
    _check_runtime_contract(runtime, manifest, metadata, checks)
    _check_lab_contract(summary, checks)
    _check_aiguard_contract(guard_bundle, checks)
    _check_cross_repo_handoff(manifest, metadata, runtime, checks)

    failed = [check for check in checks if not check["passed"]]
    layer_status = _layer_status(checks)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "pass" if not failed else "fail",
        "generated_at": _utc_now_iso(),
        "repo_root": str(root),
        "scope": "local-first Core 4 contract conformance smoke",
        "layers": layer_status,
        "check_count": len(checks),
        "failed_count": len(failed),
        "checks": checks,
        "core_contracts": {
            "forge_manifest": str(manifest_path),
            "forge_metadata": str(metadata_path),
            "runtime_result": str(runtime_path),
            "lab_compare_source": "examples/studio_demo via demo evidence summary",
            "aiguard_guard_analysis": str(guard_path),
        },
        "notes": [
            "This is a local-first fixture conformance check, not a production worker run.",
            "Lab remains the deployment decision owner; AIGuard remains optional deterministic diagnosis evidence.",
            "Existing metadata.json, manifest.json, result.json, compare output, and guard_analysis contracts are validated without mutation.",
        ],
    }


def build_core4_conformance_text(report: dict[str, Any] | None = None) -> str:
    report = report or build_core4_conformance_report()
    lines = [
        "InferEdge Core 4 Contract Conformance Check",
        f"status: {report['status']}",
        f"checks: {report['check_count']} total / {report['failed_count']} failed",
        "",
        "Layer status:",
    ]
    for layer, status in report["layers"].items():
        lines.append(
            f"- {layer}: {status['status']} ({status['passed']}/{status['total']} passed)"
        )
    failed = [check for check in report["checks"] if not check["passed"]]
    if failed:
        lines.extend(["", "Failed checks:"])
        for check in failed:
            lines.append(
                f"- {check['name']}: expected={check.get('expected')} observed={check.get('observed')}"
            )
    else:
        lines.extend(["", "All Core 4 contract conformance checks passed."])
    lines.append("")
    return "\n".join(lines)


def core4_conformance_json(report: dict[str, Any] | None = None) -> str:
    return json.dumps(report or build_core4_conformance_report(), ensure_ascii=False, indent=2) + "\n"


def _check_forge_contract(
    manifest: dict[str, Any] | None,
    metadata: dict[str, Any] | None,
    checks: list[dict[str, Any]],
) -> None:
    checks.extend(
        _required_path_checks(
            manifest,
            "forge_manifest",
            [
                ("schema_version",),
                ("build_id",),
                ("source_model", "path"),
                ("source_model", "sha256"),
                ("artifact", "path"),
                ("artifact", "sha256"),
                ("artifact", "type"),
                ("backend",),
                ("target",),
                ("precision",),
                ("input_shape",),
                ("preset", "name"),
                ("runtime_handoff", "compare_key_hint"),
                ("runtime_handoff", "backend_key_hint"),
            ],
            category="forge",
        )
    )
    checks.extend(
        _required_path_checks(
            metadata,
            "forge_metadata",
            [
                ("schema_version",),
                ("build_id",),
                ("source_model_path",),
                ("source_model_sha256",),
                ("artifact_path",),
                ("artifact_sha256",),
                ("artifact_type",),
                ("backend",),
                ("target",),
                ("precision",),
                ("batch",),
                ("height",),
                ("width",),
                ("preset_name",),
                ("runtime_handoff", "compare_key_hint"),
                ("runtime_handoff", "backend_key_hint"),
            ],
            category="forge",
        )
    )


def _check_runtime_contract(
    runtime: dict[str, Any] | None,
    manifest: dict[str, Any] | None,
    metadata: dict[str, Any] | None,
    checks: list[dict[str, Any]],
) -> None:
    checks.extend(
        _required_path_checks(
            runtime,
            "runtime_result",
            [
                ("runtime_role",),
                ("compare_key",),
                ("backend_key",),
                ("engine_backend",),
                ("device_name",),
                ("precision",),
                ("mean_ms",),
                ("p95_ms",),
                ("p99_ms",),
                ("fps_value",),
                ("success",),
                ("status",),
                ("run_config",),
                ("extra", "source_model_path"),
                ("extra", "source_model_sha256"),
                ("extra", "runtime_artifact_sha256"),
                ("extra", "compare_ready"),
            ],
            category="runtime",
        )
    )
    if runtime is None:
        return

    checks.append(
        _check_item(
            name="runtime:result_role",
            passed=runtime.get("runtime_role") == "runtime-result",
            category="runtime",
            expected="runtime-result",
            observed=runtime.get("runtime_role"),
        )
    )
    checks.append(
        _check_item(
            name="runtime:success_status",
            passed=runtime.get("success") is True and runtime.get("status") == "success",
            category="runtime",
            expected="success true/status success",
            observed=f"success={runtime.get('success')} status={runtime.get('status')}",
        )
    )
    if manifest is not None:
        checks.append(
            _check_item(
                name="runtime:manifest_handoff_compare_key",
                passed=runtime.get("compare_key") == _dig(manifest, ("runtime_handoff", "compare_key_hint")),
                category="runtime",
                expected=_dig(manifest, ("runtime_handoff", "compare_key_hint")),
                observed=runtime.get("compare_key"),
            )
        )
    if metadata is not None:
        checks.append(
            _check_item(
                name="runtime:metadata_handoff_backend_key",
                passed=runtime.get("backend_key") == _dig(metadata, ("runtime_handoff", "backend_key_hint")),
                category="runtime",
                expected=_dig(metadata, ("runtime_handoff", "backend_key_hint")),
                observed=runtime.get("backend_key"),
            )
        )


def _check_lab_contract(summary: dict[str, Any], checks: list[dict[str, Any]]) -> None:
    comparison = summary.get("comparison") if isinstance(summary.get("comparison"), dict) else {}
    decision = summary.get("deployment_decision") if isinstance(summary.get("deployment_decision"), dict) else {}
    checks.extend(
        [
            _check_item(
                name="lab:compare_baseline_backend_key",
                passed=bool(comparison.get("baseline_backend_key")),
                category="lab",
                expected="non-empty baseline backend_key",
                observed=comparison.get("baseline_backend_key"),
            ),
            _check_item(
                name="lab:compare_candidate_backend_key",
                passed=bool(comparison.get("candidate_backend_key")),
                category="lab",
                expected="non-empty candidate backend_key",
                observed=comparison.get("candidate_backend_key"),
            ),
            _check_item(
                name="lab:compare_speedup",
                passed=_is_number(comparison.get("speedup")) and float(comparison["speedup"]) > 1.0,
                category="lab",
                expected="numeric speedup > 1.0",
                observed=comparison.get("speedup"),
            ),
            _check_item(
                name="lab:deployment_decision_present",
                passed=decision.get("decision") in {"deployable", "review_required", "review", "blocked", "unknown"},
                category="lab",
                expected="known Lab decision value",
                observed=decision.get("decision"),
            ),
            _check_item(
                name="lab:deployment_reason_present",
                passed=bool(decision.get("reason")),
                category="lab",
                expected="non-empty reason",
                observed=decision.get("reason"),
            ),
        ]
    )


def _check_aiguard_contract(
    guard_bundle: dict[str, Any] | None,
    checks: list[dict[str, Any]],
) -> None:
    cases = guard_bundle.get("cases") if isinstance(guard_bundle, dict) else None
    checks.append(
        _check_item(
            name="aiguard:case_bundle",
            passed=isinstance(cases, list) and len(cases) >= 4,
            category="aiguard",
            expected="at least 4 portfolio guard cases",
            observed=len(cases) if isinstance(cases, list) else None,
        )
    )
    if not isinstance(cases, list):
        return

    guard_verdicts = set()
    for index, case in enumerate(cases):
        guard = case.get("guard_analysis") if isinstance(case, dict) else None
        prefix = f"aiguard:case_{index}"
        checks.extend(
            _required_path_checks(
                guard,
                prefix,
                [
                    ("schema_version",),
                    ("guard_verdict",),
                    ("severity",),
                    ("primary_reason",),
                    ("evidence",),
                    ("recommendations",),
                ],
                category="aiguard",
            )
        )
        if isinstance(guard, dict):
            guard_verdicts.add(guard.get("guard_verdict"))
            evidence = guard.get("evidence")
            checks.append(
                _check_item(
                    name=f"{prefix}:evidence_items",
                    passed=isinstance(evidence, list) and len(evidence) > 0,
                    category="aiguard",
                    expected="non-empty evidence list",
                    observed=len(evidence) if isinstance(evidence, list) else None,
                )
            )
            if isinstance(evidence, list) and evidence:
                item = evidence[0] if isinstance(evidence[0], dict) else None
                checks.extend(
                    _required_path_checks(
                        item,
                        f"{prefix}:evidence_0",
                        [
                            ("type",),
                            ("metric_name",),
                            ("observed_value",),
                            ("threshold",),
                            ("severity",),
                            ("status",),
                            ("explanation",),
                            ("suspected_causes",),
                            ("recommendation",),
                        ],
                        category="aiguard",
                    )
                )

    checks.append(
        _check_item(
            name="aiguard:verdict_coverage",
            passed={"pass", "blocked", "review_required"}.issubset(guard_verdicts),
            category="aiguard",
            expected=["blocked", "pass", "review_required"],
            observed=sorted(v for v in guard_verdicts if isinstance(v, str)),
        )
    )


def _check_cross_repo_handoff(
    manifest: dict[str, Any] | None,
    metadata: dict[str, Any] | None,
    runtime: dict[str, Any] | None,
    checks: list[dict[str, Any]],
) -> None:
    if manifest is None or metadata is None or runtime is None:
        return

    extra = runtime.get("extra") if isinstance(runtime.get("extra"), dict) else {}
    checks.extend(
        [
            _check_item(
                name="handoff:source_model_sha256",
                passed=extra.get("source_model_sha256")
                == _dig(manifest, ("source_model", "sha256"))
                == metadata.get("source_model_sha256"),
                category="handoff",
                expected=_dig(manifest, ("source_model", "sha256")),
                observed=extra.get("source_model_sha256"),
            ),
            _check_item(
                name="handoff:artifact_sha256",
                passed=extra.get("runtime_artifact_sha256")
                == _dig(manifest, ("artifact", "sha256"))
                == metadata.get("artifact_sha256"),
                category="handoff",
                expected=_dig(manifest, ("artifact", "sha256")),
                observed=extra.get("runtime_artifact_sha256"),
            ),
            _check_item(
                name="handoff:precision",
                passed=runtime.get("precision") == manifest.get("precision") == metadata.get("precision"),
                category="handoff",
                expected=manifest.get("precision"),
                observed=runtime.get("precision"),
            ),
            _check_item(
                name="handoff:backend",
                passed=runtime.get("engine_backend") == manifest.get("backend") == metadata.get("backend"),
                category="handoff",
                expected=manifest.get("backend"),
                observed=runtime.get("engine_backend"),
            ),
        ]
    )


def _required_path_checks(
    data: dict[str, Any] | None,
    prefix: str,
    paths: list[tuple[str, ...]],
    *,
    category: str,
) -> list[dict[str, Any]]:
    checks = []
    for path in paths:
        value = _dig(data, path)
        checks.append(
            _check_item(
                name=f"{prefix}:{'.'.join(path)}",
                passed=value is not None and value != "",
                category=category,
                expected="present",
                observed="present" if value is not None and value != "" else "missing",
            )
        )
    return checks


def _layer_status(checks: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    layers = ("forge", "runtime", "lab", "aiguard", "handoff")
    status: dict[str, dict[str, Any]] = {}
    for layer in layers:
        items = [check for check in checks if check["category"] == layer]
        passed = sum(1 for check in items if check["passed"])
        status[layer] = {
            "status": "pass" if passed == len(items) else "fail",
            "passed": passed,
            "total": len(items),
        }
    return status


def _load_json(path: Path, checks: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        checks.append(
            _check_item(
                name=name,
                passed=False,
                category=name.split(":", 1)[0],
                expected="readable JSON file",
                observed=str(exc),
            )
        )
        return None
    checks.append(
        _check_item(
            name=name,
            passed=True,
            category=name.split(":", 1)[0],
            expected="readable JSON file",
            observed=str(path),
        )
    )
    return data


def _dig(data: dict[str, Any] | None, path: tuple[str, ...]) -> Any:
    current: Any = data
    for part in path:
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _check_item(
    *,
    name: str,
    passed: bool,
    category: str,
    expected: Any | None = None,
    observed: Any | None = None,
) -> dict[str, Any]:
    item = {
        "name": name,
        "category": category,
        "passed": bool(passed),
    }
    if expected is not None:
        item["expected"] = expected
    if observed is not None:
        item["observed"] = observed
    return item


def _is_number(value: Any) -> bool:
    if isinstance(value, bool) or value is None:
        return False
    try:
        float(value)
    except (TypeError, ValueError):
        return False
    return True


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
