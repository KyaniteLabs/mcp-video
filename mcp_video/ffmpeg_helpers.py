"""Shared FFmpeg helper functions.

Centralises duplicated utilities used across engine modules so there is a
single authoritative copy of each helper.
"""

from __future__ import annotations

import os
import subprocess
from typing import Any

from .errors import InputFileError, ProcessingError
from .limits import DEFAULT_FFMPEG_TIMEOUT, FFPROBE_TIMEOUT


def _validate_input_path(path: str) -> str:
    """Validate and resolve a file path. Rejects null bytes and symlinks."""
    if "\x00" in path:
        raise InputFileError(path, "Path contains null bytes")
    resolved = os.path.realpath(path)
    if not os.path.isfile(resolved):
        raise InputFileError(resolved)
    return resolved


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
    return float(result.stdout.strip())


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
    return _json.loads(result.stdout)


def _seconds_to_srt_time(seconds: float) -> str:
    """Convert seconds to SRT time format HH:MM:SS,mmm."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
