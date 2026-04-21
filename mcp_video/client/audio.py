"""mcp-video Python client — clean API for programmatic video editing."""

from __future__ import annotations

from ..errors import MCPVideoError

from typing import Literal

from ..engine import (
    audio_waveform as _audio_waveform,
)
from ..models import (
    WaveformResult,
)


class ClientAudioMixin:
    """Audio operations mixin."""

    def audio_waveform(
        self,
        video: str,
        bins: int = 50,
    ) -> WaveformResult:
        """Extract audio waveform data (peaks and silence regions)."""
        return _audio_waveform(video, bins=bins)

    def audio_synthesize(
        self,
        output: str,
        waveform: Literal["sine", "square", "sawtooth", "triangle", "noise"] = "sine",
        frequency: float = 440.0,
        duration: float = 1.0,
        volume: float = 0.5,
        effects: dict | None = None,
    ) -> str:
        """Generate audio procedurally using synthesis.

        Args:
            output: Output WAV file path
            waveform: Type of waveform (sine, square, sawtooth, triangle, noise)
            frequency: Base frequency in Hz
            duration: Duration in seconds
            volume: Amplitude (0-1)
            effects: Optional effects dict with envelope, fade_in, fade_out, reverb, lowpass

        Returns:
            Path to generated WAV file
        """
        from ..audio_engine import audio_synthesize

        return audio_synthesize(
            output=output,
            waveform=waveform,
            frequency=frequency,
            duration=duration,
            volume=volume,
            effects=effects,
        )

    def audio_preset(
        self,
        preset: str,
        output: str,
        pitch: Literal["low", "mid", "high"] = "mid",
        duration: float | None = None,
        intensity: float = 0.5,
    ) -> str:
        """Generate preset sound design elements.

        Presets: ui-blip, ui-click, ui-tap, ui-whoosh-up, ui-whoosh-down,
                 drone-low, drone-mid, drone-tech, drone-ominous,
                 chime-success, chime-error, chime-notification,
                 typing, scan, processing, data-flow,
                 upload, download

        Returns:
            Path to generated WAV file
        """
        from ..audio_engine import audio_preset

        return audio_preset(
            preset=preset,
            output=output,
            pitch=pitch,
            duration=duration,
            intensity=intensity,
        )

    def audio_sequence(
        self,
        sequence: list[dict],
        output: str,
    ) -> str:
        """Compose multiple audio events into a timed sequence.

        Args:
            sequence: List of audio events with type, at (time), duration, etc.
            output: Output WAV file path

        Returns:
            Path to generated WAV file
        """
        if not sequence:
            raise MCPVideoError("sequence cannot be empty", error_type="validation_error", code="empty_sequence")
        from ..audio_engine import audio_sequence

        return audio_sequence(sequence=sequence, output=output)

    def audio_compose(
        self,
        tracks: list[dict],
        duration: float,
        output: str,
    ) -> str:
        """Layer multiple audio tracks with mixing.

        Args:
            tracks: List of track configs. Each dict has keys:
                - file (str): Absolute path to WAV file (required)
                - volume (float): Volume multiplier 0-1 (default 1.0)
                - start (float): Start time offset in seconds (default 0.0)
                - loop (bool): Whether to loop the track (default False)
            duration: Total duration of output in seconds
            output: Output WAV file path

        CLI equivalent: mcp-video audio-compose --tracks '<json>' ...

        Returns:
            Path to generated WAV file
        """
        from ..audio_engine import audio_compose

        return audio_compose(tracks=tracks, duration=duration, output=output)

    def audio_effects(
        self,
        input_path: str,
        output: str,
        effects: list[dict],
    ) -> str:
        """Apply audio effects chain.

        Args:
            input_path: Input WAV file path
            output: Output WAV file path
            effects: List of effect configs with type and parameters

        Returns:
            Path to processed WAV file
        """
        from ..audio_engine import audio_effects

        return audio_effects(input_path=input_path, output=output, effects=effects)

    def add_generated_audio(
        self,
        video: str,
        audio_config: dict,
        output: str,
    ) -> str:
        """Add generated audio to a video file.

        Args:
            video: Input video path
            audio_config: Configuration with drone and/or events
            output: Output video path

        Returns:
            Path to output video
        """
        from ..audio_engine import add_generated_audio

        return add_generated_audio(video=video, audio_config=audio_config, output=output)

    # ------------------------------------------------------------------
    # Visual Effects (P1 Features)
    # ------------------------------------------------------------------

    def audio_spatial(self, video: str, output: str, positions: list[dict], method: str = "hrtf") -> str:
        """Apply 3D spatial audio positioning."""
        from ..ai_engine import audio_spatial

        return audio_spatial(video, output, positions, method)
