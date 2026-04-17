#!/usr/bin/env python3
"""Repository readiness audit for maintainability, accessibility, and growth."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_FILES = [
    "README.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    "SUPPORT.md",
    ".github/pull_request_template.md",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/publish.yml",
    ".github/workflows/pages.yml",
    "docs/git-branch-governance.md",
    "docs/repository-audit-checklist.md",
]


def check(condition: bool, ok: str, bad: str, *, failures: list[str], warnings: list[str], warn: bool = False) -> None:
    if condition:
        print(f"PASS {ok}")
        return
    if warn:
        warnings.append(bad)
        print(f"WARN {bad}")
    else:
        failures.append(bad)
        print(f"FAIL {bad}")


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def git_stdout(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def main() -> int:
    failures: list[str] = []
    warnings: list[str] = []

    print("== File presence checks ==")
    for file_path in REQUIRED_FILES:
        check((ROOT / file_path).exists(), f"{file_path} exists", f"Missing required file: {file_path}", failures=failures, warnings=warnings)

    print("\n== Git hygiene checks ==")
    status = git_stdout("status", "--porcelain")
    check(status == "", "Working tree is clean", "Working tree has uncommitted changes", failures=failures, warnings=warnings, warn=True)

    upstream_result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    check(upstream_result.returncode == 0, "Current branch has an upstream", "Current branch has no upstream configured", failures=failures, warnings=warnings, warn=True)

    print("\n== README checks ==")
    readme = read("README.md")
    for section in ["## Installation", "## Quick Start", "## MCP Tools", "## Testing", "## License"]:
        check(section in readme, f"README contains '{section}'", f"README missing expected section '{section}'", failures=failures, warnings=warnings)

    for doc_link in ["CONTRIBUTING.md", "SECURITY.md", "SUPPORT.md", "CODE_OF_CONDUCT.md"]:
        check(doc_link in readme, f"README links {doc_link}", f"README should link {doc_link}", failures=failures, warnings=warnings, warn=True)

    print("\n== Metadata checks ==")
    pyproject = read("pyproject.toml")
    for key in ["Homepage =", "Documentation =", "Repository ="]:
        check(key in pyproject, f"pyproject has project URL '{key[:-2]}'", f"pyproject missing URL key '{key[:-2]}'", failures=failures, warnings=warnings)

    version_match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, flags=re.MULTILINE)
    check(version_match is not None, "Project version is set in pyproject", "Unable to find project version in pyproject", failures=failures, warnings=warnings)

    print("\n== Release/tag visibility checks ==")
    tags = git_stdout("tag", "--list")
    check(tags != "", "At least one git tag exists", "No git tags found locally; ensure releases are tagged", failures=failures, warnings=warnings, warn=True)

    print("\n== Result ==")
    if failures:
        print(f"FAILURES: {len(failures)}")
        print("- " + "\n- ".join(failures))
    if warnings:
        print(f"WARNINGS: {len(warnings)}")
        print("- " + "\n- ".join(warnings))

    if failures:
        return 1
    print("Repository readiness baseline passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
