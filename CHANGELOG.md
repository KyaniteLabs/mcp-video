# Changelog

All notable user-facing changes should be recorded here.

This project follows a simple release-note style:

- `Added` for new capabilities.
- `Changed` for behavior changes.
- `Fixed` for bug fixes.
- `Security` for vulnerability fixes.

## 1.2.6 - 2026-04-27

### Changed

- Bumped version to 1.2.6 (1.2.5 tag already existed).

## 1.2.5 - 2026-04-27

### Added

- **Hyperframes integration** — 8 new MCP tools, Python client methods, and CLI commands for HTML-native video creation:
  - `hyperframes_init` — scaffold new projects (blank, warm-grain, swiss-grid templates)
  - `hyperframes_render` — render compositions to MP4/WebM/MOV
  - `hyperframes_still` — render single frames via snapshot
  - `hyperframes_compositions` — list compositions in a project
  - `hyperframes_preview` — launch live preview studio
  - `hyperframes_validate` — validate project structure and run lint
  - `hyperframes_add_block` — install blocks from the Hyperframes catalog
  - `hyperframes_to_mcpvideo` — render then post-process with mcp-video in one step
- Full test suite for Hyperframes engine: 54 unit + integration tests in `tests/test_hyperframes_engine.py`.
- `sample_hyperframes_project` pytest fixture.

### Changed

- **Remotion is deprecated.** All Remotion MCP tools, client methods, and CLI commands now emit `DeprecationWarning`. Remotion will be removed in a future major version. Migrate to Hyperframes (Apache 2.0) or Revideo (MIT).
- Public tool count updated from 82 to 90 unique MCP tools.
- `mcp_video/client/remotion.py` — all methods now warn on usage.

### Fixed

- `hyperframes_engine.validate()` no longer raises `HyperframesProjectError` when no HTML entry point is found; it correctly reports the issue in the validation result.

## 1.2.4 - 2026-04-22

### Added
- `Client.subtitles_styled()` alias for `text_subtitles()` to match MCP tool rename.
- Runnable `workflow.py` for `02-podcast-clip` (6 stages).
- Runnable `workflow.py` for `03-explainer-video` (7 stages, client-only, no raw FFmpeg).

### Changed
- Documentation updated for `search_tools`, `workflows/`, and ICM alignment.
- `workflows/01-social-media-clip/workflow.py` fixed client arg names.

## 1.2.3 - 2026-04-22

### Changed

- Consolidated duplicate tools: removed `video_blur`, `video_color_grade`, and `video_extract_frame` as standalone tools. Functionality preserved through `video_filter` and `video_thumbnail`.
- Renamed `video_text_subtitles` to `video_subtitles_styled` for clearer naming.
- Added `search_tools` meta-tool for fast tool discovery by keyword.
- Updated public tool count from 83 to 81 unique tools.
- Reorganized docs/TOOLS.md into 12 functional categories.

### Fixed

- Image analysis tools (`image_extract_colors`, `image_generate_palette`, `image_analyze_product`) now accept video input by auto-extracting a representative frame.

### Added

- Added ICM-style `workflows/` directory with 3 production-ready pipelines: social-media-clip, podcast-clip, and explainer-video.
- Added `CLAUDE.md` and `workflows/CONTEXT.md` for agent context routing.

## 1.2.2 - 2026-04-21

### Added

- Added GitHub Discussions templates, CODEOWNERS, maintainer/governance docs, and Dependabot configuration.
- Added `llms.txt`, `robots.txt`, `sitemap.xml`, and `server.json` for search, AI-agent discovery, and MCP Registry readiness.
- Added `docs/AI_AGENT_DISCOVERY.md` and an adversarial remediation plan.
- Added `_validate_output_path()` and rolled it out across all engines for safer output directory handling.
- Added client-side validation and return type annotations for improved API contract consistency.
- Added current edge-case audit document (`docs/CURRENT_EDGE_CASE_AUDIT_2026-04-21.md`).

### Changed

- Updated public tool count messaging from 82 to the current 83 MCP tools.
- Updated the landing page with crawl metadata and structured software/source metadata.
- Normalized root metadata links to the canonical repository URL.
- Replaced the grey social preview image with generated media artwork.

### Security

- Fixed TOCTOU race conditions and sanitized numeric values in FFmpeg filters.
- Hardened AI engine resource guards for scene detection, spatial audio, stem separation, transcription, and upscaling.
- Hardened direct download paths with timeout and size limits.
- Closed top-priority audit validation gaps across engine boundaries.
- Fixed design quality security and SRT format safety issues.

### Fixed

- Added startup validation to `remotion_engine.studio()` to catch immediate process crashes.

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
