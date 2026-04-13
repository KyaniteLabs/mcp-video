"""End-to-end workflow tests — needs FFmpeg."""

import os

import pytest

from mcp_video import Client
from mcp_video.engine import (
    _check_filter_available,
    get_duration,
    probe,
)
from mcp_video.templates import tiktok_template


def requires_filter(name: str, feature: str):
    return pytest.mark.skipif(
        not _check_filter_available(name),
        reason=f"FFmpeg filter '{name}' not available ({feature} requires it)",
    )


@pytest.fixture
def editor():
    return Client()


class TestTikTokWorkflow:
    """trim -> add_text -> resize(9:16) -> add_audio -> export"""

    @requires_filter("drawtext", "Text overlay")
    def test_tiktok_workflow(self, editor, sample_video, sample_audio):
        # 1. Trim
        trimmed = editor.trim(sample_video, start="0", duration="2")
        assert os.path.isfile(trimmed.output_path)

        # 2. Add text
        titled = editor.add_text(
            trimmed.output_path, text="Follow for more!",
            position="bottom-center", size=36,
        )
        assert os.path.isfile(titled.output_path)

        # 3. Resize to 9:16
        resized = editor.resize(titled.output_path, aspect_ratio="9:16")
        assert os.path.isfile(resized.output_path)
        info = probe(resized.output_path)
        assert info.width == 1080
        assert info.height == 1920

        # 4. Add audio
        with_audio = editor.add_audio(resized.output_path, sample_audio, volume=0.5)
        assert os.path.isfile(with_audio.output_path)

        # 5. Export
        final = editor.export(with_audio.output_path, quality="medium")
        assert os.path.isfile(final.output_path)


class TestYouTubeWorkflow:
    """merge(2 clips) -> add_text(title, timed) -> resize(16:9) -> export"""

    @requires_filter("drawtext", "Text overlay")
    def test_youtube_workflow(self, editor, sample_video):
        # 1. Merge two clips
        merged = editor.merge([sample_video, sample_video])
        assert os.path.isfile(merged.output_path)

        # 2. Add title text
        titled = editor.add_text(
            merged.output_path, text="EPISODE 1",
            position="top-center", size=48,
            start_time=0, duration=2,
        )
        assert os.path.isfile(titled.output_path)

        # 3. Resize to 16:9
        resized = editor.resize(titled.output_path, aspect_ratio="16:9")
        assert os.path.isfile(resized.output_path)

        # 4. Export
        final = editor.export(resized.output_path, quality="high")
        assert os.path.isfile(final.output_path)


class TestGifConversionWorkflow:
    """trim -> convert(gif) -> verify file size"""

    def test_gif_workflow(self, editor, sample_video):
        # 1. Trim to short clip
        trimmed = editor.trim(sample_video, start="0", duration="1")
        assert os.path.isfile(trimmed.output_path)

        # 2. Convert to GIF
        gif_result = editor.convert(trimmed.output_path, format="gif", quality="low")
        assert os.path.isfile(gif_result.output_path)
        assert gif_result.format == "gif"

        # 3. Verify file size is reasonable (< 5 MB for 1s clip)
        size_mb = os.path.getsize(gif_result.output_path) / (1024 * 1024)
        assert size_mb < 5.0


class TestStoryboardReviewWorkflow:
    """video -> storyboard -> verify frames -> preview"""

    def test_storyboard_workflow(self, editor, sample_video):
        # 1. Generate storyboard
        sb = editor.storyboard(sample_video, frame_count=4)
        assert sb.count == 4
        for frame in sb.frames:
            assert os.path.isfile(frame)

        # 2. Extract a thumbnail from one of the timestamps
        dur = get_duration(sample_video)
        ts = dur * 0.5
        thumb = editor.thumbnail(sample_video, timestamp=ts)
        assert os.path.isfile(thumb.frame_path)

        # 3. Generate a preview
        prev = editor.preview(sample_video)
        assert os.path.isfile(prev.output_path)


class TestTemplateWorkflow:
    """tiktok_template -> client.edit() -> verify output"""

    @requires_filter("drawtext", "Text overlay")
    def test_template_workflow(self, editor, sample_video):
        # 1. Generate template
        tl = tiktok_template(sample_video, caption="Test caption")
        assert tl["width"] == 1080
        assert tl["height"] == 1920

        # 2. Execute via client.edit()
        # Note: edit will try to use drawtext for the caption
        # which requires the filter
        result = editor.edit(tl)
        assert os.path.isfile(result.output_path)


class TestAudioExtractionWorkflow:
    """video -> extract_audio(mp3) -> verify file exists and is playable"""

    def test_audio_extraction_workflow(self, editor, sample_video):
        # 1. Extract audio as MP3
        mp3_result = editor.extract_audio(sample_video, format="mp3")
        assert os.path.isfile(mp3_result.output_path)
        assert mp3_result.output_path.endswith(".mp3")

        # 2. Verify file size is reasonable
        size = os.path.getsize(mp3_result.output_path)
        assert size > 0

        # 3. Also extract as WAV
        wav_result = editor.extract_audio(sample_video, format="wav")
        assert os.path.isfile(wav_result.output_path)
        assert wav_result.output_path.endswith(".wav")
        wav_size = os.path.getsize(wav_result.output_path)
        assert wav_size > size  # WAV should be larger


class TestSpeedChangeWorkflow:
    """video -> speed(0.5x) -> verify duration doubled -> speed(2x) -> verify ~original"""

    def test_speed_workflow(self, editor, sample_video):
        # 1. Get original duration
        orig_info = probe(sample_video)
        orig_dur = orig_info.duration

        # 2. Slow down to 0.5x
        slow = editor.speed(sample_video, factor=0.5)
        slow_info = probe(slow.output_path)
        assert slow_info.duration >= orig_dur * 1.5

        # 3. Speed up the slow version back to 2x
        fast = editor.speed(slow.output_path, factor=2.0)
        fast_info = probe(fast.output_path)
        # Should be roughly back to original duration
        assert abs(fast_info.duration - orig_dur) < 0.5


class TestErrorRecoveryWorkflow:
    """nonexistent file -> verify error dict with suggested_action"""

    def test_error_recovery(self, editor):
        from mcp_video.errors import InputFileError

        # Operations on nonexistent file should raise InputFileError
        with pytest.raises(InputFileError) as exc_info:
            editor.info("/nonexistent/video.mp4")

        err = exc_info.value
        d = err.to_dict()
        assert d["type"] == "input_error"
        assert "suggested_action" in d
