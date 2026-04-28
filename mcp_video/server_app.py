"""Shared FastMCP app and result helpers."""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from .errors import MCPVideoError

mcp = FastMCP(
    "mcp-video",
    instructions=(
        "mcp-video is a video editing MCP server. Use these tools to trim, merge, "
        "add text overlays, sync audio, resize, convert, and export video files. "
        "All file paths should be absolute. Output files are generated automatically "
        "if no output_path is provided."
    ),
)

# Optional anonymous usage ping (disabled via MCP_VIDEO_ANALYTICS=0)
try:
    from .analytics import ping

    ping(event="server_start")
except Exception:
    pass

logger = logging.getLogger(__name__)


def _error_result(err: MCPVideoError | Exception) -> dict[str, Any]:
    if isinstance(err, MCPVideoError):
        return {"success": False, "error": err.to_dict()}
    # Unexpected exception — log full traceback, return generic message
    logger.exception("Unexpected error in MCP tool handler")
    return {
        "success": False,
        "error": {
            "type": "internal_error",
            "code": "internal_error",
            "message": "An internal error occurred. Check server logs for details.",
        },
    }


def _result(result: Any) -> dict[str, Any]:
    if result is None:
        return {
            "success": False,
            "error": {"type": "processing_error", "code": "no_result", "message": "Operation returned no result"},
        }
    if hasattr(result, "model_dump"):
        data = result.model_dump()
        # Include thumbnail_base64 only if it was generated (keep MCP responses lean)
        if not data.get("thumbnail_base64"):
            data.pop("thumbnail_base64", None)
        return data
    if isinstance(result, dict):
        result.setdefault("success", True)
        return result
    return {"success": True, "output_path": str(result)}
