"""Verify pip compatibility files still match the canonical uv lockfile."""

import subprocess
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    valid = True
    for filename, options in (
        ("requirements.txt", ["--no-dev"]),
        ("requirements-dev.txt", []),
    ):
        result = subprocess.run(
            ["uv", "export", "--frozen", "--no-header", "--no-emit-project", *options],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
        destination = root / filename
        if not destination.exists() or destination.read_text(encoding="utf-8") != result.stdout:
            print(f"{filename} is outdated; run make exports and review the changes.")
            valid = False
    if valid:
        print("Generated dependency exports: PASS")
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
