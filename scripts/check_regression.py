from __future__ import annotations

import glob
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

import typer
from rich import print as rprint


@dataclass
class Measured:
    key: str
    mean_ms: Optional[float]
    p99_ms: Optional[float]
    src: str


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def model_name_from_report(d: Dict[str, Any]) -> str:
    mp = (d.get("model") or {}).get("path") or ""
    return mp.split("/")[-1] if mp else "unknown"


def key_from_report(d: Dict[str, Any]) -> str:
    model = model_name_from_report(d)
    runtime = d.get("runtime") or {}
    engine = str(runtime.get("engine") or "unknown")
    device = str(runtime.get("device") or "unknown")
    extra = runtime.get("extra") or {}

    b = extra.get("batch")
    h = extra.get("height")
    w = extra.get("width")

    return f"{model}::{engine}::{device}::b{b}::h{h}w{w}"


def to_measured(d: Dict[str, Any], src: str) -> Measured:
    runtime = d.get("runtime") or {}
    latency = runtime.get("latency_ms") or {}

    mean_ms = latency.get("mean")
    p99_ms = latency.get("p99")

    return Measured(
        key=key_from_report(d),
        mean_ms=float(mean_ms) if mean_ms is not None else None,
        p99_ms=float(p99_ms) if p99_ms is not None else None,
        src=src,
    )


def main(
    baseline: str = typer.Option(..., "--baseline", help="baseline json path"),
    reports: str = typer.Option(..., "--reports", help='glob pattern e.g. "reports/*.json"'),
    metric: str = typer.Option("p99", "--metric", help="p99 or mean"),
    max_regress_pct: float = typer.Option(15.0, "--max-regress-pct", help="allowed regression percent"),
    allow_missing_keys: bool = typer.Option(False, "--allow-missing-keys", help="do not fail if some baseline keys are missing in current reports"),
) -> int:
    metric = metric.lower()
    if metric not in ("p99", "mean"):
        raise typer.BadParameter("--metric must be one of: p99, mean")

    base_raw = load_json(baseline)
    base_items = base_raw.get("items") or []
    baseline_map: Dict[str, float] = {}

    for it in base_items:
        k = str(it.get("key") or "")
        if not k:
            continue
        v = it.get("p99_ms") if metric == "p99" else it.get("mean_ms")
        if v is None:
            continue
        baseline_map[k] = float(v)

    paths = sorted(glob.glob(reports))
    if not paths:
        rprint(f"[red]No report files matched:[/red] {reports}")
        return 2

    current: Dict[str, Measured] = {}
    for p in paths:
        d = load_json(p)
        m = to_measured(d, src=p)
        current[m.key] = m

    bad = 0

    for k, base_v in baseline_map.items():
        cur = current.get(k)
        if cur is None:
            msg = f"[yellow]Missing current key[/yellow]: {k}"
            if allow_missing_keys:
                rprint(msg)
                continue
            rprint(msg)
            bad += 1
            continue

        cur_v = cur.p99_ms if metric == "p99" else cur.mean_ms
        if cur_v is None:
            rprint(f"[yellow]Missing metric in report[/yellow]: {k} ({cur.src})")
            bad += 1
            continue

        if base_v <= 0:
            continue

        regress_pct = ((cur_v - base_v) / base_v) * 100.0

        if regress_pct > max_regress_pct:
            bad += 1
            rprint(
                f"[red]REGRESSION[/red] {k}  "
                f"base={base_v:.3f}ms  cur={cur_v:.3f}ms  "
                f"(+{regress_pct:.1f}%)  src={cur.src}"
            )
        else:
            rprint(
                f"[green]OK[/green] {k}  "
                f"base={base_v:.3f}ms  cur={cur_v:.3f}ms  "
                f"(+{regress_pct:.1f}%)"
            )

    if bad > 0:
        rprint(f"[red]Regression guard failed[/red]: {bad} issue(s)")
        return 2

    rprint(f"[green]Regression guard passed[/green] (metric={metric}, max_regress_pct={max_regress_pct:.1f}%)")
    return 0


if __name__ == "__main__":
    typer.run(main)