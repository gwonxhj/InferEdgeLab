from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import import_rknn_results


def write_curated_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def make_valid_item(**overrides):
    item = {
        "model": "yolov8n",
        "engine": "rknn",
        "device": "odroid_m2",
        "precision": "int8",
        "batch": 1,
        "height": 640,
        "width": 640,
        "mean_ms": 16.289,
        "p99_ms": None,
        "timestamp": "2026-04-13T00:10:00Z",
        "accuracy": {
            "task": "detection",
            "metrics": {
                "map50": 0.7977,
                "f1_score": 0.8129,
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


def test_load_curated_results_reads_valid_items(tmp_path):
    path = tmp_path / "rknn_curated_results.json"
    data = [make_valid_item(), make_valid_item(model="yolov8s", precision="fp16")]
    write_curated_json(path, data)

    items = import_rknn_results.load_curated_results(path)

    assert len(items) == 2
    assert items[0]["engine"] == "rknn"
    assert items[1]["model"] == "yolov8s"


def test_load_curated_results_rejects_non_list_json(tmp_path):
    path = tmp_path / "rknn_curated_results.json"
    write_curated_json(path, {"not": "a-list"})

    with pytest.raises(SystemExit, match="Expected a JSON array"):
        import_rknn_results.load_curated_results(path)


def test_load_curated_results_rejects_non_object_entry(tmp_path):
    path = tmp_path / "rknn_curated_results.json"
    write_curated_json(path, [make_valid_item(), "bad-entry"])

    with pytest.raises(SystemExit, match="Each curated result must be an object"):
        import_rknn_results.load_curated_results(path)


def test_load_curated_results_rejects_missing_required_keys(tmp_path):
    path = tmp_path / "rknn_curated_results.json"
    broken = make_valid_item()
    broken.pop("model")
    write_curated_json(path, [broken])

    with pytest.raises(SystemExit, match="Missing required keys"):
        import_rknn_results.load_curated_results(path)


def test_load_curated_results_rejects_non_rknn_engine(tmp_path):
    path = tmp_path / "rknn_curated_results.json"
    write_curated_json(path, [make_valid_item(engine="onnxruntime")])

    with pytest.raises(SystemExit, match="must use engine='rknn'"):
        import_rknn_results.load_curated_results(path)


def test_to_optional_float_handles_none_and_numeric_values():
    assert import_rknn_results._to_optional_float(None) is None
    assert import_rknn_results._to_optional_float(1) == 1.0
    assert import_rknn_results._to_optional_float("2.5") == 2.5


def test_to_benchmark_result_converts_types():
    item = make_valid_item(
        batch="1",
        height="640",
        width="640",
        mean_ms="16.289",
        p99_ms="20.5",
    )

    result = import_rknn_results.to_benchmark_result(item)

    assert result.model == "yolov8n"
    assert result.engine == "rknn"
    assert result.device == "odroid_m2"
    assert result.precision == "int8"
    assert result.batch == 1
    assert result.height == 640
    assert result.width == 640
    assert result.mean_ms == 16.289
    assert result.p99_ms == 20.5
    assert result.timestamp == "2026-04-13T00:10:00Z"
    assert result.accuracy["task"] == "detection"


def test_main_saves_results_and_prints_paths(tmp_path, monkeypatch, capsys):
    curated_path = tmp_path / "rknn_curated_results.json"
    write_curated_json(
        curated_path,
        [
            make_valid_item(),
            make_valid_item(model="yolov8s", timestamp="2026-04-13T00:15:00Z"),
        ],
    )

    saved_paths = []

    def fake_save_result(result):
        out = f"results/{result.model}__{result.engine}__{result.device}.json"
        saved_paths.append((result, out))
        return out

    monkeypatch.setattr(import_rknn_results, "CURATED_RESULTS_PATH", curated_path)
    monkeypatch.setattr(import_rknn_results, "save_result", fake_save_result)

    import_rknn_results.main()

    captured = capsys.readouterr()
    assert len(saved_paths) == 2
    assert "saved: results/yolov8n__rknn__odroid_m2.json" in captured.out
    assert "saved: results/yolov8s__rknn__odroid_m2.json" in captured.out