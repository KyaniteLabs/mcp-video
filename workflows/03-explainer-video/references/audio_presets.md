# Audio Presets for Explainer Videos

## Scene Types and Recommended Audio

| Scene Type | Preset | Duration | Volume |
|---|---|---|---|
| Intro / Title | `drone-low` | Full scene | 0.12 |
| Problem statement | `ui-blip` | 0.1s at start | 0.30 |
| Feature demo | `ui-whoosh-up` | 0.3s at transition | 0.30 |
| Success / CTA | `chime-success` | 0.5s at peak moment | 0.40 |

## Composition Pattern

```python
tracks = [
    {"file": "intro_drone.wav", "volume": 0.12, "start": 0, "loop": True},
    {"file": "blip.wav", "volume": 0.30, "start": 5.0, "loop": False},
    {"file": "whoosh.wav", "volume": 0.30, "start": 40.0, "loop": False},
    {"file": "chime.wav", "volume": 0.40, "start": 85.0, "loop": False},
]
audio_compose(tracks, duration=90, output="soundtrack.wav")
```

## Tips

- Keep background drone low (0.10-0.15) so it doesn't compete with voice
- Use percussive sounds (blips, whooshes) at scene transitions
- End with a chime or success sound for the CTA
- Always normalize final mix to -16 LUFS for YouTube
