import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "smoke_agent_runtime_edgeenv_preservation.sh"


def test_agent_runtime_edgeenv_preservation_smoke_script_help():
    result = subprocess.run(
        ["bash", str(SCRIPT), "--help"],
        check=False,
        cwd=str(REPO_ROOT),
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    assert "Agent Runtime EdgeEnv preservation smoke" in result.stdout
    assert "does not require a live Jetson device" in result.stdout


def test_agent_runtime_edgeenv_preservation_smoke_script_rejects_missing_output_dir_value():
    result = subprocess.run(
        ["bash", str(SCRIPT), "--output-dir"],
        check=False,
        cwd=str(REPO_ROOT),
        text=True,
        capture_output=True,
    )

    assert result.returncode == 2
    assert "--output-dir requires a value" in result.stderr


def test_agent_runtime_edgeenv_preservation_smoke_script_runs_gate(tmp_path):
    output_dir = tmp_path / "agent_runtime_edgeenv_preservation"

    result = subprocess.run(
        ["bash", str(SCRIPT), "--output-dir", str(output_dir)],
        check=False,
        cwd=str(REPO_ROOT),
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Agent Runtime EdgeEnv preservation smoke passed." in result.stdout

    report_json = output_dir / "agent_runtime_edgeenv_preservation.json"
    report_md = output_dir / "agent_runtime_edgeenv_preservation.md"
    assert report_json.is_file()
    assert report_md.is_file()

    json_text = report_json.read_text(encoding="utf-8")
    assert "edgeenv_preservation_context" in json_text
    assert "run-fixture-edgeenv-operation-0001" in json_text

    markdown = report_md.read_text(encoding="utf-8")
    assert "Runtime Intelligence EdgeEnv Preservation" in markdown
    assert "| edgeenv_run_id | run-fixture-edgeenv-operation-0001 |" in markdown
    assert "| comparability_role | supplemental_evidence_not_gate |" in markdown
    assert "Lab remains the final deployment decision owner" in markdown
