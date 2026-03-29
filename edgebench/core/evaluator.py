from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import json
import os

import numpy as np

from edgebench.engines.base import EngineModelIO
from edgebench.engines.onnxruntime_cpu import OnnxRuntimeCpuEngine

@dataclass
class ClassificationSample:
    input_path: str
    label: int


@dataclass
class ClassificationEvalResult:
    task: str
    engine: str
    device: str
    sample_count: int
    correct_count: int
    metrics: Dict[str, float]
    notes: List[str]
    model_input: Dict[str, Any]
    actual_input_shape: List[int]
    extra: Dict[str, Any]


def load_classification_manifest(
    manifest_path: str,
    input_key: str = "input",
    label_key: str = "label",
) -> List[ClassificationSample]:
    if not os.path.isfile(manifest_path):
        raise FileNotFoundError(f"evaluation manifest 파일을 찾을 수 없습니다: {manifest_path}")

    samples: List[ClassificationSample] = []

    with open(manifest_path, "r", encoding="utf-8") as f:
        for line_idx, raw_line in enumerate(f, start=1):
            line = raw_line.strip()
            if not line:
                continue

            try:
                item = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"manifest {line_idx}번째 줄이 올바른 JSON이 아닙니다: {e}") from e

            if input_key not in item:
                raise ValueError(f"manifest {line_idx}번째 줄에 '{input_key}' 키가 없습니다.")
            if label_key not in item:
                raise ValueError(f"manifest {line_idx}번째 줄에 '{label_key}' 키가 없습니다.")

            input_path = str(item[input_key])
            label = int(item[label_key])

            samples.append(ClassificationSample(input_path=input_path, label=label))

    if not samples:
        raise ValueError("evaluation manifest에 유효한 샘플이 없습니다.")

    return samples


def _normalize_input_array(arr: np.ndarray, model_input: EngineModelIO) -> np.ndarray:
    expected_rank = len(model_input.shape)

    # 모델 입력 rank보다 1 작으면 batch 차원이 빠졌다고 보고 앞에 1을 추가
    if expected_rank > 0 and arr.ndim == expected_rank - 1:
        arr = np.expand_dims(arr, axis=0)

    if expected_rank > 0 and arr.ndim != expected_rank:
        raise ValueError(
            f"입력 rank 불일치: expected rank={expected_rank}, got rank={arr.ndim}, input={model_input.name}"
        )

    for i, dim in enumerate(model_input.shape):
        if dim is None:
            continue
        if int(arr.shape[i]) != int(dim):
            raise ValueError(
                f"입력 shape 불일치: axis={i}, expected={dim}, got={arr.shape[i]}, input={model_input.name}"
            )

    if arr.dtype != model_input.dtype:
        arr = arr.astype(model_input.dtype, copy=False)

    return arr


def _extract_top1_prediction(output: Any) -> int:
    scores = np.asarray(output)

    if scores.ndim == 0:
        raise ValueError("classification output이 scalar입니다. top-1 prediction을 계산할 수 없습니다.")

    if scores.ndim == 1:
        flat_scores = scores
    else:
        # batch=1 기준으로 첫 샘플만 사용
        flat_scores = scores[0].reshape(-1)

    return int(np.argmax(flat_scores))


def evaluate_classification_top1(
    model_path: str,
    manifest_path: str,
    input_key: str = "input",
    label_key: str = "label",
    intra_threads: int = 1,
    inter_threads: int = 1,
) -> ClassificationEvalResult:
    samples = load_classification_manifest(
        manifest_path=manifest_path,
        input_key=input_key,
        label_key=label_key,
    )

    engine = OnnxRuntimeCpuEngine()
    engine.load(
        model_path,
        intra_threads=intra_threads,
        inter_threads=inter_threads,
    )

    if len(engine.inputs) != 1:
        raise ValueError(
            f"현재 evaluate 1차 버전은 single-input 모델만 지원합니다. 현재 입력 수: {len(engine.inputs)}"
        )

    model_input = engine.inputs[0]

    correct_count = 0
    actual_input_shape: Optional[List[int]] = None

    for sample in samples:
        if not os.path.isfile(sample.input_path):
            raise FileNotFoundError(f"평가 입력 파일을 찾을 수 없습니다: {sample.input_path}")

        arr = np.load(sample.input_path)
        arr = _normalize_input_array(arr, model_input)

        if actual_input_shape is None:
            actual_input_shape = [int(v) for v in arr.shape]

        feeds = {
            model_input.name: arr,
        }

        outputs = engine.run(feeds)

        if len(outputs) != 1:
            raise ValueError(
                f"현재 evaluate 1차 버전은 single-output classification만 지원합니다. 현재 출력 수: {len(outputs)}"
            )

        pred = _extract_top1_prediction(outputs[0])

        if pred == sample.label:
            correct_count += 1

    sample_count = len(samples)
    top1 = correct_count / sample_count

    return ClassificationEvalResult(
        task="classification",
        engine=engine.name,
        device=engine.device,
        sample_count=sample_count,
        correct_count=correct_count,
        metrics={
            "top1_accuracy": float(top1),
        },
        notes=[
            "Current evaluator supports classification only.",
            "Current evaluator expects JSONL manifest and .npy inputs.",
            "Current evaluator supports single-input, single-output models only.",
            "Top-1 accuracy is computed with batch=1 style inference.",
        ],
        model_input={
            "name": model_input.name,
            "dtype": str(model_input.dtype),
            "shape": model_input.shape,
        },
        actual_input_shape=actual_input_shape or [],
        extra={
            "input_key": input_key,
            "label_key": label_key,
            "input_format": "npy",
            "intra_threads": intra_threads,
            "inter_threads": inter_threads,
        },
    )