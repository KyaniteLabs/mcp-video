"""Basic edit operations for the FFmpeg engine."""

from __future__ import annotations

from .engine_probe import probe
from .engine_runtime_utils import _auto_output, _movflags_args, _run_ffmpeg, _validate_input
from .models import EditResult


def trim(
    input_path: str,
    start: str | float = 0,
    duration: str | float | None = None,
    end: str | float | None = None,
    output_path: str | None = None,
) -> EditResult:
    """Trim a video by start time and duration or end time."""
    _validate_input(input_path)
    output = output_path or _auto_output(input_path, "trimmed")

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
            "fast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            *_movflags_args(output),
            output,
        ]
    )
    _run_ffmpeg(args)

    info = probe(output)
    return EditResult(
        output_path=output,
        duration=info.duration,
        resolution=info.resolution,
        size_mb=info.size_mb,
        format="mp4",
        operation="trim",
    )
