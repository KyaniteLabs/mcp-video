"""Text overlay operations for the FFmpeg engine."""

from __future__ import annotations


from .engine_probe import probe
from .errors import MCPVideoError
from .engine_runtime_utils import (
    _default_font,
    _movflags_args,
    _quality_args,
    _require_filter,
    _timed_operation,
)
from .paths import (
    _auto_output,
)
from .models import (
    _position_coords,
)
from .ffmpeg_helpers import (
    _build_ffmpeg_cmd,
    _run_ffmpeg,
    _sanitize_ffmpeg_number,
)
from .validation import (
    _validate_color,
)
from .ffmpeg_helpers import _validate_input_path, _validate_output_path, _escape_ffmpeg_filter_value
from .models import EditResult, Position


def add_text(
    input_path: str,
    text: str,
    position: Position = "top-center",
    font: str | None = None,
    size: int = 48,
    color: str = "white",
    shadow: bool = True,
    start_time: float | None = None,
    duration: float | None = None,
    output_path: str | None = None,
    crf: int | None = None,
    preset: str | None = None,
) -> EditResult:
    """Overlay text on a video."""
    input_path = _validate_input_path(input_path)
    _require_filter("drawtext", "Text overlay")
    if not text or not text.strip():
        raise MCPVideoError(
            "Text cannot be empty",
            error_type="validation_error",
            code="invalid_parameter",
        )
    _validate_color(color)
    output = output_path or _auto_output(input_path, "titled")
    _validate_output_path(output)

    coords = _position_coords(position)
    fontfile = font or _default_font()

    # Validate font file exists when explicitly provided
    if font is not None:
        _validate_input_path(fontfile)

    # Escape font path for FFmpeg filter syntax
    escaped_fontfile = _escape_ffmpeg_filter_value(fontfile)

    # Escape FFmpeg drawtext special characters
    escaped_text = _escape_ffmpeg_filter_value(text)

    filter_parts = [
        f"drawtext=text='{escaped_text}'",
        f"fontsize={size}",
        f"fontcolor={color}",
        f"fontfile={escaped_fontfile}",
        coords,
    ]

    if shadow:
        filter_parts.append("shadowcolor=black@0.5")
        filter_parts.append("shadowx=2")
        filter_parts.append("shadowy=2")

    if start_time is not None and duration is not None:
        safe_start = _escape_ffmpeg_filter_value(str(_sanitize_ffmpeg_number(start_time, "start_time")))
        safe_end = _escape_ffmpeg_filter_value(
            str(_sanitize_ffmpeg_number(start_time + duration, "start_time + duration"))
        )
        filter_parts.append(f"enable='between(t\\,{safe_start}\\,{safe_end})'")
    elif start_time is not None:
        safe_start = _escape_ffmpeg_filter_value(str(_sanitize_ffmpeg_number(start_time, "start_time")))
        filter_parts.append(f"enable='gte(t\\,{safe_start})'")

    vf = ":".join(filter_parts)

    with _timed_operation() as timing:
        _run_ffmpeg(
            _build_ffmpeg_cmd(
                input_path,
                output_path=output,
                video_filter=vf,
                audio_codec="copy",
                crf=crf,
                preset=preset,
            )
        )

    info = probe(output)
    return EditResult(
        output_path=output,
        duration=info.duration,
        resolution=info.resolution,
        size_mb=info.size_mb,
        format="mp4",
        operation="add_text",
        elapsed_ms=timing["elapsed_ms"],
    )
