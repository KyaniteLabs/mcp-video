"""Tests for the Python client — needs FFmpeg."""

import os

import pytest

from agentcut import Client
from agentcut.engine import _check_filter_available
from agentcut.models import EditResult, StoryboardResult, ThumbnailResult, VideoInfo


def requires_filter(name: str, feature: str):
    return pytest.mark.skipif(
        not _check_filter_available(name),
        reason=f"FFmpeg filter '{name}' not available ({feature} requires it)",
    )


@pytest.fixture
def editor():
    return Client()


class TestClientInstantiation:
    def test_create_client(self):
        client = Client()
        assert client is not None


class TestClientInfo:
    def test_info_returns_video_info(self, editor, sample_video):
        info = editor.info(sample_video)
        assert isinstance(info, VideoInfo)
        assert info.duration > 0
        assert info.width == 640
        assert info.height == 480

    def test_info_nonexistent_file(self, editor):
        from agentcut.errors import InputFileError
        with pytest.raises(InputFileError):
            editor.info("/nonexistent/video.mp4")


class TestClientTrim:
    def test_trim_returns_edit_result(self, editor, sample_video):
        result = editor.trim(sample_video, start="0", duration="1")
        assert isinstance(result, EditResult)
        assert os.path.isfile(result.output_path)
        assert result.operation == "trim"

    def test_trim_passes_params(self, editor, sample_video):
        result = editor.trim(sample_video, start="0.5", end="2")
        assert isinstance(result, EditResult)
        assert os.path.isfile(result.output_path)

    def test_trim_custom_output(self, editor, sample_video, tmp_path):
        out = str(tmp_path / "custom.mp4")
        result = editor.trim(sample_video, start="0", duration="1", output=out)
        assert result.output_path == out


class TestClientMerge:
    def test_merge_returns_edit_result(self, editor, sample_video):
        result = editor.merge([sample_video, sample_video])
        assert isinstance(result, EditResult)
        assert os.path.isfile(result.output_path)
        assert result.operation == "merge"

    def test_merge_with_transitions(self, editor, sample_video):
        result = editor.merge(
            [sample_video, sample_video],
            transitions=["fade"],
        )
        assert isinstance(result, EditResult)


class TestClientAddText:
    @requires_filter("drawtext", "Text overlay")
    def test_add_text_returns_edit_result(self, editor, sample_video):
        result = editor.add_text(sample_video, text="Hello")
        assert isinstance(result, EditResult)
        assert os.path.isfile(result.output_path)

    @requires_filter("drawtext", "Text overlay")
    def test_add_text_passes_params(self, editor, sample_video):
        result = editor.add_text(
            sample_video, text="Test",
            position="bottom-center", font=None, size=36,
            color="yellow", shadow=False,
        )
        assert isinstance(result, EditResult)


class TestClientAddAudio:
    def test_add_audio_returns_edit_result(self, editor, sample_video, sample_audio):
        result = editor.add_audio(sample_video, sample_audio)
        assert isinstance(result, EditResult)
        assert os.path.isfile(result.output_path)

    def test_add_audio_with_mix(self, editor, sample_video, sample_audio):
        result = editor.add_audio(sample_video, sample_audio, mix=True)
        assert isinstance(result, EditResult)

    def test_add_audio_with_fade(self, editor, sample_video, sample_audio):
        result = editor.add_audio(
            sample_video, sample_audio,
            volume=0.8, fade_in=0.5, fade_out=0.5,
        )
        assert isinstance(result, EditResult)


class TestClientResize:
    def test_resize_returns_edit_result(self, editor, sample_video):
        result = editor.resize(sample_video, width=320, height=240)
        assert isinstance(result, EditResult)
        assert os.path.isfile(result.output_path)

    def test_resize_by_aspect_ratio(self, editor, sample_video):
        result = editor.resize(sample_video, aspect_ratio="1:1")
        assert isinstance(result, EditResult)
        assert os.path.isfile(result.output_path)


class TestClientConvert:
    def test_convert_returns_edit_result(self, editor, sample_video):
        result = editor.convert(sample_video, format="webm")
        assert isinstance(result, EditResult)
        assert result.format == "webm"

    def test_convert_gif(self, editor, sample_video):
        result = editor.convert(sample_video, format="gif")
        assert isinstance(result, EditResult)
        assert result.format == "gif"


class TestClientSpeed:
    def test_speed_returns_edit_result(self, editor, sample_video):
        result = editor.speed(sample_video, factor=2.0)
        assert isinstance(result, EditResult)
        assert os.path.isfile(result.output_path)


class TestClientThumbnail:
    def test_thumbnail_returns_thumbnail_result(self, editor, sample_video):
        result = editor.thumbnail(sample_video, timestamp=1.0)
        assert isinstance(result, ThumbnailResult)
        assert os.path.isfile(result.frame_path)
        assert result.timestamp == 1.0


class TestClientPreview:
    def test_preview_returns_edit_result(self, editor, sample_video):
        result = editor.preview(sample_video)
        assert isinstance(result, EditResult)
        assert os.path.isfile(result.output_path)
        assert result.operation == "preview"


class TestClientStoryboard:
    def test_storyboard_returns_storyboard_result(self, editor, sample_video):
        result = editor.storyboard(sample_video, frame_count=4)
        assert isinstance(result, StoryboardResult)
        assert result.count == 4
        for frame in result.frames:
            assert os.path.isfile(frame)


class TestClientSubtitles:
    @requires_filter("subtitles", "Subtitle burn-in")
    def test_subtitles_returns_edit_result(self, editor, sample_video, sample_srt):
        result = editor.subtitles(sample_video, sample_srt)
        assert isinstance(result, EditResult)
        assert os.path.isfile(result.output_path)


class TestClientWatermark:
    def test_watermark_returns_edit_result(self, editor, sample_video, sample_watermark_png):
        result = editor.watermark(sample_video, sample_watermark_png)
        assert isinstance(result, EditResult)
        assert os.path.isfile(result.output_path)


class TestClientExport:
    def test_export_returns_edit_result(self, editor, sample_video):
        result = editor.export(sample_video)
        assert isinstance(result, EditResult)
        assert os.path.isfile(result.output_path)


class TestClientEdit:
    @requires_filter("drawtext", "Text overlay")
    def test_edit_validates_timeline(self, editor, sample_video):
        timeline = {
            "width": 640,
            "height": 480,
            "tracks": [
                {
                    "type": "video",
                    "clips": [{"source": sample_video, "start": 0}],
                }
            ],
            "export": {"format": "mp4", "quality": "medium"},
        }
        result = editor.edit(timeline)
        assert isinstance(result, EditResult)

    def test_edit_invalid_timeline_raises(self, editor):
        with pytest.raises(Exception):
            editor.edit({"width": "not_an_int"})


class TestClientExtractAudio:
    def test_extract_audio_returns_string(self, editor, sample_video):
        result = editor.extract_audio(sample_video)
        assert isinstance(result, str)
        assert os.path.isfile(result)
