from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def import_script_module(script_name: str):
    module_path = Path(__file__).resolve().parents[1] / "scripts" / script_name
    spec = importlib.util.spec_from_file_location(f"test_{script_name.replace('.', '_')}", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check_doc_markers = import_script_module("check_doc_markers.py")
check_doc_update_scope = import_script_module("check_doc_update_scope.py")


def test_validate_marker_contract_raises_when_marker_is_missing():
    text = "# README\nmissing markers\n"

    with pytest.raises(RuntimeError) as exc_info:
        check_doc_markers.validate_marker_contract(
            text,
            check_doc_markers.README_MARK_START,
            check_doc_markers.README_MARK_END,
            "README.md",
        )

    assert "missing required marker block" in str(exc_info.value)
    assert "README.md" in str(exc_info.value)


def test_validate_changed_files_passes_for_readme_and_benchmarks_only():
    check_doc_update_scope.validate_changed_files(["README.md", "BENCHMARKS.md"])


def test_validate_changed_files_fails_for_unexpected_tracked_file():
    with pytest.raises(RuntimeError) as exc_info:
        check_doc_update_scope.validate_changed_files(["README.md", "Roadmap.md"])

    assert "unexpected tracked files" in str(exc_info.value)
    assert "Roadmap.md" in str(exc_info.value)
