"""mcp-video Python client — clean API for programmatic video editing."""

from __future__ import annotations

from typing import Any, Self

from ..errors import MCPVideoError
from ..engine import (
    probe as _probe,
)
from ..models import (
    VideoInfo,
)


class ClientBase:
    """Base client with core lifecycle methods."""

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: Any) -> None:
        pass

    def info(self, input_path: str) -> VideoInfo:
        """Get metadata about a video file."""
        return _probe(input_path)

    @staticmethod
    def _validate_choice(name: str, value: str, valid_values: set[str]) -> None:
        if value not in valid_values:
            raise MCPVideoError(
                f"{name} must be one of {sorted(valid_values)}, got {value}",
                error_type="validation_error",
                code="invalid_parameter",
            )
