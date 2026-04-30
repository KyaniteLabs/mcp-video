"""Tests for audio sequencing, composition, and effects."""

import wave
from pathlib import Path

import pytest

from mcp_video.audio_engine.sequencing import audio_compose, audio_effects, audio_sequence
from mcp_video.audio_engine.synthesis import audio_synthesize


def _make_wav(path: str, duration: float = 0.1, freq: float = 440) -> str:
    """Generate a simple test WAV file."""
    audio_synthesize(output=path, duration=duration, frequency=freq, volume=0.1)
    return path


class TestAudioSequence:
    def test_tone_sequence(self, tmp_path):
        output = str(tmp_path / "out.wav")
        seq = [
            {"type": "tone", "at": 0.0, "duration": 0.05, "freq": 440, "waveform": "sine"},
            {"type": "tone", "at": 0.05, "duration": 0.05, "freq": 880, "waveform": "square"},
            {"type": "tone", "at": 0.1, "duration": 0.05, "freq": 220, "waveform": "sawtooth"},
            {"type": "tone", "at": 0.15, "duration": 0.05, "freq": 330, "waveform": "triangle"},
        ]
        result = audio_sequence(seq, output, sample_rate=8000)
        assert Path(result).exists()

    def test_preset_sequence(self, tmp_path):
        output = str(tmp_path / "out.wav")
        seq = [
            {"type": "preset", "at": 0.0, "duration": 0.05, "name": "ui-blip"},
        ]
        result = audio_sequence(seq, output, sample_rate=8000)
        assert Path(result).exists()

    def test_whoosh_sequence(self, tmp_path):
        output = str(tmp_path / "out.wav")
        seq = [
            {"type": "whoosh", "at": 0.0, "duration": 0.05, "direction": "up"},
        ]
        result = audio_sequence(seq, output, sample_rate=8000)
        assert Path(result).exists()

    def test_unknown_event_type_ignored(self, tmp_path):
        output = str(tmp_path / "out.wav")
        seq = [
            {"type": "unknown", "at": 0.0, "duration": 0.05},
            {"type": "tone", "at": 0.0, "duration": 0.05, "freq": 440},
        ]
        result = audio_sequence(seq, output, sample_rate=8000)
        assert Path(result).exists()

    def test_normalization_on_clipping(self, tmp_path):
        output = str(tmp_path / "out.wav")
        seq = [
            {"type": "tone", "at": 0.0, "duration": 0.1, "freq": 440, "volume": 1.0},
            {"type": "tone", "at": 0.0, "duration": 0.1, "freq": 440, "volume": 1.0},
        ]
        result = audio_sequence(seq, output, sample_rate=8000)
        assert Path(result).exists()

    def test_empty_sequence_raises(self, tmp_path):
        from mcp_video.errors import MCPVideoError
        output = str(tmp_path / "out.wav")
        with pytest.raises(MCPVideoError, match="empty"):
            audio_sequence([], output, sample_rate=8000)


class TestAudioCompose:
    def test_compose_single_track(self, tmp_path):
        track = _make_wav(str(tmp_path / "track.wav"))
        output = str(tmp_path / "out.wav")
        result = audio_compose(
            [{"file": track, "volume": 0.5, "start": 0.0}],
            duration=0.2,
            output=output,
            sample_rate=8000,
        )
        assert Path(result).exists()

    def test_compose_with_loop(self, tmp_path):
        track = _make_wav(str(tmp_path / "track.wav"), duration=0.05)
        output = str(tmp_path / "out.wav")
        result = audio_compose(
            [{"file": track, "volume": 0.5, "start": 0.0, "loop": True}],
            duration=0.2,
            output=output,
            sample_rate=8000,
        )
        assert Path(result).exists()

    def test_compose_missing_file_skipped(self, tmp_path):
        output = str(tmp_path / "out.wav")
        result = audio_compose(
            [{"file": "/nonexistent.wav", "volume": 0.5}],
            duration=0.1,
            output=output,
            sample_rate=8000,
        )
        assert Path(result).exists()

    def test_compose_multiple_tracks(self, tmp_path):
        t1 = _make_wav(str(tmp_path / "t1.wav"), freq=440)
        t2 = _make_wav(str(tmp_path / "t2.wav"), freq=880)
        output = str(tmp_path / "out.wav")
        result = audio_compose(
            [
                {"file": t1, "volume": 0.3, "start": 0.0},
                {"file": t2, "volume": 0.3, "start": 0.05},
            ],
            duration=0.2,
            output=output,
            sample_rate=8000,
        )
        assert Path(result).exists()


class TestAudioEffects:
    def test_lowpass_effect(self, tmp_path):
        src = _make_wav(str(tmp_path / "src.wav"))
        output = str(tmp_path / "out.wav")
        result = audio_effects(
            src,
            output,
            [{"type": "lowpass", "frequency": 1000}],
        )
        assert Path(result).exists()

    def test_highpass_effect(self, tmp_path):
        src = _make_wav(str(tmp_path / "src.wav"))
        output = str(tmp_path / "out.wav")
        result = audio_effects(
            src,
            output,
            [{"type": "highpass", "frequency": 200}],
        )
        assert Path(result).exists()

    def test_reverb_effect(self, tmp_path):
        src = _make_wav(str(tmp_path / "src.wav"))
        output = str(tmp_path / "out.wav")
        result = audio_effects(
            src,
            output,
            [{"type": "reverb", "room_size": 0.5, "damping": 0.5, "wet_level": 0.2}],
        )
        assert Path(result).exists()

    def test_normalize_effect(self, tmp_path):
        src = _make_wav(str(tmp_path / "src.wav"))
        output = str(tmp_path / "out.wav")
        result = audio_effects(
            src,
            output,
            [{"type": "normalize"}],
        )
        assert Path(result).exists()

    def test_fade_effect(self, tmp_path):
        src = _make_wav(str(tmp_path / "src.wav"))
        output = str(tmp_path / "out.wav")
        result = audio_effects(
            src,
            output,
            [{"type": "fade", "fade_in": 0.01, "fade_out": 0.01}],
        )
        assert Path(result).exists()

    def test_empty_effects(self, tmp_path):
        src = _make_wav(str(tmp_path / "src.wav"))
        output = str(tmp_path / "out.wav")
        result = audio_effects(src, output, [])
        assert Path(result).exists()

    def test_chain_of_effects(self, tmp_path):
        src = _make_wav(str(tmp_path / "src.wav"))
        output = str(tmp_path / "out.wav")
        result = audio_effects(
            src,
            output,
            [
                {"type": "lowpass", "frequency": 2000},
                {"type": "reverb", "room_size": 0.3},
                {"type": "normalize"},
            ],
        )
        assert Path(result).exists()
