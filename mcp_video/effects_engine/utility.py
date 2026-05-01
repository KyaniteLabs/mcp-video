"""Video effects and filters engine.

Visual effects using FFmpeg filters and PIL for custom processing.
"""

from __future__ import annotations

import logging
import subprocess
from typing import Any

from ..errors import MCPVideoError
from ..ffmpeg_helpers import _validate_input_path, _run_command, _run_ffmpeg

logger = logging.getLogger(__name__)


def video_info_detailed(video: str) -> dict[str, Any]:
    """Get extended video metadata.

    Args:
        video: Video file path

    Returns:
        Dict with duration, fps, resolution, bitrate, has_audio,
        scene_changes, dominant_colors
    """
    import json

    video = _validate_input_path(video)

    # Get basic info
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_format",
        "-show_streams",
        "-print_format",
        "json",
        video,
    ]

    result = _run_ffmpeg(cmd)
    data = json.loads(result.stdout)

    # Extract video stream info
    video_stream = None
    audio_stream = None

    for stream in data.get("streams", []):
        if stream["codec_type"] == "video":
            video_stream = stream
        elif stream["codec_type"] == "audio":
            audio_stream = stream

    if not video_stream:
        raise MCPVideoError("No video stream found", error_type="processing_error", code="no_video_stream")

    # Calculate duration
    duration = float(video_stream.get("duration", 0) or data.get("format", {}).get("duration", 0))

    # Calculate FPS
    fps_str = video_stream.get("r_frame_rate", "30/1")
    if "/" in fps_str:
        num, den = map(int, fps_str.split("/"))
        fps = num / den if den else 30
    else:
        fps = float(fps_str)

    resolution = [video_stream.get("width", 0), video_stream.get("height", 0)]
    bitrate = int(data.get("format", {}).get("bit_rate", 0))

    # Try to detect scene changes
    scene_changes = []
    try:
        scene_cmd = [
            "ffmpeg",
            "-i",
            video,
            "-filter:v",
            "select='gt(scene,0.3)',showinfo",
            "-f",
            "null",
            "-",
        ]
        scene_result = subprocess.run(scene_cmd, capture_output=True, text=True, timeout=30)
        # Parse scene change timestamps from stderr
        for line in scene_result.stderr.split("\n"):
            if "pts_time:" in line:
                # Extract timestamp
                parts = line.split("pts_time:")
                if len(parts) > 1:
                    try:
                        ts = float(parts[1].split()[0])
                        scene_changes.append(ts)
                    except (ValueError, IndexError):
                        pass
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning("Scene detection failed (optional): %s", e)

    return {
        "duration": duration,
        "fps": fps,
        "resolution": resolution,
        "bitrate": bitrate,
        "has_audio": audio_stream is not None,
        "scene_changes": scene_changes[:10],  # Limit to first 10
        "dominant_colors": None,  # Frame analysis not yet implemented
    }


def auto_chapters(
    video: str,
    threshold: float = 0.3,
) -> list[tuple[float, str]]:
    """Auto-detect scene changes and create chapters.

    Args:
        video: Video file path
        threshold: Scene change detection threshold

    Returns:
        List of (timestamp, description) tuples

    Raises:
        MCPVideoError: If *threshold* is not a number in [0.0, 1.0].
    """
    video = _validate_input_path(video)

    if not isinstance(threshold, (int, float)) or not (0.0 <= threshold <= 1.0):
        raise MCPVideoError(f"threshold must be a number between 0.0 and 1.0, got {threshold!r}")

    chapters = []

    cmd = [
        "ffmpeg",
        "-i",
        video,
        "-filter:v",
        f"select='gt(scene,{threshold})',showinfo",
        "-f",
        "null",
        "-",
    ]

    result = _run_command(cmd, timeout=60)

    chapter_num = 1
    for line in result.stderr.split("\n"):
        if "pts_time:" in line:
            parts = line.split("pts_time:")
            if len(parts) > 1:
                try:
                    ts = float(parts[1].split()[0])
                    chapters.append((ts, f"Chapter {chapter_num}"))
                    chapter_num += 1
                except (ValueError, IndexError):
                    pass

    return chapters
