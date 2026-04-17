#!/usr/bin/env python3
"""Repository readiness audit for maintainability, accessibility, and growth."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_FILES = [
    "README.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "GOVERNANCE.md",
    "MAINTAINERS.md",
    "SECURITY.md",
    "SUPPORT.md",
    "llms.txt",
    "robots.txt",
    "sitemap.xml",
    "server.json",
    ".github/CODEOWNERS",
    ".github/dependabot.yml",
    ".github/pull_request_template.md",
    ".github/DISCUSSION_TEMPLATE/ideas.yml",
    ".github/DISCUSSION_TEMPLATE/q-a.yml",
    ".github/DISCUSSION_TEMPLATE/show-and-tell.yml",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/publish.yml",
    ".github/workflows/pages.yml",
    "docs/AI_AGENT_DISCOVERY.md",
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


def dependabot_groups_by_ecosystem() -> dict[tuple[str, str], set[str]]:
    """Return Dependabot group names keyed by package ecosystem and directory."""
    try:
        import yaml
    except ImportError:
        return {}

    data = yaml.safe_load(read(".github/dependabot.yml")) or {}
    grouped: dict[tuple[str, str], set[str]] = {}
    for update in data.get("updates", []):
        key = (str(update.get("package-ecosystem", "")), str(update.get("directory", "")))
        grouped[key] = set((update.get("groups") or {}).keys())
    return grouped


def main() -> int:
    failures: list[str] = []
    warnings: list[str] = []

    print("== File presence checks ==")
    for file_path in REQUIRED_FILES:
        check(
            (ROOT / file_path).exists(),
            f"{file_path} exists",
            f"Missing required file: {file_path}",
            failures=failures,
            warnings=warnings,
        )

    print("\n== Git hygiene checks ==")
    status = git_stdout("status", "--porcelain")
    check(
        status == "",
        "Working tree is clean",
        "Working tree has uncommitted changes",
        failures=failures,
        warnings=warnings,
        warn=True,
    )

    upstream_result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    check(
        upstream_result.returncode == 0,
        "Current branch has an upstream",
        "Current branch has no upstream configured",
        failures=failures,
        warnings=warnings,
        warn=True,
    )

    print("\n== README checks ==")
    readme = read("README.md")
    for section in ["## Installation", "## Quick Start", "## MCP Tools", "## Testing", "## License"]:
        check(
            section in readme,
            f"README contains '{section}'",
            f"README missing expected section '{section}'",
            failures=failures,
            warnings=warnings,
        )

    for doc_link in [
        "CONTRIBUTING.md",
        "SECURITY.md",
        "SUPPORT.md",
        "CODE_OF_CONDUCT.md",
        "CHANGELOG.md",
        "GOVERNANCE.md",
        "MAINTAINERS.md",
        "docs/AI_AGENT_DISCOVERY.md",
    ]:
        check(
            doc_link in readme,
            f"README links {doc_link}",
            f"README should link {doc_link}",
            failures=failures,
            warnings=warnings,
            warn=True,
        )

    print("\n== AI/search discovery checks ==")
    llms = read("llms.txt")
    for phrase in ["MCP server", "FFmpeg", "Claude Code", "Safety Rules For Agents"]:
        check(
            phrase in llms,
            f"llms.txt contains '{phrase}'",
            f"llms.txt missing expected phrase '{phrase}'",
            failures=failures,
            warnings=warnings,
        )

    check(
        "mcp-name: io.github.pastorsimon1798/mcp-video" in readme,
        "README contains MCP Registry verification marker",
        "README missing MCP Registry verification marker",
        failures=failures,
        warnings=warnings,
    )

    server_json = read("server.json")
    check(
        '"registryType": "pypi"' in server_json and '"identifier": "mcp-video"' in server_json,
        "server.json declares PyPI package metadata",
        "server.json should declare PyPI package metadata",
        failures=failures,
        warnings=warnings,
    )

    robots = read("robots.txt")
    for agent in ["OAI-SearchBot", "GPTBot", "Claude-SearchBot", "Sitemap:"]:
        check(
            agent in robots,
            f"robots.txt mentions {agent}",
            f"robots.txt should mention {agent}",
            failures=failures,
            warnings=warnings,
        )

    print("\n== Metadata checks ==")
    pyproject = read("pyproject.toml")
    for key in ["Homepage =", "Documentation =", "Repository =", "Changelog =", "Discussions ="]:
        check(
            key in pyproject,
            f"pyproject has project URL '{key[:-2]}'",
            f"pyproject missing URL key '{key[:-2]}'",
            failures=failures,
            warnings=warnings,
        )

    version_match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, flags=re.MULTILINE)
    check(
        version_match is not None,
        "Project version is set in pyproject",
        "Unable to find project version in pyproject",
        failures=failures,
        warnings=warnings,
    )
    init_version_match = re.search(r'^__version__\s*=\s*"([^"]+)"', read("mcp_video/__init__.py"), flags=re.MULTILINE)
    check(
        bool(version_match and init_version_match and version_match.group(1) == init_version_match.group(1)),
        "pyproject version matches mcp_video.__version__",
        "pyproject version should match mcp_video.__version__",
        failures=failures,
        warnings=warnings,
    )

    print("\n== Dependabot checks ==")
    dependabot_groups = dependabot_groups_by_ecosystem()
    for ecosystem, directory, group_name in [
        ("uv", "/", "python-runtime"),
        ("npm", "/explainer-video", "explainer-video"),
        ("github-actions", "/", "github-actions"),
    ]:
        check(
            group_name in dependabot_groups.get((ecosystem, directory), set()),
            f"Dependabot groups {ecosystem} updates in {directory} as {group_name}",
            f"Dependabot should group {ecosystem} updates in {directory} as {group_name}",
            failures=failures,
            warnings=warnings,
        )

    print("\n== Release/tag visibility checks ==")
    tags = git_stdout("tag", "--list")
    check(
        tags != "",
        "At least one git tag exists",
        "No git tags found locally; ensure releases are tagged",
        failures=failures,
        warnings=warnings,
        warn=True,
    )

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
