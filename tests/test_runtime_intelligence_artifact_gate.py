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
    assert "## Validated Duration Traceability" in summary
    assert (
        "duration_handoff_alignment: EdgeEnv/AIGuard report context preserved"
        in summary
    )
    assert "duration_source: source=entrypoint_requested_frames" in summary
    assert (
        "duration_scope_label: scope_label=source=entrypoint_requested_frames"
        in summary
    )
    assert "duration_label: short 96-frame-class replay (96 frames)" in summary
    assert "## Validated Reviewer Focus" in summary
    assert (
        "reviewer_focus_operation_quick_scan: Reviewer Focus / "
        "Operation quick scan marker validated"
    ) in summary
    assert "reviewer_focus_fixture_matrix: EdgeEnv fixture matrix row validated" in summary
    assert "## Validated EdgeEnv Fixture Matrix" in summary
    assert (
        "edgeenv_fixture_matrix_coverage: EdgeEnv fixture matrix coverage row validated"
        in summary
    )
    assert "## Validated Review Path" in summary
    assert "review_path_section: short Review Path section rendered" in summary
    assert "review_path_fast_path: readable Review Path fast path rendered" in summary
    assert (
        "review_path: Reviewer Focus -> Detailed Evidence Rows guidance validated"
        in summary
    )
    assert (
        "review_path_scope: comparable regression / telemetry replay / "
        "operation evidence preserved"
    ) in summary
    markdown = markdown_path.read_text(encoding="utf-8")
    html = html_path.read_text(encoding="utf-8")
    assert "### Review Path" in markdown
    assert "Review path: start with `Reviewer Focus`" in markdown
    assert (
        "Fast path: `Reviewer Focus` -> `Detailed Evidence Rows` only when a quick "
        "signal needs supporting evidence."
    ) in markdown
    assert "| Step | Open | Use it for |" in markdown
    assert 'class="review-path"' in html
    assert "<h3>Review Path</h3>" in html
    assert "Review path:" in html
    assert "Runtime replay duration scope" in markdown
    assert "short 96-frame-class replay (96 frames)" in markdown
    assert "source=entrypoint_requested_frames" in markdown
    assert "scope_label=source=entrypoint_requested_frames" in markdown
    assert "| Operation quick scan | candidate: " in markdown
    assert "rendered_label=Reviewer operation quick scan" in markdown
    assert "raw_marker=reviewer_focus_operation_quick_scan" in markdown
    assert "Operation quick scan" in html
    assert "raw_marker=reviewer_focus_operation_quick_scan" in html
    assert "| EdgeEnv fixture matrix |" in markdown
    assert "| EdgeEnv fixture matrix coverage |" in markdown
    assert "schema=edgeenv-regression-replay-fixture-matrix-v1" in markdown
    assert (
        "modes=same-condition,runtime-comparison,target-comparison,protocol_mismatch"
        in markdown
    )
    assert "not_a_deployment_decision=True" in markdown
    assert "EdgeEnv fixture matrix coverage" in html
    assert "roles=6/6" in html


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
    summary = summary_path.read_text(encoding="utf-8")
    assert "- Status: passed" in summary
    assert "duration_handoff_alignment" in summary
    assert "reviewer_focus_operation_quick_scan" in summary
    assert "reviewer_focus_operation_quick_scan_raw_marker" in summary
    assert "reviewer_focus_fixture_matrix" in summary
    assert "Validated EdgeEnv Fixture Matrix" in summary
    assert "Validated Review Path" in summary
    assert "review_path_section: short Review Path section rendered" in summary
    assert "review_path_fast_path: readable Review Path fast path rendered" in summary
    assert "review_path: Reviewer Focus -> Detailed Evidence Rows guidance validated" in summary


def test_runtime_intelligence_docs_describe_duration_traceability_gate_summary():
    docs = [
        REPO_ROOT / "docs" / "ci" / "runtime_intelligence_gitlab_artifacts.md",
        REPO_ROOT
        / "docs"
        / "portfolio"
        / "edgeenv_runtime_regression_lab_handoff.md",
    ]

    for path in docs:
        text = path.read_text(encoding="utf-8")
        assert "Validated Duration Traceability" in text
        assert "duration_handoff_alignment" in text
        assert "source=entrypoint_requested_frames" in text
        assert "scope_label=source=entrypoint_requested_frames" in text
        assert "Validated Reviewer Focus" in text
        assert "Operation quick scan marker validated" in text
        assert "EdgeEnv fixture matrix coverage" in text
        assert "Validated Review Path" in text
        assert "Reviewer Focus -> Detailed Evidence Rows guidance validated" in text


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


def test_runtime_intelligence_artifact_gate_fails_when_run_config_traceability_is_missing(
    tmp_path,
):
    markdown_path, html_path = _write_runtime_intelligence_reports(tmp_path)
    markdown = markdown_path.read_text(encoding="utf-8").replace(
        "runtime_history_seed_run_config_traceability",
        "run_config traceability marker removed",
    )
    html = html_path.read_text(encoding="utf-8").replace(
        "runtime_history_seed_run_config_traceability",
        "run_config traceability marker removed",
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
    assert "`aiguard_run_config_traceability_evidence`" in summary


def test_runtime_intelligence_artifact_gate_fails_when_lab_preservation_context_is_missing(
    tmp_path,
):
    markdown_path, html_path = _write_runtime_intelligence_reports(tmp_path)
    markdown = markdown_path.read_text(encoding="utf-8").replace(
        "Lab EdgeEnv preservation context",
        "Lab preservation context marker removed",
    )
    html = html_path.read_text(encoding="utf-8").replace(
        "Lab EdgeEnv preservation context",
        "Lab preservation context marker removed",
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
    assert "`lab_edgeenv_preservation_context`" in summary


def test_runtime_intelligence_artifact_gate_fails_when_jetson_identity_is_missing(
    tmp_path,
):
    markdown_path, html_path = _write_runtime_intelligence_reports(tmp_path)
    markdown = markdown_path.read_text(encoding="utf-8").replace(
        "identity=jetson_device_local_preservation",
        "identity marker removed",
    )
    html = html_path.read_text(encoding="utf-8").replace(
        "identity=jetson_device_local_preservation",
        "identity marker removed",
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
    assert "`jetson_edgeenv_preservation_identity`" in summary


def test_runtime_intelligence_artifact_gate_fails_when_jetson_details_are_missing(
    tmp_path,
):
    markdown_path, html_path = _write_runtime_intelligence_reports(tmp_path)
    markdown = markdown_path.read_text(encoding="utf-8").replace(
        "Jetson/device-local EdgeEnv preservation details",
        "Jetson detail row removed",
    )
    html = html_path.read_text(encoding="utf-8").replace(
        "Jetson/device-local EdgeEnv preservation details",
        "Jetson detail row removed",
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
    assert "`jetson_edgeenv_preservation_details`" in summary


def test_runtime_intelligence_artifact_gate_fails_when_remote_summary_is_missing(
    tmp_path,
):
    markdown_path, html_path = _write_runtime_intelligence_reports(tmp_path)
    markdown = markdown_path.read_text(encoding="utf-8").replace(
        "AIGuard remote dispatch event summary",
        "remote dispatch summary marker removed",
    )
    html = html_path.read_text(encoding="utf-8").replace(
        "AIGuard remote dispatch event summary",
        "remote dispatch summary marker removed",
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
    assert "`aiguard_remote_dispatch_summary`" in summary
