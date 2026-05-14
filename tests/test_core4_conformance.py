from __future__ import annotations

import json

from inferedgelab.commands.core4_conformance import core4_conformance_check_cmd
from inferedgelab.services.core4_conformance import (
    SCHEMA_VERSION,
    build_core4_conformance_report,
    build_core4_conformance_text,
)


def test_core4_conformance_report_passes_for_committed_fixtures():
    report = build_core4_conformance_report()

    assert report["schema_version"] == SCHEMA_VERSION
    assert report["status"] == "pass"
    assert report["failed_count"] == 0
    assert report["layers"]["forge"]["status"] == "pass"
    assert report["layers"]["runtime"]["status"] == "pass"
    assert report["layers"]["lab"]["status"] == "pass"
    assert report["layers"]["aiguard"]["status"] == "pass"
    assert report["layers"]["handoff"]["status"] == "pass"
    assert any(check["name"] == "handoff:source_model_sha256" for check in report["checks"])
    assert any(check["name"] == "lab:compare_speedup" for check in report["checks"])
    assert any(check["name"] == "aiguard:verdict_coverage" for check in report["checks"])


def test_core4_conformance_text_lists_layer_statuses():
    text = build_core4_conformance_text()

    assert "InferEdge Core 4 Contract Conformance Check" in text
    assert "status: pass" in text
    assert "- forge: pass" in text
    assert "- runtime: pass" in text
    assert "- lab: pass" in text
    assert "- aiguard: pass" in text
    assert "All Core 4 contract conformance checks passed." in text


def test_core4_conformance_command_outputs_json(capsys):
    core4_conformance_check_cmd(format="json", repo_root=".")
    out = capsys.readouterr().out
    report = json.loads(out)

    assert report["schema_version"] == SCHEMA_VERSION
    assert report["status"] == "pass"
    assert report["layers"]["handoff"]["status"] == "pass"
