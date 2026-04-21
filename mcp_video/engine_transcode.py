"""Transcoding helpers for the FFmpeg engine."""

from __future__ import annotations

from .defaults import DEFAULT_AUDIO_BITRATE
from .ffmpeg_helpers import _validate_input_path
from .engine_runtime_utils import _auto_output, _movflags_args, _run_ffmpeg

# ---------------------------------------------------------------------------
# Normalize — convert to H.264/AAC for editing
# ---------------------------------------------------------------------------


def normalize(input_path: str, output_path: str | None = None) -> str:
    """Normalize a video to H.264 video + AAC audio for reliable editing."""
    _validate_input_path(input_path)
    output = output_path or _auto_output(input_path, "normalized")
    _run_ffmpeg(
        [
            "-i",
            input_path,
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            DEFAULT_AUDIO_BITRATE,
            *_movflags_args(output),
            output,
        ]
    )
    return output
