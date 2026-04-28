"""Shared FFmpeg helper functions.

Centralises duplicated utilities used across engine modules so there is a
single authoritative copy of each helper.
"""

from __future__ import annotations

import os
import subprocess
from typing import Any

from .errors import InputFileError, MCPVideoError, ProcessingError
from .limits import DEFAULT_FFMPEG_TIMEOUT, FFPROBE_TIMEOUT, MAX_FILE_SIZE_MB


def _validate_input_path(path: str) -> str:
    """Validate and resolve a file path. Rejects null bytes, symlinks, and oversize files."""
    if "\x00" in path:
        raise InputFileError(path, "Path contains null bytes")
    resolved = os.path.realpath(path)
    if not os.path.isfile(resolved):
        raise InputFileError(resolved)
    try:
        size_mb = os.path.getsize(resolved) / (1024 * 1024)
    except OSError as e:
        raise InputFileError(resolved, f"Cannot read file size: {e}") from None
    if size_mb > MAX_FILE_SIZE_MB:
        raise InputFileError(
            resolved,
            f"File size ({size_mb:.1f} MB) exceeds maximum of {MAX_FILE_SIZE_MB} MB",
        )
    return resolved


def _validate_project_path(path: str) -> str:
    """Validate a project directory path."""
    if "\x00" in path:
        raise InputFileError(path, "Path contains null bytes")
    resolved = os.path.realpath(path)
    if not os.path.isdir(resolved):
        raise InputFileError(resolved, "Directory does not exist")
    return resolved


def _validate_output_path(path: str) -> str:
    """Validate an output file path without rejecting valid parent-relative paths."""
    if "\x00" in path:
        raise MCPVideoError(
            f"Output path contains null bytes: {path!r}",
            error_type="validation_error",
            code="invalid_output_path",
        )
    # Parent-relative outputs such as ../clips/out.mp4 are valid local filesystem
    # paths. Canonicalize before checking for unresolved traversal markers so
    # auto-generated outputs from relative inputs do not become false positives.
    parts = os.path.normpath(os.path.abspath(path)).split(os.sep)
    if ".." in parts:
        raise MCPVideoError(
            f"Output path contains unresolved directory traversal: {path!r}",
            error_type="validation_error",
            code="invalid_output_path",
        )
    return path


def _run_ffmpeg(cmd: list[str], timeout: int = DEFAULT_FFMPEG_TIMEOUT) -> subprocess.CompletedProcess[str]:
    """Run an FFmpeg/FFprobe command with timeout and error handling."""
    # Ensure output directory exists — find the last non-flag argument (the output file)
    for arg in reversed(cmd):
        if not arg.startswith("-") and not arg.startswith("ffmpeg") and not arg.startswith("ffprobe"):
            out_dir = os.path.dirname(arg)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            break
    cmd_str = " ".join(cmd)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise ProcessingError(cmd_str, -1, f"FFmpeg command timed out after {timeout}s") from None
    if result.returncode != 0:
        raise ProcessingError(cmd_str, result.returncode, result.stderr)
    return result


def _escape_ffmpeg_filter_value(value: str) -> str:
    """Escape special characters for FFmpeg filter expressions (subtitles, drawtext, etc.)."""
    return (
        value.replace("\\", "\\\\")
        .replace("'", "'\\''")
        .replace(":", "\\:")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("=", "\\=")
    )


def _get_video_duration(video_path: str) -> float:
    """Get video duration using ffprobe."""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]
    result = _run_ffmpeg(cmd)
    stdout = result.stdout.strip()
    if not stdout:
        raise ProcessingError(" ".join(cmd), result.returncode, result.stderr)
    try:
        return float(stdout)
    except ValueError:
        raise ProcessingError(
            " ".join(cmd), result.returncode, f"Non-numeric duration from ffprobe: {stdout!r}"
        ) from None


def _run_ffprobe_json(path: str) -> dict[str, Any]:
    """Run ffprobe returning full JSON (format + streams)."""
    import json as _json

    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        path,
    ]
    result = _run_ffmpeg(cmd, timeout=FFPROBE_TIMEOUT)
    try:
        return _json.loads(result.stdout)
    except _json.JSONDecodeError as e:
        raise ProcessingError(" ".join(cmd), result.returncode, f"Invalid JSON from ffprobe: {e}") from None


def _seconds_to_srt_time(seconds: float) -> str:
    """Convert seconds to SRT time format HH:MM:SS,mmm."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
