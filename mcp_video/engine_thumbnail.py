"""Thumbnail/frame extraction operations for the FFmpeg engine."""

from __future__ import annotations

from .ffmpeg_helpers import _validate_input_path, _validate_output_path
from .engine_probe import get_duration
from .engine_runtime_utils import _auto_output, _run_ffmpeg
from .models import ThumbnailResult


def thumbnail(
    input_path: str,
    timestamp: float | None = None,
    output_path: str | None = None,
) -> ThumbnailResult:
    """Extract a single frame from a video."""
    _validate_input_path(input_path)

    if timestamp is None:
        # Grab frame at 10% of video duration
        dur = get_duration(input_path)
        timestamp = dur * 0.1
    else:
        # Clamp to valid range
        dur = get_duration(input_path)
        timestamp = min(timestamp, dur * 0.99)

    output = output_path or _auto_output(input_path, f"frame_{timestamp:.1f}s", ext=".jpg")
    _validate_output_path(output)

    _run_ffmpeg(
        [
            "-ss",
            str(timestamp),
            "-i",
            input_path,
            "-vframes",
            "1",
            "-q:v",
            "2",
            "-y",
            output,
        ]
    )

    return ThumbnailResult(
        frame_path=output,
        timestamp=timestamp,
    )
