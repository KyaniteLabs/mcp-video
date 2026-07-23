from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from kinocut.ai_engine import _longform_runtime as runtime
from kinocut.ai_engine import transcribe
from kinocut.ai_engine._longform_models import LongformChunk
from kinocut.errors import MCPVideoError


def _chunk() -> LongformChunk:
    return LongformChunk(index=2, start=12.5, end=20, duration=7.5)


def test_extract_audio_segment_builds_bounded_ffmpeg_command(monkeypatch, tmp_path) -> None:
    calls = []
    monkeypatch.setattr(transcribe, "_run_command", lambda command, **kwargs: calls.append((command, kwargs)))
    output = transcribe._extract_audio_segment("source.mp4", 12.5, 7.5, sample_rate=16_000, output_dir=str(tmp_path))
    command, kwargs = calls[0]
    assert command[:6] == ["ffmpeg", "-y", "-ss", "12.500000", "-i", "source.mp4"]
    assert command[command.index("-t") + 1] == "7.500000"
    assert command[command.index("-ar") + 1] == "16000"
    assert Path(output).parent == tmp_path
    assert kwargs["timeout"] > 0
    Path(output).unlink()


@pytest.mark.parametrize(
    "start,duration,sample_rate",
    [(-1, 1, 16_000), (True, 1, 16_000), (0, 0, 16_000), (0, float("inf"), 16_000), (0, 1, 0)],
)
def test_extract_audio_segment_rejects_invalid_parameters(start, duration, sample_rate) -> None:
    with pytest.raises(MCPVideoError) as exc:
        transcribe._extract_audio_segment("source.mp4", start, duration, sample_rate=sample_rate)
    assert exc.value.code == "invalid_parameter"


def test_extract_audio_segment_removes_temp_file_when_ffmpeg_fails(monkeypatch, tmp_path) -> None:
    def fail(command, **kwargs):
        assert Path(command[-1]).exists()
        raise RuntimeError("ffmpeg failed")

    monkeypatch.setattr(transcribe, "_run_command", fail)
    with pytest.raises(RuntimeError, match="ffmpeg failed"):
        transcribe._extract_audio_segment("source.mp4", 0, 1, output_dir=str(tmp_path))
    assert list(tmp_path.iterdir()) == []


def test_format_chunk_result_preserves_real_word_timings() -> None:
    result = runtime._format_chunk_result(
        {
            "text": "hello world",
            "language": "en",
            "segments": [
                {
                    "start": 0.1,
                    "end": 1.8,
                    "text": "hello world",
                    "words": [
                        {"word": "hello", "start": 0.1, "end": 0.6, "probability": 0.8},
                        {"word": "world", "start": 1.2, "end": 1.8},
                    ],
                }
            ],
        }
    )
    assert result["segments"][0]["words"][0]["start"] == 0.1
    assert result["segments"][0]["words"][0]["probability"] == 0.8
    assert result["segments"][0]["words"][1]["end"] == 1.8


def test_transcribe_chunk_requests_word_timestamps_and_cleans_up(monkeypatch, tmp_path) -> None:
    audio_path = tmp_path / "chunk.wav"
    audio_path.write_bytes(b"wav")
    seen = {}

    class Model:
        def transcribe(self, path, **options):
            seen.update(path=path, options=options)
            return {"text": "hello", "language": "en", "segments": []}

    monkeypatch.setattr(runtime, "_extract_audio_segment", lambda *args, **kwargs: str(audio_path))
    monkeypatch.setitem(sys.modules, "whisper", SimpleNamespace(load_model=lambda name: Model()))
    result = runtime._transcribe_chunk("source.mp4", _chunk(), model="base", language="en", work_dir=str(tmp_path))
    assert result["transcript"] == "hello"
    assert seen["options"] == {"word_timestamps": True, "task": "transcribe", "language": "en"}
    assert not audio_path.exists()


def test_transcribe_chunk_missing_whisper_is_actionable_and_cleans_up(monkeypatch, tmp_path) -> None:
    audio_path = tmp_path / "chunk.wav"
    audio_path.write_bytes(b"wav")
    monkeypatch.setattr(runtime, "_extract_audio_segment", lambda *args, **kwargs: str(audio_path))
    monkeypatch.setitem(sys.modules, "whisper", None)
    with pytest.raises(MCPVideoError) as exc:
        runtime._transcribe_chunk("source.mp4", _chunk(), model="base", language=None, work_dir=str(tmp_path))
    assert exc.value.code == "missing_whisper"
    assert exc.value.suggested_action["auto_fix"] is False
    assert not audio_path.exists()
