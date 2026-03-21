"""Tests for the FFmpeg engine."""

import json
import os

import pytest

from mcp_video.engine import (
    _check_filter_available,
    _generate_thumbnail_base64,
    _parse_ffmpeg_time,
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
from mcp_video.errors import MCPVideoError, InputFileError
from mcp_video.models import VideoInfo


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
        from mcp_video.engine import resize
        result = resize(sample_video, width=320, height=240)
        assert os.path.isfile(result.output_path)
        info = probe(result.output_path)
        assert info.width == 320
        assert info.height == 240

    def test_resize_by_aspect_ratio(self, sample_video):
        from mcp_video.engine import resize
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


class TestProgressCallbacks:
    """Tests for progress callback functionality."""

    def test_parse_ffmpeg_time_parsing(self):
        """Test _parse_ffmpeg_time with various time formats."""
        # Format: HH:MM:SS.xx
        assert _parse_ffmpeg_time("00:00:05.12") == 5.12
        assert _parse_ffmpeg_time("00:01:30.00") == 90.0
        assert _parse_ffmpeg_time("00:00:00.00") == 0.0
        assert _parse_ffmpeg_time("01:00:00.00") == 3600.0
        assert _parse_ffmpeg_time("00:00:59.99") == 59.99

    def test_parse_ffmpeg_time_invalid_format(self):
        """Test _parse_ffmpeg_time with invalid format returns 0.0."""
        assert _parse_ffmpeg_time("invalid") == 0.0
        assert _parse_ffmpeg_time("00:00") == 0.0
        assert _parse_ffmpeg_time("") == 0.0

    def test_run_ffmpeg_with_progress_no_duration(self, sample_video, tmp_path):
        """When estimated_duration is None, should fall back to regular _run_ffmpeg."""
        from mcp_video.engine import _run_ffmpeg_with_progress
        import subprocess

        # Create a simple FFmpeg command
        output = str(tmp_path / "output.mp4")
        args = [
            "-i", sample_video,
            "-t", "1",
            "-c", "copy",
            output,
        ]

        # With estimated_duration=None, on_progress should not be called
        progress_calls = []
        def mock_on_progress(pct):
            progress_calls.append(pct)

        result = _run_ffmpeg_with_progress(args, estimated_duration=None, on_progress=mock_on_progress)
        assert isinstance(result, subprocess.CompletedProcess)
        # Progress callback should not have been called (falls back to regular _run_ffmpeg)
        assert len(progress_calls) == 0

    def test_run_ffmpeg_with_progress_convert(self, sample_video):
        """Use convert with on_progress callback, verify progress reaches 100."""
        progress_values = []

        def track_progress(pct):
            progress_values.append(pct)

        result = convert(sample_video, format="webm", on_progress=track_progress)

        # Verify the conversion succeeded
        assert os.path.isfile(result.output_path)
        assert result.format == "webm"

        # Verify progress was tracked and reached 100
        assert len(progress_values) > 0
        assert 100.0 in progress_values

    def test_convert_returns_progress_field(self, sample_video):
        """Verify that convert returns EditResult with progress=100.0."""
        result = convert(sample_video, format="webm")
        assert result.progress == 100.0
        assert result.success is True


class TestThumbnailBase64:
    """Tests for base64 thumbnail generation."""

    def test_generate_thumbnail_base64_valid_video(self, sample_video):
        """Call _generate_thumbnail_base64 on a real video, verify it returns valid base64."""
        import base64

        thumb_b64 = _generate_thumbnail_base64(sample_video)
        assert isinstance(thumb_b64, str)
        assert len(thumb_b64) > 0

        # Verify it's valid base64 by attempting to decode it
        try:
            decoded = base64.b64decode(thumb_b64, validate=True)
            assert len(decoded) > 0
        except Exception as e:
            pytest.fail(f"Failed to decode base64 thumbnail: {e}")

    def test_generate_thumbnail_base64_invalid_path(self):
        """Call with nonexistent path, verify it returns None."""
        result = _generate_thumbnail_base64("/nonexistent/video.mp4")
        assert result is None
