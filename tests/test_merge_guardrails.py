"""Tests for merge_guardrails module."""

import pytest

from mcp_video.merge_guardrails import validate_merge_compatibility
from mcp_video.errors import MCPVideoError
from mcp_video.models import VideoInfo


def _make_info(
    path: str = "test.mp4",
    duration: float = 5.0,
    width: int = 320,
    height: int = 240,
    fps: float = 30.0,
    audio_codec: str | None = "aac",
) -> VideoInfo:
    return VideoInfo(
        path=path,
        duration=duration,
        width=width,
        height=height,
        fps=fps,
        codec="h264",
        audio_codec=audio_codec,
        audio_sample_rate=48000 if audio_codec else None,
    )


class TestValidateMergeCompatibility:
    def test_empty_list_no_warnings(self):
        assert validate_merge_compatibility([]) == []

    def test_single_clip_no_warnings(self):
        infos = [_make_info()]
        assert validate_merge_compatibility(infos) == []

    def test_identical_clips_no_warnings(self):
        infos = [_make_info(), _make_info()]
        assert validate_merge_compatibility(infos) == []

    def test_transition_too_long_raises(self):
        infos = [_make_info(duration=5.0), _make_info(duration=5.0)]
        with pytest.raises(MCPVideoError, match="transition_duration"):
            validate_merge_compatibility(infos, transition_duration=999.0)

    def test_zero_transition_clean(self):
        infos = [_make_info(), _make_info()]
        warnings = validate_merge_compatibility(infos, transition_duration=0.0)
        assert isinstance(warnings, list)

    def test_mixed_audio_warns(self):
        infos = [_make_info(audio_codec="aac"), _make_info(audio_codec=None)]
        warnings = validate_merge_compatibility(infos)
        assert any("mixed audio/no-audio" in w for w in warnings)

    def test_resolution_mismatch_warns(self):
        infos = [_make_info(width=320, height=240), _make_info(width=640, height=480)]
        warnings = validate_merge_compatibility(infos)
        assert any("different resolutions" in w for w in warnings)

    def test_fps_mismatch_warns(self):
        infos = [_make_info(fps=30.0), _make_info(fps=24.0)]
        warnings = validate_merge_compatibility(infos)
        assert any("different frame rates" in w for w in warnings)

    def test_zero_duration_raises(self):
        # Single clip returns [] — need 2 clips to trigger validation
        infos = [_make_info(duration=5.0), _make_info(duration=0.0)]
        with pytest.raises(MCPVideoError, match="zero or negative duration"):
            validate_merge_compatibility(infos)

    def test_transition_half_duration_warns(self):
        infos = [_make_info(duration=2.0), _make_info(duration=5.0)]
        warnings = validate_merge_compatibility(infos, transition_duration=1.5)
        assert any(">50%" in w for w in warnings)
