from __future__ import annotations

import importlib.util
import io
import json
import sys
import types
from contextlib import redirect_stdout
from pathlib import Path


def import_update_benchmarks_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "update_benchmarks.py"
    spec = importlib.util.spec_from_file_location("test_update_benchmarks_module", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


update_benchmarks = import_update_benchmarks_module()


def import_summarize_module():
    if "typer" not in sys.modules:
        typer_stub = types.ModuleType("typer")

        class BadParameter(Exception):
            pass

        def argument(default=None, *args, **kwargs):
            return default

        def option(default=None, *args, **kwargs):
            return default

        typer_stub.BadParameter = BadParameter
        typer_stub.Argument = argument
        typer_stub.Option = option
        sys.modules["typer"] = typer_stub

    if "rich" not in sys.modules:
        rich_stub = types.ModuleType("rich")
        rich_stub.print = print
        sys.modules["rich"] = rich_stub

    module_path = Path(__file__).resolve().parents[1] / "inferedgelab" / "commands" / "summarize.py"
    spec = importlib.util.spec_from_file_location("test_update_benchmarks_summarize_module", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def make_readme(text: str = "old summary") -> str:
    return (
        "# Demo README\n\n"
        "Manual intro\n\n"
        f"{update_benchmarks.README_MARK_START}\n"
        f"{text}\n"
        f"{update_benchmarks.README_MARK_END}\n\n"
        "Manual outro\n"
    )


def make_benchmarks(text: str = "old auto summary") -> str:
    return (
        "# Benchmarks\n\n"
        "Manual validation evidence before\n\n"
        f"{update_benchmarks.BENCHMARKS_MARK_START}\n"
        f"{text}\n"
        f"{update_benchmarks.BENCHMARKS_MARK_END}\n\n"
        "Manual validation evidence after\n"
    )


def write_report(
    path: Path,
    *,
    model_name: str,
    mean_ms: float,
    p99_ms: float,
    timestamp: str,
) -> None:
    path.write_text(
        json.dumps(
            {
                "model": {"path": f"models/{model_name}"},
                "static": {"flops_estimate": 126444160},
                "runtime": {
                    "engine": "onnxruntime",
                    "device": "cpu",
                    "latency_ms": {
                        "mean": mean_ms,
                        "p99": p99_ms,
                    },
                    "extra": {
                        "batch": 1,
                        "height": 224,
                        "width": 224,
                    },
                },
                "timestamp": timestamp,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def test_replace_named_marker_block_replaces_readme_marker_block():
    text = make_readme()

    replaced = update_benchmarks.replace_named_marker_block(
        text,
        update_benchmarks.README_MARK_START,
        update_benchmarks.README_MARK_END,
        "new summary",
    )

    assert "new summary" in replaced
    assert "old summary" not in replaced
    assert "Manual intro" in replaced
    assert "Manual outro" in replaced


def test_replace_named_marker_block_replaces_benchmarks_marker_block():
    text = make_benchmarks()

    replaced = update_benchmarks.replace_named_marker_block(
        text,
        update_benchmarks.BENCHMARKS_MARK_START,
        update_benchmarks.BENCHMARKS_MARK_END,
        "history summary",
    )

    assert "history summary" in replaced
    assert "old auto summary" not in replaced
    assert "Manual validation evidence before" in replaced
    assert "Manual validation evidence after" in replaced


def test_replace_named_marker_block_raises_clear_error_when_readme_marker_missing():
    text = "# Demo README\nwithout marker\n"

    try:
        update_benchmarks.replace_named_marker_block(
            text,
            update_benchmarks.README_MARK_START,
            update_benchmarks.README_MARK_END,
            "new summary",
        )
    except RuntimeError as exc:
        assert "Marker block is missing" in str(exc)
        assert update_benchmarks.README_MARK_START in str(exc)
    else:
        raise AssertionError("RuntimeError was not raised")


def test_main_raises_clear_error_when_benchmarks_marker_missing(tmp_path, monkeypatch):
    (tmp_path / "README.md").write_text(make_readme(), encoding="utf-8")
    (tmp_path / "BENCHMARKS.md").write_text("# Benchmarks\nmanual only\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(update_benchmarks, "_has_glob_matches", lambda pattern: False)

    try:
        update_benchmarks.main()
    except RuntimeError as exc:
        assert "Marker block is missing" in str(exc)
        assert update_benchmarks.BENCHMARKS_MARK_START in str(exc)
    else:
        raise AssertionError("RuntimeError was not raised")


def test_main_when_reports_do_not_exist_preserves_readme_and_updates_benchmarks_fallback(tmp_path, monkeypatch, capsys):
    readme_path = tmp_path / "README.md"
    benchmarks_path = tmp_path / "BENCHMARKS.md"

    readme_path.write_text(make_readme(), encoding="utf-8")
    benchmarks_path.write_text(make_benchmarks(), encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(update_benchmarks, "_has_glob_matches", lambda pattern: False)

    update_benchmarks.main()

    captured = capsys.readouterr()
    readme_text = readme_path.read_text(encoding="utf-8")
    benchmarks_text = benchmarks_path.read_text(encoding="utf-8")

    assert "old summary" in readme_text
    assert update_benchmarks.NO_AUTO_SUMMARY_MESSAGE in benchmarks_text
    assert "Manual validation evidence before" in benchmarks_text
    assert "Manual validation evidence after" in benchmarks_text
    assert "README marker skipped because no reports matched" in captured.out


def test_main_when_reports_exist_updates_readme_and_benchmarks_markers_only(tmp_path, monkeypatch, capsys):
    readme_path = tmp_path / "README.md"
    benchmarks_path = tmp_path / "BENCHMARKS.md"

    readme_path.write_text(make_readme(), encoding="utf-8")
    benchmarks_path.write_text(make_benchmarks(), encoding="utf-8")

    md_both = "## Auto Summary\n\n| latest |"
    md_history = "## History\n\n| history |"
    calls = []

    def fake_run(cmd):
        calls.append(cmd)
        if "--mode" in cmd and "both" in cmd:
            return md_both
        if "--mode" in cmd and "history" in cmd:
            return md_history
        raise AssertionError(f"Unexpected command: {cmd}")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(update_benchmarks, "_has_glob_matches", lambda pattern: True)
    monkeypatch.setattr(update_benchmarks, "run", fake_run)

    update_benchmarks.main()

    captured = capsys.readouterr()
    readme_text = readme_path.read_text(encoding="utf-8")
    benchmarks_text = benchmarks_path.read_text(encoding="utf-8")

    assert len(calls) == 2
    assert md_both in readme_text
    assert "old summary" not in readme_text
    assert md_history in benchmarks_text
    assert "old auto summary" not in benchmarks_text
    assert "Manual intro" in readme_text
    assert "Manual outro" in readme_text
    assert "Manual validation evidence before" in benchmarks_text
    assert "Manual validation evidence after" in benchmarks_text
    assert "Updated README.md marker block + BENCHMARKS.md auto marker block" in captured.out


def test_main_end_to_end_smoke_uses_real_summarize_output_and_preserves_manual_sections(tmp_path, monkeypatch, capsys):
    summarize = import_summarize_module()
    readme_path = tmp_path / "README.md"
    benchmarks_path = tmp_path / "BENCHMARKS.md"
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()

    readme_path.write_text(make_readme(), encoding="utf-8")
    benchmarks_path.write_text(
        (
            "# Benchmarks\n\n"
            "Jetson TensorRT Validation Reference\n\n"
            f"{update_benchmarks.BENCHMARKS_MARK_START}\n"
            "old auto summary\n"
            f"{update_benchmarks.BENCHMARKS_MARK_END}\n\n"
            "RKNN Runtime Validation Reference\n"
        ),
        encoding="utf-8",
    )

    write_report(
        reports_dir / "older.json",
        model_name="toy224.onnx",
        mean_ms=0.500,
        p99_ms=0.600,
        timestamp="2026-04-16T09:00:00Z",
    )
    write_report(
        reports_dir / "newer.json",
        model_name="toy224.onnx",
        mean_ms=0.450,
        p99_ms=0.488,
        timestamp="2026-04-16T10:00:00Z",
    )

    def fake_run(cmd):
        output = io.StringIO()
        with redirect_stdout(output):
            summarize.summarize(
                pattern=str(tmp_path / "reports" / "*.json"),
                mode=cmd[cmd.index("--mode") + 1],
                sort=cmd[cmd.index("--sort") + 1],
                recent=int(cmd[cmd.index("--recent") + 1]) if "--recent" in cmd else 0,
            )
        return output.getvalue()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(update_benchmarks, "_has_glob_matches", lambda pattern: True)
    monkeypatch.setattr(update_benchmarks, "run", fake_run)

    update_benchmarks.main()

    captured = capsys.readouterr()
    readme_text = readme_path.read_text(encoding="utf-8")
    benchmarks_text = benchmarks_path.read_text(encoding="utf-8")

    assert "## Latest (recommended)" in readme_text
    assert "## History (raw)" in readme_text
    assert "| Model | Engine | Device | Batch | Input(HxW) | FLOPs | Mean (ms) | P99 (ms) | Timestamp (UTC) |" in readme_text
    assert "Manual intro" in readme_text
    assert "Manual outro" in readme_text
    assert "Jetson TensorRT Validation Reference" in benchmarks_text
    assert "RKNN Runtime Validation Reference" in benchmarks_text
    assert update_benchmarks.NO_AUTO_SUMMARY_MESSAGE not in benchmarks_text
    assert "## History (raw)" in benchmarks_text
    assert "| Model | Engine | Device | Batch | Input(HxW) | FLOPs | Mean (ms) | P99 (ms) | Timestamp (UTC) |" in benchmarks_text
    assert readme_text.count("| toy224.onnx | onnxruntime | cpu |") == 3
    assert "Updated README.md marker block + BENCHMARKS.md auto marker block" in captured.out
