"""Preview generation operation for the FFmpeg engine."""

from __future__ import annotations

from .engine_probe import probe
from .engine_runtime_utils import _auto_output, _movflags_args, _run_ffmpeg, _timed_operation, _validate_input
from .errors import MCPVideoError
from .models import PREVIEW_PRESETS, EditResult


def preview(
    input_path: str,
    output_path: str | None = None,
    scale_factor: int = 4,
) -> EditResult:
    """Generate a fast low-resolution preview for quick review."""
    _validate_input(input_path)
    if scale_factor < 1:
        raise MCPVideoError("scale_factor must be at least 1", code="invalid_scale_factor")
    info = probe(input_path)

    w = max(info.width // scale_factor, 320)
    h = max(info.height // scale_factor, 240)

    output = output_path or _auto_output(input_path, "preview")

    with _timed_operation() as timing:
        _run_ffmpeg(
            [
                "-i",
                input_path,
                "-vf",
                f"scale={w}:{h}",
                "-c:v",
                "libx264",
                "-crf",
                str(PREVIEW_PRESETS["crf"]),
                "-preset",
                PREVIEW_PRESETS["preset"],
                "-c:a",
                "aac",
                "-b:a",
                "64k",
                "-ac",
                "2",
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
        operation="preview",
        elapsed_ms=timing["elapsed_ms"],
    )
