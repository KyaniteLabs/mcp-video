"""Subtitle file generation operation for the FFmpeg engine."""

from __future__ import annotations

import os

from .engine_runtime_utils import (
    _auto_output_dir,
    _movflags_args,
    _quality_args,
    _require_filter,
    _run_ffmpeg,
)
from .errors import MCPVideoError
from .ffmpeg_helpers import _validate_input_path, _escape_ffmpeg_filter_value, _seconds_to_srt_time
from .models import SubtitleResult


def generate_subtitles(
    entries: list[dict],
    input_path: str,
    output_path: str | None = None,
    burn: bool = False,
) -> SubtitleResult:
    """Generate SRT subtitles from text entries and optionally burn into video."""
    input_path = _validate_input_path(input_path)
    _validate_entries(entries)

    srt_file = _write_srt(entries, input_path, output_path)
    if burn:
        _require_filter("subtitles", "Subtitle burn-in")
        video_out = os.path.join(os.path.dirname(srt_file), "subtitled.mp4")
        escaped_srt = _escape_ffmpeg_filter_value(srt_file)
        _run_ffmpeg(
            [
                "-i",
                input_path,
                "-vf",
                f"subtitles={escaped_srt}",
                "-c:v",
                "libx264",
                *_quality_args(),
                "-c:a",
                "copy",
                *_movflags_args(video_out),
                video_out,
            ]
        )
        return SubtitleResult(
            srt_path=srt_file,
            video_path=video_out,
            entry_count=len(entries),
        )

    return SubtitleResult(
        srt_path=srt_file,
        entry_count=len(entries),
    )


def _validate_entries(entries: list[dict]) -> None:
    if not entries:
        raise MCPVideoError(
            "entries cannot be empty",
            error_type="validation_error",
            code="empty_entries",
        )
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict) or "text" not in entry or "start" not in entry or "end" not in entry:
            raise MCPVideoError(
                f"Invalid subtitle entry {i}: must have 'start', 'end', 'text' keys",
                error_type="validation_error",
                code="invalid_parameter",
            )
        start = entry.get("start", 0)
        end = entry.get("end", 0)
        if start >= end:
            raise MCPVideoError(
                f"Entry {i}: start ({start}) must be less than end ({end})",
                error_type="validation_error",
                code="invalid_entry_range",
            )


def _write_srt(entries: list[dict], input_path: str, output_path: str | None) -> str:
    if output_path:
        srt_dir = output_path if os.path.isdir(output_path) else os.path.dirname(output_path) or "."
        os.makedirs(srt_dir, exist_ok=True)
    else:
        srt_dir = _auto_output_dir(input_path, "subtitles")
        os.makedirs(srt_dir, exist_ok=True)

    srt_file = os.path.join(srt_dir, "subtitles.srt")
    with open(srt_file, "w", encoding="utf-8") as f:
        f.write(_build_srt_content(entries))
    return srt_file


def _build_srt_content(entries: list[dict]) -> str:
    srt_lines: list[str] = []
    for i, entry in enumerate(entries, 1):
        start = entry["start"]
        end = entry["end"]
        text = entry["text"]
        srt_lines.append(str(i))
        srt_lines.append(_seconds_to_srt_time(start) + " --> " + _seconds_to_srt_time(end))
        srt_lines.append(text)
        srt_lines.append("")
    return "\n".join(srt_lines)
