"""Audio synthesis and sound design engine.

Pure NumPy-based audio generation with no external dependencies.
"""

from __future__ import annotations

import math
import os
import struct
import tempfile
import wave
from pathlib import Path
from typing import Any, Literal

from ..defaults import DEFAULT_FFMPEG_TIMEOUT
from ..errors import InputFileError, MCPVideoError, ProcessingError

# ---------------------------------------------------------------------------
# Audio Constants
# ---------------------------------------------------------------------------

DEFAULT_SAMPLE_RATE = 44100
DEFAULT_CHANNELS = 1
DEFAULT_SAMPLE_WIDTH = 2  # 16-bit

# Re-exports for backward compatibility
from .core import (
    apply_envelope,
    apply_fade,
    apply_highpass,
    apply_lowpass,
    apply_reverb,
    generate_noise,
    generate_sawtooth,
    generate_sine,
    generate_square,
    generate_triangle,
    write_wav,
)
from .sequencing import audio_compose, audio_effects, audio_sequence
from .synthesis import audio_preset, audio_synthesize

def add_generated_audio(
    video: str,
    audio_config: dict[str, Any],
    output: str,
) -> str:
    """Add generated audio to a video file.

    Args:
        video: Input video path
        audio_config: Configuration dict with:
            - drone: {"frequency", "volume"} for background drone
            - events: List of timed events [{"type", "at", ...}]
        output: Output video path

    Returns:
        Path to output video
    """
    import subprocess
    import tempfile

    # Generate audio sequence
    events = audio_config.get("events", [])

    # Add drone if specified
    drone_config = audio_config.get("drone")
    if drone_config:
        events.insert(
            0,
            {
                "type": "tone",
                "at": 0,
                "duration": 60,  # Will be truncated to video length
                "freq": drone_config.get("frequency", 100),
                "volume": drone_config.get("volume", 0.2),
                "waveform": "sine",
            },
        )

    if not events:
        raise MCPVideoError("No audio events specified", error_type="validation_error", code="invalid_parameter")

    # Create temp audio file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        audio_path = tmp.name

    # Input validation before FFmpeg
    if "\x00" in video:
        raise InputFileError(video, "Path contains null bytes")
    if not os.path.isfile(video):
        raise InputFileError(video)

    try:
        # Generate audio
        audio_sequence(events, audio_path)

        # Mix with video using FFmpeg
        out_dir = os.path.dirname(output)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            video,
            "-i",
            audio_path,
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-shortest",
            output,
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=DEFAULT_FFMPEG_TIMEOUT)
        except subprocess.TimeoutExpired:
            raise ProcessingError(" ".join(cmd), -1, f"Audio processing command timed out after {DEFAULT_FFMPEG_TIMEOUT}s") from None
        if result.returncode != 0:
            raise ProcessingError(" ".join(cmd), result.returncode, result.stderr)

        return output

    finally:
        Path(audio_path).unlink(missing_ok=True)
