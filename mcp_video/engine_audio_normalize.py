"""Audio normalization operation for the FFmpeg engine."""

from __future__ import annotations

from .engine_probe import probe
from .engine_runtime_utils import (
    _auto_output,
    _movflags_args,
    _require_filter,
    _run_ffmpeg,
    _sanitize_ffmpeg_number,
    _timed_operation,
)
from .errors import MCPVideoError
from .ffmpeg_helpers import _validate_input_path, _validate_output_path, _escape_ffmpeg_filter_value
from .models import EditResult


def normalize_audio(
    input_path: str,
    target_lufs: float = -16.0,
    lra: float = 11.0,
    output_path: str | None = None,
) -> EditResult:
    """Normalize audio loudness to a target LUFS level.

    Args:
        input_path: Path to the input video.
        target_lufs: Target integrated loudness in LUFS. Common values:
            -16 (YouTube), -23 (EBU R128/broadcast), -14 (Apple/Spotify).
        lra: Loudness range target in LU. Default 11.0.
        output_path: Where to save the output.
    """
    _validate_input_path(input_path)
    if not isinstance(target_lufs, (int, float)) or not (-70 <= target_lufs <= -5):
        raise MCPVideoError(
            f"target_lufs must be -70 to -5, got {target_lufs}", error_type="validation_error", code="invalid_parameter"
        )
    _require_filter("loudnorm", "Audio normalization")
    output = output_path or _auto_output(input_path, "normalized")
    _validate_output_path(output)

    safe_target_lufs = _escape_ffmpeg_filter_value(str(_sanitize_ffmpeg_number(target_lufs, "target_lufs")))
    safe_lra = _escape_ffmpeg_filter_value(str(_sanitize_ffmpeg_number(lra, "lra")))

    # loudnorm parameters: I=integrated loudness, TP=true peak, LRA=loudness range
    # TP (true peak) should be a fixed value near -1.5 dBTP regardless of target LUFS.
    safe_tp = _escape_ffmpeg_filter_value(str(-1.5))

    with _timed_operation() as timing:
        _run_ffmpeg(
            [
                "-i",
                input_path,
                "-af",
                f"loudnorm=I={safe_target_lufs}:TP={safe_tp}:LRA={safe_lra}",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
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
        operation="normalize_audio",
        elapsed_ms=timing["elapsed_ms"],
    )
