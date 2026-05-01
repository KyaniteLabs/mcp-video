"""Tests for shared FFmpeg helper contracts."""

import subprocess


def test_ffprobe_timeout_constant_exists():
    from mcp_video import limits

    assert hasattr(limits, "FFPROBE_TIMEOUT")
    assert limits.FFPROBE_TIMEOUT > 0
    assert limits.FFPROBE_TIMEOUT < limits.DEFAULT_FFMPEG_TIMEOUT


def test_run_ffprobe_json_uses_named_timeout(monkeypatch):
    from mcp_video import ffmpeg_helpers
    from mcp_video.limits import FFPROBE_TIMEOUT

    captured = {}

    class Result:
        stdout = '{"format": {}, "streams": []}'

    def fake_run_command(cmd, timeout=0):
        captured["timeout"] = timeout
        return Result()

    monkeypatch.setattr(ffmpeg_helpers, "_run_command", fake_run_command)

    assert ffmpeg_helpers._run_ffprobe_json("/tmp/video.mp4") == {"format": {}, "streams": []}
    assert captured["timeout"] == FFPROBE_TIMEOUT


def test_validate_input_path_rejects_null_bytes():
    from mcp_video.errors import InputFileError
    from mcp_video.ffmpeg_helpers import _validate_input_path

    try:
        _validate_input_path("/tmp/video\x00.mp4")
        raise AssertionError("Expected InputFileError")
    except InputFileError as e:
        assert "null bytes" in str(e).lower()


def test_validate_input_path_rejects_nonexistent_file():
    from mcp_video.errors import InputFileError
    from mcp_video.ffmpeg_helpers import _validate_input_path

    try:
        _validate_input_path("/nonexistent/path/video.mp4")
        raise AssertionError("Expected InputFileError")
    except InputFileError:
        pass


def test_validate_output_path_rejects_null_bytes():
    from mcp_video.errors import MCPVideoError
    from mcp_video.ffmpeg_helpers import _validate_output_path

    try:
        _validate_output_path("/tmp/video\x00.mp4")
        raise AssertionError("Expected MCPVideoError")
    except MCPVideoError as e:
        assert "null bytes" in str(e).lower()


def test_validate_output_path_accepts_parent_relative_paths():
    from mcp_video.ffmpeg_helpers import _validate_output_path

    assert _validate_output_path("../clips/output.mp4") == "../clips/output.mp4"


def test_validate_output_path_accepts_safe_paths():
    from mcp_video.ffmpeg_helpers import _validate_output_path

    assert _validate_output_path("output.mp4") == "output.mp4"
    assert _validate_output_path("/tmp/output.mp4") == "/tmp/output.mp4"
    assert _validate_output_path("foo/bar/baz.mp4") == "foo/bar/baz.mp4"


def test_run_ffmpeg_prepends_runtime_binary_for_raw_args(monkeypatch):
    from mcp_video import ffmpeg_helpers

    captured = {}

    def fake_ffmpeg():
        return "/custom/ffmpeg"

    def fake_run(cmd, capture_output, text, timeout):
        captured["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr("mcp_video.engine_runtime_utils._ffmpeg", fake_ffmpeg)
    monkeypatch.setattr(ffmpeg_helpers.subprocess, "run", fake_run)

    ffmpeg_helpers._run_ffmpeg(["-i", "input.mp4", "output.mp4"])

    assert captured["cmd"] == ["/custom/ffmpeg", "-y", "-i", "input.mp4", "output.mp4"]


def test_run_ffmpeg_preserves_full_ffprobe_command(monkeypatch):
    from mcp_video import ffmpeg_helpers

    captured = {}

    def fake_run(cmd, capture_output, text, timeout):
        captured["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, "320x240", "")

    monkeypatch.setattr(ffmpeg_helpers.subprocess, "run", fake_run)

    ffmpeg_helpers._run_ffmpeg(["ffprobe", "-v", "error", "video.mp4"])

    assert captured["cmd"] == ["ffprobe", "-v", "error", "video.mp4"]


def test_run_ffmpeg_preserves_full_ffmpeg_command(monkeypatch):
    from mcp_video import ffmpeg_helpers

    captured = {}

    def fake_run(cmd, capture_output, text, timeout):
        captured["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(ffmpeg_helpers.subprocess, "run", fake_run)

    ffmpeg_helpers._run_ffmpeg(["ffmpeg", "-y", "-i", "input.mp4", "output.mp4"])

    assert captured["cmd"] == ["ffmpeg", "-y", "-i", "input.mp4", "output.mp4"]
