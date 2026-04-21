"""Basic edit operations for the FFmpeg engine."""

from __future__ import annotations

from .defaults import DEFAULT_AUDIO_BITRATE, DEFAULT_CRF, DEFAULT_PRESET
from .ffmpeg_helpers import _validate_input_path, _validate_output_path
from .engine_probe import probe
from .engine_runtime_utils import _auto_output, _movflags_args, _run_ffmpeg, _timed_operation
from .errors import MCPVideoError
from .models import EditResult


def _time_to_seconds(value: str | float) -> float:
    """Convert a time string (HH:MM:SS or seconds) to float seconds."""
    if isinstance(value, (int, float)):
        return float(value)
    value = value.strip()
    # Handle HH:MM:SS or MM:SS
    if ":" in value:
        parts = value.split(":")
        if len(parts) == 2:
            m, s = parts
            return int(m) * 60 + float(s)
        elif len(parts) == 3:
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
    return float(value)


def trim(
    input_path: str,
    start: str | float = 0,
    duration: str | float | None = None,
    end: str | float | None = None,
    output_path: str | None = None,
) -> EditResult:
    """Trim a video by start time and duration or end time."""
    input_path = _validate_input_path(input_path)
    output = output_path or _auto_output(input_path, "trimmed")
    _validate_output_path(output)

    # Validate time values
    try:
        start_sec = _time_to_seconds(start)
    except ValueError:
        raise MCPVideoError(
            f"Invalid start time: '{start}'. Expected seconds or HH:MM:SS format.",
            error_type="validation_error",
            code="invalid_parameter",
        ) from None
    if start_sec < 0:
        raise MCPVideoError(
            f"Start time must be non-negative, got {start_sec}",
            error_type="validation_error",
            code="invalid_parameter",
        )

    if duration is not None:
        try:
            dur_sec = _time_to_seconds(duration)
        except ValueError:
            raise MCPVideoError(
                f"Invalid duration: '{duration}'. Expected seconds or HH:MM:SS format.",
                error_type="validation_error",
                code="invalid_parameter",
            ) from None
        if dur_sec <= 0:
            raise MCPVideoError(
                f"Duration must be positive, got {dur_sec}",
                error_type="validation_error",
                code="invalid_parameter",
            )

    if end is not None:
        try:
            end_sec = _time_to_seconds(end)
        except ValueError:
            raise MCPVideoError(
                f"Invalid end time: '{end}'. Expected seconds or HH:MM:SS format.",
                error_type="validation_error",
                code="invalid_parameter",
            ) from None
        if end_sec <= 0:
            raise MCPVideoError(
                f"End time must be positive, got {end_sec}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        if end_sec <= start_sec:
            raise MCPVideoError(
                f"End time ({end_sec}s) must be greater than start time ({start_sec}s)",
                error_type="validation_error",
                code="invalid_parameter",
            )

    args = []
    if start:
        args.extend(["-ss", str(start)])
    args.extend(["-i", input_path])
    if duration:
        args.extend(["-t", str(duration)])
    elif end:
        args.extend(["-to", str(end)])
    args.extend(
        [
            "-c:v",
            "libx264",
            "-preset",
            DEFAULT_PRESET,
            "-crf",
            str(DEFAULT_CRF),
            "-c:a",
            "aac",
            "-b:a",
            DEFAULT_AUDIO_BITRATE,
            *_movflags_args(output),
            output,
        ]
    )

    with _timed_operation() as timing:
        _run_ffmpeg(args)

    info = probe(output)
    return EditResult(
        output_path=output,
        duration=info.duration,
        resolution=info.resolution,
        size_mb=info.size_mb,
        format="mp4",
        operation="trim",
        elapsed_ms=timing["elapsed_ms"],
    )
