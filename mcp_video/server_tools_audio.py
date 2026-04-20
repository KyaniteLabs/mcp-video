"""Audio MCP tool registrations."""

from __future__ import annotations

import os
import tempfile
from typing import Any

from .errors import MCPVideoError
from .limits import MAX_FREQUENCY, MIN_FREQUENCY
from .server_app import _error_result, _result, mcp
from .validation import (
    VALID_AUDIO_EFFECT_TYPES,
    VALID_AUDIO_PRESETS,
    VALID_AUDIO_SEQUENCE_TYPES,
    VALID_SPATIAL_METHODS,
    VALID_WAVEFORMS,
)


@mcp.tool()
def audio_synthesize(
    output_path: str | None = None,
    waveform: str = "sine",
    frequency: float = 440.0,
    duration: float = 1.0,
    volume: float = 0.5,
    effects: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate audio procedurally using synthesis.

    Creates WAV files from scratch using mathematical waveforms. No external audio
    files needed. Supports envelopes, reverb, filtering, and fade effects.

    Args:
        output_path: Absolute path for the output WAV file.
        waveform: Waveform type (sine, square, sawtooth, triangle, noise). Default sine.
        frequency: Base frequency in Hz. Default 440 (A4 note).
        duration: Duration in seconds. Default 1.0.
        volume: Amplitude 0-1. Default 0.5.
        effects: Optional effects dict with keys:
            - envelope: {"attack", "decay", "sustain", "release"} in seconds
            - fade_in: Fade in duration in seconds
            - fade_out: Fade out duration in seconds
            - reverb: {"room_size", "damping", "wet_level"}
            - lowpass: Cutoff frequency in Hz

    Returns:
        Dict with success status and output_path.
    """
    if waveform not in VALID_WAVEFORMS:
        return _error_result(
            MCPVideoError(
                f"Invalid waveform: must be one of {sorted(VALID_WAVEFORMS)}, got '{waveform}'",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if frequency < MIN_FREQUENCY or frequency > MAX_FREQUENCY:
        return _error_result(
            MCPVideoError(
                f"Invalid frequency: must be {MIN_FREQUENCY}-{MAX_FREQUENCY}, got {frequency}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if duration <= 0:
        return _error_result(
            MCPVideoError(
                f"Invalid duration: must be > 0, got {duration}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if volume < 0 or volume > 1:
        return _error_result(
            MCPVideoError(
                f"Invalid volume: must be 0-1, got {volume}", error_type="validation_error", code="invalid_parameter"
            )
        )
    output = output_path or os.path.join(tempfile.gettempdir(), f"mcp_audio_{waveform}.wav")
    try:
        from .audio_engine import audio_synthesize as _synth

        return _result(
            _synth(
                output=output,
                waveform=waveform,
                frequency=frequency,
                duration=duration,
                volume=volume,
                effects=effects,
            )
        )
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def audio_preset(
    preset: str,
    output_path: str | None = None,
    pitch: str = "mid",
    duration: float | None = None,
    intensity: float = 0.5,
) -> dict[str, Any]:
    """Generate preset sound design elements.

    Pre-configured sound effects for common use cases. No external audio files needed.

    Available presets:
    - UI: ui-blip, ui-click, ui-tap, ui-whoosh-up, ui-whoosh-down
    - Ambient: drone-low, drone-mid, drone-tech
    - Notifications: chime-success, chime-error, chime-notification
    - Data: typing, scan, processing, data-flow

    Args:
        preset: Preset name from the list above.
        output_path: Absolute path for the output WAV file.
        pitch: Pitch variation (low, mid, high). Default mid.
        duration: Override default duration (seconds).
        intensity: Effect intensity 0-1. Default 0.5.

    Returns:
        Dict with success status and output_path.
    """
    if preset not in VALID_AUDIO_PRESETS:
        return _error_result(
            MCPVideoError(
                f"Invalid preset: must be one of {sorted(VALID_AUDIO_PRESETS)}, got '{preset}'",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if pitch not in {"low", "mid", "high"}:
        return _error_result(
            MCPVideoError(
                f"Invalid pitch: must be one of ['high', 'low', 'mid'], got '{pitch}'",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if intensity < 0 or intensity > 1:
        return _error_result(
            MCPVideoError(
                f"Invalid intensity: must be 0-1, got {intensity}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if duration is not None and duration <= 0:
        return _error_result(
            MCPVideoError(
                f"Invalid duration: must be > 0, got {duration}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    output = output_path or os.path.join(tempfile.gettempdir(), f"mcp_audio_{preset}.wav")
    try:
        from .audio_engine import audio_preset as _preset

        return _result(
            _preset(
                preset=preset,
                output=output,
                pitch=pitch,
                duration=duration,
                intensity=intensity,
            )
        )
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def audio_sequence(
    sequence: list[dict[str, Any]],
    output_path: str,
) -> dict[str, Any]:
    """Compose multiple audio events into a timed sequence.

    Creates a layered audio track from multiple timed sound events.

    Args:
        sequence: List of audio events, each with:
            - type: "tone", "preset", or "whoosh"
            - at: Start time in seconds
            - duration: Event duration in seconds
            - freq/frequency: For tones (Hz)
            - name: For presets (preset name)
            - volume: 0-1 amplitude
            - waveform: For tones (sine, square, etc.)
        output_path: Absolute path for the output WAV file.

    Returns:
        Dict with success status and output_path.
    """
    if not isinstance(sequence, list) or len(sequence) < 1:
        return _error_result(
            MCPVideoError(
                "Invalid sequence: must be a non-empty list", error_type="validation_error", code="invalid_parameter"
            )
        )
    for i, event in enumerate(sequence):
        if not isinstance(event, dict):
            return _error_result(
                MCPVideoError(
                    f"Invalid sequence[{i}]: must be a dict", error_type="validation_error", code="invalid_parameter"
                )
            )
        evt_type = event.get("type")
        if evt_type not in VALID_AUDIO_SEQUENCE_TYPES:
            return _error_result(
                MCPVideoError(
                    f"Invalid sequence[{i}].type: must be one of {sorted(VALID_AUDIO_SEQUENCE_TYPES)}, got '{evt_type}'",
                    error_type="validation_error",
                    code="invalid_parameter",
                )
            )
        evt_at = event.get("at")
        if not isinstance(evt_at, (int, float)):
            return _error_result(
                MCPVideoError(
                    f"Invalid sequence[{i}].at: must be numeric, got {type(evt_at).__name__}",
                    error_type="validation_error",
                    code="invalid_parameter",
                )
            )
        evt_dur = event.get("duration")
        if evt_dur is not None and evt_dur <= 0:
            return _error_result(
                MCPVideoError(
                    f"Invalid sequence[{i}].duration: must be > 0, got {evt_dur}",
                    error_type="validation_error",
                    code="invalid_parameter",
                )
            )
    try:
        from .audio_engine import audio_sequence as _sequence

        return _result(_sequence(sequence=sequence, output=output_path))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def audio_compose(
    tracks: list[dict[str, Any]],
    duration: float,
    output_path: str,
) -> dict[str, Any]:
    """Layer multiple audio tracks with volume mixing.

    Mix multiple WAV files together with individual volume control.

    Args:
        tracks: List of track configs with:
            - file: Absolute path to WAV file
            - volume: Volume multiplier 0-1
            - start: Start time offset in seconds
            - loop: Whether to loop the track (default false)
        duration: Total output duration in seconds.
        output_path: Absolute path for the output WAV file.

    Returns:
        Dict with success status and output_path.
    """
    if duration <= 0:
        return _error_result(
            MCPVideoError(
                f"Invalid duration: must be > 0, got {duration}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if not isinstance(tracks, list) or len(tracks) < 1:
        return _error_result(
            MCPVideoError(
                "Invalid tracks: must be a non-empty list", error_type="validation_error", code="invalid_parameter"
            )
        )
    for i, track in enumerate(tracks):
        if not isinstance(track, dict):
            return _error_result(
                MCPVideoError(
                    f"Invalid tracks[{i}]: must be a dict", error_type="validation_error", code="invalid_parameter"
                )
            )
        if not isinstance(track.get("file"), str):
            return _error_result(
                MCPVideoError(
                    f"Invalid tracks[{i}].file: must be a string",
                    error_type="validation_error",
                    code="invalid_parameter",
                )
            )
        vol = track.get("volume", 1.0)
        if vol < 0 or vol > 1:
            return _error_result(
                MCPVideoError(
                    f"Invalid tracks[{i}].volume: must be 0-1, got {vol}",
                    error_type="validation_error",
                    code="invalid_parameter",
                )
            )
    try:
        from .audio_engine import audio_compose as _compose

        return _result(_compose(tracks=tracks, duration=duration, output=output_path))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def audio_effects(
    input_path: str,
    output_path: str,
    effects: list[dict[str, Any]],
) -> dict[str, Any]:
    """Apply audio effects chain to a WAV file.

    Process audio through a chain of effects like reverb, filtering, normalization.

    Args:
        input_path: Absolute path to input WAV file.
        output_path: Absolute path for output WAV file.
        effects: List of effect configs with:
            - type: "lowpass", "reverb", "normalize", "fade"
            - Additional params per effect type

    Returns:
        Dict with success status and output_path.
    """
    if not isinstance(effects, list) or len(effects) < 1:
        return _error_result(
            MCPVideoError(
                "Invalid effects: must be a non-empty list", error_type="validation_error", code="invalid_parameter"
            )
        )
    for i, effect in enumerate(effects):
        if not isinstance(effect, dict):
            return _error_result(
                MCPVideoError(
                    f"Invalid effects[{i}]: must be a dict", error_type="validation_error", code="invalid_parameter"
                )
            )
        eff_type = effect.get("type")
        if eff_type not in VALID_AUDIO_EFFECT_TYPES:
            return _error_result(
                MCPVideoError(
                    f"Invalid effects[{i}].type: must be one of {sorted(VALID_AUDIO_EFFECT_TYPES)}, got '{eff_type}'",
                    error_type="validation_error",
                    code="invalid_parameter",
                )
            )
    try:
        from .audio_engine import audio_effects as _effects

        return _result(_effects(input_path=input_path, output=output_path, effects=effects))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_add_generated_audio(
    input_path: str,
    audio_config: dict[str, Any],
    output_path: str,
) -> dict[str, Any]:
    """Add procedurally generated audio to a video.

    One-shot convenience function to generate and add audio to video.

    Args:
        input_path: Absolute path to input video.
        audio_config: Configuration dict with:
            - drone: {"frequency", "volume"} for background tone
            - events: List of timed sound events
        output_path: Absolute path for output video.

    Returns:
        Dict with success status and output_path.
    """
    try:
        if not isinstance(audio_config, dict) or not audio_config:
            raise MCPVideoError(
                "audio_config must be a non-empty dict",
                error_type="validation_error",
                code="invalid_parameter",
            )
        from .audio_engine import add_generated_audio as _add_gen_audio

        return _result(_add_gen_audio(input_path, audio_config, output_path))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_audio_spatial(
    input_path: str,
    output_path: str,
    positions: list[dict],
    method: str = "hrtf",
) -> dict[str, Any]:
    """Apply 3D spatial audio positioning."""
    if method not in VALID_SPATIAL_METHODS:
        return _error_result(
            MCPVideoError(
                f"Invalid method: must be one of {sorted(VALID_SPATIAL_METHODS)}, got '{method}'",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if not isinstance(positions, list) or len(positions) == 0:
        return _error_result(
            MCPVideoError(
                "positions must be a non-empty list",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    try:
        from .ai_engine import audio_spatial

        return _result(audio_spatial(input_path, output_path, positions, method))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)
