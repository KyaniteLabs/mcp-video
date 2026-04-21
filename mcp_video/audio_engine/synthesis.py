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
    pitch_mult = {"low": 0.7, "mid": 1.0, "high": 1.5}
    mult = pitch_mult.get(pitch, 1.0)

    presets: dict[str, dict] = {
        # UI Sounds
        "ui-blip": {
            "waveform": "sine",
            "frequency": 800 * mult,
            "duration": 0.08,
            "volume": 0.4,
            "effects": {"envelope": {"attack": 0.001, "decay": 0.05, "sustain": 0, "release": 0.02}},
        },
        "ui-click": {
            "waveform": "square",
            "frequency": 400 * mult,
            "duration": 0.05,
            "volume": 0.3,
            "effects": {"lowpass": 2000, "envelope": {"attack": 0.001, "decay": 0.02, "sustain": 0, "release": 0.01}},
        },
        "ui-tap": {
            "waveform": "noise",
            "frequency": 0,
            "duration": 0.03,
            "volume": 0.2,
            "effects": {"lowpass": 3000, "fade_out": 0.02},
        },
        "ui-whoosh-up": {
            "waveform": "sawtooth",
            "frequency": 200,
            "duration": duration or 0.3,
            "volume": 0.3,
            "effects": {"fade_in": 0.05, "fade_out": 0.1},
        },
        "ui-whoosh-down": {
            "waveform": "sawtooth",
            "frequency": 600,
            "duration": duration or 0.3,
            "volume": 0.3,
            "effects": {"fade_in": 0.05, "fade_out": 0.1},
        },
        # Ambient
        "drone-low": {
            "waveform": "sine",
            "frequency": 80,
            "duration": duration or 5.0,
            "volume": 0.3,
            "effects": {"reverb": {"room_size": 0.8, "damping": 0.3, "wet_level": 0.4}},
        },
        "drone-mid": {
            "waveform": "triangle",
            "frequency": 150,
            "duration": duration or 5.0,
            "volume": 0.25,
            "effects": {"reverb": {"room_size": 0.6, "damping": 0.4, "wet_level": 0.3}},
        },
        "drone-tech": {
            "waveform": "square",
            "frequency": 120,
            "duration": duration or 5.0,
            "volume": 0.2,
            "effects": {"lowpass": 800, "reverb": {"room_size": 0.5, "damping": 0.5, "wet_level": 0.3}},
        },
        "drone-ominous": {
            "waveform": "sawtooth",
            "frequency": 60,
            "duration": duration or 5.0,
            "volume": 0.35,
            "effects": {
                "lowpass": 400,
                "reverb": {"room_size": 0.9, "damping": 0.2, "wet_level": 0.5},
            },
        },
        # Notifications
        "chime-success": {
            "waveform": "sine",
            "frequency": 523.25,  # C5
            "duration": duration or 0.5,
            "volume": 0.4,
            "effects": {
                "envelope": {"attack": 0.01, "decay": 0.1, "sustain": 0.6, "release": 0.3},
                "reverb": {"room_size": 0.4, "damping": 0.5, "wet_level": 0.2},
            },
        },
        "chime-error": {
            "waveform": "sawtooth",
            "frequency": 200,
            "duration": duration or 0.4,
            "volume": 0.35,
            "effects": {
                "envelope": {"attack": 0.01, "decay": 0.15, "sustain": 0.3, "release": 0.2},
                "lowpass": 1500,
            },
        },
        "chime-notification": {
            "waveform": "triangle",
            "frequency": 659.25,  # E5
            "duration": duration or 0.3,
            "volume": 0.35,
            "effects": {"envelope": {"attack": 0.01, "decay": 0.08, "sustain": 0.4, "release": 0.2}},
        },
        # Data Sounds
        "typing": {
            "waveform": "noise",
            "frequency": 0,
            "duration": duration or 0.1,
            "volume": 0.15 * intensity,
            "effects": {"lowpass": 4000, "fade_out": 0.05},
        },
        "scan": {
            "waveform": "sine",
            "frequency": 1000,
            "duration": duration or 1.0,
            "volume": 0.2,
            "effects": {"lowpass": 3000},
        },
        "processing": {
            "waveform": "square",
            "frequency": 80,
            "duration": duration or 2.0,
            "volume": 0.15,
            "effects": {"lowpass": 400, "reverb": {"room_size": 0.3, "damping": 0.6, "wet_level": 0.2}},
        },
        "data-flow": {
            "waveform": "sine",
            "frequency": 200,
            "duration": duration or 0.5,
            "volume": 0.25,
            "effects": {
                "fade_in": 0.1,
                "fade_out": 0.2,
                "reverb": {"room_size": 0.3, "damping": 0.5, "wet_level": 0.2},
            },
        },
        "upload": {
            "waveform": "sine",
            "frequency": 800,
            "duration": duration or 0.8,
            "volume": 0.3,
            "effects": {
                "envelope": {"attack": 0.01, "decay": 0.3, "sustain": 0.2, "release": 0.2},
                "fade_in": 0.1,
            },
        },
        "download": {
            "waveform": "sine",
            "frequency": 600,
            "duration": duration or 0.8,
            "volume": 0.3,
            "effects": {
                "envelope": {"attack": 0.01, "decay": 0.3, "sustain": 0.2, "release": 0.2},
                "fade_out": 0.1,
            },
        },
    }

    if preset not in presets:
        raise MCPVideoError(
            f"Unknown preset: {preset}. Available: {list(presets.keys())}",
            error_type="validation_error",
            code="invalid_parameter",
        )

    config = presets[preset].copy()
    if duration:
        config["duration"] = duration

    return audio_synthesize(output=output, **config)
