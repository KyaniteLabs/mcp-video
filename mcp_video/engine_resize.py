"""Resize operations for the FFmpeg engine."""

from __future__ import annotations

from .defaults import DEFAULT_AUDIO_BITRATE
from .ffmpeg_helpers import _validate_input_path, _validate_output_path
from .engine_probe import probe
from .engine_runtime_utils import _build_edit_result, _movflags_args, _timed_operation
from .paths import _auto_output
from .ffmpeg_helpers import _run_ffmpeg
from .errors import MCPVideoError
from .models import ASPECT_RATIOS, QUALITY_PRESETS, EditResult, QualityLevel


def resize(
    input_path: str,
    width: int | None = None,
    height: int | None = None,
    aspect_ratio: str | None = None,
    quality: QualityLevel = "high",
    output_path: str | None = None,
) -> EditResult:
    """Resize a video. Use aspect_ratio for preset sizes (e.g. '9:16')."""
    input_path = _validate_input_path(input_path)

    info = probe(input_path)
    if info.width == 0 or info.height == 0:
        raise MCPVideoError(
            "Cannot resize: video has zero dimensions",
            error_type="processing_error",
            code="invalid_input",
        )

    if aspect_ratio and aspect_ratio in ASPECT_RATIOS:
        w, h = ASPECT_RATIOS[aspect_ratio]
    elif aspect_ratio:
        raise MCPVideoError(
            f"Unknown aspect ratio: {aspect_ratio}. Available: {', '.join(ASPECT_RATIOS.keys())}",
            error_type="input_error",
            code="invalid_aspect_ratio",
        )
    elif width and height:
        w, h = width, height
    elif width:
        ratio = info.height / info.width
        w, h = width, int(width * ratio)
    elif height:
        ratio = info.width / info.height
        w, h = int(height * ratio), height
    else:
        raise MCPVideoError("resize requires width+height, aspect_ratio, or single dimension")

    preset = QUALITY_PRESETS[quality]
    output = output_path or _auto_output(input_path, f"{w}x{h}")
    _validate_output_path(output)

    # Scale to fit within target, then pad to exact dimensions
    vf = f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black"

    with _timed_operation() as timing:
        _run_ffmpeg(
            [
                "-i",
                input_path,
                "-vf",
                vf,
                "-c:v",
                "libx264",
                "-crf",
                str(preset["crf"]),
                "-preset",
                preset["preset"],
                "-c:a",
                "aac",
                "-b:a",
                DEFAULT_AUDIO_BITRATE,
                *_movflags_args(output),
                output,
            ]
        )

    return _build_edit_result(
        output,
        "resize",
        timing,
    )
