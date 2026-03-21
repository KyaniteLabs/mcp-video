"""Tests for the MCP server tool layer — needs FFmpeg."""

import json
import os

import pytest

from agentcut.engine import _check_filter_available
from agentcut.server import (
    _error_result,
    _result,
    mcp,
    templates_resource,
    video_add_audio,
    video_add_text,
    video_convert,
    video_edit,
    video_export,
    video_extract_audio,
    video_info,
    video_merge,
    video_preview,
    video_resize,
    video_speed,
    video_storyboard,
    video_thumbnail,
    video_trim,
    video_watermark,
)
from agentcut.errors import AgentCutError, InputFileError


def requires_filter(name: str, feature: str):
    return pytest.mark.skipif(
        not _check_filter_available(name),
        reason=f"FFmpeg filter '{name}' not available ({feature} requires it)",
    )


class TestServerInitialization:
    def test_mcp_instance(self):
        assert mcp is not None
        assert mcp.name == "agentcut"

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
        from agentcut.models import EditResult
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
