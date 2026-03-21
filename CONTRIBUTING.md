# Contributing to AgentCut

Thanks for your interest in improving AgentCut. This is a focused project — every tool should work reliably, and every change should maintain that standard.

## Quick Start

```bash
# Clone and install dev dependencies
git clone https://github.com/pastorsimon1798/agentcut.git
cd agentcut
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run a specific test file
pytest tests/test_engine.py -v
```

## Project Structure

```
agentcut/
├── engine.py       # All FFmpeg operations (the core)
├── server.py       # MCP tool definitions
├── client.py       # Python Client wrapper
├── models.py       # Pydantic models
├── errors.py       # Error types + FFmpeg error parsing
├── templates.py    # Video templates (TikTok, YouTube, etc.)
├── __main__.py     # CLI entry point
tests/
├── conftest.py     # Shared fixtures (sample video, audio, etc.)
├── test_models.py      # Model validation (no FFmpeg)
├── test_errors.py      # Error parsing (no FFmpeg)
├── test_templates.py   # Template functions (no FFmpeg)
├── test_client.py      # Client API wrapper
├── test_server.py      # MCP tool layer
├── test_engine.py      # Core FFmpeg operations
├── test_engine_advanced.py  # Edge cases, crop, rotate, fade
├── test_cli.py         # CLI commands
└── test_e2e.py         # Multi-step workflows
```

## Making Changes

### Adding a new tool

1. **Engine first** — Add the FFmpeg function in `engine.py`. Follow the existing pattern:
   - `_validate_input(input_path)` at the top
   - `_run_ffmpeg([...])` for the FFmpeg call
   - `probe(output)` after processing
   - Return an `EditResult` with `duration`, `resolution`, `size_mb`
2. **Model if needed** — Add any new Pydantic models to `models.py`
3. **Error if needed** — Add error types to `errors.py` if the failure mode is distinct
4. **Server** — Add the `@mcp.tool()` wrapper in `server.py`
5. **Tests** — Add tests in the appropriate file:
   - `test_engine_advanced.py` for new operations
   - `test_server.py` for the MCP tool wrapper
   - `test_e2e.py` if it's a workflow-type operation
6. **Update counts** — README test counts and tool count

### Fixing a bug

1. Write a failing test that reproduces the bug
2. Fix the code
3. Verify the test passes and nothing else breaks
4. If it changes behavior, update README if needed

## Code Conventions

- **Error types matter** — Use `input_error` for validation failures, `processing_error` for FFmpeg failures, `dependency_error` for missing tools. Don't default to `unknown_error`.
- **Probe after processing** — Every operation that produces a video file should call `probe(output)` and return duration/resolution in the `EditResult`.
- **Escape FFmpeg special chars** — Colons, backslashes, and single quotes must be escaped in filter strings (see `add_text` for the pattern).
- **Sanitize output paths** — `_auto_output` replaces colons with underscores to prevent FFmpeg filter breakage.
- **No shell=True** — All subprocess calls use list args, never shell strings.
- **Keep it simple** — One function per operation. No classes for engines. No abstractions for one-time use.

## Testing Rules

- Unit tests (models, errors, templates) must not need FFmpeg installed
- Integration tests need FFmpeg and produce real video files
- Every new tool needs at least: success case, error case (bad input), and one edge case
- E2E tests chain multiple operations together
- Run the full suite before pushing: `pytest tests/ -v --tb=short`
- Target: 262+ tests, 0 failures

## Commit Messages

Keep them short and descriptive:
```
Add crop operation for rectangular region extraction
Fix colon escaping in drawtext filter strings
Bump version to 0.1.1
```

## Pull Request Process

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes with tests
4. Run `pytest tests/ -v` — all must pass
5. Open a PR with a clear description of what changed and why

## Reporting Issues

When reporting a bug, include:
- The exact tool call or command you ran
- The input file (codec, resolution, duration)
- The full error output
- Your OS and FFmpeg version (`ffmpeg -version`)

## Questions?

Open a GitHub issue with the `question` label.
