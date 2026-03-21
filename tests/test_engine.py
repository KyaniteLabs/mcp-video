"""Tests for the FFmpeg engine."""

import json
import os

import pytest

from agentcut.engine import (
    _check_filter_available,
    add_audio,
    add_text,
    convert,
    extract_audio,
    merge,
    preview,
    probe,
    storyboard,
    speed,
    subtitles,
    thumbnail,
    trim,
    watermark,
)
from agentcut.errors import AgentCutError, InputFileError
from agentcut.models import VideoInfo


def requires_filter(name: str, feature: str):
    """Skip test if FFmpeg filter is not available."""
    return pytest.mark.skipif(
        not _check_filter_available(name),
        reason=f"FFmpeg filter '{name}' not available ({feature} requires it)",
    )


class TestProbe:
    def test_probe_returns_video_info(self, sample_video):
        info = probe(sample_video)
        assert isinstance(info, VideoInfo)
        assert info.duration > 0
        assert info.width == 640
        assert info.height == 480
        assert info.codec == "h264"
        assert info.audio_codec is not None

    def test_probe_nonexistent_file(self):
        with pytest.raises(InputFileError):
            probe("/nonexistent/video.mp4")

    def test_resolution_property(self, sample_video):
        info = probe(sample_video)
        assert info.resolution == "640x480"

    def test_aspect_ratio_property(self, sample_video):
        info = probe(sample_video)
        assert info.aspect_ratio == "4:3"

    def test_size_mb_property(self, sample_video):
        info = probe(sample_video)
        assert info.size_mb is not None
        assert info.size_mb > 0


class TestTrim:
    def test_trim_by_duration(self, sample_video):
        result = trim(sample_video, start="0", duration="1")
        assert os.path.isfile(result.output_path)
        info = probe(result.output_path)
        assert abs(info.duration - 1.0) < 0.5
        assert result.operation == "trim"

    def test_trim_by_end(self, sample_video):
        result = trim(sample_video, start="0", end="2")
        assert os.path.isfile(result.output_path)
        info = probe(result.output_path)
        assert abs(info.duration - 2.0) < 0.5

    def test_trim_custom_output(self, sample_video, tmp_path):
        out = str(tmp_path / "custom_trim.mp4")
        result = trim(sample_video, start="0", duration="1", output_path=out)
        assert result.output_path == out


class TestMerge:
    def test_merge_two_clips(self, sample_video):
        result = merge([sample_video, sample_video])
        assert os.path.isfile(result.output_path)
        info = probe(result.output_path)
        # Merged video should be roughly 2x duration
        assert info.duration > 4
        assert result.operation == "merge"

    def test_merge_single_clip(self, sample_video):
        result = merge([sample_video])
        assert os.path.isfile(result.output_path)

    def test_merge_no_clips_raises(self):
        with pytest.raises(InputFileError):
            merge([])


class TestAddText:
    @requires_filter("drawtext", "Text overlay")
    def test_add_text_overlay(self, sample_video):
        result = add_text(sample_video, text="Hello World")
        assert os.path.isfile(result.output_path)
        assert result.operation == "add_text"

    @requires_filter("drawtext", "Text overlay")
    def test_add_text_with_timing(self, sample_video):
        result = add_text(
            sample_video, text="Timed",
            start_time=0.5, duration=1.0,
        )
        assert os.path.isfile(result.output_path)


class TestAddAudio:
    def test_replace_audio(self, sample_video, sample_audio):
        result = add_audio(sample_video, sample_audio)
        assert os.path.isfile(result.output_path)
        assert result.operation == "add_audio"

    def test_mix_audio(self, sample_video, sample_audio):
        result = add_audio(sample_video, sample_audio, mix=True)
        assert os.path.isfile(result.output_path)

    def test_audio_with_fade(self, sample_video, sample_audio):
        result = add_audio(
            sample_video, sample_audio,
            fade_in=0.5, fade_out=0.5,
        )
        assert os.path.isfile(result.output_path)


class TestResize:
    def test_resize_by_dimensions(self, sample_video):
        from agentcut.engine import resize
        result = resize(sample_video, width=320, height=240)
        assert os.path.isfile(result.output_path)
        info = probe(result.output_path)
        assert info.width == 320
        assert info.height == 240

    def test_resize_by_aspect_ratio(self, sample_video):
        from agentcut.engine import resize
        result = resize(sample_video, aspect_ratio="1:1")
        assert os.path.isfile(result.output_path)
        info = probe(result.output_path)
        assert info.width == info.height


class TestConvert:
    def test_convert_to_webm(self, sample_video):
        result = convert(sample_video, format="webm")
        assert os.path.isfile(result.output_path)
        assert result.format == "webm"

    def test_convert_to_gif(self, sample_video):
        result = convert(sample_video, format="gif")
        assert os.path.isfile(result.output_path)
        assert result.format == "gif"


class TestSpeed:
    def test_double_speed(self, sample_video):
        result = speed(sample_video, factor=2.0)
        assert os.path.isfile(result.output_path)
        info = probe(result.output_path)
        orig = probe(sample_video)
        assert info.duration < orig.duration


class TestThumbnail:
    def test_extract_frame(self, sample_video):
        result = thumbnail(sample_video, timestamp=1.0)
        assert os.path.isfile(result.frame_path)
        assert result.timestamp == 1.0


class TestPreview:
    def test_generate_preview(self, sample_video):
        result = preview(sample_video)
        assert os.path.isfile(result.output_path)
        info = probe(result.output_path)
        orig = probe(sample_video)
        assert info.width < orig.width
        assert info.height < orig.height
        assert result.operation == "preview"


class TestStoryboard:
    def test_extract_frames(self, sample_video):
        result = storyboard(sample_video, frame_count=4)
        assert result.count == 4
        for frame in result.frames:
            assert os.path.isfile(frame)


class TestExtractAudio:
    def test_extract_mp3(self, sample_video):
        result = extract_audio(sample_video, format="mp3")
        assert os.path.isfile(result)


class TestSubtitles:
    @requires_filter("subtitles", "Subtitle burn-in")
    def test_burn_subtitles(self, sample_video, tmp_path):
        srt_path = tmp_path / "subs.srt"
        srt_path.write_text(
            "1\n00:00:00,000 --> 00:00:02,000\nTest subtitle\n"
        )
        result = subtitles(input_path=str(sample_video), subtitle_path=str(srt_path))
        assert os.path.isfile(result.output_path)
