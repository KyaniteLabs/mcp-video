"""Hyperframes MCP tool registrations."""

from __future__ import annotations

from typing import Any
import re

from .errors import MCPVideoError
from .limits import MAX_CRF, MAX_PORT, MAX_RESOLUTION, MIN_CRF, MIN_PORT
from .server_app import _error_result, _result, _validation_error, mcp
from .validation import VALID_HYPERFRAMES_FORMATS, VALID_HYPERFRAMES_QUALITIES, VALID_HYPERFRAMES_TEMPLATES
from .ffmpeg_helpers import _validate_project_path


@mcp.tool()
def hyperframes_render(
    project_path: str,
    output_path: str | None = None,
    fps: float | None = None,
    width: int | None = None,
    height: int | None = None,
    quality: str | None = None,
    format: str | None = None,
    workers: str | int | None = None,
    crf: int | None = None,
) -> dict[str, Any]:
    """Render a Hyperframes composition to video.

    Args:
        project_path: Absolute path to the Hyperframes project directory.
        output_path: Where to save the video. Auto-generated if omitted.
        fps: Frame rate (24, 30, 60).
        width: Output width in pixels.
        height: Output height in pixels.
        quality: Render quality (draft, standard, high). Default standard.
        format: Output format (mp4, webm, mov). Default mp4.
        workers: Parallel render workers (number or 'auto'). Default auto.
        crf: Override encoder CRF (lower = better quality).
    """
    if quality is not None and quality not in VALID_HYPERFRAMES_QUALITIES:
        return _validation_error(
                f"Invalid quality: must be one of {sorted(VALID_HYPERFRAMES_QUALITIES)}, got '{quality}'")
    if format is not None and format not in VALID_HYPERFRAMES_FORMATS:
        return _validation_error(
                f"Invalid format: must be one of {sorted(VALID_HYPERFRAMES_FORMATS)}, got '{format}'")
    if width is not None and (width < 1 or width > MAX_RESOLUTION):
        return _validation_error(
                f"Invalid width: must be 1-{MAX_RESOLUTION}, got {width}")
    if height is not None and (height < 1 or height > MAX_RESOLUTION):
        return _validation_error(
                f"Invalid height: must be 1-{MAX_RESOLUTION}, got {height}")
    if crf is not None and (crf < MIN_CRF or crf > MAX_CRF):
        return _validation_error(
                f"Invalid crf: must be {MIN_CRF}-{MAX_CRF}, got {crf}")
    try:
        project_path = _validate_project_path(project_path)
        from .hyperframes_engine import render

        return _result(
            render(
                project_path,
                output_path=output_path,
                fps=fps,
                width=width,
                height=height,
                quality=quality,
                format=format,
                workers=workers,
                crf=crf,
            )
        )
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def hyperframes_compositions(
    project_path: str,
) -> dict[str, Any]:
    """List compositions in a Hyperframes project.

    Args:
        project_path: Absolute path to the Hyperframes project directory.
    """
    try:
        project_path = _validate_project_path(project_path)
        from .hyperframes_engine import compositions

        return _result(compositions(project_path))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def hyperframes_preview(
    project_path: str,
    port: int = 3002,
) -> dict[str, Any]:
    """Launch Hyperframes preview studio for live preview.

    Args:
        project_path: Absolute path to the Hyperframes project directory.
        port: Port for the preview server (default 3002).
    """
    if port < MIN_PORT or port > MAX_PORT:
        return _validation_error(
                f"Invalid port: must be {MIN_PORT}-{MAX_PORT}, got {port}")
    try:
        project_path = _validate_project_path(project_path)
        from .hyperframes_engine import preview

        return _result(preview(project_path, port=port))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def hyperframes_still(
    project_path: str,
    output_path: str | None = None,
    frame: int = 0,
) -> dict[str, Any]:
    """Render a single frame as image from a Hyperframes composition.

    Args:
        project_path: Absolute path to the Hyperframes project directory.
        output_path: Where to save the image. Auto-generated if omitted.
        frame: Frame number to render (default 0).
    """
    try:
        project_path = _validate_project_path(project_path)
        from .hyperframes_engine import still

        return _result(still(project_path, output_path=output_path, frame=frame))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def hyperframes_init(
    name: str,
    output_dir: str | None = None,
    template: str = "blank",
) -> dict[str, Any]:
    """Scaffold a new Hyperframes project.

    Args:
        name: Project name.
        output_dir: Directory to create the project in. Defaults to current directory.
        template: Project template (blank, warm-grain, swiss-grid). Default blank.
    """
    if not re.match(r"^[a-zA-Z0-9_-]+$", name):
        return _validation_error(
                "Invalid name: must match ^[a-zA-Z0-9_-]+$")
    if template not in VALID_HYPERFRAMES_TEMPLATES:
        return _validation_error(
                f"Invalid template: must be one of {sorted(VALID_HYPERFRAMES_TEMPLATES)}, got '{template}'")
    try:
        from .hyperframes_engine import create_project

        return _result(create_project(name, output_dir=output_dir, template=template))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def hyperframes_add_block(
    project_path: str,
    block_name: str,
) -> dict[str, Any]:
    """Install a block from the Hyperframes catalog.

    Args:
        project_path: Absolute path to the Hyperframes project directory.
        block_name: Registry item name (e.g. claude-code-window, shader-wipe).
    """
    if not re.match(r"^[a-zA-Z0-9_-]+$", block_name):
        return _validation_error(
                "Invalid block_name: must match ^[a-zA-Z0-9_-]+$")
    try:
        project_path = _validate_project_path(project_path)
        from .hyperframes_engine import add_block

        return _result(add_block(project_path, block_name))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def hyperframes_validate(
    project_path: str,
) -> dict[str, Any]:
    """Validate a Hyperframes project for rendering readiness.

    Args:
        project_path: Absolute path to the Hyperframes project directory.
    """
    try:
        project_path = _validate_project_path(project_path)
        from .hyperframes_engine import validate

        return _result(validate(project_path))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def hyperframes_to_mcpvideo(
    project_path: str,
    post_process: list[dict[str, Any]],
    output_path: str | None = None,
) -> dict[str, Any]:
    """Render a Hyperframes composition and post-process with mcp-video in one step.

    Args:
        project_path: Absolute path to the Hyperframes project directory.
        post_process: List of post-processing operations, each with 'op' and 'params' keys.
            Example: [{"op": "resize", "params": {"aspect_ratio": "9:16"}}]
        output_path: Where to save the final output. Auto-generated if omitted.
    """
    if not isinstance(post_process, list) or len(post_process) < 1:
        return _validation_error(
                "Invalid post_process: must be a non-empty list")
    try:
        project_path = _validate_project_path(project_path)
        from .hyperframes_engine import render_and_post

        return _result(render_and_post(project_path, post_process, output_path=output_path))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)
