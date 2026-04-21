"""Subtitle burn-in operation for the FFmpeg engine."""

from __future__ import annotations

from .engine_probe import probe
from .engine_runtime_utils import (
    _auto_output,
    _movflags_args,
    _require_filter,
    _run_ffmpeg,
    _timed_operation,
)
from .defaults import DEFAULT_CRF, DEFAULT_PRESET
from .ffmpeg_helpers import _validate_input_path, _validate_output_path, _escape_ffmpeg_filter_value
from .models import EditResult


def subtitles(
    input_path: str,
    subtitle_path: str,
    output_path: str | None = None,
    style: str = "FontSize=22,PrimaryColour=&Hffffff&,OutlineColour=&H000000&,Outline=2,Shadow=1",
) -> EditResult:
    """Burn subtitles (SRT/VTT) into a video."""
    _validate_input_path(input_path)
    _validate_input_path(subtitle_path)
    _require_filter("subtitles", "Subtitle burn-in")
    output = output_path or _auto_output(input_path, "subtitled")
    _validate_output_path(output)

    # Escape special characters for FFmpeg subtitle filter path
    escaped_sub_path = _escape_ffmpeg_filter_value(subtitle_path)
    escaped_style = _escape_ffmpeg_filter_value(style)

    with _timed_operation() as timing:
        _run_ffmpeg(
            [
                "-i",
                input_path,
                "-vf",
                f"subtitles={escaped_sub_path}:force_style={escaped_style}",
                "-c:v",
                "libx264",
                "-preset",
                DEFAULT_PRESET,
                "-crf",
                str(DEFAULT_CRF),
                "-c:a",
                "copy",
                *_movflags_args(output),
                output,
            ]
        )

    info = probe(output)
    return EditResult(
        output_path=output,
        duration=info.duration,
        resolution=info.resolution,
        size_mb=info.size_mb,
        format="mp4",
        operation="subtitles",
        elapsed_ms=timing["elapsed_ms"],
    )
