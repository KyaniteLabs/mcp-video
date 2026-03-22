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


def run_cli_json(*args: str, expect_fail: bool = False) -> subprocess.CompletedProcess:
    """Run mcp-video CLI with --format json and return result."""
    return run_cli("--format", "json", *args, expect_fail=expect_fail)


class TestCLIVersion:
    def test_version_flag(self):
        result = run_cli("--version")
        assert "0.4.0" in result.stdout


class TestCLIInfo:
    def test_info_outputs_json(self, sample_video):
        result = run_cli_json("info", sample_video)
        data = json.loads(result.stdout)
        assert data["width"] == 640
        assert data["height"] == 480
        assert data["duration"] > 0

    def test_info_outputs_text(self, sample_video):
        result = run_cli("info", sample_video)
        assert "Video Info" in result.stdout
        assert "640" in result.stdout
        assert "480" in result.stdout


class TestCLIPreview:
    def test_preview_outputs_json(self, sample_video):
        result = run_cli_json("preview", sample_video)
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["operation"] == "preview"


class TestCLIStoryboard:
    def test_storyboard_outputs_json(self, sample_video):
        result = run_cli_json("storyboard", sample_video, "-n", "4")
        data = json.loads(result.stdout)
        assert data["count"] == 4

    def test_storyboard_outputs_text(self, sample_video):
        result = run_cli("storyboard", sample_video, "-n", "4")
        assert "Storyboard" in result.stdout


class TestCLITrim:
    def test_trim_outputs_json(self, sample_video):
        result = run_cli_json("trim", sample_video, "-s", "0", "-d", "1")
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["operation"] == "trim"

    def test_trim_outputs_text(self, sample_video):
        result = run_cli("trim", sample_video, "-s", "0", "-d", "1")
        assert "Done" in result.stdout


class TestCLIConvert:
    def test_convert_outputs_json(self, sample_video):
        result = run_cli_json("convert", sample_video, "-f", "webm")
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["format"] == "webm"


class TestCLIError:
    def test_invalid_file_outputs_json_error(self):
        result = run_cli_json("info", "/nonexistent/video.mp4", expect_fail=True)
        assert result.returncode != 0
        data = json.loads(result.stderr)
        assert data["success"] is False
        assert "error" in data

    def test_invalid_file_outputs_text_error(self):
        result = run_cli("info", "/nonexistent/video.mp4", expect_fail=True)
        assert result.returncode != 0
        assert "Error" in result.stderr


class TestCLIFilter:
    def test_filter_blur_outputs_json(self, sample_video):
        result = run_cli_json("filter", sample_video, "-t", "blur")
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["operation"] == "filter_blur"

    def test_filter_color_preset_outputs_json(self, sample_video):
        result = run_cli_json("filter", sample_video, "-t", "color_preset", '--params', '{"preset": "warm"}')
        data = json.loads(result.stdout)
        assert data["success"] is True


class TestCLIBlur:
    def test_blur_outputs_json(self, sample_video):
        result = run_cli_json("blur", sample_video)
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["operation"] == "filter_blur"


class TestCLIColorGrade:
    def test_color_grade_outputs_json(self, sample_video):
        result = run_cli_json("color-grade", sample_video, "-p", "cinematic")
        data = json.loads(result.stdout)
        assert data["success"] is True


class TestCLINormalizeAudio:
    def test_normalize_audio_outputs_json(self, sample_video):
        result = run_cli_json("normalize-audio", sample_video)
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["operation"] == "normalize_audio"


class TestCLIOverlayVideo:
    def test_overlay_video_outputs_json(self, sample_video, sample_video_2):
        result = run_cli_json("overlay-video", sample_video, sample_video_2)
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["operation"] == "overlay_video"


class TestCLISplitScreen:
    def test_split_screen_outputs_json(self, sample_video, sample_video_2):
        result = run_cli_json("split-screen", sample_video, sample_video_2)
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert "split_screen" in data["operation"]


class TestCLIBatch:
    def test_batch_outputs_json(self, sample_video):
        result = run_cli_json("batch", sample_video, "--operation", "trim", '--params', '{"start": "0", "duration": "1"}')
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["succeeded"] == 1

    def test_batch_outputs_text(self, sample_video):
        result = run_cli("batch", sample_video, "--operation", "trim", '--params', '{"start": "0", "duration": "1"}')
        assert "Batch Results" in result.stdout


class TestCLITemplate:
    def test_templates_list(self):
        result = run_cli("templates")
        assert "tiktok" in result.stdout
        assert "youtube" in result.stdout
        assert "instagram" in result.stdout

    def test_template_tiktok_outputs_json(self, sample_video):
        result = run_cli_json("template", "tiktok", sample_video, "--caption", "Test")
        data = json.loads(result.stdout)
        assert data["success"] is True
