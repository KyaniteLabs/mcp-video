# Adversarial Remediation Progress Report

Date: 2026-04-19

## Executive Status

The highest-leverage remediation lanes from the 2026-04-17 adversarial audit are substantially complete. The repo now has stronger trust rails, a current release, agent-discovery metadata, GitHub community conventions, grouped dependency updates, integration smoke coverage, focused AI extras, Ruff-formatted tests, and a fully decomposed FFmpeg engine facade.

The most important result: `mcp_video/engine.py` is no longer a 3,855-line behavioral monolith. It is now an 85-line compatibility facade that preserves legacy import paths while implementation lives in focused `engine_*.py` modules.

## Fresh Evidence

- Open PR list: empty at time of report.
- Latest GitHub release: `v1.2.1`.
- PyPI latest package version: `1.2.1`.
- `mcp_video/engine.py`: 85 lines.
- All `mcp_video/engine*.py` modules are under the 800-line project rule.
- Largest engine-related module: `mcp_video/engine_runtime_utils.py` at 577 lines.
- Repository readiness audit: passed.
- Public surface and adversarial tests: 49 passed.
- Standard engine/e2e/server suite: 137 passed.
- Engine advanced suite: 129 passed.
- Full non-slow suite before test formatting: 771 passed, 9 skipped, 114 deselected, 2 xpassed.
- Integration smoke on `master`: passed.

## Completed Lanes

### P0. Trust And Distribution Rails

Done:

- GitHub community files, issue templates, discussion templates, CODEOWNERS, Dependabot grouping, governance, maintainers, support, security, changelog, discovery docs, `server.json`, `llms.txt`, `robots.txt`, and `sitemap.xml` are in place.
- Repository readiness audit exists and passes.
- `v1.2.1` release is published and is latest on GitHub.
- PyPI reports `mcp-video` version `1.2.1`.
- Release artifacts were built and checked clean.

Remaining:

- Confirm and document final branch-protection settings if they differ from `docs/git-branch-governance.md`.

### P1. Kill Integration Hell

Done:

- `mcp-video doctor` exists and reports core and optional integrations.
- Integration smoke workflow exists and passes on `master`.
- AI optional extras were split into focused groups:
  - `transcribe`
  - `ai-scene`
  - `stems`
  - `upscale`
  - `all-ai`
- Existing `ai` extra remains as a compatibility aggregate.
- Doctor hints now point to smaller, feature-specific extras.

Remaining:

- Optional dependency error messages in `ai_engine.py` still mention direct package installs in several paths. These should be aligned with the new focused extras in a separate behavior-preserving PR.
- Consider whether `all-ai` should remain long-term or only as a transition alias.

### P1. Shrink The Slop Without Breaking The Product

Done:

- CLI routing was split into focused `mcp_video/cli/*` modules.
- Server facade was split into `server_tools_*` and `server_resources.py`.
- FFmpeg engine behavior was split into focused modules while preserving `mcp_video.engine` imports.
- `mcp_video/engine.py` is now an 85-line compatibility facade.

Remaining oversized files:

- `mcp_video/ai_engine.py`: 1,993 lines.
- `mcp_video/client.py`: 1,429 lines.
- `mcp_video/design_quality.py`: 1,236 lines.
- `mcp_video/__main__.py`: 1,263 lines.
- `mcp_video/effects_engine.py`: 1,041 lines.
- `mcp_video/audio_engine.py`: 901 lines.

Recommended next maintainability lane:

1. Split `ai_engine.py` by AI feature family only after adding characterization tests for missing optional dependency behavior.
2. Split `client.py` by API family only after checking public API stability.
3. Defer `design_quality.py`, `effects_engine.py`, and `audio_engine.py` until there is a concrete defect or feature pressure.

### P1. Error And FFmpeg Contracts

Done:

- Many engine paths now use focused helpers and compatibility facades.
- Filter execution preserves parsed FFmpeg error mapping after review feedback.
- `_quality_args` defaults now come from shared constants.

Remaining:

- `ai_engine.py`, `remotion_engine.py`, `effects_engine.py`, and `client.py` still need a focused error-contract audit for raw `RuntimeError`, `ValueError`, direct stderr exposure, and missing optional dependency guidance.

### P2. CI, Tests, And Release Quality

Done:

- Repository readiness audit is part of CI.
- Integration smoke workflow exists and passes.
- Test suite has been Ruff-formatted in one mechanical PR.

Remaining:

- Two red-team tests still XPASS locally, but Codex review confirmed the `xfail` markers document real cross-platform FFmpeg behavior. Do not remove them unless the engine behavior changes.
- Decide whether test formatting should be enforced in CI permanently if not already covered by the latest `ruff format --check` scope.

### P2/P3. Growth And Community Loops

Done:

- AI discovery docs and crawler metadata exist.
- GitHub community conventions are much stronger.

Remaining:

- Golden workflow examples are still missing:
  - `examples/agent_prompts/podcast_clip.md`
  - `examples/agent_prompts/tiktok_captioned_clip.md`
  - `examples/agent_prompts/product_demo_video.md`
  - `examples/python/shorts_workflow.py`
- MCP directory publishing remains to be tracked with public URLs.
- Good-first issues have not yet been created from the cleanup plan.

## Recommended Next Work

1. **Align AI optional-dependency errors with focused extras.**
   This is the best next engineering lane because the new extras are merged, but some runtime messages still point at raw package installs or old aggregate extras.

2. **Add golden workflow examples.**
   This is the best growth lane. It should be designed briefly first because examples are public-facing and should avoid overclaiming.

3. **Publish/update MCP directory listings.**
   Add URLs back to `README.md` and `docs/AI_AGENT_DISCOVERY.md` only after submissions are live.

4. **Create good-first issues.**
   Suggested issues:
   - Add one missing CLI smoke test.
   - Add a Cursor setup docs snippet.
   - Add a Claude Desktop troubleshooting snippet.
   - Add one agent prompt example.

## Stop Conditions Met

- Engine decomposition lane: complete.
- Release mismatch lane: complete.
- Integration smoke lane: complete.
- AI extras split lane: complete.
- Test formatting lane: complete.
- Current PR board: clean.

The repo has moved from fast agent-built sprawl toward a reviewable, discoverable, contributor-ready project. Remaining work is no longer emergency cleanup; it is targeted hardening and growth.
