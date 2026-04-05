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

from .errors import InputFileError, MCPVideoError, ProcessingError

# ---------------------------------------------------------------------------
# Audio Constants
# ---------------------------------------------------------------------------

DEFAULT_SAMPLE_RATE = 44100
DEFAULT_CHANNELS = 1
DEFAULT_SAMPLE_WIDTH = 2  # 16-bit

# ---------------------------------------------------------------------------
# Waveform Generation
# ---------------------------------------------------------------------------


def generate_sine(
    frequency: float,
    duration: float,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    amplitude: float = 0.5,
) -> bytes:
    """Generate a sine wave."""
    num_samples = int(sample_rate * duration)
    samples = []

    for i in range(num_samples):
        t = i / sample_rate
        value = amplitude * math.sin(2 * math.pi * frequency * t)
        samples.append(value)

    return _float_to_pcm(samples)


def generate_square(
    frequency: float,
    duration: float,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    amplitude: float = 0.5,
) -> bytes:
    """Generate a square wave."""
    num_samples = int(sample_rate * duration)
    samples = []

    for i in range(num_samples):
        t = i / sample_rate
        value = amplitude * (1 if math.sin(2 * math.pi * frequency * t) >= 0 else -1)
        samples.append(value)

    return _float_to_pcm(samples)


def generate_sawtooth(
    frequency: float,
    duration: float,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    amplitude: float = 0.5,
) -> bytes:
    """Generate a sawtooth wave."""
    num_samples = int(sample_rate * duration)
    samples = []
    period = sample_rate / frequency

    for i in range(num_samples):
        value = amplitude * (2 * ((i % period) / period) - 1)
        samples.append(value)

    return _float_to_pcm(samples)


def generate_triangle(
    frequency: float,
    duration: float,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    amplitude: float = 0.5,
) -> bytes:
    """Generate a triangle wave."""
    num_samples = int(sample_rate * duration)
    samples = []
    period = sample_rate / frequency

    for i in range(num_samples):
        phase = (i % period) / period
        if phase < 0.25:
            value = 4 * phase
        elif phase < 0.75:
            value = 2 - 4 * phase
        else:
            value = 4 * phase - 4
        samples.append(amplitude * value)

    return _float_to_pcm(samples)


def generate_noise(
    duration: float,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    amplitude: float = 0.3,
) -> bytes:
    """Generate white noise."""
    import random

    num_samples = int(sample_rate * duration)
    samples = []

    for _ in range(num_samples):
        value = amplitude * (random.random() * 2 - 1)
        samples.append(value)

    return _float_to_pcm(samples)


# ---------------------------------------------------------------------------
# Effects
# ---------------------------------------------------------------------------


def apply_envelope(
    samples: list[float],
    attack: float,
    decay: float,
    sustain: float,
    release: float,
    duration: float,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> list[float]:
    """Apply ADSR envelope to samples."""
    total_samples = len(samples)
    attack_samples = int(attack * sample_rate)
    decay_samples = int(decay * sample_rate)
    release_samples = int(release * sample_rate)
    sustain_samples = total_samples - attack_samples - decay_samples - release_samples

    result = []
    for i, sample in enumerate(samples):
        if i < attack_samples and attack_samples > 0:
            # Attack phase
            env = i / attack_samples
        elif i < attack_samples + decay_samples and decay_samples > 0:
            # Decay phase
            decay_progress = (i - attack_samples) / decay_samples
            env = 1 - (1 - sustain) * decay_progress
        elif i < attack_samples + decay_samples + max(0, sustain_samples):
            # Sustain phase
            env = sustain
        elif release_samples > 0:
            # Release phase
            release_progress = (i - attack_samples - decay_samples - sustain_samples) / release_samples
            env = sustain * (1 - release_progress)
        else:
            env = 0

        result.append(sample * env)

    return result


def apply_fade(samples: list[float], fade_in: float, fade_out: float, duration: float, sample_rate: int) -> list[float]:
    """Apply fade in/out to samples."""
    total_samples = len(samples)
    fade_in_samples = int(fade_in * sample_rate)
    fade_out_samples = int(fade_out * sample_rate)

    result = []
    for i, sample in enumerate(samples):
        envelope = 1.0

        if fade_in_samples > 0 and i < fade_in_samples:
            envelope = i / fade_in_samples

        if fade_out_samples > 0 and i >= total_samples - fade_out_samples:
            envelope = (total_samples - i) / fade_out_samples

        result.append(sample * envelope)

    return result


def apply_lowpass(samples: list[float], cutoff: float, sample_rate: int = DEFAULT_SAMPLE_RATE) -> list[float]:
    """Simple lowpass filter."""
    rc = 1.0 / (2 * math.pi * cutoff)
    dt = 1.0 / sample_rate
    alpha = dt / (rc + dt)

    result = [samples[0]]
    for i in range(1, len(samples)):
        result.append(result[-1] + alpha * (samples[i] - result[-1]))

    return result


def apply_reverb(
    samples: list[float],
    room_size: float = 0.5,
    damping: float = 0.5,
    wet_level: float = 0.2,
) -> list[float]:
    """Simple comb filter reverb."""
    delay_samples = int(0.03 * DEFAULT_SAMPLE_RATE * room_size)  # ~30ms base
    comb1 = _comb_filter(samples, int(delay_samples * 1.0), 0.805, damping)
    comb2 = _comb_filter(samples, int(delay_samples * 0.97), 0.827, damping)
    comb3 = _comb_filter(samples, int(delay_samples * 0.94), 0.783, damping)
    comb4 = _comb_filter(samples, int(delay_samples * 0.91), 0.812, damping)

    combined = [(c1 + c2 + c3 + c4) / 4 for c1, c2, c3, c4 in zip(comb1, comb2, comb3, comb4, strict=False)]

    # Mix wet and dry
    result = []
    for dry, wet in zip(samples, combined, strict=False):
        result.append(dry * (1 - wet_level) + wet * wet_level)

    return result


def _comb_filter(samples: list[float], delay: int, feedback: float, damping: float) -> list[float]:
    """Simple comb filter for reverb."""
    buffer = [0.0] * delay
    result = []

    for sample in samples:
        output = sample + buffer[0] * feedback
        buffer.append(output * (1 - damping))
        buffer.pop(0)
        result.append(output)

    return result


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


def _float_to_pcm(samples: list[float]) -> bytes:
    """Convert float samples (-1 to 1) to 16-bit PCM bytes."""
    pcm_data = []
    for sample in samples:
        # Clamp to [-1, 1]
        sample = max(-1, min(1, sample))
        # Convert to 16-bit signed int
        pcm_data.append(struct.pack("<h", int(sample * 32767)))
    return b"".join(pcm_data)


def _pcm_to_float(pcm_bytes: bytes) -> list[float]:
    """Convert 16-bit PCM bytes to float samples."""
    samples = []
    for i in range(0, len(pcm_bytes), 2):
        value = struct.unpack("<h", pcm_bytes[i : i + 2])[0]
        samples.append(value / 32767)
    return samples


def write_wav(
    pcm_data: bytes,
    output_path: str,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    channels: int = DEFAULT_CHANNELS,
) -> str:
    """Write PCM data to a WAV file."""
    with wave.open(output_path, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(DEFAULT_SAMPLE_WIDTH)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)
    return output_path


# ---------------------------------------------------------------------------
# Main API
# ---------------------------------------------------------------------------


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
    from .limits import MAX_AUDIO_DURATION, MIN_FREQUENCY, MAX_FREQUENCY, MIN_SAMPLE_RATE, MAX_SAMPLE_RATE

    if not (MIN_FREQUENCY <= frequency <= MAX_FREQUENCY):
        raise MCPVideoError(f"Frequency must be between {MIN_FREQUENCY} and {MAX_FREQUENCY} Hz, got {frequency}", error_type="validation_error", code="invalid_parameter")
    if not (0.01 <= duration <= MAX_AUDIO_DURATION):
        raise MCPVideoError(f"Duration must be between 0.01 and {MAX_AUDIO_DURATION} seconds, got {duration}", error_type="validation_error", code="invalid_parameter")
    if not (0.0 <= volume <= 1.0):
        raise MCPVideoError(f"Volume must be between 0.0 and 1.0, got {volume}", error_type="validation_error", code="invalid_parameter")
    if not (MIN_SAMPLE_RATE <= sample_rate <= MAX_SAMPLE_RATE):
        raise MCPVideoError(f"Sample rate must be between {MIN_SAMPLE_RATE} and {MAX_SAMPLE_RATE}, got {sample_rate}", error_type="validation_error", code="invalid_parameter")
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
        raise MCPVideoError(f"Unknown preset: {preset}. Available: {list(presets.keys())}", error_type="validation_error", code="invalid_parameter")

    config = presets[preset].copy()
    if duration:
        config["duration"] = duration

    return audio_synthesize(output=output, **config)


def audio_sequence(
    sequence: list[dict[str, Any]],
    output: str,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> str:
    """Compose multiple audio events into a timed sequence.

    Args:
        sequence: List of audio events with keys:
            - type: "tone", "preset", or "whoosh"
            - at: start time in seconds
            - duration: duration in seconds
            - freq/frequency: frequency for tones
            - name: preset name for presets
            - Other parameters as needed
        output: Output WAV file path
        sample_rate: Sample rate

    Returns:
        Path to generated WAV file
    """
    if not sequence:
        raise MCPVideoError("Sequence cannot be empty", error_type="validation_error", code="invalid_parameter")

    # Calculate total duration
    max_end = max(event.get("at", 0) + event.get("duration", 1.0) for event in sequence)
    total_samples = int(max_end * sample_rate)

    # Initialize silent buffer
    mix_buffer = [0.0] * total_samples

    for event in sequence:
        start_time = event.get("at", 0)
        duration = event.get("duration", 1.0)
        event_type = event.get("type", "tone")

        start_sample = int(start_time * sample_rate)
        int(duration * sample_rate)

        # Generate based on type
        if event_type == "tone":
            freq = event.get("freq") or event.get("frequency", 440)
            volume = event.get("volume", 0.3)
            waveform = event.get("waveform", "sine")

            if waveform == "sine":
                pcm = generate_sine(freq, duration, sample_rate, volume)
            elif waveform == "square":
                pcm = generate_square(freq, duration, sample_rate, volume)
            elif waveform == "sawtooth":
                pcm = generate_sawtooth(freq, duration, sample_rate, volume)
            elif waveform == "triangle":
                pcm = generate_triangle(freq, duration, sample_rate, volume)
            else:
                pcm = generate_sine(freq, duration, sample_rate, volume)

            samples = _pcm_to_float(pcm)

        elif event_type == "preset":
            # Create temp file and read back
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name

            try:
                audio_preset(
                    preset=event.get("name", "ui-blip"),
                    output=tmp_path,
                    duration=duration,
                    intensity=event.get("intensity", 0.5),
                )

                with wave.open(tmp_path, "rb") as wav_file:
                    frames = wav_file.readframes(wav_file.getnframes())
                    samples = _pcm_to_float(frames)
            finally:
                Path(tmp_path).unlink(missing_ok=True)

        elif event_type == "whoosh":
            # Simple whoosh using filtered noise
            event.get("direction", "up")
            volume = event.get("volume", 0.3)
            pcm = generate_noise(duration, sample_rate, volume)
            samples = _pcm_to_float(pcm)
            samples = apply_lowpass(samples, 2000, sample_rate)

        else:
            continue

        # Mix into buffer
        for i, sample in enumerate(samples):
            idx = start_sample + i
            if idx < len(mix_buffer):
                mix_buffer[idx] += sample

    # Normalize to prevent clipping
    max_val = max(abs(s) for s in mix_buffer) if mix_buffer else 1
    if max_val > 1:
        mix_buffer = [s / max_val for s in mix_buffer]

    pcm_data = _float_to_pcm(mix_buffer)
    return write_wav(pcm_data, output, sample_rate)


def audio_compose(
    tracks: list[dict[str, Any]],
    duration: float,
    output: str,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> str:
    """Layer multiple audio tracks with mixing.

    Args:
        tracks: List of track configs with:
            - file: path to WAV file
            - volume: volume multiplier (0-1)
            - start: start time in seconds
            - loop: whether to loop the track
        duration: Total duration of output
        output: Output WAV file path
        sample_rate: Sample rate

    Returns:
        Path to generated WAV file
    """
    total_samples = int(duration * sample_rate)
    mix_buffer = [0.0] * total_samples

    for track in tracks:
        file_path = track.get("file")
        volume = track.get("volume", 1.0)
        start_time = track.get("start", 0)
        loop = track.get("loop", False)

        if not file_path or not Path(file_path).exists():
            continue

        # Read WAV file
        with wave.open(file_path, "rb") as wav_file:
            frames = wav_file.readframes(wav_file.getnframes())
            track_samples = _pcm_to_float(frames)

        start_sample = int(start_time * sample_rate)

        # Add to mix buffer
        if loop:
            for i in range(total_samples - start_sample):
                idx = start_sample + i
                sample_idx = i % len(track_samples)
                if idx < len(mix_buffer):
                    mix_buffer[idx] += track_samples[sample_idx] * volume
        else:
            for i, sample in enumerate(track_samples):
                idx = start_sample + i
                if idx < len(mix_buffer):
                    mix_buffer[idx] += sample * volume

    # Normalize
    max_val = max(abs(s) for s in mix_buffer) if mix_buffer else 1
    if max_val > 1:
        mix_buffer = [s / max_val * 0.95 for s in mix_buffer]  # Leave headroom

    pcm_data = _float_to_pcm(mix_buffer)
    return write_wav(pcm_data, output, sample_rate)


def audio_effects(
    input_path: str,
    output: str,
    effects: list[dict[str, Any]],
) -> str:
    """Apply audio effects chain.

    Args:
        input_path: Input WAV file path
        output: Output WAV file path
        effects: List of effect configs with:
            - type: "lowpass", "highpass", "reverb", "normalize"
            - Additional parameters per effect type

    Returns:
        Path to processed WAV file
    """
    # Read input
    with wave.open(input_path, "rb") as wav_file:
        sample_rate = wav_file.getframerate()
        frames = wav_file.readframes(wav_file.getnframes())
        samples = _pcm_to_float(frames)

    # Apply effects chain
    for effect in effects:
        effect_type = effect.get("type")

        if effect_type == "lowpass":
            cutoff = effect.get("frequency", 2000)
            samples = apply_lowpass(samples, cutoff, sample_rate)

        elif effect_type == "reverb":
            room_size = effect.get("room_size", 0.5)
            damping = effect.get("damping", 0.5)
            wet_level = effect.get("wet_level", 0.2)
            samples = apply_reverb(samples, room_size, damping, wet_level)

        elif effect_type == "normalize":
            max_val = max(abs(s) for s in samples) if samples else 1
            if max_val > 0:
                effect.get("target_lufs", -16)
                # Simple linear normalization (LUFS would require more complex analysis)
                gain = 0.5 / max_val  # Approximate -6dB as baseline
                samples = [s * gain for s in samples]

        elif effect_type == "fade":
            fade_in = effect.get("fade_in", 0)
            fade_out = effect.get("fade_out", 0)
            duration = len(samples) / sample_rate
            samples = apply_fade(samples, fade_in, fade_out, duration, sample_rate)

    # Write output
    pcm_data = _float_to_pcm(samples)
    return write_wav(pcm_data, output, sample_rate)


# ---------------------------------------------------------------------------
# Video Integration
# ---------------------------------------------------------------------------


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
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        except subprocess.TimeoutExpired:
            raise ProcessingError(" ".join(cmd), -1, "Audio processing command timed out after 600s") from None
        if result.returncode != 0:
            raise ProcessingError(" ".join(cmd), result.returncode, result.stderr)

        return output

    finally:
        Path(audio_path).unlink(missing_ok=True)
