import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "smoke_agent_runtime_remote_paths.sh"


def test_agent_runtime_remote_paths_smoke_script_help():
    result = subprocess.run(
        ["bash", str(SCRIPT), "--help"],
        check=False,
        cwd=str(REPO_ROOT),
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    assert "Agent Runtime remote dispatch path smoke" in result.stdout
    assert "production remote execution" in result.stdout


def test_agent_runtime_remote_paths_smoke_script_rejects_missing_output_dir_value():
    result = subprocess.run(
        ["bash", str(SCRIPT), "--output-dir"],
        check=False,
        cwd=str(REPO_ROOT),
        text=True,
        capture_output=True,
    )

    assert result.returncode == 2
    assert "--output-dir requires a value" in result.stderr


def test_agent_runtime_remote_paths_smoke_script_runs_both_paths(tmp_path):
    output_dir = tmp_path / "agent_runtime_remote_paths"

    result = subprocess.run(
        ["bash", str(SCRIPT), "--output-dir", str(output_dir)],
        check=False,
        cwd=str(REPO_ROOT),
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Agent Runtime remote dispatch path smoke passed." in result.stdout

    plan_only = output_dir / "remote_dispatch_plan_only.md"
    fallback = output_dir / "remote_dispatch_fallback_recovered.md"
    assert plan_only.is_file()
    assert fallback.is_file()

    plan_text = plan_only.read_text(encoding="utf-8")
    assert "execution_plan_mode" in plan_text
    assert "plan_only" in plan_text
    assert "remote_runtime_summary_boundary" in plan_text
    assert "remote dispatch starter evidence only" in plan_text

    fallback_text = fallback.read_text(encoding="utf-8")
    assert "remote_operation_final_status" in fallback_text
    assert "succeeded" in fallback_text
    assert "remote_runtime_event_count" in fallback_text
    assert "remote_runtime_summary_boundary" in fallback_text
    assert "remote dispatch starter evidence only" in fallback_text
    assert "remote_execution_recovered_by_fallback" in fallback_text
