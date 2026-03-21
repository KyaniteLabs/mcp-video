"""Tests for CLI commands via subprocess — needs FFmpeg."""

import json
import subprocess
import sys

import pytest


def run_cli(*args: str, expect_fail: bool = False) -> subprocess.CompletedProcess:
    """Run mcp-video CLI and return result."""
    cmd = [sys.executable, "-m", "mcp_video"] + list(args)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if not expect_fail and result.returncode != 0:
        pytest.fail(f"CLI failed: {result.stderr}")
    return result


class TestCLIInfo:
    def test_info_outputs_json(self, sample_video):
        result = run_cli("info", sample_video)
        data = json.loads(result.stdout)
        assert data["width"] == 640
        assert data["height"] == 480
        assert data["duration"] > 0


class TestCLIPreview:
    def test_preview_outputs_json(self, sample_video):
        result = run_cli("preview", sample_video)
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["operation"] == "preview"


class TestCLIStoryboard:
    def test_storyboard_outputs_json(self, sample_video):
        result = run_cli("storyboard", sample_video, "-n", "4")
        data = json.loads(result.stdout)
        assert data["count"] == 4


class TestCLITrim:
    def test_trim_outputs_json(self, sample_video):
        result = run_cli("trim", sample_video, "-s", "0", "-d", "1")
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["operation"] == "trim"


class TestCLIConvert:
    def test_convert_outputs_json(self, sample_video):
        result = run_cli("convert", sample_video, "-f", "webm")
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["format"] == "webm"


class TestCLIError:
    def test_invalid_file_outputs_error(self):
        result = run_cli("info", "/nonexistent/video.mp4", expect_fail=True)
        assert result.returncode != 0
        # Error should be JSON on stderr
        data = json.loads(result.stderr)
        assert data["success"] is False
        assert "error" in data


class TestCLIFilter:
    def test_filter_blur_outputs_json(self, sample_video):
        result = run_cli("filter", sample_video, "-t", "blur")
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["operation"] == "filter_blur"

    def test_filter_color_preset_outputs_json(self, sample_video):
        result = run_cli("filter", sample_video, "-t", "color_preset", '--params', '{"preset": "warm"}')
        data = json.loads(result.stdout)
        assert data["success"] is True


class TestCLIBlur:
    def test_blur_outputs_json(self, sample_video):
        result = run_cli("blur", sample_video)
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["operation"] == "filter_blur"


class TestCLIColorGrade:
    def test_color_grade_outputs_json(self, sample_video):
        result = run_cli("color-grade", sample_video, "-p", "cinematic")
        data = json.loads(result.stdout)
        assert data["success"] is True


class TestCLINormalizeAudio:
    def test_normalize_audio_outputs_json(self, sample_video):
        result = run_cli("normalize-audio", sample_video)
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["operation"] == "normalize_audio"


class TestCLIOverlayVideo:
    def test_overlay_video_outputs_json(self, sample_video, sample_video_2):
        result = run_cli("overlay-video", sample_video, sample_video_2)
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["operation"] == "overlay_video"


class TestCLISplitScreen:
    def test_split_screen_outputs_json(self, sample_video, sample_video_2):
        result = run_cli("split-screen", sample_video, sample_video_2)
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert "split_screen" in data["operation"]


class TestCLIBatch:
    def test_batch_outputs_json(self, sample_video):
        result = run_cli("batch", sample_video, "-o", "trim", '--params', '{"start": "0", "duration": "1"}')
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["succeeded"] == 1
