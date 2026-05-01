"""Watermark overlay operation for the FFmpeg engine."""

from __future__ import annotations

from .engine_runtime_utils import (
    _auto_output,
    _build_edit_result,
    _movflags_args,
    _quality_args,
    _resolve_position,
    _run_ffmpeg,
    _timed_operation,
)
from .ffmpeg_helpers import _validate_input_path, _validate_output_path
from .models import EditResult, NamedPosition, Position


def watermark(
    input_path: str,
    image_path: str,
    position: Position = "bottom-right",
    opacity: float = 0.7,
    margin: int = 20,
    output_path: str | None = None,
    crf: int | None = None,
    preset: str | None = None,
) -> EditResult:
    """Add an image watermark to a video."""
    input_path = _validate_input_path(input_path)
    image_path = _validate_input_path(image_path)
    output = output_path or _auto_output(input_path, "watermarked")
    _validate_output_path(output)

    # Position expressions for the overlay
    position_map: dict[NamedPosition, str] = {
        "top-left": f"{margin}:{margin}",
        "top-center": "(main_w-overlay_w)/2:{margin}",
        "top-right": f"main_w-overlay_w-{margin}:{margin}",
        "center-left": f"{margin}:(main_h-overlay_h)/2",
        "center": "(main_w-overlay_w)/2:(main_h-overlay_h)/2",
        "center-right": f"main_w-overlay_w-{margin}:(main_h-overlay_h)/2",
        "bottom-left": f"{margin}:main_h-overlay_h-{margin}",
        "bottom-center": "(main_w-overlay_w)/2:main_h-overlay_h-{margin}",
        "bottom-right": f"main_w-overlay_w-{margin}:main_h-overlay_h-{margin}",
    }

    overlay_pos = _resolve_position(position, position_map, "bottom-right")
    # Format opacity for FFmpeg (0.0 to 1.0)
    opacity_fmt = f"{opacity:.2f}"

    with _timed_operation() as timing:
        _run_ffmpeg(
            [
                "-i",
                input_path,
                "-i",
                image_path,
                "-filter_complex",
                f"[1:v]format=rgba,colorchannelmixer=aa={opacity_fmt}[wm];[0:v][wm]overlay={overlay_pos}",
                "-c:v",
                "libx264",
                *_quality_args(crf=crf, preset=preset),
                "-c:a",
                "copy",
                *_movflags_args(output),
                output,
            ]
        )

    return _build_edit_result(
        output,
        "watermark",
        timing,
    )
