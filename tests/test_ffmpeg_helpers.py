"""Tests for shared FFmpeg helper contracts."""


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

    def fake_run_ffmpeg(cmd, timeout=0):
        captured["timeout"] = timeout
        return Result()

    monkeypatch.setattr(ffmpeg_helpers, "_run_ffmpeg", fake_run_ffmpeg)

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


def test_validate_output_path_rejects_traversal():
    from mcp_video.errors import MCPVideoError
    from mcp_video.ffmpeg_helpers import _validate_output_path

    try:
        _validate_output_path("../../etc/passwd")
        raise AssertionError("Expected MCPVideoError")
    except MCPVideoError as e:
        assert "traversal" in str(e).lower()


def test_validate_output_path_accepts_safe_paths():
    from mcp_video.ffmpeg_helpers import _validate_output_path

    assert _validate_output_path("output.mp4") == "output.mp4"
    assert _validate_output_path("/tmp/output.mp4") == "/tmp/output.mp4"
    assert _validate_output_path("foo/bar/baz.mp4") == "foo/bar/baz.mp4"
