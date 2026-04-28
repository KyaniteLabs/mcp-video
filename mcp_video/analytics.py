"""Optional anonymous usage analytics for mcp-video."""

from __future__ import annotations

import json
import logging
import os
import platform
import urllib.request
import uuid
from typing import Any

logger = logging.getLogger(__name__)

_ANALYTICS_ENDPOINT = "https://mcp-video-analytics.vercel.app/api/ping"
_ANALYTICS_ENABLED = os.environ.get("MCP_VIDEO_ANALYTICS", "1") == "1"
_INSTALL_ID_PATH = os.path.expanduser("~/.cache/mcp-video/install-id")


def _install_id() -> str:
    """Return a persistent anonymous install ID."""
    try:
        if os.path.isfile(_INSTALL_ID_PATH):
            with open(_INSTALL_ID_PATH) as f:
                return f.read().strip()
    except OSError:
        pass
    new_id = str(uuid.uuid4())
    try:
        os.makedirs(os.path.dirname(_INSTALL_ID_PATH), exist_ok=True)
        with open(_INSTALL_ID_PATH, "w") as f:
            f.write(new_id)
    except OSError:
        pass
    return new_id


def ping(event: str = "startup", metadata: dict[str, Any] | None = None) -> None:
    """Send an anonymous usage ping if analytics are enabled.

    This is a no-op if ``MCP_VIDEO_ANALYTICS=0`` is set in the environment.
    """
    if not _ANALYTICS_ENABLED:
        return

    payload = {
        "install_id": _install_id(),
        "event": event,
        "platform": platform.system(),
        "python": platform.python_version(),
        "metadata": metadata or {},
    }

    try:
        req = urllib.request.Request(
            _ANALYTICS_ENDPOINT,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            resp.read()
    except Exception:
        # Analytics failures must never block the user
        logger.debug("Analytics ping failed (non-critical)")
