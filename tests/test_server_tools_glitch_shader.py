"""Tests for mcp_video/server_tools_glitch_shader.py — GPU shader tool layer.

These tools require Node.js + the CRUSH.js render script. On systems without
Node.js or without the CRUSH shader bundle installed, all "success path" tests
are skipped and only the input-validation paths are exercised.
"""

from __future__ import annotations

import shutil

import pytest

from mcp_video.server_tools_glitch_shader import (
    glitch_depth_splatting,
    glitch_digital_feedback,
    glitch_point_cloud,
    glitch_slit_scan,
)


def _crush_available() -> bool:
    """Return True only if Node.js and the external CRUSH GLSL sources are present.

    The render script ships with the package, but the GLSL sources live in the
    separate crush-js project (MCP_VIDEO_CRUSH_PATH / ~/.mcp-video/crush-js/src).
    """
    if not shutil.which("node"):
        return False
    from mcp_video.engine_glitch_shader import _crush_sources_available

    return _crush_sources_available()


_no_crush = pytest.mark.skipif(not _crush_available(), reason="Node.js + CRUSH shader bundle not installed")


@pytest.mark.skipif(shutil.which("node") is None, reason="requires Node.js")
def test_missing_canvas_returns_structured_error(monkeypatch, sample_video, tmp_path):
    """The wheel ships only the render script; without the canvas npm package
    the tool must name the install step, not dump a node require traceback."""
    import mcp_video.engine_glitch_shader as shader_engine

    monkeypatch.setattr(shader_engine, "_crush_sources_available", lambda: True)
    monkeypatch.setattr(shader_engine, "_crush_canvas_available", lambda: False)
    result = glitch_digital_feedback(sample_video, output_path=str(tmp_path / "x.mp4"))
    assert result["success"] is False
    assert "missing_canvas" in str(result["error"])


@pytest.mark.skipif(shutil.which("node") is None, reason="requires Node.js")
def test_missing_crush_sources_returns_structured_error(monkeypatch, sample_video, tmp_path):
    """Without the external GLSL sources the tool must return a dependency
    error with an install hint — not a raw node ENOENT traceback."""
    import mcp_video.engine_glitch_shader as shader_engine

    monkeypatch.setattr(shader_engine, "_crush_sources_available", lambda: False)
    result = glitch_digital_feedback(sample_video, output_path=str(tmp_path / "x.mp4"))
    assert result["success"] is False
    assert "missing_crush_shaders" in str(result["error"])


# ---------------------------------------------------------------------------
# glitch_digital_feedback — validation
# ---------------------------------------------------------------------------


class TestGlitchDigitalFeedbackTool:
    def test_rejects_nonexistent_file(self):
        result = glitch_digital_feedback("/nonexistent/video.mp4")
        assert result["success"] is False
        assert "error" in result

    def test_rejects_feedback_mix_above_one(self, sample_video):
        result = glitch_digital_feedback(sample_video, feedback_mix=1.5)
        assert result["success"] is False

    def test_rejects_feedback_mix_below_zero(self, sample_video):
        result = glitch_digital_feedback(sample_video, feedback_mix=-0.1)
        assert result["success"] is False

    def test_rejects_decay_above_one(self, sample_video):
        result = glitch_digital_feedback(sample_video, decay=1.5)
        assert result["success"] is False

    def test_rejects_decay_below_zero(self, sample_video):
        result = glitch_digital_feedback(sample_video, decay=-0.1)
        assert result["success"] is False

    @_no_crush
    @pytest.mark.slow
    def test_success(self, sample_video, tmp_path):
        out = str(tmp_path / "digital_feedback.mp4")
        result = glitch_digital_feedback(
            sample_video,
            output_path=out,
            feedback_mix=0.5,
            scale=1.0,
            rotation=0.0,
            decay=0.9,
        )
        assert result["success"] is True
        import os

        assert os.path.isfile(result["output_path"])


# ---------------------------------------------------------------------------
# glitch_slit_scan — validation
# ---------------------------------------------------------------------------


class TestGlitchSlitScanTool:
    def test_rejects_nonexistent_file(self):
        result = glitch_slit_scan("/nonexistent/video.mp4")
        assert result["success"] is False

    def test_rejects_depth_zero(self, sample_video):
        result = glitch_slit_scan(sample_video, depth=0)
        assert result["success"] is False

    def test_rejects_depth_above_120(self, sample_video):
        result = glitch_slit_scan(sample_video, depth=121)
        assert result["success"] is False

    def test_rejects_invalid_direction(self, sample_video):
        result = glitch_slit_scan(sample_video, direction=4)
        assert result["success"] is False

    def test_accepts_all_valid_directions(self, sample_video):
        """All validation-only checks — no CRUSH needed."""
        for direction in (0, 1, 2, 3):
            # We can only confirm no *validation* error is returned; the
            # subsequent Node.js call will fail without CRUSH, which will
            # surface as a non-validation error.
            result = glitch_slit_scan(sample_video, direction=direction)
            # If crush is unavailable, success=False but error code is NOT
            # invalid_parameter — i.e., validation passed.
            if not result["success"]:
                error = result.get("error", {})
                assert error.get("code") != "invalid_parameter", (
                    f"direction={direction} triggered a validation error unexpectedly"
                )

    @_no_crush
    @pytest.mark.slow
    def test_success(self, sample_video, tmp_path):
        out = str(tmp_path / "slit_scan.mp4")
        result = glitch_slit_scan(sample_video, output_path=out, depth=10, direction=0)
        assert result["success"] is True
        import os

        assert os.path.isfile(result["output_path"])


# ---------------------------------------------------------------------------
# glitch_depth_splatting — validation
# ---------------------------------------------------------------------------


class TestGlitchDepthSplattingTool:
    def test_rejects_nonexistent_file(self):
        result = glitch_depth_splatting("/nonexistent/video.mp4")
        assert result["success"] is False

    def test_rejects_threshold_above_one(self, sample_video):
        result = glitch_depth_splatting(sample_video, threshold=1.5)
        assert result["success"] is False

    def test_rejects_threshold_below_zero(self, sample_video):
        result = glitch_depth_splatting(sample_video, threshold=-0.1)
        assert result["success"] is False

    @_no_crush
    @pytest.mark.slow
    def test_success(self, sample_video, tmp_path):
        out = str(tmp_path / "depth_splatting.mp4")
        result = glitch_depth_splatting(
            sample_video,
            output_path=out,
            depth_scale=1.0,
            spread=5.0,
            point_size=2.0,
            threshold=0.5,
        )
        assert result["success"] is True
        import os

        assert os.path.isfile(result["output_path"])


# ---------------------------------------------------------------------------
# glitch_point_cloud — validation
# ---------------------------------------------------------------------------


class TestGlitchPointCloudTool:
    def test_rejects_nonexistent_file(self):
        result = glitch_point_cloud("/nonexistent/video.mp4")
        assert result["success"] is False

    def test_rejects_density_above_one(self, sample_video):
        result = glitch_point_cloud(sample_video, density=1.5)
        assert result["success"] is False

    def test_rejects_density_below_zero(self, sample_video):
        result = glitch_point_cloud(sample_video, density=-0.1)
        assert result["success"] is False

    @_no_crush
    @pytest.mark.slow
    def test_success(self, sample_video, tmp_path):
        out = str(tmp_path / "point_cloud.mp4")
        result = glitch_point_cloud(
            sample_video,
            output_path=out,
            density=0.5,
            point_size=2.0,
            rotation=0.0,
            depth=1.0,
        )
        assert result["success"] is True
        import os

        assert os.path.isfile(result["output_path"])


# ---------------------------------------------------------------------------
# Graceful failure when CRUSH is unavailable
# ---------------------------------------------------------------------------


class TestShaderGracefulFailure:
    """Verify that missing CRUSH produces a structured error, not an unhandled crash."""

    def test_digital_feedback_no_crush_returns_error_dict(self, sample_video, monkeypatch):
        """When CRUSH render script is absent, the tool must return success=False."""
        monkeypatch.setattr(
            "mcp_video.engine_glitch_shader._RENDER_SCRIPT",
            __import__("pathlib").Path("/nonexistent/render_frames.mjs"),
        )
        result = glitch_digital_feedback(sample_video)
        assert result["success"] is False

    def test_slit_scan_no_crush_returns_error_dict(self, sample_video, monkeypatch):
        monkeypatch.setattr(
            "mcp_video.engine_glitch_shader._RENDER_SCRIPT",
            __import__("pathlib").Path("/nonexistent/render_frames.mjs"),
        )
        result = glitch_slit_scan(sample_video)
        assert result["success"] is False

    def test_depth_splatting_no_crush_returns_error_dict(self, sample_video, monkeypatch):
        monkeypatch.setattr(
            "mcp_video.engine_glitch_shader._RENDER_SCRIPT",
            __import__("pathlib").Path("/nonexistent/render_frames.mjs"),
        )
        result = glitch_depth_splatting(sample_video)
        assert result["success"] is False

    def test_point_cloud_no_crush_returns_error_dict(self, sample_video, monkeypatch):
        monkeypatch.setattr(
            "mcp_video.engine_glitch_shader._RENDER_SCRIPT",
            __import__("pathlib").Path("/nonexistent/render_frames.mjs"),
        )
        result = glitch_point_cloud(sample_video)
        assert result["success"] is False
