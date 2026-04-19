"""Video stabilization operation for the FFmpeg engine."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile

from .engine_probe import probe
from .engine_runtime_utils import (
    _auto_output,
    _ffmpeg,
    _movflags_args,
    _quality_args,
    _require_filter,
    _run_ffmpeg,
    _sanitize_ffmpeg_number,
    _validate_input,
)
from .errors import ProcessingError, parse_ffmpeg_error
from .ffmpeg_helpers import _escape_ffmpeg_filter_value
from .limits import DEFAULT_FFMPEG_TIMEOUT
from .models import EditResult


def stabilize(
    input_path: str,
    smoothing: float = 15,
    zooming: float = 0,
    output_path: str | None = None,
) -> EditResult:
    """Stabilize a shaky video with FFmpeg vidstab detect/transform passes.

    Args:
        input_path: Path to the input video.
        smoothing: Smoothing strength (higher is more stable).
        zooming: Zoom percentage to avoid black borders.
        output_path: Optional output video path.
    """
    _validate_input(input_path)
    _require_filter("vidstabdetect", "Video stabilization")
    output = output_path or _auto_output(input_path, "stabilized")

    safe_smoothing = _escape_ffmpeg_filter_value(str(_sanitize_ffmpeg_number(smoothing, "smoothing")))
    safe_zooming = _escape_ffmpeg_filter_value(str(_sanitize_ffmpeg_number(zooming, "zooming")))

    tmpdir = tempfile.mkdtemp(prefix="mcp_video_stab_")
    try:
        vectors_file = os.path.join(tmpdir, "vectors.trf")
        _detect_motion_vectors(input_path, vectors_file)

        safe_vectors_file = _escape_ffmpeg_filter_value(vectors_file)
        _run_ffmpeg(
            [
                "-i",
                input_path,
                "-vf",
                f"vidstabtransform=input={safe_vectors_file}:smoothing={safe_smoothing}:zoom={safe_zooming}:crop=black",
                "-c:v",
                "libx264",
                *_quality_args(),
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                *_movflags_args(output),
                output,
            ]
        )
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    result_info = probe(output)
    return EditResult(
        output_path=output,
        duration=result_info.duration,
        resolution=result_info.resolution,
        size_mb=result_info.size_mb,
        format="mp4",
        operation="stabilize",
    )


def _detect_motion_vectors(input_path: str, vectors_file: str) -> None:
    safe_vectors_file = _escape_ffmpeg_filter_value(vectors_file)
    try:
        result = subprocess.run(
            [
                _ffmpeg(),
                "-y",
                "-i",
                input_path,
                "-vf",
                "vidstabdetect=shakiness=10:accuracy=15:result=" + safe_vectors_file,
                "-f",
                "null",
                "-",
            ],
            capture_output=True,
            text=True,
            timeout=DEFAULT_FFMPEG_TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        raise ProcessingError(
            f"ffmpeg -i {input_path} -vf vidstabdetect",
            -1,
            f"Video stabilization analysis timed out after {DEFAULT_FFMPEG_TIMEOUT} seconds",
        ) from exc
    if result.returncode != 0:
        raise parse_ffmpeg_error(result.stderr)
