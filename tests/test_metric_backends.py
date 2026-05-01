from __future__ import annotations

import importlib

import pytest

from inferedgelab.evaluation.metrics import MetricBackendError
from inferedgelab.evaluation.metrics import get_metric_backend
from inferedgelab.evaluation.metrics import supported_metric_backends
from inferedgelab.evaluation.pycocotools_backend import require_pycocotools


def test_simplified_metric_backend_records_backend_and_note():
    backend = get_metric_backend("simplified")

    result = backend.evaluate(
        predictions_by_image=[],
        ground_truths_by_image=[],
        num_classes=1,
        iou_threshold=0.5,
        average_precision_fn=lambda *args, **kwargs: 0.68,
        precision_recall_fn=lambda *args, **kwargs: (0.7, 0.6, 0.646),
        mean_fn=lambda values: sum(values) / len(values),
    )

    assert result.metrics["backend"] == "simplified"
    assert result.metrics["map50"] == pytest.approx(0.68)
    assert result.metrics["precision"] == pytest.approx(0.7)
    assert result.metrics["recall"] == pytest.approx(0.6)
    assert result.metrics["note"] == "lightweight simplified mAP50 implementation"


def test_unsupported_metric_backend_fails_clearly():
    with pytest.raises(MetricBackendError, match="unsupported metric backend"):
        get_metric_backend("made_up_backend")


def test_pycocotools_backend_requested_without_dependency_fails_clearly(monkeypatch):
    def fake_import_module(name: str):
        if name.startswith("pycocotools"):
            raise ImportError("missing pycocotools")
        return importlib.import_module(name)

    monkeypatch.setattr(importlib, "import_module", fake_import_module)

    with pytest.raises(RuntimeError, match="pycocotools backend requested but pycocotools is not installed"):
        require_pycocotools()


def test_supported_metric_backends_include_simplified_and_pycocotools():
    assert supported_metric_backends() == ("simplified", "pycocotools")
