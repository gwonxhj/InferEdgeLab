from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
import time

import numpy as np

from edgebench.engines.base import InferenceEngine
from edgebench.engines.registry import create_engine, normalize_engine_name


@dataclass
class ProfileResult:
    engine: str
    device: str
    warmup: int
    runs: int
    latency_ms: Dict[str, float]
    extra: Dict[str, Any]


def _latency_stats_ms(samples_ms: np.ndarray) -> Dict[str, float]:
    mean = float(samples_ms.mean())
    std = float(samples_ms.std(ddof=0))
    p50 = float(np.percentile(samples_ms, 50))
    p90 = float(np.percentile(samples_ms, 90))
    p99 = float(np.percentile(samples_ms, 99))
    mn = float(samples_ms.min())
    mx = float(samples_ms.max())
    return {
        "mean": mean,
        "std": std,
        "p50": p50,
        "p90": p90,
        "p99": p99,
        "min": mn,
        "max": mx,
    }


def profile_engine(
    engine: InferenceEngine,
    model_path: str,
    warmup: int = 10,
    runs: int = 100,
    batch: Optional[int] = None,
    height: Optional[int] = None,
    width: Optional[int] = None,
    load_kwargs: Optional[Dict[str, Any]] = None,
) -> ProfileResult:
    if warmup < 0 or runs <= 0:
        raise ValueError("warmup은 0 이상, runs는 1 이상이어야 합니다.")

    load_kwargs = load_kwargs or {}

    try:
        engine.load(model_path, **load_kwargs)

        feeds = engine.make_dummy_inputs(
            batch_override=batch,
            height_override=height,
            width_override=width,
        )

        input_names = list(feeds.keys())

        for _ in range(warmup):
            engine.run(feeds)

        samples = np.empty((runs,), dtype=np.float64)
        for i in range(runs):
            t0 = time.perf_counter()
            engine.run(feeds)
            t1 = time.perf_counter()
            samples[i] = (t1 - t0) * 1000.0

        stats = _latency_stats_ms(samples)

        extra = {
            "batch": batch if batch is not None else 1,
            "input_names": input_names,
            "height": height,
            "width": width,
            "load_kwargs": load_kwargs,
        }

        return ProfileResult(
            engine=engine.name,
            device=engine.device,
            warmup=warmup,
            runs=runs,
            latency_ms=stats,
            extra=extra,
        )
    finally:
        engine.close()


def profile_model(
    model_path: str,
    engine: str = "onnxruntime",
    engine_path: Optional[str] = None,
    warmup: int = 10,
    runs: int = 100,
    batch: Optional[int] = None,
    height: Optional[int] = None,
    width: Optional[int] = None,
    intra_threads: int = 1,
    inter_threads: int = 1,
) -> ProfileResult:
    normalized_engine = normalize_engine_name(engine)
    engine_instance = create_engine(normalized_engine)

    load_kwargs: Dict[str, Any] = {
        "intra_threads": intra_threads,
        "inter_threads": inter_threads,
    }
    if engine_path is not None:
        load_kwargs["engine_path"] = engine_path

    return profile_engine(
        engine=engine_instance,
        model_path=model_path,
        warmup=warmup,
        runs=runs,
        batch=batch,
        height=height,
        width=width,
        load_kwargs=load_kwargs,
    )


def profile_onnxruntime_cpu(
    model_path: str,
    warmup: int = 10,
    runs: int = 100,
    batch: Optional[int] = None,
    height: Optional[int] = None,
    width: Optional[int] = None,
    intra_threads: int = 1,
    inter_threads: int = 1,
) -> ProfileResult:
    engine = create_engine("onnxruntime")

    result = profile_engine(
        engine=engine,
        model_path=model_path,
        warmup=warmup,
        runs=runs,
        batch=batch,
        height=height,
        width=width,
        load_kwargs={
            "intra_threads": intra_threads,
            "inter_threads": inter_threads,
        },
    )

    result.extra["intra_threads"] = intra_threads
    result.extra["inter_threads"] = inter_threads
    return result