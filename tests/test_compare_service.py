from __future__ import annotations

import json

import pytest

from edgebench.services.compare_service import build_compare_bundle, select_latest_compare_pair


def write_result(
    tmp_path,
    name: str,
    *,
    timestamp: str,
    precision: str,
    mean_ms: float = 10.0,
    p99_ms: float = 12.0,
    model: str = "resnet18",
    engine: str = "onnxruntime",
    device: str = "cpu",
    batch: int = 1,
    height: int = 224,
    width: int = 224,
    run_config: dict | None = None,
    system: dict | None = None,
    accuracy: dict | None = None,
    extra: dict | None = None,
) -> str:
    path = tmp_path / name
    path.write_text(
        json.dumps(
            {
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
                "run_config": run_config or {},
                "system": system or {"os": "Linux", "python": "3.11.0", "machine": "x86_64", "cpu_count_logical": 8},
                "accuracy": accuracy
                or {
                    "task": "classification",
                    "sample_count": 100,
                    "metrics": {"top1_accuracy": 0.9},
                },
                "extra": extra or {},
            }
        ),
        encoding="utf-8",
    )
    return str(path)


def test_build_compare_bundle_returns_compare_artifacts_for_same_precision_pair(tmp_path):
    base_path = write_result(
        tmp_path,
        "base.json",
        timestamp="2026-04-13T09:00:00Z",
        precision="fp32",
        mean_ms=10.0,
        p99_ms=12.0,
    )
    new_path = write_result(
        tmp_path,
        "new.json",
        timestamp="2026-04-13T10:00:00Z",
        precision="fp32",
        mean_ms=9.0,
        p99_ms=11.0,
        accuracy={
            "task": "classification",
            "sample_count": 100,
            "metrics": {"top1_accuracy": 0.92},
        },
    )

    bundle = build_compare_bundle(base_path=base_path, new_path=new_path)

    assert bundle["base_path"] == base_path
    assert bundle["new_path"] == new_path
    assert bundle["result"]["precision"]["comparison_mode"] == "same_precision"
    assert bundle["judgement"]["comparison_mode"] == "same_precision"
    assert isinstance(bundle["markdown"], str) and bundle["markdown"]
    assert isinstance(bundle["html"], str) and bundle["html"]
    assert bundle["legacy_warning"] is False


def test_select_latest_compare_pair_selects_latest_same_precision_pair(tmp_path):
    older = write_result(tmp_path, "older.json", timestamp="2026-04-13T09:00:00Z", precision="fp32")
    write_result(tmp_path, "other.json", timestamp="2026-04-13T09:30:00Z", precision="fp16")
    newer = write_result(
        tmp_path,
        "newer.json",
        timestamp="2026-04-13T10:00:00Z",
        precision="fp32",
        run_config={"runs": 50},
    )

    pair = select_latest_compare_pair(
        pattern=str(tmp_path / "*.json"),
        selection_mode="same_precision",
    )

    assert pair["selection_mode"] == "same_precision"
    assert pair["base_path"] == older
    assert pair["new_path"] == newer
    assert pair["run_config_mismatch_fields"] == ["runs"]


def test_select_latest_compare_pair_cross_precision_with_precision_filter_raises(tmp_path):
    write_result(tmp_path, "base.json", timestamp="2026-04-13T09:00:00Z", precision="fp32")
    write_result(tmp_path, "new.json", timestamp="2026-04-13T10:00:00Z", precision="fp16")

    with pytest.raises(ValueError, match="cross_precision"):
        select_latest_compare_pair(
            pattern=str(tmp_path / "*.json"),
            selection_mode="cross_precision",
            precision="fp16",
        )
