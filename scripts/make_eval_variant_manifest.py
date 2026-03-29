from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a variant evaluation manifest by perturbing labels."
    )
    parser.add_argument("--src", required=True, help="source JSONL manifest path")
    parser.add_argument("--out", required=True, help="output JSONL manifest path")
    parser.add_argument(
        "--label-key",
        default="label",
        help="label key name in manifest (default: label)",
    )
    parser.add_argument(
        "--num-classes",
        type=int,
        default=10,
        help="number of classes used to wrap perturbed labels",
    )
    parser.add_argument(
        "--flip-count",
        type=int,
        default=2,
        help="number of leading samples to perturb",
    )
    parser.add_argument(
        "--delta",
        type=int,
        default=1,
        help="label shift amount for perturbed samples",
    )
    args = parser.parse_args()

    src_path = Path(args.src)
    out_path = Path(args.out)

    if not src_path.is_file():
        raise FileNotFoundError(f"source manifest not found: {src_path}")

    lines = src_path.read_text(encoding="utf-8").splitlines()
    rows: list[str] = []

    valid_count = 0

    for idx, raw in enumerate(lines):
        line = raw.strip()
        if not line:
            continue

        item = json.loads(line)

        if args.label_key not in item:
            raise ValueError(f"missing label key '{args.label_key}' at line {idx + 1}")

        original = int(item[args.label_key])

        if valid_count < args.flip_count:
            item[args.label_key] = int((original + args.delta) % args.num_classes)

        rows.append(json.dumps(item, ensure_ascii=False))
        valid_count += 1

    if valid_count == 0:
        raise ValueError("source manifest has no valid samples")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(rows) + "\n", encoding="utf-8")

    print(f"Saved variant manifest: {out_path}")
    print(f"Samples              : {valid_count}")
    print(f"Perturbed labels     : {min(args.flip_count, valid_count)}")
    print(f"Num classes          : {args.num_classes}")
    print("Done.")


if __name__ == "__main__":
    main()