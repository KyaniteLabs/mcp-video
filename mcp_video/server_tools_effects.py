"""MCP tool registrations for visual effects, layouts, mograph, and transitions."""

from __future__ import annotations

import os
from typing import Any

from .engine_runtime_utils import _auto_output
from .errors import MCPVideoError
from .server_app import _error_result, _result, mcp
from .validation import VALID_MOGRAPH_STYLES

# ---------------------------------------------------------------------------
# Visual Effects Tools (P1 Features)
# ---------------------------------------------------------------------------


@mcp.tool()
def effect_vignette(
    input_path: str,
    output_path: str | None = None,
    intensity: float = 0.5,
    radius: float = 0.8,
    smoothness: float = 0.5,
) -> dict[str, Any]:
    """Apply vignette effect - darkened edges.

    Creates a darkened border effect that draws attention to the center of the frame.

    Args:
        input_path: Absolute path to input video.
        output_path: Absolute path for output video.
        intensity: Darkness amount 0-1. Default 0.5.
        radius: Vignette radius 0-1 (1 = edge of frame). Default 0.8.
        smoothness: Edge softness 0-1. Default 0.5.

    Returns:
        Dict with success status and output_path.
    """
    try:
        if not (0.0 <= intensity <= 1.0):
            return _error_result(ValueError(f"intensity must be between 0.0 and 1.0, got {intensity}"))
        if not (0.0 <= radius <= 1.0):
            return _error_result(ValueError(f"radius must be between 0.0 and 1.0, got {radius}"))
        if not (0.0 <= smoothness <= 1.0):
            return _error_result(ValueError(f"smoothness must be between 0.0 and 1.0, got {smoothness}"))
        from .effects_engine import effect_vignette as _vignette

        output = output_path or _auto_output(input_path, "vignette")
        return _result(_vignette(input_path, output, intensity, radius, smoothness))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def effect_chromatic_aberration(
    input_path: str,
    output_path: str,
    intensity: float = 2.0,
    angle: float = 0,
) -> dict[str, Any]:
    """Apply chromatic aberration - RGB channel separation.

    Creates a trendy RGB split effect popular in tech/glitch aesthetics.

    Args:
        input_path: Absolute path to input video.
        output_path: Absolute path for output video.
        intensity: Pixel offset amount. Default 2.0.
        angle: Separation direction in degrees. Default 0 (horizontal).

    Returns:
        Dict with success status and output_path.
    """
    try:
        if intensity < 0:
            return _error_result(ValueError(f"intensity must be non-negative, got {intensity}"))
        from .effects_engine import effect_chromatic_aberration as _chroma

        return _result(_chroma(input_path, output_path, intensity, angle))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def effect_scanlines(
    input_path: str,
    output_path: str,
    line_height: int = 2,
    opacity: float = 0.3,
    flicker: float = 0.1,
) -> dict[str, Any]:
    """Apply CRT-style scanlines overlay.

    Simulates old CRT monitor scanline effect with optional flicker.

    Args:
        input_path: Absolute path to input video.
        output_path: Absolute path for output video.
        line_height: Pixels per scanline. Default 2.
        opacity: Line opacity 0-1. Default 0.3.
        flicker: Brightness variation 0-1. Default 0.1.

    Returns:
        Dict with success status and output_path.
    """
    try:
        if line_height < 1:
            return _error_result(ValueError(f"line_height must be at least 1, got {line_height}"))
        if not (0.0 <= opacity <= 1.0):
            return _error_result(ValueError(f"opacity must be between 0.0 and 1.0, got {opacity}"))
        if not (0.0 <= flicker <= 1.0):
            return _error_result(ValueError(f"flicker must be between 0.0 and 1.0, got {flicker}"))
        from .effects_engine import effect_scanlines as _scanlines

        return _result(_scanlines(input_path, output_path, line_height, opacity, flicker))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def effect_noise(
    input_path: str,
    output_path: str,
    intensity: float = 0.05,
    mode: str = "film",
    animated: bool = True,
) -> dict[str, Any]:
    """Apply film grain or digital noise.

    Adds texture noise to video for vintage or lo-fi aesthetics.

    Args:
        input_path: Absolute path to input video.
        output_path: Absolute path for output video.
        intensity: Noise amount 0-1. Default 0.05.
        mode: Noise type (film, digital, color). Default film.
        animated: Whether noise changes per frame. Default true.

    Returns:
        Dict with success status and output_path.
    """
    try:
        if not (0.0 <= intensity <= 1.0):
            return _error_result(ValueError(f"intensity must be between 0.0 and 1.0, got {intensity}"))
        if mode not in ("film", "digital", "color"):
            return _error_result(ValueError(f"mode must be film, digital, or color, got {mode}"))
        from .effects_engine import effect_noise as _noise

        return _result(_noise(input_path, output_path, intensity, mode, animated))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def effect_glow(
    input_path: str,
    output_path: str,
    intensity: float = 0.5,
    radius: int = 10,
    threshold: float = 0.7,
) -> dict[str, Any]:
    """Apply bloom/glow effect for highlights.

    Creates a soft glow around bright areas of the video.

    Args:
        input_path: Absolute path to input video.
        output_path: Absolute path for output video.
        intensity: Glow strength 0-1. Default 0.5.
        radius: Blur radius in pixels. Default 10.
        threshold: Brightness threshold 0-1. Default 0.7.

    Returns:
        Dict with success status and output_path.
    """
    try:
        if not (0.0 <= intensity <= 1.0):
            return _error_result(ValueError(f"intensity must be between 0.0 and 1.0, got {intensity}"))
        if radius < 0:
            return _error_result(ValueError(f"radius must be non-negative, got {radius}"))
        if not (0.0 <= threshold <= 1.0):
            return _error_result(ValueError(f"threshold must be between 0.0 and 1.0, got {threshold}"))
        from .effects_engine import effect_glow as _glow

        return _result(_glow(input_path, output_path, intensity, radius, threshold))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_layout_grid(
    clips: list[str],
    layout: str,
    output_path: str,
    gap: int = 10,
    padding: int = 20,
    background: str = "#141414",
) -> dict[str, Any]:
    """Create grid-based multi-video layout.

    Arranges multiple videos in a grid pattern (2x2, 3x1, etc.).

    Args:
        clips: List of absolute paths to video files.
        layout: Grid layout (2x2, 3x1, 1x3, 2x3).
        output_path: Absolute path for output video.
        gap: Pixels between clips. Default 10.
        padding: Padding around grid. Default 20.
        background: Background color hex. Default #141414.

    Returns:
        Dict with success status and output_path.
    """
    try:
        if gap < 0:
            return _error_result(ValueError(f"gap must be non-negative, got {gap}"))
        if padding < 0:
            return _error_result(ValueError(f"padding must be non-negative, got {padding}"))
        from .effects_engine import layout_grid as _grid

        return _result(_grid(clips, layout, output_path, gap, padding, background))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_layout_pip(
    main_path: str,
    pip_path: str,
    output_path: str,
    position: str = "bottom-right",
    size: float = 0.25,
    margin: int = 20,
    border: bool = True,
    border_color: str = "#CCFF00",
    border_width: int = 2,
    rounded_corners: bool = True,
) -> dict[str, Any]:
    """Picture-in-picture overlay.

    Overlay a smaller video on top of a main video.

    Args:
        main_path: Absolute path to main video.
        pip_path: Absolute path to picture-in-picture video.
        output_path: Absolute path for output video.
        position: Position (top-left, top-right, bottom-left, bottom-right). Default bottom-right.
        size: PIP size as fraction of main. Default 0.25.
        margin: Margin from edges in pixels. Default 20.
        border: Add border around PIP. Default true.
        border_color: Border color hex. Default #CCFF00.
        border_width: Border width in pixels. Default 2.
        rounded_corners: Apply rounded corners to PIP. Default true.

    Returns:
        Dict with success status and output_path.
    """
    try:
        if not (0.0 < size <= 1.0):
            return _error_result(ValueError(f"size must be between 0.0 and 1.0, got {size}"))
        if border_width < 0:
            return _error_result(ValueError(f"border_width must be non-negative, got {border_width}"))
        from .effects_engine import layout_pip as _pip

        return _result(
            _pip(
                main_path,
                pip_path,
                output_path,
                position=position,
                size=size,
                margin=margin,
                rounded_corners=rounded_corners,
                border=border,
                border_color=border_color,
                border_width=border_width,
            )
        )
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_text_animated(
    input_path: str,
    text: str,
    output_path: str | None = None,
    animation: str = "fade",
    font: str = "Arial",
    size: int = 48,
    color: str = "white",
    position: str = "center",
    start: float = 0,
    duration: float = 3.0,
) -> dict[str, Any]:
    """Add animated text to video.

    Overlay text with animation effects (fade, slide, etc.).

    Args:
        input_path: Absolute path to input video.
        text: Text to display.
        output_path: Absolute path for output video.
        animation: Animation type (fade, slide-up, typewriter). Default fade.
        font: Font family. Default Arial.
        size: Font size. Default 48.
        color: Text color. Default white.
        position: Text position. Default center.
        start: Start time in seconds. Default 0.
        duration: Display duration. Default 3.0.

    Returns:
        Dict with success status and output_path.
    """
    try:
        if not (8 <= size <= 500):
            return _error_result(ValueError(f"size must be between 8 and 500, got {size}"))
        if duration <= 0:
            return _error_result(ValueError(f"duration must be positive, got {duration}"))
        if start < 0:
            return _error_result(ValueError(f"start must be non-negative, got {start}"))
        from .effects_engine import text_animated as _text

        output = output_path or _auto_output(input_path, "animated")
        return _result(_text(input_path, text, output, animation, font, size, color, position, start, duration))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_text_subtitles(
    input_path: str,
    subtitles_path: str,
    output_path: str,
    style: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Burn subtitles from SRT/VTT with styling.

    Embeds subtitle file into video with customizable appearance.

    Args:
        input_path: Absolute path to input video.
        subtitles_path: Absolute path to SRT or VTT file.
        output_path: Absolute path for output video.
        style: Optional style dict with font, size, color, outline, etc.

    Returns:
        Dict with success status and output_path.
    """
    if not os.path.isfile(subtitles_path):
        return _error_result(
            MCPVideoError(
                f"Subtitles file not found: {subtitles_path}",
                error_type="validation_error",
                code="file_not_found",
            )
        )
    try:
        from .effects_engine import text_subtitles as _subs

        return _result(_subs(input_path, subtitles_path, output_path, style))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_mograph_count(
    start: int,
    end: int,
    duration: float,
    output_path: str,
    style: dict[str, Any] | None = None,
    fps: int = 30,
) -> dict[str, Any]:
    """Generate animated number counter video.

    Creates a standalone video of an animated counting number.

    Args:
        start: Starting number.
        end: Ending number.
        duration: Animation duration in seconds.
        output_path: Absolute path for output video.
        style: Optional style dict with font, size, color, glow.
        fps: Frame rate. Default 30.

    Returns:
        Dict with success status and output_path.
    """
    try:
        if not (1 <= fps <= 120):
            return _error_result(ValueError(f"fps must be between 1 and 120, got {fps}"))
        if duration <= 0:
            return _error_result(ValueError(f"duration must be positive, got {duration}"))
        from .effects_engine import mograph_count as _count

        return _result(_count(start, end, duration, output_path, style=style, fps=fps))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_mograph_progress(
    duration: float,
    output_path: str,
    style: str = "bar",
    color: str = "#CCFF00",
    track_color: str = "#333333",
    fps: int = 30,
) -> dict[str, Any]:
    """Generate progress bar / loading animation.

    Creates a standalone progress animation video.

    Args:
        duration: Animation duration in seconds.
        output_path: Absolute path for output video.
        style: Progress style (bar, circle, dots). Default bar.
        color: Progress color hex. Default #CCFF00.
        track_color: Background track color hex. Default #333333.
        fps: Frame rate. Default 30.

    Returns:
        Dict with success status and output_path.
    """
    if style not in VALID_MOGRAPH_STYLES:
        return _error_result(
            MCPVideoError(
                f"Invalid style: must be one of {sorted(VALID_MOGRAPH_STYLES)}, got '{style}'",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    try:
        if not (1 <= fps <= 120):
            return _error_result(ValueError(f"fps must be between 1 and 120, got {fps}"))
        if duration <= 0:
            return _error_result(ValueError(f"duration must be positive, got {duration}"))
        from .effects_engine import mograph_progress as _progress

        return _result(_progress(duration, output_path, style=style, color=color, track_color=track_color, fps=fps))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_info_detailed(
    input_path: str,
) -> dict[str, Any]:
    """Get extended video metadata.

    Returns detailed video information including scene change detection
    and dominant colors.

    Args:
        input_path: Absolute path to input video.

    Returns:
        Dict with duration, fps, resolution, bitrate, has_audio, scene_changes.
    """
    try:
        from .effects_engine import video_info_detailed as _info

        return _result(_info(input_path))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_auto_chapters(
    input_path: str,
    threshold: float = 0.3,
) -> dict[str, Any]:
    """Auto-detect scene changes and create chapters.

    Analyzes video for scene cuts and returns chapter timestamps.

    Args:
        input_path: Absolute path to input video.
        threshold: Scene detection threshold 0-1. Default 0.3.

    Returns:
        List of (timestamp, description) chapter tuples.
    """
    if not 0.0 <= threshold <= 1.0:
        return _error_result(
            MCPVideoError(
                f"threshold must be between 0.0 and 1.0, got {threshold}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    try:
        from .effects_engine import auto_chapters as _chapters

        return _result(_chapters(input_path, threshold))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


# ---------------------------------------------------------------------------
# Transition Tools (Advanced Effects)
# ---------------------------------------------------------------------------


@mcp.tool()
def transition_glitch(
    clip1_path: str,
    clip2_path: str,
    output_path: str | None = None,
    duration: float = 0.5,
    intensity: float = 0.3,
) -> dict[str, Any]:
    """Apply glitch transition between two video clips.

    Args:
        clip1_path: Absolute path to first video clip.
        clip2_path: Absolute path to second video clip.
        output_path: Absolute path for output video.
        duration: Transition duration in seconds (default 0.5).
        intensity: Glitch intensity 0-1 (default 0.3).
    """
    if duration <= 0:
        return _error_result(
            MCPVideoError(
                f"duration must be positive, got {duration}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if not 0.0 <= intensity <= 1.0:
        return _error_result(
            MCPVideoError(
                f"intensity must be between 0.0 and 1.0, got {intensity}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    try:
        from .transitions_engine import transition_glitch

        output = output_path or _auto_output(clip1_path, "transition")
        return _result(transition_glitch(clip1_path, clip2_path, output, duration, intensity))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def transition_pixelate(
    clip1_path: str,
    clip2_path: str,
    output_path: str,
    duration: float = 0.4,
    pixel_size: int = 50,
) -> dict[str, Any]:
    """Apply pixelate transition between two video clips."""
    if duration <= 0:
        return _error_result(
            MCPVideoError(
                f"duration must be positive, got {duration}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if pixel_size < 2:
        return _error_result(
            MCPVideoError(
                f"pixel_size must be at least 2, got {pixel_size}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    try:
        from .transitions_engine import transition_pixelate

        return _result(transition_pixelate(clip1_path, clip2_path, output_path, duration, pixel_size))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def transition_morph(
    clip1_path: str,
    clip2_path: str,
    output_path: str,
    duration: float = 0.6,
    mesh_size: int = 10,
) -> dict[str, Any]:
    """Apply morph transition between two video clips."""
    if duration <= 0:
        return _error_result(
            MCPVideoError(
                f"duration must be positive, got {duration}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if mesh_size < 2:
        return _error_result(
            MCPVideoError(
                f"mesh_size must be at least 2, got {mesh_size}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    try:
        from .transitions_engine import transition_morph

        return _result(transition_morph(clip1_path, clip2_path, output_path, duration, mesh_size))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)
