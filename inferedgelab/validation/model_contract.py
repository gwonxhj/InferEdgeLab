from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from inferedgelab.validation.presets import get_preset


class ModelContractError(ValueError):
    pass


@dataclass(frozen=True)
class ModelContractIO:
    shape: list[int]
    format: str
    name: str | None = None
    dtype: str | None = None
    type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ModelContract:
    contract_version: str
    task: str
    preset: str
    labels: list[str]
    input: ModelContractIO
    output: ModelContractIO
    thresholds: dict[str, float]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "task": self.task,
            "preset": self.preset,
            "labels": list(self.labels),
            "input": self.input.to_dict(),
            "output": self.output.to_dict(),
            "thresholds": dict(self.thresholds),
            "metadata": dict(self.metadata),
        }


def build_default_contract(preset_name: str = "yolov8_coco") -> ModelContract:
    preset = get_preset(preset_name)
    return ModelContract(
        contract_version="1",
        task=preset.task,
        preset=preset.name,
        labels=list(preset.labels),
        input=ModelContractIO(shape=list(preset.input_shape), format=preset.input_format),
        output=ModelContractIO(
            shape=list(preset.output_shape),
            format="tensor",
            type=preset.output_type,
        ),
        thresholds=dict(preset.thresholds),
        metadata={"source": "preset", "description": preset.description},
    )


def parse_model_contract(payload: dict[str, Any], *, default_preset: str = "yolov8_coco") -> ModelContract:
    if not isinstance(payload, dict):
        raise ModelContractError("model_contract payload must be a JSON object.")

    preset_name = str(payload.get("preset") or default_preset).strip().lower()
    preset = get_preset(preset_name)
    default_contract = build_default_contract(preset.name)

    input_payload = payload.get("input") or {}
    output_payload = payload.get("output") or {}
    if not isinstance(input_payload, dict):
        raise ModelContractError("model_contract.input must be an object.")
    if not isinstance(output_payload, dict):
        raise ModelContractError("model_contract.output must be an object.")

    labels = payload.get("labels", default_contract.labels)
    if labels is None:
        labels = []
    if not isinstance(labels, list) or not all(isinstance(label, str) for label in labels):
        raise ModelContractError("model_contract.labels must be a list of strings.")

    thresholds = payload.get("thresholds", default_contract.thresholds)
    if not isinstance(thresholds, dict):
        raise ModelContractError("model_contract.thresholds must be an object.")

    input_shape = input_payload.get("shape", default_contract.input.shape)
    output_shape = output_payload.get("shape", default_contract.output.shape)
    _validate_shape(input_shape, "input.shape")
    _validate_shape(output_shape, "output.shape")

    task = str(payload.get("task") or preset.task)
    if preset.name != "custom_contract" and task != preset.task:
        raise ModelContractError(f"model_contract.task '{task}' does not match preset '{preset.name}'.")

    return ModelContract(
        contract_version=str(payload.get("contract_version") or default_contract.contract_version),
        task=task,
        preset=preset.name,
        labels=list(labels),
        input=ModelContractIO(
            shape=[int(value) for value in input_shape],
            format=str(input_payload.get("format") or default_contract.input.format),
            name=_optional_string(input_payload.get("name")),
            dtype=_optional_string(input_payload.get("dtype")),
        ),
        output=ModelContractIO(
            shape=[int(value) for value in output_shape],
            format=str(output_payload.get("format") or default_contract.output.format),
            name=_optional_string(output_payload.get("name")),
            dtype=_optional_string(output_payload.get("dtype")),
            type=str(output_payload.get("type") or default_contract.output.type),
        ),
        thresholds={str(key): float(value) for key, value in thresholds.items()},
        metadata=dict(payload.get("metadata") or {}),
    )


def load_model_contract(path: str, *, default_preset: str = "yolov8_coco") -> ModelContract:
    contract_path = Path(path)
    try:
        payload = json.loads(contract_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ModelContractError(f"model_contract is not valid JSON: {path}") from exc
    return parse_model_contract(payload, default_preset=default_preset)


def _validate_shape(shape: Any, field_name: str) -> None:
    if not isinstance(shape, list) or not shape:
        raise ModelContractError(f"model_contract.{field_name} must be a non-empty list.")
    if not all(isinstance(value, int) and value > 0 for value in shape):
        raise ModelContractError(f"model_contract.{field_name} must contain positive integers.")


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
