"""Tests for visual effects engine behavior."""

from pathlib import Path

from mcp_video.errors import ProcessingError


def test_chromatic_aberration_falls_back_when_chromashift_missing(tmp_path, monkeypatch):
    from mcp_video import effects_engine

    input_path = tmp_path / "input.mp4"
    output_path = tmp_path / "output.mp4"
    input_path.write_bytes(b"placeholder")
    calls = []

    def fake_run_ffmpeg(cmd):
        calls.append(cmd.copy())
        if len(calls) == 1:
            raise ProcessingError(" ".join(cmd), 1, "No such filter: 'chromashift'")
        Path(cmd[-1]).write_bytes(b"output")

    monkeypatch.setattr(effects_engine.core, "_run_ffmpeg", fake_run_ffmpeg)

    result = effects_engine.effect_chromatic_aberration(str(input_path), str(output_path), intensity=3.0)

    assert result == str(output_path)
    assert len(calls) == 2
    assert calls[0][5].startswith("chromashift=")
    assert calls[1][5].startswith("colorbalance=")


def test_glow_falls_back_when_gblur_missing(tmp_path, monkeypatch):
    from mcp_video import effects_engine

    input_path = tmp_path / "input.mp4"
    output_path = tmp_path / "output.mp4"
    input_path.write_bytes(b"placeholder")
    calls = []

    def fake_run_ffmpeg(cmd):
        calls.append(cmd.copy())
        if len(calls) == 1:
            raise ProcessingError(" ".join(cmd), 1, "No such filter: 'gblur'")
        Path(cmd[-1]).write_bytes(b"output")

    monkeypatch.setattr(effects_engine.core, "_run_ffmpeg", fake_run_ffmpeg)

    result = effects_engine.effect_glow(str(input_path), str(output_path), radius=15)

    assert result == str(output_path)
    assert len(calls) == 2
    assert "gblur=sigma=15" in calls[0][5]
    assert "boxblur=15:15" in calls[1][5]


def test_chromatic_aberration_reraises_unrelated_processing_error(tmp_path, monkeypatch):
    from mcp_video import effects_engine

    input_path = tmp_path / "input.mp4"
    output_path = tmp_path / "output.mp4"
    input_path.write_bytes(b"placeholder")
    error = ProcessingError("ffmpeg", 1, "encoder failed")

    def fake_run_ffmpeg(cmd):
        raise error

    monkeypatch.setattr(effects_engine.core, "_run_ffmpeg", fake_run_ffmpeg)

    try:
        effects_engine.effect_chromatic_aberration(str(input_path), str(output_path))
    except ProcessingError as exc:
        assert exc is error
    else:
        raise AssertionError("Expected ProcessingError")
