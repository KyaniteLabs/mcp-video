# mcp-video Audio Features Needed

Based on the generative sound design implementation in the explainer video, here are the features that should be added to mcp-video to support procedural audio.

---

## 🎯 **Core Audio Engine**

### `video_audio_synthesize`
Generate audio procedurally using Web Audio API-style synthesis.

```python
from mcp_video import video_audio_synthesize

# Generate a drone tone
video_audio_synthesize(
    output="drone.wav",
    waveform="sine",  # sine, square, sawtooth, triangle, noise
    frequency=100,    # Hz base frequency
    duration=5.0,     # seconds
    volume=0.3,
    effects={
        "lfo": {"rate": 0.1, "depth": 5},  # Frequency modulation
        "harmonic": 0.5,  # Add harmonic overtones
    }
)
```

### `video_audio_sequence`
Compose multiple audio events into a sequence.

```python
from mcp_video import video_audio_sequence

sequence = [
    {"type": "tone", "freq": 800, "duration": 0.05, "at": 0},
    {"type": "tone", "freq": 1000, "duration": 0.05, "at": 0.1},
    {"type": "chime", "notes": [523, 659, 784], "at": 2.0},
    {"type": "whoosh", "direction": "up", "duration": 0.3, "at": 3.0},
]

video_audio_sequence(sequence, output="sound-design.wav")
```

---

## 🔊 **Sound Design Presets**

### `video_audio_preset`
Pre-configured sound design elements.

```python
from mcp_video import video_audio_preset

# UI interaction sounds
video_audio_preset("ui-blip", pitch="high", output="click.wav")
video_audio_preset("ui-click", pitch="mid", output="click.wav")
video_audio_preset("ui-whoosh", direction="up", output="whoosh.wav")

# Ambient textures
video_audio_preset("drone-low", freq=80, output="drone.wav")
video_audio_preset("drone-tech", freq=120, modulation=True, output="drone.wav")

# Success/notification
video_audio_preset("chime-success", output="chime.wav")
video_audio_preset("chime-error", output="error.wav")

# Data/processing
video_audio_preset("typing", intensity=0.5, output="typing.wav")
video_audio_preset("scan", duration=1.0, output="scan.wav")
video_audio_preset("data-flow", duration=0.3, output="flow.wav")
```

---

## 🎵 **Audio Composition**

### `video_audio_compose`
Layer multiple audio tracks with timing.

```python
from mcp_video import video_audio_compose

video_audio_compose(
    tracks=[
        {"file": "drone.wav", "volume": 0.2, "loop": True},
        {"file": "blips.wav", "volume": 0.3, "at": 5.0},
        {"file": "chime.wav", "volume": 0.5, "at": 10.0},
    ],
    duration=15.0,
    output="soundtrack.wav"
)
```

---

## 🎚️ **Audio Effects Chain**

### `video_audio_effects`
Apply effects to audio.

```python
from mcp_video import video_audio_effects

video_audio_effects(
    input="raw.wav",
    output="processed.wav",
    effects=[
        {"type": "lowpass", "freq": 2000},
        {"type": "reverb", "room": 0.3, "damping": 0.5},
        {"type": "compressor", "threshold": -20, "ratio": 4},
        {"type": "normalize", "target": -16},  # LUFS
    ]
)
```

---

## 🎬 **Video + Audio Integration**

### `video_add_generated_audio`
Add procedurally generated audio to video.

```python
from mcp_video import video_add_generated_audio

# Generate and add in one call
video_add_generated_audio(
    video="input.mp4",
    audio_config={
        "drone": {"freq": 100, "volume": 0.2},
        "events": [
            {"type": "blip", "at": 2.0},
            {"type": "chime", "at": 5.0},
        ]
    },
    output="with-audio.mp4"
)
```

---

## 🎹 **MCP Tools Interface**

These would be exposed as MCP tools:

```json
{
  "name": "video_audio_synthesize",
  "description": "Generate procedural audio using synthesis",
  "parameters": {
    "waveform": {"type": "string", "enum": ["sine", "square", "sawtooth", "triangle", "noise"]},
    "frequency": {"type": "number", "description": "Base frequency in Hz"},
    "duration": {"type": "number", "description": "Duration in seconds"},
    "volume": {"type": "number", "minimum": 0, "maximum": 1},
    "effects": {"type": "object"}
  }
}
```

```json
{
  "name": "video_audio_preset",
  "description": "Generate preset sound design elements",
  "parameters": {
    "preset": {"type": "string", "enum": ["ui-blip", "ui-click", "ui-whoosh", "drone-low", "drone-tech", "chime-success", "typing", "scan"]},
    "pitch": {"type": "string", "enum": ["low", "mid", "high"]},
    "direction": {"type": "string", "enum": ["up", "down"]},
    "duration": {"type": "number"},
    "output": {"type": "string"}
  }
}
```

---

## 🔧 **Implementation Notes**

### Tech Stack Options

1. **Python + NumPy** (Pure Python)
   - Generate waveforms as NumPy arrays
   - Write to WAV using `scipy.io.wavfile`
   - Apply effects with `pydub` or custom DSP
   - **Pros:** No external dependencies, fully portable
   - **Cons:** Slower for complex synthesis

2. **Python + Pedalboard** (Spotify)
   - Use `pedalboard` for audio effects
   - `numpy` for synthesis
   - **Pros:** Professional quality effects
   - **Cons:** Heavy dependency

3. **Python + sox** (External)
   - Generate base tones
   - Use `sox` command-line for effects
   - **Pros:** Fast, proven audio tools
   - **Cons:** Requires sox installation

### Recommended: Option 1 (Pure Python)

Most aligned with mcp-video's philosophy of minimal dependencies.

```python
import numpy as np
from scipy.io import wavfile

def generate_tone(freq, duration, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration))
    waveform = np.sin(2 * np.pi * freq * t)
    return (waveform * 32767).astype(np.int16)

# Write to file
wavfile.write("tone.wav", 44100, generate_tone(440, 1.0))
```

---

## 📊 **Priority Ranking**

| Feature | Priority | Effort | Value |
|---------|----------|--------|-------|
| `video_audio_synthesize` | P1 | Medium | High - Core building block |
| `video_audio_preset` | P1 | Low | High - Easy UX |
| `video_audio_compose` | P2 | Medium | Medium - Composition layer |
| `video_audio_effects` | P2 | High | Medium - Polish |
| `video_add_generated_audio` | P1 | Low | High - Integration convenience |

---

## 🎨 **Sound Design Preset Library**

Suggested initial presets:

| Category | Presets |
|----------|---------|
| **UI** | `ui-blip`, `ui-click`, `ui-tap`, `ui-whoosh-up`, `ui-whoosh-down` |
| **Ambient** | `drone-low`, `drone-mid`, `drone-tech`, `drone-ominous` |
| **Notifications** | `chime-success`, `chime-error`, `chime-notification` |
| **Data** | `typing`, `scan`, `processing`, `data-flow`, `upload`, `download` |
| **Nature** | `wind`, `water`, `fire` (abstract, not realistic) |

---

## 🚀 **MVP Scope**

For immediate implementation:

1. `video_audio_synthesize` - Basic waveform generation
2. `video_audio_preset` - 10 most common presets
3. `video_add_generated_audio` - Convenience wrapper

Total: ~200 lines of Python + tests.
