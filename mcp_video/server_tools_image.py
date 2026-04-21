"""Image MCP tool registrations."""

from __future__ import annotations

from typing import Any

from .errors import MCPVideoError
from .server_app import _error_result, _result, mcp
from .ffmpeg_helpers import _validate_input_path


@mcp.tool()
def image_extract_colors(
    image_path: str,
    n_colors: int = 5,
) -> dict[str, Any]:
    """Extract dominant colors from an image.

    Uses K-means clustering to find the most prominent colors. Returns hex codes,
    RGB values, CSS color names, and percentage coverage.

    Args:
        image_path: Absolute path to the image file.
        n_colors: Number of dominant colors to extract (1-20, default 5).
    """
    try:
        image_path = _validate_input_path(image_path)
        from .image_engine import extract_colors

        return _result(extract_colors(image_path, n_colors=n_colors))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def image_generate_palette(
    image_path: str,
    harmony: str = "complementary",
    n_colors: int = 5,
) -> dict[str, Any]:
    """Generate a color harmony palette from an image.

    Extracts the dominant color and generates harmonious colors based on
    color theory (complementary, analogous, triadic, split_complementary).

    Args:
        image_path: Absolute path to the image file.
        harmony: Harmony type (complementary, analogous, triadic, split_complementary).
        n_colors: Number of dominant colors to base palette on (default 5).
    """
    try:
        image_path = _validate_input_path(image_path)
        from .image_engine import generate_palette

        return _result(generate_palette(image_path, harmony=harmony, n_colors=n_colors))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def image_analyze_product(
    image_path: str,
    use_ai: bool = False,
    n_colors: int = 5,
) -> dict[str, Any]:
    """Analyze a product image — extract colors and optionally generate AI description.

    Extracts dominant colors from an image. Optionally uses Claude Vision to
    generate a natural language description of the product.

    Args:
        image_path: Absolute path to the image file.
        use_ai: If True, use Claude Vision to generate a description (requires ANTHROPIC_API_KEY).
        n_colors: Number of dominant colors to extract (default 5).
    """
    try:
        image_path = _validate_input_path(image_path)
        from .image_engine import analyze_product

        return _result(analyze_product(image_path, use_ai=use_ai, n_colors=n_colors))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)
