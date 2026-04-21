"""Audio synthesis and sound design engine.

Pure NumPy-based audio generation with no external dependencies.
"""

from __future__ import annotations

import math
import struct
import wave

from mcp_video.ffmpeg_helpers import _validate_output_path


# ---------------------------------------------------------------------------
# Audio Constants
# ---------------------------------------------------------------------------

DEFAULT_SAMPLE_RATE = 44100
DEFAULT_CHANNELS = 1
DEFAULT_SAMPLE_WIDTH = 2  # 16-bit

"""Audio synthesis and sound design engine.

Pure NumPy-based audio generation with no external dependencies.
"""


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


def apply_highpass(samples: list[float], cutoff: float, sample_rate: int = DEFAULT_SAMPLE_RATE) -> list[float]:
    """Simple highpass filter."""
    rc = 1.0 / (2 * math.pi * cutoff)
    dt = 1.0 / sample_rate
    alpha = rc / (rc + dt)

    result = [samples[0]]
    for i in range(1, len(samples)):
        result.append(alpha * (result[-1] + samples[i] - samples[i - 1]))

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
    _validate_output_path(output_path)
    with wave.open(output_path, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(DEFAULT_SAMPLE_WIDTH)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)
    return output_path


# ---------------------------------------------------------------------------
# Main API
# ---------------------------------------------------------------------------
