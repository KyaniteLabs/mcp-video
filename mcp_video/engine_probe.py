"""Probe helpers for the FFmpeg engine."""

from __future__ import annotations

from .errors import InputFileError
from .ffmpeg_helpers import _run_ffprobe_json
from .models import VideoInfo
from .engine_runtime_utils import _get_audio_stream, _get_video_stream, _validate_input

# ---------------------------------------------------------------------------
# Probe
# ---------------------------------------------------------------------------


def probe(path: str) -> VideoInfo:
    """Get metadata about a video file using ffprobe."""
    _validate_input(path)
    data = _run_ffprobe_json(path)

    vs = _get_video_stream(data)
    if vs is None:
        raise InputFileError(path, "No video stream found")

    # Duration
    duration = float(data.get("format", {}).get("duration", 0) or vs.get("duration", 0))

    # Resolution
    width = int(vs.get("width", 0))
    height = int(vs.get("height", 0))

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
    bitrate = int(fmt.get("bit_rate", 0)) or None
    size_bytes = int(fmt.get("size", 0)) or None
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


def get_duration(path: str) -> float:
    """Get duration of a video in seconds."""
    return probe(path).duration
