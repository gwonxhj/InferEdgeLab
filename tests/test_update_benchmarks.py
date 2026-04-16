from __future__ import annotations

import importlib.util
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
