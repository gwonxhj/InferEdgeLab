from __future__ import annotations

import json
from pathlib import Path

from scripts import update_benchmarks


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def make_curated_item(**overrides):
    item = {
        "model": "YOLOv8n",
        "engine": "rknn",
        "device": "odroid_m2",
        "precision": "int8",
        "batch": 1,
        "height": 640,
        "width": 640,
        "mean_ms": 15.403,
        "p99_ms": 17.086,
        "timestamp": "2026-04-13T00:10:00Z",
        "accuracy": {
            "task": "detection",
            "metrics": {
                "map50": 0.612,
                "f1_score": 0.581,
                "precision": 0.635,
                "recall": 0.537,
            },
        },
        "extra": {
            "quantization_mode": "hybrid_int8",
            "quantization_preset": "default",
            "source": "odroid_report",
        },
    }
    item.update(overrides)
    return item


def test_replace_marked_block_replaces_existing_marker_block():
    readme = (
        "# Demo\n\n"
        f"{update_benchmarks.MARK_START}\n"
        "old block\n"
        f"{update_benchmarks.MARK_END}\n"
    )

    replaced = update_benchmarks.replace_marked_block(readme, "new block")

    assert "new block" in replaced
    assert "old block" not in replaced


def test_replace_marked_block_raises_when_marker_missing():
    readme = "# Demo without markers\n"

    try:
        update_benchmarks.replace_marked_block(readme, "new block")
    except SystemExit as exc:
        assert "marker not found" in str(exc)
    else:
        raise AssertionError("SystemExit was not raised")


def test_load_curated_results_returns_empty_when_file_missing(tmp_path):
    path = tmp_path / "missing.json"

    items = update_benchmarks._load_curated_results(path)

    assert items == []


def test_load_curated_results_reads_only_dict_items(tmp_path):
    path = tmp_path / "curated.json"
    write_json(path, [make_curated_item(), "bad", make_curated_item(model="YOLOv8s")])

    items = update_benchmarks._load_curated_results(path)

    assert len(items) == 2
    assert items[0]["model"] == "YOLOv8n"
    assert items[1]["model"] == "YOLOv8s"


def test_build_curated_hardware_validation_markdown_contains_expected_table(tmp_path):
    path = tmp_path / "curated.json"
    write_json(
        path,
        [
            make_curated_item(),
            make_curated_item(model="YOLOv8s", mean_ms=24.917, p99_ms=27.844),
        ],
    )

    text = update_benchmarks._build_curated_hardware_validation_markdown(path)

    assert "## Curated Hardware Validation" in text
    assert "### Odroid RKNN Benchmarks" in text
    assert "| Model | Engine | Device | Precision |" in text
    assert "YOLOv8n" in text
    assert "YOLOv8s" in text
    assert "hybrid_int8" in text
    assert "odroid_report" in text


def test_has_glob_matches_returns_true_when_files_exist(tmp_path):
    file_path = tmp_path / "a.json"
    file_path.write_text("{}", encoding="utf-8")

    assert update_benchmarks._has_glob_matches(str(tmp_path / "*.json")) is True
    assert update_benchmarks._has_glob_matches(str(tmp_path / "*.md")) is False


def test_main_updates_benchmarks_only_when_reports_missing(tmp_path, monkeypatch, capsys):
    readme_path = tmp_path / "README.md"
    benchmarks_path = tmp_path / "BENCHMARKS.md"
    curated_path = tmp_path / "curated.json"

    readme_path.write_text(
        "# Demo README\n\n"
        f"{update_benchmarks.MARK_START}\nold\n{update_benchmarks.MARK_END}\n",
        encoding="utf-8",
    )
    write_json(curated_path, [make_curated_item()])

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(update_benchmarks, "CURATED_RESULTS_PATH", curated_path)
    monkeypatch.setattr(update_benchmarks, "_has_glob_matches", lambda pattern: False)

    update_benchmarks.main()

    captured = capsys.readouterr()
    benchmarks_text = benchmarks_path.read_text(encoding="utf-8")
    readme_text = readme_path.read_text(encoding="utf-8")

    assert "No auto-generated report summaries are available yet." in benchmarks_text
    assert "Curated Hardware Validation" in benchmarks_text
    assert "YOLOv8n" in benchmarks_text
    assert "README marker skipped because no reports matched" in captured.out
    assert "old" in readme_text


def test_main_updates_readme_and_benchmarks_when_reports_exist(tmp_path, monkeypatch, capsys):
    readme_path = tmp_path / "README.md"
    benchmarks_path = tmp_path / "BENCHMARKS.md"
    curated_path = tmp_path / "curated.json"

    readme_path.write_text(
        "# Demo README\n\n"
        f"{update_benchmarks.MARK_START}\nold block\n{update_benchmarks.MARK_END}\n",
        encoding="utf-8",
    )
    write_json(curated_path, [make_curated_item()])

    md_both = "## Auto Summary\n\n| demo |"
    md_history = "# Benchmarks\n\n## History\n\n| row |"

    calls = []

    def fake_run(cmd):
        calls.append(cmd)
        if "--mode" in cmd and "both" in cmd:
            return md_both
        if "--mode" in cmd and "history" in cmd:
            return md_history
        raise AssertionError(f"Unexpected command: {cmd}")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(update_benchmarks, "CURATED_RESULTS_PATH", curated_path)
    monkeypatch.setattr(update_benchmarks, "_has_glob_matches", lambda pattern: True)
    monkeypatch.setattr(update_benchmarks, "run", fake_run)

    update_benchmarks.main()

    captured = capsys.readouterr()
    benchmarks_text = benchmarks_path.read_text(encoding="utf-8")
    readme_text = readme_path.read_text(encoding="utf-8")

    assert len(calls) == 2
    assert "## History" in benchmarks_text
    assert "Curated Hardware Validation" in benchmarks_text
    assert "YOLOv8n" in benchmarks_text
    assert "## Auto Summary" in readme_text
    assert "old block" not in readme_text
    assert "Updated README.md (marker block) + BENCHMARKS.md" in captured.out