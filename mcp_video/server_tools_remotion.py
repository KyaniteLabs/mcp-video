"""Remotion MCP tool registrations."""

from __future__ import annotations

from typing import Any
import re
import warnings

from .errors import MCPVideoError
from .limits import MAX_CONCURRENCY, MAX_CRF, MAX_PORT, MAX_RESOLUTION, MIN_CRF, MIN_PORT
from .server_app import _error_result, _result, mcp
from .validation import VALID_CODECS, VALID_REMOTION_TEMPLATES
from .ffmpeg_helpers import _validate_project_path


_REMOTION_DEPRECATION_MSG = (
    "Remotion integration is deprecated and will be removed in a future version. "
    "Please migrate to Hyperframes (HTML-native, fully open source under Apache 2.0) "
    "or Revideo (Canvas-based, MIT licensed)."
)


def _warn_remotion_deprecated() -> None:
    warnings.warn(_REMOTION_DEPRECATION_MSG, DeprecationWarning, stacklevel=3)


@mcp.tool()
def remotion_render(
    project_path: str,
    composition_id: str,
    output_path: str | None = None,
    codec: str = "h264",
    crf: int | None = None,
    width: int | None = None,
    height: int | None = None,
    fps: float | None = None,
    concurrency: int | None = None,
    frames: str | None = None,
    props: dict[str, Any] | None = None,
    scale: float | None = None,
) -> dict[str, Any]:
    """Render a Remotion composition to video.

    Args:
        project_path: Absolute path to the Remotion project directory.
        composition_id: The composition ID to render.
        output_path: Where to save the video. Auto-generated if omitted.
        codec: Video codec (h264, h265, vp8, vp9, prores, gif). Default h264.
        crf: CRF quality value (lower = better quality).
        width: Output width in pixels.
        height: Output height in pixels.
        fps: Frames per second.
        concurrency: Number of concurrent render threads.
        frames: Frame range to render (e.g. '0-90').
        props: Input props as JSON dict.
        scale: Render scale factor.
    """
    _warn_remotion_deprecated()
    if codec not in VALID_CODECS:
        return _error_result(
            MCPVideoError(
                f"Invalid codec: must be one of {sorted(VALID_CODECS)}, got '{codec}'",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if width is not None and (width < 1 or width > MAX_RESOLUTION):
        return _error_result(
            MCPVideoError(
                f"Invalid width: must be 1-{MAX_RESOLUTION}, got {width}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if height is not None and (height < 1 or height > MAX_RESOLUTION):
        return _error_result(
            MCPVideoError(
                f"Invalid height: must be 1-{MAX_RESOLUTION}, got {height}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if concurrency is not None and (concurrency < 1 or concurrency > MAX_CONCURRENCY):
        return _error_result(
            MCPVideoError(
                f"Invalid concurrency: must be 1-{MAX_CONCURRENCY}, got {concurrency}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if scale is not None and scale <= 0:
        return _error_result(
            MCPVideoError(
                f"Invalid scale: must be > 0, got {scale}", error_type="validation_error", code="invalid_parameter"
            )
        )
    if crf is not None and (crf < MIN_CRF or crf > MAX_CRF):
        return _error_result(
            MCPVideoError(
                f"Invalid crf: must be {MIN_CRF}-{MAX_CRF}, got {crf}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    try:
        project_path = _validate_project_path(project_path)
        from .remotion_engine import render

        return _result(
            render(
                project_path,
                composition_id,
                output_path=output_path,
                codec=codec,
                crf=crf,
                width=width,
                height=height,
                fps=fps,
                concurrency=concurrency,
                frames=frames,
                props=props,
                scale=scale,
            )
        )
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def remotion_compositions(
    project_path: str,
) -> dict[str, Any]:
    """List compositions in a Remotion project.

    Args:
        project_path: Absolute path to the Remotion project directory.
    """
    _warn_remotion_deprecated()
    try:
        project_path = _validate_project_path(project_path)
        from .remotion_engine import compositions

        return _result(compositions(project_path))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def remotion_studio(
    project_path: str,
    port: int = 3000,
) -> dict[str, Any]:
    """Launch Remotion Studio for live preview.

    Args:
        project_path: Absolute path to the Remotion project directory.
        port: Port for the studio server (default 3000).
    """
    _warn_remotion_deprecated()
    if port < MIN_PORT or port > MAX_PORT:
        return _error_result(
            MCPVideoError(
                f"Invalid port: must be {MIN_PORT}-{MAX_PORT}, got {port}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    try:
        project_path = _validate_project_path(project_path)
        from .remotion_engine import studio

        return _result(studio(project_path, port=port))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def remotion_still(
    project_path: str,
    composition_id: str,
    output_path: str | None = None,
    frame: int = 0,
    image_format: str = "png",
) -> dict[str, Any]:
    """Render a single frame as image from a Remotion composition.

    Args:
        project_path: Absolute path to the Remotion project directory.
        composition_id: The composition ID to render.
        output_path: Where to save the image. Auto-generated if omitted.
        frame: Frame number to render (default 0).
        image_format: Image format (png, jpeg, webp). Default png.
    """
    _warn_remotion_deprecated()
    try:
        project_path = _validate_project_path(project_path)
        from .remotion_engine import still

        return _result(
            still(project_path, composition_id, output_path=output_path, frame=frame, image_format=image_format)
        )
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def remotion_create_project(
    name: str,
    output_dir: str | None = None,
    template: str = "blank",
) -> dict[str, Any]:
    """Scaffold a new Remotion project.

    Args:
        name: Project name.
        output_dir: Directory to create the project in. Defaults to current directory.
        template: Project template (blank, hello-world). Default blank.
    """
    _warn_remotion_deprecated()
    if not re.match(r"^[a-zA-Z0-9_-]+$", name):
        return _error_result(
            MCPVideoError(
                "Invalid name: must match ^[a-zA-Z0-9_-]+$", error_type="validation_error", code="invalid_parameter"
            )
        )
    if template not in VALID_REMOTION_TEMPLATES:
        return _error_result(
            MCPVideoError(
                f"Invalid template: must be one of {sorted(VALID_REMOTION_TEMPLATES)}, got '{template}'",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    try:
        from .remotion_engine import create_project

        return _result(create_project(name, output_dir=output_dir, template=template))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def remotion_scaffold_template(
    project_path: str,
    spec: dict[str, Any],
    slug: str,
) -> dict[str, Any]:
    """Generate a generic composition from a spec into a Remotion project.

    Args:
        project_path: Absolute path to the Remotion project directory.
        spec: Composition spec as JSON dict with keys like primary_color, heading_font, target_fps, target_duration, etc.
        slug: Slug for the composition (used for filenames and component naming).
    """
    _warn_remotion_deprecated()
    if not re.match(r"^[a-zA-Z0-9_-]+$", slug):
        return _error_result(
            MCPVideoError(
                "Invalid slug: must match ^[a-zA-Z0-9_-]+$", error_type="validation_error", code="invalid_parameter"
            )
        )
    try:
        project_path = _validate_project_path(project_path)
        from .remotion_engine import scaffold_template

        return _result(scaffold_template(project_path, spec, slug))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def remotion_validate(
    project_path: str,
    composition_id: str | None = None,
) -> dict[str, Any]:
    """Validate a Remotion project for rendering readiness.

    Args:
        project_path: Absolute path to the Remotion project directory.
        composition_id: Optional specific composition ID to validate.
    """
    _warn_remotion_deprecated()
    try:
        project_path = _validate_project_path(project_path)
        from .remotion_engine import validate

        return _result(validate(project_path, composition_id=composition_id))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def remotion_to_mcpvideo(
    project_path: str,
    composition_id: str,
    post_process: list[dict[str, Any]],
    output_path: str | None = None,
) -> dict[str, Any]:
    """Render a Remotion composition and post-process with mcp-video in one step.

    Args:
        project_path: Absolute path to the Remotion project directory.
        composition_id: The composition ID to render.
        post_process: List of post-processing operations, each with 'op' and 'params' keys.
            Example: [{"op": "resize", "params": {"aspect_ratio": "9:16"}}]
        output_path: Where to save the final output. Auto-generated if omitted.
    """
    _warn_remotion_deprecated()
    if not isinstance(post_process, list) or len(post_process) < 1:
        return _error_result(
            MCPVideoError(
                "Invalid post_process: must be a non-empty list",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    try:
        project_path = _validate_project_path(project_path)
        from .remotion_engine import render_and_post

        return _result(render_and_post(project_path, composition_id, post_process, output_path=output_path))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)
