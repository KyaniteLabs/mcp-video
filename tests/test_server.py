"""Tests for the MCP server tool layer — needs FFmpeg."""

import json
import os

import pytest

from mcp_video.engine import _check_filter_available
from mcp_video.server import (
    _error_result,
    _result,
    mcp,
    templates_resource,
    video_add_audio,
    video_add_text,
    video_batch,
    video_blur,
    video_color_grade,
    video_convert,
    video_crop,
    video_edit,
    video_export,
    video_extract_audio,
    video_fade,
    video_filter,
    video_info,
    video_merge,
    video_normalize_audio,
    video_overlay,
    video_preview,
    video_resize,
    video_rotate,
    video_speed,
    video_split_screen,
    video_storyboard,
    video_thumbnail,
    video_trim,
    video_watermark,
)
from mcp_video.errors import MCPVideoError, InputFileError


def requires_filter(name: str, feature: str):
    return pytest.mark.skipif(
        not _check_filter_available(name),
        reason=f"FFmpeg filter '{name}' not available ({feature} requires it)",
    )


class TestServerInitialization:
    def test_mcp_instance(self):
        assert mcp is not None
        assert mcp.name == "mcp-video"

    def test_tools_registered(self):
        # Check that the server has tools registered
        tool_names = [t.name for t in mcp._tool_manager.list_tools()]
        assert "video_info" in tool_names
        assert "video_trim" in tool_names
        assert "video_merge" in tool_names
        assert "video_add_text" in tool_names
        assert "video_add_audio" in tool_names
        assert "video_resize" in tool_names
        assert "video_convert" in tool_names
        assert "video_speed" in tool_names
        assert "video_thumbnail" in tool_names
        assert "video_preview" in tool_names
        assert "video_storyboard" in tool_names
        assert "video_export" in tool_names
        assert "video_edit" in tool_names
        assert "video_extract_audio" in tool_names
        assert "video_crop" in tool_names
        assert "video_rotate" in tool_names
        assert "video_fade" in tool_names
        assert "video_filter" in tool_names
        assert "video_blur" in tool_names
        assert "video_color_grade" in tool_names
        assert "video_normalize_audio" in tool_names
        assert "video_overlay" in tool_names
        assert "video_split_screen" in tool_names
        assert "video_batch" in tool_names

    def test_resources_registered(self):
        # Verify templates resource is defined (can't call async list_resources in sync test)
        assert templates_resource is not None
        result = templates_resource()
        assert len(result) > 0


class TestVideoInfoTool:
    def test_returns_metadata(self, sample_video):
        result = video_info(sample_video)
        assert result["success"] is True
        info = result["info"]
        assert info["width"] == 640
        assert info["height"] == 480
        assert info["duration"] > 0

    def test_nonexistent_file(self):
        result = video_info("/nonexistent/video.mp4")
        assert result["success"] is False
        assert "error" in result


class TestVideoTrimTool:
    def test_returns_success(self, sample_video):
        result = video_trim(sample_video, start="0", duration="1")
        assert result["success"] is True
        assert os.path.isfile(result["output_path"])

    def test_error_result(self):
        result = video_trim("/nonexistent/video.mp4", start="0", duration="1")
        assert result["success"] is False
        assert "error" in result


class TestVideoMergeTool:
    def test_returns_success(self, sample_video):
        result = video_merge([sample_video, sample_video])
        assert result["success"] is True
        assert os.path.isfile(result["output_path"])

    def test_empty_clips_error(self):
        result = video_merge([])
        assert result["success"] is False
        assert "error" in result


class TestVideoAddTextTool:
    @requires_filter("drawtext", "Text overlay")
    def test_returns_success(self, sample_video):
        result = video_add_text(sample_video, text="Hello")
        assert result["success"] is True
        assert os.path.isfile(result["output_path"])

    def test_error_on_missing_filter(self, sample_video):
        if not _check_filter_available("drawtext"):
            result = video_add_text(sample_video, text="Hello")
            assert result["success"] is False
            assert "error" in result


class TestVideoAddAudioTool:
    def test_returns_success(self, sample_video, sample_audio):
        result = video_add_audio(sample_video, sample_audio)
        assert result["success"] is True
        assert os.path.isfile(result["output_path"])


class TestVideoResizeTool:
    def test_returns_success(self, sample_video):
        result = video_resize(sample_video, width=320, height=240)
        assert result["success"] is True
        assert os.path.isfile(result["output_path"])


class TestVideoConvertTool:
    def test_returns_success(self, sample_video):
        result = video_convert(sample_video, format="webm")
        assert result["success"] is True
        assert result["format"] == "webm"


class TestVideoSpeedTool:
    def test_returns_success(self, sample_video):
        result = video_speed(sample_video, factor=2.0)
        assert result["success"] is True
        assert os.path.isfile(result["output_path"])


class TestVideoThumbnailTool:
    def test_returns_success(self, sample_video):
        result = video_thumbnail(sample_video, timestamp=1.0)
        assert result["success"] is True
        assert os.path.isfile(result["frame_path"])


class TestVideoPreviewTool:
    def test_returns_success(self, sample_video):
        result = video_preview(sample_video)
        assert result["success"] is True
        assert os.path.isfile(result["output_path"])


class TestVideoStoryboardTool:
    def test_returns_success(self, sample_video):
        result = video_storyboard(sample_video, frame_count=4)
        assert result["success"] is True
        assert result["count"] == 4


class TestVideoExportTool:
    def test_returns_success(self, sample_video):
        result = video_export(sample_video)
        assert result["success"] is True
        assert os.path.isfile(result["output_path"])


class TestVideoExtractAudioTool:
    def test_returns_success(self, sample_video):
        result = video_extract_audio(sample_video)
        assert result["success"] is True
        assert os.path.isfile(result["output_path"])
        assert result["operation"] == "extract_audio"


class TestVideoEditTool:
    def test_valid_timeline(self, sample_video):
        timeline = {
            "width": 640,
            "height": 480,
            "tracks": [
                {
                    "type": "video",
                    "clips": [{"source": sample_video}],
                }
            ],
            "export": {"format": "mp4", "quality": "low"},
        }
        result = video_edit(timeline)
        assert result["success"] is True

    def test_invalid_timeline_json(self):
        result = video_edit({"width": "not_a_number"})
        assert result["success"] is False
        assert "error" in result

    def test_empty_tracks(self):
        result = video_edit({"tracks": []})
        assert result["success"] is False
        assert "error" in result


class TestErrorHandling:
    def test_error_result_helper(self):
        err = InputFileError("/bad/path.mp4")
        result = _error_result(err)
        assert result["success"] is False
        assert result["error"]["type"] == "input_error"
        assert result["error"]["code"] == "invalid_input"

    def test_result_helper_with_model(self):
        from mcp_video.models import EditResult
        edit = EditResult(output_path="/tmp/out.mp4", operation="trim")
        result = _result(edit)
        assert result["success"] is True
        assert result["output_path"] == "/tmp/out.mp4"

    def test_result_helper_with_string(self):
        result = _result("/tmp/audio.mp3")
        assert result["success"] is True
        assert result["output_path"] == "/tmp/audio.mp3"


class TestTemplatesResource:
    def test_returns_json(self):
        result = templates_resource()
        data = json.loads(result)
        assert "aspect_ratios" in data
        assert "quality_presets" in data
        assert "transition_types" in data
        assert "export_formats" in data
        assert "text_positions" in data

    def test_aspect_ratios_content(self):
        result = templates_resource()
        data = json.loads(result)
        ratios = data["aspect_ratios"]
        assert "16:9" in ratios
        assert "9:16" in ratios

    def test_export_formats_content(self):
        result = templates_resource()
        data = json.loads(result)
        formats = data["export_formats"]
        assert "mp4" in formats
        assert "webm" in formats
        assert "gif" in formats
        assert "mov" in formats


class TestVideoCropTool:
    def test_returns_success(self, sample_video):
        result = video_crop(sample_video, width=320, height=240)
        assert result["success"] is True
        assert os.path.isfile(result["output_path"])

    def test_error_on_too_large(self, sample_video):
        result = video_crop(sample_video, width=9999, height=9999)
        assert result["success"] is False
        assert "error" in result


class TestVideoRotateTool:
    def test_rotate_90(self, sample_video):
        result = video_rotate(sample_video, angle=90)
        assert result["success"] is True
        assert os.path.isfile(result["output_path"])

    def test_flip_horizontal(self, sample_video):
        result = video_rotate(sample_video, flip_horizontal=True)
        assert result["success"] is True
        assert os.path.isfile(result["output_path"])

    def test_error_on_invalid_angle(self, sample_video):
        result = video_rotate(sample_video, angle=45)
        assert result["success"] is False
        assert "error" in result


class TestVideoFadeTool:
    def test_fade_in_and_out(self, sample_video):
        result = video_fade(sample_video, fade_in=0.5, fade_out=0.5)
        assert result["success"] is True
        assert os.path.isfile(result["output_path"])

    def test_error_on_no_fade(self, sample_video):
        result = video_fade(sample_video, fade_in=0, fade_out=0)
        assert result["success"] is False
        assert "error" in result


class TestVideoFilterTool:
    @requires_filter("boxblur", "Blur filter")
    def test_blur_filter(self, sample_video):
        result = video_filter(sample_video, filter_type="blur")
        assert result["success"] is True
        assert os.path.isfile(result["output_path"])

    @requires_filter("eq", "Color preset filter")
    def test_color_preset_filter(self, sample_video):
        result = video_filter(sample_video, filter_type="color_preset", params={"preset": "warm"})
        assert result["success"] is True
        assert os.path.isfile(result["output_path"])

    def test_error_on_missing_filter(self, sample_video):
        if not _check_filter_available("boxblur"):
            result = video_filter(sample_video, filter_type="blur")
            assert result["success"] is False
            assert "error" in result


class TestVideoBlurTool:
    @requires_filter("boxblur", "Blur filter")
    def test_blur_default(self, sample_video):
        result = video_blur(sample_video)
        assert result["success"] is True
        assert os.path.isfile(result["output_path"])

    @requires_filter("boxblur", "Blur filter")
    def test_blur_custom_radius(self, sample_video):
        result = video_blur(sample_video, radius=10, strength=2)
        assert result["success"] is True


class TestVideoColorGradeTool:
    @requires_filter("eq", "Color preset filter")
    def test_warm_preset(self, sample_video):
        result = video_color_grade(sample_video, preset="warm")
        assert result["success"] is True
        assert os.path.isfile(result["output_path"])


class TestVideoNormalizeAudioTool:
    @requires_filter("loudnorm", "Audio normalization")
    def test_normalize_default(self, sample_video):
        result = video_normalize_audio(sample_video)
        assert result["success"] is True
        assert os.path.isfile(result["output_path"])
        assert result["operation"] == "normalize_audio"

    @requires_filter("loudnorm", "Audio normalization")
    def test_normalize_broadcast(self, sample_video):
        result = video_normalize_audio(sample_video, target_lufs=-23.0)
        assert result["success"] is True


class TestVideoOverlayTool:
    def test_overlay_default(self, sample_video, sample_video_2):
        result = video_overlay(sample_video, overlay_path=sample_video_2)
        assert result["success"] is True
        assert os.path.isfile(result["output_path"])

    def test_overlay_with_scale(self, sample_video, sample_video_2):
        result = video_overlay(sample_video, overlay_path=sample_video_2, width=160, height=120)
        assert result["success"] is True

    def test_error_on_missing_file(self, sample_video):
        result = video_overlay(sample_video, overlay_path="/nonexistent/video.mp4")
        assert result["success"] is False
        assert "error" in result


class TestVideoSplitScreenTool:
    def test_side_by_side(self, sample_video, sample_video_2):
        result = video_split_screen(sample_video, right_path=sample_video_2)
        assert result["success"] is True
        assert os.path.isfile(result["output_path"])

    def test_top_bottom(self, sample_video, sample_video_2):
        result = video_split_screen(sample_video, right_path=sample_video_2, layout="top-bottom")
        assert result["success"] is True


class TestVideoBatchTool:
    def test_batch_trim(self, sample_video):
        result = video_batch(
            [sample_video, sample_video],
            operation="trim",
            params={"start": "0", "duration": "1"},
        )
        assert result["success"] is True
        assert result["total"] == 2
        assert result["succeeded"] == 2
        assert result["failed"] == 0

    def test_batch_convert(self, sample_video):
        result = video_batch(
            [sample_video],
            operation="convert",
            params={"format": "webm"},
        )
        assert result["success"] is True
        assert result["succeeded"] == 1

    def test_batch_empty_inputs(self):
        result = video_batch([], operation="trim")
        assert result["success"] is False
        assert "error" in result

    def test_batch_unknown_operation(self, sample_video):
        result = video_batch([sample_video], operation="nonexistent")
        assert result["success"] is False
        assert result["failed"] == 1

    def test_batch_partial_failure(self, sample_video):
        result = video_batch(
            [sample_video, "/nonexistent/video.mp4"],
            operation="trim",
            params={"start": "0", "duration": "1"},
        )
        assert result["success"] is False
        assert result["succeeded"] == 1
        assert result["failed"] == 1

    def test_batch_output_dir(self, sample_video, tmp_path):
        """Regression: output_dir must actually be used by batch operations."""
        out_dir = str(tmp_path / "batch_out")
        result = video_batch(
            [sample_video],
            operation="trim",
            params={"start": "0", "duration": "1"},
            output_dir=out_dir,
        )
        assert result["success"] is True
        assert result["succeeded"] == 1
        # Output file should be in the specified directory, not next to the input
        output_path = result["results"][0]["output_path"]
        assert os.path.dirname(output_path) == out_dir
