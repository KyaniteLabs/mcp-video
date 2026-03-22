# Wave 5: Verification & Red Team

## Overview

Final verification pass for the 38 MCP tools added across Waves 1-4. Two-phase approach: fill CLI test gaps, then adversarial red team testing.

## Current State

- 38 MCP tools, 100% server test coverage, ~50% CLI test coverage
- 472 tests passing, 3 skipped (vidstab-dependent)
- 17 CLI commands untested

## Phase A: CLI Test Gaps

Add CLI tests for 17 missing commands in `tests/test_cli.py`, following existing patterns (subprocess-based, create test video, assert exit code 0 + output exists).

**Batch 1:** merge, add-text, add-audio, subtitles, watermark
**Batch 2:** resize, speed, thumbnail, crop, rotate, fade
**Batch 3:** export, extract-audio, edit, reverse, chroma-key, audio-waveform, generate-subtitles

## Phase B: Red Team Adversarial Tests

New file `tests/test_red_team.py` covering:

1. **Path traversal** - `../../../etc/passwd` as input/output paths
2. **Unicode filenames** - emoji, CJK, spaces, special chars
3. **Invalid inputs** - negative durations, zero dimensions, empty strings, NaN
4. **File type mismatches** - image to video tools, text file as video
5. **Concurrent operations** - multiple FFmpeg processes on same file
6. **Large batch** - batch tool with many inputs, some invalid
7. **Resource exhaustion** - high quality settings, absurd resolution
8. **Missing dependencies** - codecs not present

## Out of Scope

- Full MCP protocol integration testing (MCP SDK handles this)
- Real media performance benchmarks
- Network/remote file testing
