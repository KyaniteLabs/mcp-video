"""Reverse playback operation for the FFmpeg engine."""

from __future__ import annotations

from .defaults import DEFAULT_AUDIO_BITRATE
from .engine_probe import probe
from .engine_runtime_utils import (
    _auto_output,
    _movflags_args,
    _quality_args,
    _run_ffmpeg,
    _timed_operation,
)
from .ffmpeg_helpers import _validate_input_path
from .models import EditResult


def reverse(
    input_path: str,
    output_path: str | None = None,
) -> EditResult:
    """Reverse video and audio playback.

    Args:
        input_path: Path to the input video.
        output_path: Where to save the output. Auto-generated if omitted.
    """
    _validate_input_path(input_path)
    output = output_path or _auto_output(input_path, "reversed")

    input_info = probe(input_path)

    args = ["-i", input_path, "-vf", "reverse"]
    # Only reverse audio if the input has an audio stream
    if input_info.audio_codec:
        args += ["-af", "areverse", "-c:a", "aac", "-b:a", DEFAULT_AUDIO_BITRATE]
    else:
        args += ["-an"]
    args += ["-c:v", "libx264", *_quality_args()]

    with _timed_operation() as timing:
        _run_ffmpeg(
            args
            + _movflags_args(output)
            + [
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
        operation="reverse",
        elapsed_ms=timing["elapsed_ms"],
    )
