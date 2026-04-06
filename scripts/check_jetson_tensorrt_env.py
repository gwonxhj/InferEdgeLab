from __future__ import annotations

import argparse
import importlib.util
import platform
import sys
from pathlib import Path


def _module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _print_check(label: str, ok: bool, detail: str) -> None:
    status = "OK" if ok else "MISSING"
    print(f"[{status}] {label}: {detail}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Preflight check for Jetson TensorRT bring-up."
    )
    parser.add_argument(
        "--model-path",
        default="",
        help="Optional ONNX model path used for analysis/reporting validation.",
    )
    parser.add_argument(
        "--engine-path",
        default="",
        help="Optional compiled TensorRT engine artifact path used for runtime validation.",
    )
    args = parser.parse_args()

    checks: list[bool] = []

    python_info = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    platform_info = f"{platform.system()} {platform.release()} ({platform.machine()})"
    print("== Jetson TensorRT Environment Check ==")
    print(f"Python   : {python_info}")
    print(f"Platform : {platform_info}")

    nv_tegra_release = Path("/etc/nv_tegra_release")
    has_nv_tegra_release = nv_tegra_release.exists()
    _print_check(
        "/etc/nv_tegra_release",
        has_nv_tegra_release,
        "Jetson release marker found" if has_nv_tegra_release else "Jetson release marker not found",
    )
    checks.append(has_nv_tegra_release)

    for module_name in ("tensorrt", "onnxruntime", "numpy"):
        available = _module_available(module_name)
        _print_check(
            f"import {module_name}",
            available,
            "module import is available" if available else "module import is not available",
        )
        checks.append(available)

    if args.model_path:
        model_path = Path(args.model_path)
        model_exists = model_path.exists()
        _print_check(
            "model_path",
            model_exists,
            str(model_path) if model_exists else f"not found: {model_path}",
        )
        checks.append(model_exists)
    else:
        print("[SKIP] model_path: not provided")

    if args.engine_path:
        engine_path = Path(args.engine_path)
        engine_exists = engine_path.exists()
        _print_check(
            "engine_path",
            engine_exists,
            str(engine_path) if engine_exists else f"not found: {engine_path}",
        )
        checks.append(engine_exists)
    else:
        print("[SKIP] engine_path: not provided")

    ok_count = sum(1 for item in checks if item)
    total_count = len(checks)
    passed = all(checks)

    print("\n== Summary ==")
    if passed:
        print(
            f"PASS: basic Jetson TensorRT bring-up prerequisites are present ({ok_count}/{total_count})."
        )
        print("This script only checks environment/preflight status. It does not execute TensorRT runtime inference.")
        return 0

    print(
        f"FAIL: some Jetson TensorRT bring-up prerequisites are missing ({ok_count}/{total_count})."
    )
    print("Review the failed checks above before starting TensorRT runtime implementation.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
