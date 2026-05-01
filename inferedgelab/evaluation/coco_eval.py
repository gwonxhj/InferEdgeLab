from __future__ import annotations

from typing import Any


def build_metric_payload(
    *,
    backend: str,
    metrics: dict[str, Any],
    note: str | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    payload = {"backend": backend, **metrics}
    if note:
        payload["note"] = note
    if warnings:
        payload["warnings"] = list(warnings)
    return payload
