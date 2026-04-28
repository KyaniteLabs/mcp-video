"""Tests that Remotion client mixin methods emit deprecation warnings."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_video.client.remotion import ClientRemotionMixin


class _DummyClient(ClientRemotionMixin):
    """Minimal client instance for testing the mixin in isolation."""

    pass


@pytest.fixture
def client():
    return _DummyClient()


class TestRemotionClientDeprecation:
    """All Remotion client methods should emit DeprecationWarning."""

    @patch("mcp_video.remotion_engine.render")
    def test_remotion_render_warns(self, mock_render, client):
        mock_render.return_value = {"output_path": "/tmp/out.mp4"}
        with pytest.warns(DeprecationWarning, match="Remotion integration is deprecated"):
            client.remotion_render("/tmp/proj", "Comp")

    @patch("mcp_video.remotion_engine.compositions")
    def test_remotion_compositions_warns(self, mock_compositions, client):
        mock_compositions.return_value = []
        with pytest.warns(DeprecationWarning, match="Remotion integration is deprecated"):
            client.remotion_compositions("/tmp/proj")

    @patch("mcp_video.remotion_engine.studio")
    def test_remotion_studio_warns(self, mock_studio, client):
        mock_studio.return_value = {"url": "http://localhost:3000"}
        with pytest.warns(DeprecationWarning, match="Remotion integration is deprecated"):
            client.remotion_studio("/tmp/proj")

    @patch("mcp_video.remotion_engine.still")
    def test_remotion_still_warns(self, mock_still, client):
        mock_still.return_value = {"output_path": "/tmp/frame.png"}
        with pytest.warns(DeprecationWarning, match="Remotion integration is deprecated"):
            client.remotion_still("/tmp/proj", "Comp")

    @patch("mcp_video.remotion_engine.create_project")
    def test_remotion_create_project_warns(self, mock_create, client):
        mock_create.return_value = {"project_path": "/tmp/proj"}
        with pytest.warns(DeprecationWarning, match="Remotion integration is deprecated"):
            client.remotion_create_project("my-project")

    @patch("mcp_video.remotion_engine.scaffold_template")
    def test_remotion_scaffold_template_warns(self, mock_scaffold, client):
        mock_scaffold.return_value = None
        with pytest.warns(DeprecationWarning, match="Remotion integration is deprecated"):
            client.remotion_scaffold_template("/tmp/proj", {}, "test")

    @patch("mcp_video.remotion_engine.validate")
    def test_remotion_validate_warns(self, mock_validate, client):
        mock_validate.return_value = {"valid": True}
        with pytest.warns(DeprecationWarning, match="Remotion integration is deprecated"):
            client.remotion_validate("/tmp/proj")

    @patch("mcp_video.remotion_engine.render_and_post")
    def test_remotion_to_mcpvideo_warns(self, mock_pipeline, client):
        mock_pipeline.return_value = {"final_output": "/tmp/out.mp4"}
        with pytest.warns(DeprecationWarning, match="Remotion integration is deprecated"):
            client.remotion_to_mcpvideo("/tmp/proj", "Comp", [])


class TestRemotionServerToolDeprecation:
    """Remotion MCP server tools should emit DeprecationWarning."""

    @patch("mcp_video.server_tools_remotion._validate_project_path", return_value="/tmp/proj")
    @patch("mcp_video.remotion_engine.render")
    def test_remotion_render_tool_warns(self, mock_render, mock_validate):
        mock_render.return_value = MagicMock()
        from mcp_video.server_tools_remotion import remotion_render

        with pytest.warns(DeprecationWarning, match="Remotion integration is deprecated"):
            remotion_render("/tmp/proj", "Comp")

    @patch("mcp_video.server_tools_remotion._validate_project_path", return_value="/tmp/proj")
    @patch("mcp_video.remotion_engine.compositions")
    def test_remotion_compositions_tool_warns(self, mock_compositions, mock_validate):
        mock_compositions.return_value = MagicMock()
        from mcp_video.server_tools_remotion import remotion_compositions

        with pytest.warns(DeprecationWarning, match="Remotion integration is deprecated"):
            remotion_compositions("/tmp/proj")
