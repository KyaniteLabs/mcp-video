"""Playback speed operations for the FFmpeg engine."""

from __future__ import annotations

from .defaults import DEFAULT_AUDIO_BITRATE
from .ffmpeg_helpers import _validate_input_path
from .engine_probe import probe
from .engine_runtime_utils import _auto_output, _movflags_args, _run_ffmpeg, _timed_operation
from .errors import MCPVideoError
from .limits import MAX_SPEED_CHAIN_COUNT
from .models import EditResult


def speed(
    input_path: str,
    factor: float = 1.0,
    output_path: str | None = None,
) -> EditResult:
    """Change playback speed. factor > 1 = faster, < 1 = slower."""
    _validate_input_path(input_path)
    if factor <= 0:
        raise MCPVideoError("Speed factor must be positive")

    output = output_path or _auto_output(input_path, f"speed_{factor}x")

    # Use setpts for video, atempo for audio
    video_filter = f"setpts={1 / factor}*PTS"
    audio_filter = f"atempo={factor}"

    # atempo only supports 0.5 to 100.0; chain if needed
    if factor < 0.5:
        chain_count = 2
        while factor ** (1 / chain_count) < 0.5:
            chain_count += 1
            if chain_count > MAX_SPEED_CHAIN_COUNT:
                raise MCPVideoError(
                    "Speed factor too extreme: would require more than 20 atempo filters",
                    error_type="validation_error",
                    code="invalid_parameter",
                )
        tempo_val = factor ** (1 / chain_count)
        audio_filter = ",".join([f"atempo={tempo_val}"] * chain_count)
    elif factor > 100:
        chain_count = 2
        while factor ** (1 / chain_count) > 100:
            chain_count += 1
            if chain_count > MAX_SPEED_CHAIN_COUNT:
                raise MCPVideoError(
                    "Speed factor too extreme: would require more than 20 atempo filters",
                    error_type="validation_error",
                    code="invalid_parameter",
                )
        tempo_val = factor ** (1 / chain_count)
        audio_filter = ",".join([f"atempo={tempo_val}"] * chain_count)

    # Check if input has audio
    info = probe(input_path)
    has_audio = info.audio_codec is not None

    with _timed_operation() as timing:
        if has_audio:
            _run_ffmpeg(
                [
                    "-i",
                    input_path,
                    "-filter_complex",
                    f"[0:v]{video_filter}[v];[0:a]{audio_filter}[a]",
                    "-map",
                    "[v]",
                    "-map",
                    "[a]",
                    "-c:v",
                    "libx264",
                    "-preset",
                    "fast",
                    "-crf",
                    "23",
                    "-c:a",
                    "aac",
                    "-b:a",
                    DEFAULT_AUDIO_BITRATE,
                    *_movflags_args(output),
                    output,
                ]
            )
        else:
            _run_ffmpeg(
                [
                    "-i",
                    input_path,
                    "-vf",
                    video_filter,
                    "-an",
                    "-c:v",
                    "libx264",
                    "-preset",
                    "fast",
                    "-crf",
                    "23",
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
        operation="speed",
        elapsed_ms=timing["elapsed_ms"],
    )
