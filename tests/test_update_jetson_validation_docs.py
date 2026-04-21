from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def import_update_jetson_validation_docs_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "update_jetson_validation_docs.py"
    spec = importlib.util.spec_from_file_location("test_update_jetson_validation_docs_module", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


update_jetson_validation_docs = import_update_jetson_validation_docs_module()


def make_readme(text: str = "old evidence") -> str:
    return (
        "# README\n\n"
        "manual intro\n\n"
        f"{update_jetson_validation_docs.README_MARK_START}\n"
        f"{text}\n"
        f"{update_jetson_validation_docs.README_MARK_END}\n\n"
        "manual outro\n"
    )


def make_runbook(text: str = "old runbook evidence") -> str:
    return (
        "# Runbook\n\n"
        "manual runbook intro\n\n"
        f"{update_jetson_validation_docs.RUNBOOK_MARK_START}\n"
        f"{text}\n"
        f"{update_jetson_validation_docs.RUNBOOK_MARK_END}\n\n"
        "manual runbook outro\n"
    )


def test_update_jetson_validation_docs_replaces_both_marker_blocks(tmp_path):
    readme_path = tmp_path / "README.md"
    runbook_path = tmp_path / "jetson_tensorrt_validation.md"
    resnet18_evidence_path = tmp_path / "resnet18_tensorrt_evidence.md"
    yolov8n_evidence_path = tmp_path / "yolov8n_tensorrt_evidence.md"

    readme_path.write_text(make_readme(), encoding="utf-8")
    runbook_path.write_text(make_runbook(), encoding="utf-8")
    resnet18_evidence_path.write_text("## ResNet18 Evidence", encoding="utf-8")
    yolov8n_evidence_path.write_text("## YOLOv8n Evidence", encoding="utf-8")

    update_jetson_validation_docs.update_jetson_validation_docs(
        readme_path=readme_path,
        runbook_path=runbook_path,
        resnet18_evidence_path=resnet18_evidence_path,
        yolov8n_evidence_path=yolov8n_evidence_path,
    )

    readme_text = readme_path.read_text(encoding="utf-8")
    runbook_text = runbook_path.read_text(encoding="utf-8")

    assert "## ResNet18 Evidence" in readme_text
    assert "## YOLOv8n Evidence" in readme_text
    assert "## ResNet18 Evidence" in runbook_text
    assert "## YOLOv8n Evidence" in runbook_text
    assert "manual intro" in readme_text
    assert "manual outro" in readme_text
    assert "manual runbook intro" in runbook_text
    assert "manual runbook outro" in runbook_text


def test_update_jetson_validation_docs_raises_when_marker_block_is_missing(tmp_path):
    readme_path = tmp_path / "README.md"
    runbook_path = tmp_path / "jetson_tensorrt_validation.md"
    resnet18_evidence_path = tmp_path / "resnet18_tensorrt_evidence.md"
    yolov8n_evidence_path = tmp_path / "yolov8n_tensorrt_evidence.md"

    readme_path.write_text("# README\nno marker\n", encoding="utf-8")
    runbook_path.write_text(make_runbook(), encoding="utf-8")
    resnet18_evidence_path.write_text("## ResNet18 Evidence", encoding="utf-8")
    yolov8n_evidence_path.write_text("## YOLOv8n Evidence", encoding="utf-8")

    with pytest.raises(RuntimeError) as exc_info:
        update_jetson_validation_docs.update_jetson_validation_docs(
            readme_path=readme_path,
            runbook_path=runbook_path,
            resnet18_evidence_path=resnet18_evidence_path,
            yolov8n_evidence_path=yolov8n_evidence_path,
        )

    assert "Could not find marker block" in str(exc_info.value)


def test_update_jetson_validation_docs_raises_when_evidence_source_file_is_missing(tmp_path):
    readme_path = tmp_path / "README.md"
    runbook_path = tmp_path / "jetson_tensorrt_validation.md"
    resnet18_evidence_path = tmp_path / "resnet18_tensorrt_evidence.md"
    missing_yolov8n_evidence_path = tmp_path / "missing_yolov8n_tensorrt_evidence.md"

    readme_path.write_text(make_readme(), encoding="utf-8")
    runbook_path.write_text(make_runbook(), encoding="utf-8")
    resnet18_evidence_path.write_text("## ResNet18 Evidence", encoding="utf-8")

    with pytest.raises(FileNotFoundError) as exc_info:
        update_jetson_validation_docs.update_jetson_validation_docs(
            readme_path=readme_path,
            runbook_path=runbook_path,
            resnet18_evidence_path=resnet18_evidence_path,
            yolov8n_evidence_path=missing_yolov8n_evidence_path,
        )

    assert "Evidence source file not found" in str(exc_info.value)
