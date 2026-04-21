"""Crop operation for the FFmpeg engine."""

from __future__ import annotations

from .engine_probe import probe
from .engine_runtime_utils import (
    _auto_output,
    _movflags_args,
    _quality_args,
    _run_ffmpeg,
    _timed_operation,
)
from .errors import MCPVideoError
from .ffmpeg_helpers import _validate_input_path, _validate_output_path, _escape_ffmpeg_filter_value
from .models import EditResult


def crop(
    input_path: str,
    width: int,
    height: int,
    x: int | None = None,
    y: int | None = None,
    output_path: str | None = None,
) -> EditResult:
    """Crop a video to a rectangular region."""
    _validate_input_path(input_path)
    if width <= 0 or height <= 0:
        raise MCPVideoError("Crop dimensions must be positive", code="invalid_crop")

    info = probe(input_path)
    if width > info.width or height > info.height:
        raise MCPVideoError(
            f"Crop size ({width}x{height}) larger than video ({info.width}x{info.height})",
            code="crop_too_large",
        )

    if x is None:
        x = (info.width - width) // 2
    if y is None:
        y = (info.height - height) // 2

    output = output_path or _auto_output(input_path, f"crop_{width}x{height}")
    _validate_output_path(output)
    crop_filter = f"crop={_escape_ffmpeg_filter_value(str(width))}:{_escape_ffmpeg_filter_value(str(height))}:{_escape_ffmpeg_filter_value(str(x))}:{_escape_ffmpeg_filter_value(str(y))}"

    with _timed_operation() as timing:
        _run_ffmpeg(
            [
                "-i",
                input_path,
                "-vf",
                crop_filter,
                "-c:v",
                "libx264",
                *_quality_args(),
                "-c:a",
                "copy",
                *_movflags_args(output),
                output,
            ]
        )

    result_info = probe(output)
    return EditResult(
        output_path=output,
        duration=result_info.duration,
        resolution=result_info.resolution,
        size_mb=result_info.size_mb,
        format="mp4",
        operation="crop",
        elapsed_ms=timing["elapsed_ms"],
    )
