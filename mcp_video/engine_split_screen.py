"""Split-screen composition operation for the FFmpeg engine."""

from __future__ import annotations

from .engine_probe import probe
from .engine_runtime_utils import (
    _auto_output,
    _movflags_args,
    _quality_args,
    _run_ffmpeg,
    _sanitize_ffmpeg_number,
    _timed_operation,
)
from .ffmpeg_helpers import _validate_input_path, _escape_ffmpeg_filter_value
from .models import EditResult, SplitLayout


def split_screen(
    left_path: str,
    right_path: str,
    layout: SplitLayout = "side-by-side",
    output_path: str | None = None,
) -> EditResult:
    """Place two videos side by side or top/bottom.

    Args:
        left_path: Path to the first video.
        right_path: Path to the second video.
        layout: 'side-by-side' or 'top-bottom'.
        output_path: Where to save the output.
    """
    _validate_input_path(left_path)
    _validate_input_path(right_path)
    output = output_path or _auto_output(left_path, f"split_{layout}")

    left_info = probe(left_path)
    right_info = probe(right_path)
    filter_complex = _split_filter(left_info.width, left_info.height, right_info.width, right_info.height, layout)

    with _timed_operation() as timing:
        _run_ffmpeg(
            [
                "-i",
                left_path,
                "-i",
                right_path,
                "-filter_complex",
                filter_complex,
                "-map",
                "[v]",
                "-map",
                "0:a?",
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

    info = probe(output)
    return EditResult(
        output_path=output,
        duration=info.duration,
        resolution=info.resolution,
        size_mb=info.size_mb,
        format="mp4",
        operation=f"split_screen_{layout}",
        elapsed_ms=timing["elapsed_ms"],
    )


def _split_filter(left_width: int, left_height: int, right_width: int, right_height: int, layout: SplitLayout) -> str:
    if layout == "side-by-side":
        target_h = _safe_dimension(max(left_height, right_height), "target_h")
        if left_height != right_height:
            return (
                f"[0:v]scale=-1:{target_h},setsar=1[left];"
                f"[1:v]scale=-1:{target_h},setsar=1[right];"
                f"[left][right]hstack=inputs=2[v]"
            )
        return "[0:v][1:v]hstack=inputs=2[v]"

    target_w = _safe_dimension(max(left_width, right_width), "target_w")
    if left_width != right_width:
        return (
            f"[0:v]scale={target_w}:-1,setsar=1[top];"
            f"[1:v]scale={target_w}:-1,setsar=1[bottom];"
            f"[top][bottom]vstack=inputs=2[v]"
        )
    return "[0:v][1:v]vstack=inputs=2[v]"


def _safe_dimension(value: int, name: str) -> str:
    return _escape_ffmpeg_filter_value(str(_sanitize_ffmpeg_number(value, name)))
