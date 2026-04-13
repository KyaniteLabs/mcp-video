#!/usr/bin/env python3
"""Fail if outward-facing workflows would include forbidden tracked artifacts."""

from __future__ import annotations

import subprocess
import sys

FORBIDDEN_PREFIXES = (
    ".playwright-mcp/",
    ".stitch/",
    "out/",
)

FORBIDDEN_EXACT = {
    "test_comprehensive.py",
    "test_real_video.py",
}


def main() -> int:
    proc = subprocess.run(
        ["git", "ls-files"],
        check=True,
        capture_output=True,
        text=True,
    )
    tracked = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    offenders = [
        path
        for path in tracked
        if path in FORBIDDEN_EXACT or path.startswith(FORBIDDEN_PREFIXES)
    ]

    if not offenders:
        print("No forbidden tracked artifacts found.")
        return 0

    print("Forbidden tracked artifacts detected:")
    for path in offenders:
        print(f"- {path}")
    print(f"Total: {len(offenders)}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
