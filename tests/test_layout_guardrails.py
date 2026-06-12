"""Tests for layout grid and split screen guardrails."""

import subprocess

import pytest

from mcp_video.engine import split_screen
from mcp_video.engine_probe import probe


@pytest.fixture(scope="module")
def long_video(tmp_path_factory) -> str:
    """A 5s clip — long enough to trip the >1s duration-mismatch guardrail."""
    path = str(tmp_path_factory.mktemp("videos") / "long_video.mp4")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "smptehdbars=size=640x480:duration=5:rate=30",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-an",
            path,
        ],
        capture_output=True,
        timeout=30,
        check=True,
    )
    return path


class TestLayoutGridGuardrails:
    def test_excess_clips_warns(self, sample_video, tmp_path):
        from mcp_video.effects_engine import layout_grid

        out = str(tmp_path / "grid.mp4")
        with pytest.warns(UserWarning, match="GRID GUARDRAIL"):
            layout_grid([sample_video] * 4, "3x1", out)
        assert probe(out).duration > 0


class TestSplitScreenGuardrails:
    def test_duration_mismatch_warns(self, sample_video, long_video, tmp_path):
        out = str(tmp_path / "split.mp4")
        with pytest.warns(UserWarning, match="SPLIT GUARDRAIL"):
            result = split_screen(sample_video, long_video, output_path=out)
        assert result.success
        assert probe(out).duration > 0
