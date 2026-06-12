import json
from pathlib import Path

from scripts.check_runtime_intelligence_source_traceability import (
    EXPECTED_AIGUARD_REPRODUCTION_COMMAND_MARKER,
    EXPECTED_AIGUARD_SOURCE_ARTIFACT_MARKER,
    main as source_traceability_gate,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
EDGEENV_HANDOFF = (
    REPO_ROOT
    / "examples"
    / "runtime_intelligence_chain"
    / "edgeenv_lab_handoff_manifest.json"
)
AIGUARD_OPTIONAL_PRESENT_ALIGNMENT = (
    REPO_ROOT
    / "examples"
    / "runtime_intelligence_chain"
    / "aiguard_edgeenv_handoff_alignment_optional_present.json"
)


def test_runtime_intelligence_source_traceability_gate_passes(tmp_path):
    summary_path = tmp_path / "source_traceability_summary.md"

    result = source_traceability_gate(
        edgeenv_handoff=str(EDGEENV_HANDOFF),
        aiguard_alignment=str(AIGUARD_OPTIONAL_PRESENT_ALIGNMENT),
        summary_out=str(summary_path),
    )

    assert result == 0
    summary = summary_path.read_text(encoding="utf-8")
    assert "- Status: passed" in summary
    assert "## Validated Source Traceability" in summary
    assert (
        "source_traceability_alignment: EdgeEnv handoff and AIGuard "
        "optional-present fixture match"
    ) in summary
    assert (
        "edgeenv_optional_source_traceability: "
        "read_only_optional_source_traceability preserved"
    ) in summary
    assert (
        f"aiguard_optional_present_source_artifact: "
        f"{EXPECTED_AIGUARD_SOURCE_ARTIFACT_MARKER}"
    ) in summary
    assert (
        f"aiguard_optional_present_reproduction_command: "
        f"{EXPECTED_AIGUARD_REPRODUCTION_COMMAND_MARKER}"
    ) in summary
    assert (
        "ownership: edgeenv_does_not_generate_guard_analysis=true, "
        "lab_is_final_decision_owner=true"
    ) in summary


def test_runtime_intelligence_source_traceability_gate_fails_for_mismatched_source(
    tmp_path,
):
    alignment = json.loads(AIGUARD_OPTIONAL_PRESENT_ALIGNMENT.read_text("utf-8"))
    alignment["optional_present_source_artifact"]["repository"] = "InferEdgeEnv"
    alignment_path = tmp_path / "aiguard_optional_present_alignment.json"
    alignment_path.write_text(json.dumps(alignment), encoding="utf-8")
    summary_path = tmp_path / "source_traceability_summary.md"

    result = source_traceability_gate(
        edgeenv_handoff=str(EDGEENV_HANDOFF),
        aiguard_alignment=str(alignment_path),
        summary_out=str(summary_path),
    )

    assert result == 2
    summary = summary_path.read_text(encoding="utf-8")
    assert "- Status: failed" in summary
    assert (
        "AIGuard alignment source artifact must match the Lab-known AIGuard "
        "optional stale-drop source artifact"
    ) in summary
    assert (
        "EdgeEnv handoff and AIGuard optional-present alignment must reference "
        "the same source artifact and reproduction command"
    ) in summary
