"""Frame sequence export operations for the FFmpeg engine."""

from __future__ import annotations

import os

from .ffmpeg_helpers import _validate_input_path
from .engine_probe import probe
from .engine_runtime_utils import _auto_output_dir, _run_ffmpeg, _sanitize_ffmpeg_number
from .errors import MCPVideoError
from .models import ImageSequenceResult


def export_frames(
    input_path: str,
    output_dir: str | None = None,
    fps: float = 1.0,
    format: str = "jpg",
) -> ImageSequenceResult:
    """Export frames from a video as individual images.

    Args:
        input_path: Path to the input video.
        output_dir: Directory for extracted frames.
        fps: Frames per second to extract (1.0 = 1 frame per second).
        format: Output image format (jpg, png).
    """
    input_path = _validate_input_path(input_path)
    fps = _sanitize_ffmpeg_number(fps, "fps")
    if format == "mjpeg":
        format = "jpg"
    if format not in ("jpg", "png"):
        raise MCPVideoError(
            f"Invalid format '{format}': must be 'jpg', 'mjpeg' or 'png'",
            error_type="validation_error",
            code="invalid_format",
        )
    probe(input_path)

    out_dir = output_dir or _auto_output_dir(input_path, "frames")
    os.makedirs(out_dir, exist_ok=True)

    ext = format if format.startswith(".") else f".{format}"
    pattern = os.path.join(out_dir, f"frame_%04d{ext}")

    _run_ffmpeg(
        [
            "-i",
            input_path,
            "-vf",
            f"fps={fps}",
            "-q:v",
            "2",
            "-y",
            pattern,
        ]
    )

    # Collect generated frame paths
    frame_paths = sorted(
        [os.path.join(out_dir, f) for f in os.listdir(out_dir) if f.startswith("frame_") and f.endswith(ext)]
    )

    return ImageSequenceResult(
        frame_paths=frame_paths,
        frame_count=len(frame_paths),
        fps=fps,
    )
