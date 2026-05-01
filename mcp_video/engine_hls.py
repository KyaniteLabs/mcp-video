"""HLS/DASH streaming segment generation for the FFmpeg engine."""

from __future__ import annotations

import os

from .engine_probe import probe
from .engine_runtime_utils import _build_edit_result, _timed_operation
from .ffmpeg_helpers import _run_ffmpeg
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
    _info = probe(input_path)

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

        # Write a master playlist that references all variants
        master_lines = ["#EXTM3U"]
        for quality in qualities:
            q_dir = os.path.join(output_dir, quality)
            variant_playlist = os.path.join(q_dir, "playlist.m3u8")
            if os.path.isfile(variant_playlist):
                # Infer bandwidth roughly from height
                height_map = {"low": 480, "medium": 720, "high": 1080, "ultra": 1080}
                bw = height_map.get(quality, 1080) * 3000  # rough kbps
                master_lines.append(f"#EXT-X-STREAM-INF:BANDWIDTH={bw}")
                master_lines.append(os.path.join(quality, "playlist.m3u8"))
        with open(playlist_path, "w") as f:
            f.write("\n".join(master_lines) + "\n")

    return _build_edit_result(
        playlist_path,
        "hls_segment",
        timing,
        format="hls",
    )
