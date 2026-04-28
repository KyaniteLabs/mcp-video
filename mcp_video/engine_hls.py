"""HLS/DASH streaming segment generation for the FFmpeg engine."""

from __future__ import annotations

import os

from .engine_probe import probe
from .engine_runtime_utils import _run_ffmpeg, _timed_operation
from .ffmpeg_helpers import _validate_input_path
from .models import EditResult


def hls_segment(
    input_path: str,
    output_dir: str | None = None,
    segment_duration: int = 4,
    playlist_name: str = "playlist.m3u8",
    qualities: list[str] | None = None,
) -> EditResult:
    """Segment a video into HLS (HTTP Live Streaming) format.

    Args:
        input_path: Path to the input video.
        output_dir: Directory to save segments. Auto-generated if omitted.
        segment_duration: Target segment duration in seconds (default 4).
        playlist_name: Name of the master playlist file.
        qualities: List of quality levels to generate (e.g. ["low", "medium", "high"]).
            Default is a single high-quality variant.

    Returns:
        EditResult with the playlist path as ``output_path``.
    """
    input_path = _validate_input_path(input_path)
    info = probe(input_path)

    if output_dir is None:
        base, _ = os.path.splitext(input_path)
        output_dir = f"{base}_hls"
    os.makedirs(output_dir, exist_ok=True)

    playlist_path = os.path.join(output_dir, playlist_name)
    qualities = qualities or ["high"]

    with _timed_operation() as timing:
        for quality in qualities:
            q_dir = os.path.join(output_dir, quality)
            os.makedirs(q_dir, exist_ok=True)

            # Map quality to scale height
            height_map = {"low": 480, "medium": 720, "high": 1080, "ultra": 1080}
            target_h = height_map.get(quality, 1080)
            scale_filter = f"scale=-2:{target_h}"

            _run_ffmpeg(
                [
                    "-i",
                    input_path,
                    "-vf",
                    scale_filter,
                    "-c:v",
                    "libx264",
                    "-crf",
                    "23",
                    "-preset",
                    "fast",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "128k",
                    "-f",
                    "hls",
                    "-hls_time",
                    str(segment_duration),
                    "-hls_playlist_type",
                    "vod",
                    "-hls_segment_filename",
                    os.path.join(q_dir, "segment_%03d.ts"),
                    os.path.join(q_dir, "playlist.m3u8"),
                ]
            )

    return EditResult(
        output_path=playlist_path,
        duration=info.duration,
        resolution=info.resolution,
        format="hls",
        operation="hls_segment",
        elapsed_ms=timing["elapsed_ms"],
    )
