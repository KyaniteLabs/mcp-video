# Changelog

All notable user-facing changes should be recorded here.

This project follows a simple release-note style:

- `Added` for new capabilities.
- `Changed` for behavior changes.
- `Fixed` for bug fixes.
- `Security` for vulnerability fixes.

## Unreleased

### Added

- Added GitHub Discussions templates, CODEOWNERS, maintainer/governance docs, and Dependabot configuration.
- Added `llms.txt`, `robots.txt`, `sitemap.xml`, and `server.json` for search, AI-agent discovery, and MCP Registry readiness.
- Added `docs/AI_AGENT_DISCOVERY.md` and an adversarial remediation plan.

### Changed

- Updated public tool count messaging from 82 to the current 83 MCP tools.
- Updated the landing page with crawl metadata and structured software/source metadata.

## 1.2.1 - 2026-04-13

### Changed

- Prepared the 1.2.1 package metadata and public badge.
- Improved runtime error contracts and diagnostics.
- Repaired repository trust rails for deploys, packages, tests, and AI extras.

### Fixed

- Aligned `mcp_video.__version__` with the package version in `pyproject.toml`.
- Moved optional dependency metadata out of Ruff configuration.
- Centralized chroma-key color validation for safer FFmpeg filter construction.

## 1.2.0 - 2026-03-31

### Added

- Published the 1.2.0 package release.
- Documented the broad MCP, CLI, Python client, FFmpeg, Remotion, image, audio, AI, and quality-guardrail surface.
