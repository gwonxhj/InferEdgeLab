from __future__ import annotations

import json
import os

from edgebench.services.list_results_service import build_list_result_items, build_list_results_bundle


def write_result(
    tmp_path,
    name: str,
    *,
    timestamp: str,
    precision: str,
    model: str = "resnet18",
    engine: str = "onnxruntime",
    device: str = "cpu",
    batch: int = 1,
    height: int = 224,
    width: int = 224,
    mean_ms: float = 10.0,
    p99_ms: float = 12.0,
    include_system: bool = True,
    include_run_config: bool = True,
    mtime: int = 0,
) -> str:
    payload = {
        "model": model,
        "engine": engine,
        "device": device,
        "precision": precision,
        "batch": batch,
        "height": height,
        "width": width,
        "mean_ms": mean_ms,
        "p99_ms": p99_ms,
        "timestamp": timestamp,
    }
    if include_system:
        payload["system"] = {"os": "Linux"}
    if include_run_config:
        payload["run_config"] = {}

    path = tmp_path / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    if mtime:
        os.utime(path, (mtime, mtime))
    return str(path)


def test_build_list_result_items_returns_newest_first_by_mtime(tmp_path):
    write_result(tmp_path, "old.json", timestamp="2026-04-16T10:00:00Z", precision="fp32", mtime=100)
    write_result(tmp_path, "new.json", timestamp="2026-04-16T09:00:00Z", precision="fp16", mtime=200)

    items = build_list_result_items(pattern=str(tmp_path / "*.json"), limit=0)

    assert [item["precision"] for item in items] == ["fp16", "fp32"]


def test_build_list_result_items_applies_model_and_precision_filters(tmp_path):
    write_result(tmp_path, "one.json", timestamp="2026-04-16T09:00:00Z", precision="fp32", model="resnet18")
    write_result(tmp_path, "two.json", timestamp="2026-04-16T10:00:00Z", precision="int8", model="resnet18")
    write_result(tmp_path, "three.json", timestamp="2026-04-16T11:00:00Z", precision="fp32", model="mobilenet")

    items = build_list_result_items(
        pattern=str(tmp_path / "*.json"),
        limit=0,
        model="resnet18",
        precision="fp32",
    )

    assert len(items) == 1
    assert items[0]["model"] == "resnet18"
    assert items[0]["precision"] == "fp32"


def test_build_list_result_items_legacy_only_keeps_only_legacy_results(tmp_path):
    write_result(
        tmp_path,
        "legacy.json",
        timestamp="2026-04-16T09:00:00Z",
        precision="fp32",
        include_system=False,
        include_run_config=False,
    )
    write_result(
        tmp_path,
        "structured.json",
        timestamp="2026-04-16T10:00:00Z",
        precision="fp16",
        include_system=True,
        include_run_config=True,
    )

    items = build_list_result_items(pattern=str(tmp_path / "*.json"), limit=0, legacy_only=True)

    assert len(items) == 1
    assert items[0]["legacy_result"] is True
    assert items[0]["precision"] == "fp32"


def test_build_list_result_items_applies_limit(tmp_path):
    write_result(tmp_path, "one.json", timestamp="2026-04-16T09:00:00Z", precision="fp32", mtime=100)
    write_result(tmp_path, "two.json", timestamp="2026-04-16T10:00:00Z", precision="fp16", mtime=200)
    write_result(tmp_path, "three.json", timestamp="2026-04-16T11:00:00Z", precision="int8", mtime=300)

    items = build_list_result_items(pattern=str(tmp_path / "*.json"), limit=2)

    assert [item["precision"] for item in items] == ["int8", "fp16"]


def test_build_list_result_items_returns_empty_list_when_no_match(tmp_path):
    write_result(tmp_path, "one.json", timestamp="2026-04-16T09:00:00Z", precision="fp32", model="resnet18")

    items = build_list_result_items(pattern=str(tmp_path / "*.json"), limit=0, model="mobilenet")

    assert items == []


def test_build_list_results_bundle_returns_meta_and_data_contract(tmp_path):
    write_result(tmp_path, "one.json", timestamp="2026-04-16T09:00:00Z", precision="fp32", mtime=100)
    write_result(tmp_path, "two.json", timestamp="2026-04-16T10:00:00Z", precision="fp16", mtime=200)

    bundle = build_list_results_bundle(
        pattern=str(tmp_path / "*.json"),
        limit=1,
        model="resnet18",
        precision="fp16",
    )
    items = build_list_result_items(
        pattern=str(tmp_path / "*.json"),
        limit=1,
        model="resnet18",
        precision="fp16",
    )

    assert set(bundle.keys()) == {"meta", "data"}
    assert bundle["meta"]["pattern"] == str(tmp_path / "*.json")
    assert bundle["meta"]["limit"] == 1
    assert bundle["meta"]["filters"] == {
        "model": "resnet18",
        "engine": "",
        "device": "",
        "precision": "fp16",
        "batch": None,
        "height": None,
        "width": None,
        "legacy_only": False,
    }
    assert bundle["data"]["items"] == items
    assert bundle["meta"]["count"] == len(bundle["data"]["items"]) == 1


def test_build_list_results_bundle_empty_items_keeps_empty_contract(tmp_path):
    bundle = build_list_results_bundle(
        pattern=str(tmp_path / "*.json"),
        limit=5,
        model="missing",
        legacy_only=True,
    )

    assert bundle["data"]["items"] == []
    assert bundle["meta"]["count"] == 0
    assert bundle["meta"]["filters"]["model"] == "missing"
    assert bundle["meta"]["filters"]["legacy_only"] is True
