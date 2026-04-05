# mcp-video — Project Rules

## Before Writing Any Code

1. **Check if it already exists.** Search `ffmpeg_helpers.py`, `validation.py`, `limits.py`, and `defaults.py` before writing any utility function. Import, don't duplicate.
2. **Check the public API.** Functions registered as MCP tools in `server.py` are the public surface. Internal functions are prefixed with `_`. Don't break tool signatures.

## FFmpeg Security

3. **ALL user-controlled values in FFmpeg filter strings MUST be escaped** with `_escape_ffmpeg_filter_value()` from `ffmpeg_helpers.py`. This includes: colors, fonts, text, paths, and any string that goes into a `-vf` or `-filter_complex` argument.
4. **Gold standard pattern** (from `effects_engine.py:text_animated`):
   ```python
   safe_text = _escape_ffmpeg_filter_value(text)
   safe_font = _escape_ffmpeg_filter_value(font) if font is not None else font
   safe_color = _escape_ffmpeg_filter_value(color) if color is not None else color
   ```
5. **Never use f-string interpolation of user values directly into filter strings** without escaping.

## Error Handling

6. **Always raise custom types from `errors.py`**, never raw `ValueError`, `RuntimeError`, or `FileNotFoundError`.
   - Input file issues → `InputFileError`
   - FFmpeg processing failures → `ProcessingError` (auto-truncates stderr to 500 chars)
   - Bad parameters → `MCPVideoError` with `error_type="validation_error"`
7. **Never embed `result.stderr` directly in error messages.** Route through `ProcessingError` which truncates to 500 chars.
8. **Never use bare `except Exception:` without logging.** Always `except Exception as e: logger.warning(...)`.

## Subprocess Calls

9. **ALL `subprocess.run()` and `subprocess.Popen()` calls MUST have a `timeout` parameter.** Use `DEFAULT_FFMPEG_TIMEOUT` from `defaults.py`.
10. **Catch `subprocess.TimeoutExpired`** and raise `ProcessingError` with a clear timeout message.
11. **Validate input paths** with `_validate_input_path()` from `ffmpeg_helpers.py` before passing to subprocess.

## Configuration

12. **All default values MUST be defined in `defaults.py`.** Reference by name, never hardcode magic numbers like `crf=23`, `timeout=600`, `fps=30`.
13. **Validation constants** go in `validation.py`. Resource limits go in `limits.py`. Runtime defaults go in `defaults.py`.

## Size Limits

14. **No module may exceed 800 LOC.** If it does, split into a subpackage.
15. **No function may exceed 80 lines.** If it does, extract helpers.
16. **No dead code.** If a function/method/constant has zero callers outside its definition, remove it.

## Architecture

17. **`ffmpeg_helpers.py` is the single source of truth** for: `_run_ffmpeg()`, `_validate_input_path()`, `_escape_ffmpeg_filter_value()`, `_get_video_duration()`, `_run_ffprobe()`, `_seconds_to_srt_time()`. Never duplicate these.
18. **`server.py` is the tool registration layer.** Business logic goes in engine modules, not in server tool handlers.
19. **Lazy imports in `server.py`** keep startup fast. Follow the existing pattern: import inside the tool handler function.

## Testing

20. **Every fix must pass `python3 -m pytest tests/ -x -q --tb=short`** before committing.
21. **Run `python3 -c "import mcp_video"`** to verify no broken imports after changes.
