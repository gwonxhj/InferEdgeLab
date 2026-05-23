import subprocess
import sys
from pathlib import Path

from inferedgelab.services.compare_service import build_compare_bundle
from scripts.check_runtime_intelligence_artifact_bundle import main as gate_main


REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_RESULT = REPO_ROOT / "examples" / "edgeenv_regression" / "lab_baseline_result.json"
CANDIDATE_RESULT = REPO_ROOT / "examples" / "edgeenv_regression" / "lab_candidate_result.json"
EDGEENV_WITH_ORCHESTRATOR = (
    REPO_ROOT
    / "examples"
    / "runtime_intelligence_chain"
    / "edgeenv_regression_with_orchestrator_context.json"
)
AIGUARD_RUNTIME_OPERATION = (
    REPO_ROOT
    / "examples"
    / "runtime_intelligence_chain"
    / "aiguard_runtime_operation_guard_analysis.json"
)


def _write_runtime_intelligence_reports(tmp_path):
    bundle = build_compare_bundle(
        base_path=str(BASE_RESULT),
        new_path=str(CANDIDATE_RESULT),
        edgeenv_regression_path=str(EDGEENV_WITH_ORCHESTRATOR),
        guard_analysis_path=str(AIGUARD_RUNTIME_OPERATION),
    )
    markdown_path = tmp_path / "runtime_intelligence_chain.md"
    html_path = tmp_path / "runtime_intelligence_chain.html"
    markdown_path.write_text(bundle["markdown"], encoding="utf-8")
    html_path.write_text(bundle["html"], encoding="utf-8")
    return markdown_path, html_path


def test_runtime_intelligence_artifact_gate_passes_for_chain_report(tmp_path):
    markdown_path, html_path = _write_runtime_intelligence_reports(tmp_path)
    summary_path = tmp_path / "gate_summary.md"

    result = gate_main(
        markdown=str(markdown_path),
        html=str(html_path),
        summary_out=str(summary_path),
    )

    assert result == 0
    summary = summary_path.read_text(encoding="utf-8")
    assert "- Status: passed" in summary
    assert "- Missing Markdown markers: 0" in summary
    assert "- Missing HTML markers: 0" in summary


def test_runtime_intelligence_artifact_gate_cli_passes_for_chain_report(tmp_path):
    markdown_path, html_path = _write_runtime_intelligence_reports(tmp_path)
    summary_path = tmp_path / "gate_summary.md"

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "check_runtime_intelligence_artifact_bundle.py"),
            "--markdown",
            str(markdown_path),
            "--html",
            str(html_path),
            "--summary-out",
            str(summary_path),
        ],
        check=False,
        cwd=str(REPO_ROOT),
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    assert "Runtime Intelligence artifact bundle gate passed." in result.stdout
    assert "- Status: passed" in summary_path.read_text(encoding="utf-8")


def test_runtime_intelligence_artifact_gate_fails_when_owner_row_is_missing(
    tmp_path,
):
    markdown_path, html_path = _write_runtime_intelligence_reports(tmp_path)
    markdown = markdown_path.read_text(encoding="utf-8").replace(
        "Lab remains the final deployment decision owner.",
        "Lab ownership marker removed.",
    )
    markdown_path.write_text(markdown, encoding="utf-8")
    summary_path = tmp_path / "gate_summary.md"

    result = gate_main(
        markdown=str(markdown_path),
        html=str(html_path),
        summary_out=str(summary_path),
    )

    assert result == 2
    summary = summary_path.read_text(encoding="utf-8")
    assert "- Status: failed" in summary
    assert "`lab_decision_owner`" in summary


def test_runtime_intelligence_artifact_gate_fails_when_coverage_gap_marker_is_missing(
    tmp_path,
):
    markdown_path, html_path = _write_runtime_intelligence_reports(tmp_path)
    markdown = markdown_path.read_text(encoding="utf-8").replace(
        "runtime_telemetry_field_gap",
        "coverage marker removed",
    )
    html = html_path.read_text(encoding="utf-8").replace(
        "runtime_telemetry_field_gap",
        "coverage marker removed",
    )
    markdown_path.write_text(markdown, encoding="utf-8")
    html_path.write_text(html, encoding="utf-8")
    summary_path = tmp_path / "gate_summary.md"

    result = gate_main(
        markdown=str(markdown_path),
        html=str(html_path),
        summary_out=str(summary_path),
    )

    assert result == 2
    summary = summary_path.read_text(encoding="utf-8")
    assert "`aiguard_coverage_field_gap`" in summary
