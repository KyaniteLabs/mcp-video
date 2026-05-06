"""Launch-remediation regression tests."""

from __future__ import annotations

from pathlib import Path

import pytest


def test_analytics_disabled_by_default(monkeypatch):
    monkeypatch.delenv("MCP_VIDEO_ANALYTICS", raising=False)

    import importlib
    import mcp_video.analytics as analytics

    analytics = importlib.reload(analytics)

    assert analytics.analytics_enabled() is False


def test_analytics_enabled_only_by_explicit_opt_in(monkeypatch):
    monkeypatch.setenv("MCP_VIDEO_ANALYTICS", "1")

    import importlib
    import mcp_video.analytics as analytics

    analytics = importlib.reload(analytics)

    assert analytics.analytics_enabled() is True


def test_mograph_frame_count_is_capped(monkeypatch):
    from mcp_video.server_tools_effects import video_mograph_count

    def should_not_run(*_args, **_kwargs):
        raise AssertionError("mograph engine should not run for oversized requests")

    import mcp_video.effects_engine

    monkeypatch.setattr(mcp_video.effects_engine, "mograph_count", should_not_run)

    result = video_mograph_count(0, 100, duration=10_000, output_path="counter.mp4", fps=120)

    assert result["success"] is False
    assert result["error"]["code"] == "mograph_too_large"


def test_hyperframes_command_uses_no_install_npx(monkeypatch, tmp_path):
    from mcp_video import hyperframes_engine

    project = tmp_path / "project"
    project.mkdir()
    (project / "index.html").write_text("<html></html>")
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd

        class Result:
            returncode = 0
            stdout = "[]"
            stderr = ""

        return Result()

    monkeypatch.setattr(hyperframes_engine.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(hyperframes_engine.subprocess, "run", fake_run)

    hyperframes_engine.compositions(str(project))

    assert captured["cmd"][:4] == ["npx", "--yes", "--no-install", "hyperframes"]


def test_ytdlp_rejects_resolved_private_media_url(monkeypatch, tmp_path):
    import sys
    import types

    from mcp_video.ai_engine.download import _download_with_ytdlp
    from mcp_video.errors import MCPVideoError

    class FakeYoutubeDL:
        def __init__(self, opts):
            self.opts = opts

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def extract_info(self, _url, download):
            assert self.opts["proxy"] == ""
            assert download is False
            return {
                "id": "unsafe",
                "ext": "mp4",
                "requested_downloads": [{"url": "http://127.0.0.1/internal.mp4"}],
            }

        def prepare_filename(self, _info):
            return str(Path(tmp_path) / "unsafe.mp4")

    fake_module = types.SimpleNamespace(YoutubeDL=FakeYoutubeDL)
    monkeypatch.setitem(sys.modules, "yt_dlp", fake_module)

    with pytest.raises(MCPVideoError) as exc_info:
        _download_with_ytdlp("https://youtube.com/watch?v=unsafe", str(tmp_path))

    assert exc_info.value.code == "ssrf_blocked"
