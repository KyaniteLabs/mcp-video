"""Probe helpers for the FFmpeg engine."""

from __future__ import annotations

import os

from .errors import InputFileError, MCPVideoError
from .ffmpeg_helpers import _run_ffprobe_json, _validate_input_path
from .models import VideoInfo
from .engine_runtime_utils import _get_audio_stream, _get_video_stream
from .limits import MAX_VIDEO_DURATION

# ---------------------------------------------------------------------------
# Probe cache — keyed by (path, mtime, size) so stale data is never returned
# ---------------------------------------------------------------------------

_probe_cache: dict[tuple[str, float, int], VideoInfo] = {}
_MAX_PROBE_CACHE = 256


def _cache_key(path: str) -> tuple[str, float, int]:
    stat = os.stat(path)
    return (path, stat.st_mtime, stat.st_size)


def _parse_probe_duration(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _build_video_info(path: str, data: dict) -> VideoInfo:
    """Construct a VideoInfo from raw ffprobe JSON data."""
    vs = _get_video_stream(data)
    if vs is None:
        raise InputFileError(path, "No video stream found")

    # Duration: prefer container duration, then fall back to the video stream.
    duration = _parse_probe_duration(data.get("format", {}).get("duration"))
    if duration is None:
        duration = _parse_probe_duration(vs.get("duration")) or 0.0
    if duration > MAX_VIDEO_DURATION:
        raise MCPVideoError(
            f"Video duration ({duration:.0f}s) exceeds maximum of {MAX_VIDEO_DURATION}s",
            error_type="validation_error",
            code="duration_too_long",
        )

    # Resolution
    try:
        width = int(vs.get("width", 0))
        height = int(vs.get("height", 0))
    except (ValueError, TypeError):
        width = height = 0

    # FPS — r_frame_rate is "num/den"
    rfr = vs.get("r_frame_rate", "30/1")
    try:
        if "/" in rfr:
            num, den = rfr.split("/")
            den_val = float(den)
            fps = float(num) / den_val if den_val != 0 else 30.0
        else:
            fps = float(rfr) if float(rfr) != 0 else 30.0
    except (ValueError, ZeroDivisionError):
        fps = 30.0

    # Codecs
    codec = vs.get("codec_name", "unknown")
    audio_s = _get_audio_stream(data)
    audio_codec = audio_s.get("codec_name") if audio_s else None
    audio_sr = int(audio_s.get("sample_rate", 0)) if audio_s else None

    # Bitrate / size
    fmt = data.get("format", {})
    try:
        bitrate = int(fmt.get("bit_rate", 0)) or None
        size_bytes = int(fmt.get("size", 0)) or None
    except (ValueError, TypeError):
        bitrate = size_bytes = None
    fmt_name = fmt.get("format_name")

    return VideoInfo(
        path=path,
        duration=duration,
        width=width,
        height=height,
        fps=fps,
        codec=codec,
        audio_codec=audio_codec,
        audio_sample_rate=audio_sr,
        bitrate=bitrate,
        size_bytes=size_bytes,
        format=fmt_name,
    )


def probe(path: str) -> VideoInfo:
    """Get metadata about a video file using ffprobe.

    Results are cached by (path, mtime, size) so repeated calls on the
    same unmodified file skip the ffprobe subprocess.
    """
    _validate_input_path(path)
    key = _cache_key(path)

    cached = _probe_cache.get(key)
    if cached is not None:
        return cached

    data = _run_ffprobe_json(path)
    info = _build_video_info(path, data)

    # Evict oldest entries when cache is full
    if len(_probe_cache) >= _MAX_PROBE_CACHE:
        _probe_cache.pop(next(iter(_probe_cache)))
    _probe_cache[key] = info

    return info


def invalidate_probe_cache(path: str | None = None) -> None:
    """Drop cached probe data. Pass a path to evict one entry, or None for all."""
    if path is None:
        _probe_cache.clear()
    else:
        keys_to_remove = [k for k in _probe_cache if k[0] == path]
        for k in keys_to_remove:
            del _probe_cache[k]


def get_duration(path: str) -> float:
    """Get duration of a video in seconds."""
    return probe(path).duration
