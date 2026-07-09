"""mcp-video Python client — agent workflow-engine methods."""

from __future__ import annotations

from typing import Any


class ClientWorkflowMixin:
    """Agent workflow-engine operations mixin."""

    def workflow_validate(self, spec: str | dict) -> dict[str, Any]:
        """Validate a workflow job-spec without rendering any media.

        Args:
            spec: Path to a workflow job-spec JSON file, or the spec as a dict.

        Returns:
            A structured validation verdict (``{"valid": True, ...}``).

        Raises:
            MCPVideoError: on any structural violation (fail-closed).
        """
        from ..workflow import validate_workflow_spec

        if isinstance(spec, dict):
            import json
            import os
            import tempfile

            with tempfile.TemporaryDirectory(prefix="mcp_video_workflow_") as tmpdir:
                spec_path = os.path.join(tmpdir, "workflow.json")
                with open(spec_path, "w", encoding="utf-8") as handle:
                    json.dump(spec, handle)
                return validate_workflow_spec(spec_path)
        return validate_workflow_spec(spec)
