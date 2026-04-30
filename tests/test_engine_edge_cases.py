"""Tests for engine edge cases that raise errors or handle special inputs."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from mcp_video.errors import MCPVideoError


class TestEngineResizeEdgeCases:
    def test_zero_dimensions_raises(self):
        from mcp_video.engine_resize import resize

        mock_info = SimpleNamespace(width=0, height=0, duration=1.0, resolution="0x0")
        with patch("mcp_video.engine_resize.probe", return_value=mock_info):
            with patch("mcp_video.engine_resize._validate_input_path", return_value="/tmp/v.mp4"):
                with pytest.raises(MCPVideoError, match="zero dimensions"):
                    resize("/tmp/v.mp4")

    def test_unknown_aspect_ratio_raises(self):
        from mcp_video.engine_resize import resize

        mock_info = SimpleNamespace(width=640, height=480, duration=1.0, resolution="640x480", size_mb=1.0, format="mp4")
        with patch("mcp_video.engine_resize.probe", return_value=mock_info):
            with patch("mcp_video.engine_resize._validate_input_path", return_value="/tmp/v.mp4"):
                with pytest.raises(MCPVideoError, match="Unknown aspect ratio"):
                    resize("/tmp/v.mp4", aspect_ratio="99:1")


class TestEngineRotateAngles:
    def test_rotate_90(self):
        from mcp_video.engine_rotate import rotate

        mock_info = SimpleNamespace(width=640, height=480, duration=1.0, resolution="640x480", size_mb=1.0, format="mp4")
        with patch("mcp_video.engine_rotate.probe", return_value=mock_info):
            with patch("mcp_video.engine_rotate._validate_input_path", return_value="/tmp/v.mp4"):
                with patch("mcp_video.engine_rotate._run_ffmpeg"):
                    with patch("mcp_video.engine_rotate._timed_operation") as mock_timing:
                        mock_timing.return_value.__enter__ = MagicMock(return_value={"elapsed_ms": 10})
                        mock_timing.return_value.__exit__ = MagicMock(return_value=False)
                        result = rotate("/tmp/v.mp4", angle=90)
                        assert result.operation == "rotate"

    def test_rotate_180(self):
        from mcp_video.engine_rotate import rotate

        mock_info = SimpleNamespace(width=640, height=480, duration=1.0, resolution="640x480", size_mb=1.0, format="mp4")
        with patch("mcp_video.engine_rotate.probe", return_value=mock_info):
            with patch("mcp_video.engine_rotate._validate_input_path", return_value="/tmp/v.mp4"):
                with patch("mcp_video.engine_rotate._run_ffmpeg"):
                    with patch("mcp_video.engine_rotate._timed_operation") as mock_timing:
                        mock_timing.return_value.__enter__ = MagicMock(return_value={"elapsed_ms": 10})
                        mock_timing.return_value.__exit__ = MagicMock(return_value=False)
                        result = rotate("/tmp/v.mp4", angle=180)
                        assert result.operation == "rotate"

    def test_rotate_270(self):
        from mcp_video.engine_rotate import rotate

        mock_info = SimpleNamespace(width=640, height=480, duration=1.0, resolution="640x480", size_mb=1.0, format="mp4")
        with patch("mcp_video.engine_rotate.probe", return_value=mock_info):
            with patch("mcp_video.engine_rotate._validate_input_path", return_value="/tmp/v.mp4"):
                with patch("mcp_video.engine_rotate._run_ffmpeg"):
                    with patch("mcp_video.engine_rotate._timed_operation") as mock_timing:
                        mock_timing.return_value.__enter__ = MagicMock(return_value={"elapsed_ms": 10})
                        mock_timing.return_value.__exit__ = MagicMock(return_value=False)
                        result = rotate("/tmp/v.mp4", angle=270)
                        assert result.operation == "rotate"

    def test_rotate_flip_horizontal(self):
        from mcp_video.engine_rotate import rotate

        mock_info = SimpleNamespace(width=640, height=480, duration=1.0, resolution="640x480", size_mb=1.0, format="mp4")
        with patch("mcp_video.engine_rotate.probe", return_value=mock_info):
            with patch("mcp_video.engine_rotate._validate_input_path", return_value="/tmp/v.mp4"):
                with patch("mcp_video.engine_rotate._run_ffmpeg"):
                    with patch("mcp_video.engine_rotate._timed_operation") as mock_timing:
                        mock_timing.return_value.__enter__ = MagicMock(return_value={"elapsed_ms": 10})
                        mock_timing.return_value.__exit__ = MagicMock(return_value=False)
                        result = rotate("/tmp/v.mp4", flip_horizontal=True)
                        assert result.operation == "rotate"

    def test_rotate_flip_vertical(self):
        from mcp_video.engine_rotate import rotate

        mock_info = SimpleNamespace(width=640, height=480, duration=1.0, resolution="640x480", size_mb=1.0, format="mp4")
        with patch("mcp_video.engine_rotate.probe", return_value=mock_info):
            with patch("mcp_video.engine_rotate._validate_input_path", return_value="/tmp/v.mp4"):
                with patch("mcp_video.engine_rotate._run_ffmpeg"):
                    with patch("mcp_video.engine_rotate._timed_operation") as mock_timing:
                        mock_timing.return_value.__enter__ = MagicMock(return_value={"elapsed_ms": 10})
                        mock_timing.return_value.__exit__ = MagicMock(return_value=False)
                        result = rotate("/tmp/v.mp4", flip_vertical=True)
                        assert result.operation == "rotate"


class TestEnginePreviewScale:
    def test_scale_factor_too_small(self):
        from mcp_video.engine_preview import preview

        with patch("mcp_video.engine_preview._validate_input_path", return_value="/tmp/v.mp4"):
            with pytest.raises(MCPVideoError, match="scale_factor"):
                preview("/tmp/v.mp4", scale_factor=0)


class TestEngineReverseAudio:
    def test_reverse_with_audio(self):
        from mcp_video.engine_reverse import reverse

        mock_info = SimpleNamespace(
            width=640, height=480, duration=1.0, resolution="640x480", audio_codec="aac", size_mb=1.0, format="mp4"
        )
        with patch("mcp_video.engine_reverse.probe", return_value=mock_info):
            with patch("mcp_video.engine_reverse._validate_input_path", return_value="/tmp/v.mp4"):
                with patch("mcp_video.engine_reverse._run_ffmpeg"):
                    with patch("mcp_video.engine_reverse._timed_operation") as mock_timing:
                        mock_timing.return_value.__enter__ = MagicMock(return_value={"elapsed_ms": 10})
                        mock_timing.return_value.__exit__ = MagicMock(return_value=False)
                        result = reverse("/tmp/v.mp4")
                        assert result.operation == "reverse"

    def test_reverse_without_audio(self):
        from mcp_video.engine_reverse import reverse

        mock_info = SimpleNamespace(
            width=640, height=480, duration=1.0, resolution="640x480", audio_codec=None, size_mb=1.0, format="mp4"
        )
        with patch("mcp_video.engine_reverse.probe", return_value=mock_info):
            with patch("mcp_video.engine_reverse._validate_input_path", return_value="/tmp/v.mp4"):
                with patch("mcp_video.engine_reverse._run_ffmpeg"):
                    with patch("mcp_video.engine_reverse._timed_operation") as mock_timing:
                        mock_timing.return_value.__enter__ = MagicMock(return_value={"elapsed_ms": 10})
                        mock_timing.return_value.__exit__ = MagicMock(return_value=False)
                        result = reverse("/tmp/v.mp4")
                        assert result.operation == "reverse"


class TestEngineSplitScreen:
    def test_split_screen_top_bottom(self):
        from mcp_video.engine_split_screen import split_screen

        mock_info = SimpleNamespace(width=640, height=480, duration=1.0, resolution="640x480", size_mb=1.0, format="mp4")
        with patch("mcp_video.engine_split_screen.probe", return_value=mock_info):
            with patch("mcp_video.engine_split_screen._validate_input_path", return_value="/tmp/a.mp4"):
                with patch("mcp_video.engine_split_screen._run_ffmpeg"):
                    with patch("mcp_video.engine_split_screen._timed_operation") as mock_timing:
                        mock_timing.return_value.__enter__ = MagicMock(return_value={"elapsed_ms": 10})
                        mock_timing.return_value.__exit__ = MagicMock(return_value=False)
                        result = split_screen("/tmp/a.mp4", "/tmp/b.mp4", layout="top-bottom")
                        assert "split_screen" in result.operation


class TestRunnerPlainCmd:
    def test_plain_cmd_without_formatter(self):
        from mcp_video.cli.runner import plain_cmd

        handler = plain_cmd("mcp_video.engine:probe", "input")
        args = SimpleNamespace(input="/tmp/v.mp4")
        with patch("mcp_video.cli.runner._resolve_engine", return_value=lambda x: "ok"):
            with patch("builtins.print") as mock_print:
                handler(args, use_json=False)
                mock_print.assert_called_once_with("ok")
