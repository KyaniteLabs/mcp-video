"""Audio synthesis and sound design engine.

Pure NumPy-based audio generation with no external dependencies.
"""

from __future__ import annotations

from typing import Any, Literal

from ..errors import MCPVideoError

from .core import (
    _float_to_pcm,
    _pcm_to_float,
    apply_envelope,
    apply_fade,
    apply_lowpass,
    apply_reverb,
    generate_noise,
    generate_sawtooth,
    generate_sine,
    generate_square,
    generate_triangle,
    write_wav,
)

# ---------------------------------------------------------------------------
# Audio Constants
# ---------------------------------------------------------------------------

DEFAULT_SAMPLE_RATE = 44100
DEFAULT_CHANNELS = 1
DEFAULT_SAMPLE_WIDTH = 2  # 16-bit


def audio_synthesize(
    output: str,
    waveform: Literal["sine", "square", "sawtooth", "triangle", "noise"] = "sine",
    frequency: float = 440.0,
    duration: float = 1.0,
    volume: float = 0.5,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    effects: dict[str, Any] | None = None,
) -> str:
    """Generate audio procedurally using synthesis.

    Args:
        output: Output WAV file path
        waveform: Type of waveform to generate
        frequency: Base frequency in Hz
        duration: Duration in seconds
        volume: Amplitude (0-1)
        sample_rate: Sample rate in Hz
        effects: Optional effects dictionary with keys:
            - envelope: {"attack", "decay", "sustain", "release"}
            - fade_in: seconds
            - fade_out: seconds
            - reverb: {"room_size", "damping", "wet_level"}
            - lowpass: cutoff frequency

    Returns:
        Path to generated WAV file
    """
    from ..limits import MAX_AUDIO_DURATION, MIN_FREQUENCY, MAX_FREQUENCY, MIN_SAMPLE_RATE, MAX_SAMPLE_RATE

    if not (MIN_FREQUENCY <= frequency <= MAX_FREQUENCY):
        raise MCPVideoError(
            f"Frequency must be between {MIN_FREQUENCY} and {MAX_FREQUENCY} Hz, got {frequency}",
            error_type="validation_error",
            code="invalid_parameter",
        )
    if not (0.01 <= duration <= MAX_AUDIO_DURATION):
        raise MCPVideoError(
            f"Duration must be between 0.01 and {MAX_AUDIO_DURATION} seconds, got {duration}",
            error_type="validation_error",
            code="invalid_parameter",
        )
    if not (0.0 <= volume <= 1.0):
        raise MCPVideoError(
            f"Volume must be between 0.0 and 1.0, got {volume}", error_type="validation_error", code="invalid_parameter"
        )
    if not (MIN_SAMPLE_RATE <= sample_rate <= MAX_SAMPLE_RATE):
        raise MCPVideoError(
            f"Sample rate must be between {MIN_SAMPLE_RATE} and {MAX_SAMPLE_RATE}, got {sample_rate}",
            error_type="validation_error",
            code="invalid_parameter",
        )
    # Generate base waveform
    if waveform == "sine":
        pcm_data = generate_sine(frequency, duration, sample_rate, volume)
    elif waveform == "square":
        pcm_data = generate_square(frequency, duration, sample_rate, volume)
    elif waveform == "sawtooth":
        pcm_data = generate_sawtooth(frequency, duration, sample_rate, volume)
    elif waveform == "triangle":
        pcm_data = generate_triangle(frequency, duration, sample_rate, volume)
    elif waveform == "noise":
        pcm_data = generate_noise(duration, sample_rate, volume)
    else:
        raise MCPVideoError(f"Unknown waveform: {waveform}", error_type="validation_error", code="invalid_parameter")

    # Convert to float for processing
    samples = _pcm_to_float(pcm_data)

    # Apply effects
    if effects:
        # Envelope
        if "envelope" in effects:
            env = effects["envelope"]
            samples = apply_envelope(
                samples,
                attack=env.get("attack", 0.01),
                decay=env.get("decay", 0.1),
                sustain=env.get("sustain", 0.7),
                release=env.get("release", 0.2),
                duration=duration,
                sample_rate=sample_rate,
            )

        # Fade in/out
        fade_in = effects.get("fade_in", 0)
        fade_out = effects.get("fade_out", 0)
        if fade_in > 0 or fade_out > 0:
            samples = apply_fade(samples, fade_in, fade_out, duration, sample_rate)

        # Reverb
        if "reverb" in effects:
            rev = effects["reverb"]
            samples = apply_reverb(
                samples,
                room_size=rev.get("room_size", 0.5),
                damping=rev.get("damping", 0.5),
                wet_level=rev.get("wet_level", 0.2),
            )

        # Lowpass
        if "lowpass" in effects:
            samples = apply_lowpass(samples, effects["lowpass"], sample_rate)

    # Convert back to PCM and write
    pcm_data = _float_to_pcm(samples)
    return write_wav(pcm_data, output, sample_rate)


def audio_preset(
    preset: str,
    output: str,
    pitch: Literal["low", "mid", "high"] = "mid",
    duration: float | None = None,
    intensity: float = 0.5,
) -> str:
    """Generate preset sound design elements.

    Presets:
        UI: ui-blip, ui-click, ui-tap, ui-whoosh-up, ui-whoosh-down
        Ambient: drone-low, drone-mid, drone-tech
        Notifications: chime-success, chime-error, chime-notification
        Data: typing, scan, processing, data-flow

    Args:
        preset: Preset name
        output: Output WAV file path
        pitch: Pitch variation (low/mid/high)
        duration: Override default duration
        intensity: Effect intensity (0-1)

    Returns:
        Path to generated WAV file
    """
    from .presets import _PITCH_MULT, get_preset_config

    try:
        config = get_preset_config(preset)
    except KeyError as exc:
        raise MCPVideoError(
            str(exc),
            error_type="validation_error",
            code="invalid_parameter",
        ) from None

    mult = _PITCH_MULT.get(pitch, 1.0)
    config["frequency"] = config["frequency"] * mult

    if duration is not None:
        config["duration"] = duration

    if preset == "typing":
        config["volume"] = config["volume"] * intensity

    return audio_synthesize(output=output, **config)
