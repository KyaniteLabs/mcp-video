"""Export operation wrapper for the FFmpeg engine."""

from __future__ import annotations

from collections.abc import Callable

from .engine_runtime_utils import _validate_input
from .models import EditResult, ExportFormat, QualityLevel


def export_video(
    input_path: str,
    output_path: str | None = None,
    quality: QualityLevel = "high",
    format: ExportFormat = "mp4",
    on_progress: Callable[[float], None] | None = None,
    two_pass: bool = False,
    target_bitrate: int | None = None,
) -> EditResult:
    """Export a video with specified quality and format settings."""
    _validate_input(input_path)
    from .engine_convert import convert

    result = convert(
        input_path,
        format=format,
        quality=quality,
        output_path=output_path,
        on_progress=on_progress,
        two_pass=two_pass,
        target_bitrate=target_bitrate,
    )
    result.operation = "export"
    return result
