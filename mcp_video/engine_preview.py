"""Preview generation operation for the FFmpeg engine."""

from __future__ import annotations

from .ffmpeg_helpers import _validate_input_path, _validate_output_path
from .engine_probe import probe
from .engine_runtime_utils import _auto_output, _build_edit_result, _movflags_args, _run_ffmpeg, _timed_operation
from .errors import MCPVideoError
from .models import PREVIEW_PRESETS, EditResult


def preview(
    input_path: str,
    output_path: str | None = None,
    scale_factor: int = 4,
) -> EditResult:
    """Generate a fast low-resolution preview for quick review."""
    input_path = _validate_input_path(input_path)
    if scale_factor < 1:
        raise MCPVideoError("scale_factor must be at least 1", code="invalid_scale_factor")
    info = probe(input_path)

    w = max(info.width // scale_factor, 320)
    h = max(info.height // scale_factor, 240)

    output = output_path or _auto_output(input_path, "preview")
    _validate_output_path(output)

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

    return _build_edit_result(
        output,
        "preview",
        timing,
    )
