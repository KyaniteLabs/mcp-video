"""Audio preset definitions and helpers."""

from __future__ import annotations

import copy

_PITCH_MULT = {"low": 0.7, "mid": 1.0, "high": 1.5}

_PRESETS: dict[str, dict] = {
    # UI Sounds
    "ui-blip": {
        "waveform": "sine",
        "frequency": 800,
        "duration": 0.08,
        "volume": 0.4,
        "effects": {"envelope": {"attack": 0.001, "decay": 0.05, "sustain": 0, "release": 0.02}},
    },
    "ui-click": {
        "waveform": "square",
        "frequency": 400,
        "duration": 0.05,
        "volume": 0.3,
        "effects": {"lowpass": 2000, "envelope": {"attack": 0.001, "decay": 0.02, "sustain": 0, "release": 0.01}},
    },
    "ui-tap": {
        "waveform": "noise",
        "frequency": 440.0,
        "duration": 0.03,
        "volume": 0.2,
        "effects": {"lowpass": 3000, "fade_out": 0.02},
    },
    "ui-whoosh-up": {
        "waveform": "sawtooth",
        "frequency": 200,
        "duration": 0.3,
        "volume": 0.3,
        "effects": {"fade_in": 0.05, "fade_out": 0.1},
    },
    "ui-whoosh-down": {
        "waveform": "sawtooth",
        "frequency": 600,
        "duration": 0.3,
        "volume": 0.3,
        "effects": {"fade_in": 0.05, "fade_out": 0.1},
    },
    # Ambient
    "drone-low": {
        "waveform": "sine",
        "frequency": 80,
        "duration": 5.0,
        "volume": 0.3,
        "effects": {"reverb": {"room_size": 0.8, "damping": 0.3, "wet_level": 0.4}},
    },
    "drone-mid": {
        "waveform": "triangle",
        "frequency": 150,
        "duration": 5.0,
        "volume": 0.25,
        "effects": {"reverb": {"room_size": 0.6, "damping": 0.4, "wet_level": 0.3}},
    },
    "drone-tech": {
        "waveform": "square",
        "frequency": 120,
        "duration": 5.0,
        "volume": 0.2,
        "effects": {"lowpass": 800, "reverb": {"room_size": 0.5, "damping": 0.5, "wet_level": 0.3}},
    },
    "drone-ominous": {
        "waveform": "sawtooth",
        "frequency": 60,
        "duration": 5.0,
        "volume": 0.35,
        "effects": {
            "lowpass": 400,
            "reverb": {"room_size": 0.9, "damping": 0.2, "wet_level": 0.5},
        },
    },
    # Notifications
    "chime-success": {
        "waveform": "sine",
        "frequency": 523.25,
        "duration": 0.5,
        "volume": 0.4,
        "effects": {
            "envelope": {"attack": 0.01, "decay": 0.1, "sustain": 0.6, "release": 0.3},
            "reverb": {"room_size": 0.4, "damping": 0.5, "wet_level": 0.2},
        },
    },
    "chime-error": {
        "waveform": "sawtooth",
        "frequency": 200,
        "duration": 0.4,
        "volume": 0.35,
        "effects": {
            "envelope": {"attack": 0.01, "decay": 0.15, "sustain": 0.3, "release": 0.2},
            "lowpass": 1500,
        },
    },
    "chime-notification": {
        "waveform": "triangle",
        "frequency": 659.25,
        "duration": 0.3,
        "volume": 0.35,
        "effects": {"envelope": {"attack": 0.01, "decay": 0.08, "sustain": 0.4, "release": 0.2}},
    },
    # Data Sounds
    "typing": {
        "waveform": "noise",
        "frequency": 440.0,
        "duration": 0.1,
        "volume": 0.15,
        "effects": {"lowpass": 4000, "fade_out": 0.05},
    },
    "scan": {
        "waveform": "sine",
        "frequency": 1000,
        "duration": 1.0,
        "volume": 0.2,
        "effects": {"lowpass": 3000},
    },
    "processing": {
        "waveform": "square",
        "frequency": 80,
        "duration": 2.0,
        "volume": 0.15,
        "effects": {"lowpass": 400, "reverb": {"room_size": 0.3, "damping": 0.6, "wet_level": 0.2}},
    },
    "data-flow": {
        "waveform": "sine",
        "frequency": 200,
        "duration": 0.5,
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
        "duration": 0.8,
        "volume": 0.3,
        "effects": {
            "envelope": {"attack": 0.01, "decay": 0.3, "sustain": 0.2, "release": 0.2},
            "fade_in": 0.1,
        },
    },
    "download": {
        "waveform": "sine",
        "frequency": 600,
        "duration": 0.8,
        "volume": 0.3,
        "effects": {
            "envelope": {"attack": 0.01, "decay": 0.3, "sustain": 0.2, "release": 0.2},
            "fade_out": 0.1,
        },
    },
}


def list_presets() -> list[str]:
    """Return a sorted list of available audio preset names."""
    return sorted(_PRESETS.keys())


def get_preset_config(name: str) -> dict:
    """Return a deep copy of the configuration dict for the given preset.

    Raises:
        KeyError: If the preset name is not recognized.
    """
    if name not in _PRESETS:
        raise KeyError(f"Unknown preset: {name}. Available: {list_presets()}")
    return copy.deepcopy(_PRESETS[name])
