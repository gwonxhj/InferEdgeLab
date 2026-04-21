from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from inferedgelab.engines.onnxruntime_cpu import OnnxRuntimeCpuEngine


def _resolve_input_shape(shape: list[object], height: int, width: int) -> list[int]:
    resolved: list[int] = []

    for i, dim in enumerate(shape):
        if dim is None:
            if i == 0:
                resolved.append(1)
            elif i == 2:
                resolved.append(height)
            elif i == 3:
                resolved.append(width)
            else:
                resolved.append(1)
        else:
            resolved.append(int(dim))

    return resolved


def _extract_top1(output) -> int:
    scores = np.asarray(output)

    if scores.ndim == 0:
        raise ValueError("model output is scalar; classification top-1 cannot be computed")

    if scores.ndim == 1:
        flat = scores
    else:
        flat = scores[0].reshape(-1)

    return int(np.argmax(flat))


def main() -> None:
    parser = argparse.ArgumentParser(description="Create demo .npy inputs and JSONL manifest for evaluate")
    parser.add_argument("--model", required=True, help="ONNX model path")
    parser.add_argument("--out-dir", default="tmp_eval", help="output directory")
    parser.add_argument("--count", type=int, default=5, help="number of demo samples")
    parser.add_argument("--height", type=int, default=224, help="fallback height for dynamic input")
    parser.add_argument("--width", type=int, default=224, help="fallback width for dynamic input")
    parser.add_argument("--seed", type=int, default=42, help="random seed")
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = out_dir / "manifest.jsonl"

    engine = OnnxRuntimeCpuEngine()
    engine.load(args.model)

    if len(engine.inputs) != 1:
        raise ValueError(f"demo generator supports single-input models only. current: {len(engine.inputs)}")

    model_input = engine.inputs[0]
    input_shape = _resolve_input_shape(model_input.shape, height=args.height, width=args.width)

    rows: list[str] = []

    for idx in range(args.count):
        arr = rng.random(input_shape, dtype=np.float32).astype(model_input.dtype, copy=False)

        outputs = engine.run({model_input.name: arr})

        if len(outputs) != 1:
            raise ValueError(f"demo generator supports single-output models only. current: {len(outputs)}")

        label = _extract_top1(outputs[0])

        sample_path = out_dir / f"sample_{idx:03d}.npy"
        np.save(sample_path, arr)

        row = {
            "input": str(sample_path),
            "label": label,
        }
        rows.append(json.dumps(row, ensure_ascii=False))

    manifest_path.write_text("\n".join(rows) + "\n", encoding="utf-8")

    print(f"Saved manifest: {manifest_path}")
    print(f"Saved samples : {args.count}")
    print(f"Input shape    : {input_shape}")
    print("Done.")


if __name__ == "__main__":
    main()