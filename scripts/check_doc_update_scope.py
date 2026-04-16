from __future__ import annotations

import subprocess


ALLOWED_CHANGED_FILES = {"README.md", "BENCHMARKS.md"}


def get_tracked_changed_files() -> list[str]:
    process = subprocess.run(
        ["git", "diff", "--name-only"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if process.returncode != 0:
        message = process.stderr.strip() or "git diff --name-only failed"
        raise RuntimeError(message)

    return [line.strip() for line in process.stdout.splitlines() if line.strip()]


def validate_changed_files(changed_files: list[str], allowed_files: set[str] | None = None) -> None:
    allowed = allowed_files or ALLOWED_CHANGED_FILES
    disallowed = [path for path in changed_files if path not in allowed]
    if disallowed:
        raise RuntimeError(
            "Benchmark doc auto-update modified unexpected tracked files: "
            + ", ".join(disallowed)
        )


def main() -> None:
    changed_files = get_tracked_changed_files()
    validate_changed_files(changed_files)
    print("Tracked file changes are limited to README.md and BENCHMARKS.md.")


if __name__ == "__main__":
    main()
