#!/usr/bin/env python3
"""Fail if built release artifacts contain forbidden repo surface paths."""

from __future__ import annotations

import argparse
import tarfile
import zipfile
from pathlib import Path

FORBIDDEN_SUBSTRINGS = (
    "/.playwright-mcp/",
    "/.stitch/",
    "/out/",
    "/manual/",
    "/explainer-video/",
)

FORBIDDEN_SUFFIXES = (
    "/test_comprehensive.py",
    "/test_real_video.py",
)


def find_offenders(artifact: Path) -> list[str]:
    names: list[str]
    if artifact.suffix == ".whl":
        with zipfile.ZipFile(artifact) as zf:
            names = zf.namelist()
    elif artifact.suffixes[-2:] == [".tar", ".gz"]:
        with tarfile.open(artifact, "r:gz") as tf:
            names = [m.name for m in tf.getmembers() if m.isfile()]
    else:
        raise ValueError(f"Unsupported artifact type: {artifact}")

    return [
        name
        for name in names
        if any(fragment in name for fragment in FORBIDDEN_SUBSTRINGS)
        or any(name.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES)
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact_dir", nargs="?", default="dist")
    args = parser.parse_args()

    artifact_dir = Path(args.artifact_dir)
    artifacts = sorted(artifact_dir.glob("*.whl")) + sorted(artifact_dir.glob("*.tar.gz"))
    if not artifacts:
        raise SystemExit(f"No wheel or sdist artifacts found in {artifact_dir}")

    failed = False
    for artifact in artifacts:
        offenders = find_offenders(artifact)
        if offenders:
            failed = True
            print(f"{artifact.name}: forbidden contents detected")
            for offender in offenders:
                print(f"- {offender}")
        else:
            print(f"{artifact.name}: clean")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
