"""mcp-video MCP server — exposes video editing tools for AI agents."""

from __future__ import annotations

import os
import re
from typing import Any

from .engine import (
    _validate_chroma_color,
    apply_filter,
    apply_mask,
    audio_waveform,
    chroma_key,
    compare_quality,
    create_from_images,
    detect_scenes,
    export_frames,
    generate_subtitles,
    normalize_audio,
    overlay_video,
    read_metadata,
    reverse,
    split_screen,
    stabilize,
    thumbnail,
    write_metadata,
)
from .errors import MCPVideoError
from .server_app import _error_result, _result, mcp
from .server_resources import (
    templates_resource as templates_resource,
    video_audio_resource as video_audio_resource,
    video_info_resource as video_info_resource,
    video_preview_resource as video_preview_resource,
)
from .server_tools_basic import (
    VALID_XFADE_TRANSITIONS as VALID_XFADE_TRANSITIONS,
    video_add_audio as video_add_audio,
    video_add_text as video_add_text,
    video_convert as video_convert,
    video_info as video_info,
    video_merge as video_merge,
    video_resize as video_resize,
    video_speed as video_speed,
    video_trim as video_trim,
)
from .server_tools_media import (
    video_crop as video_crop,
    video_edit as video_edit,
    video_export as video_export,
    video_extract_audio as video_extract_audio,
    video_fade as video_fade,
    video_preview as video_preview,
    video_rotate as video_rotate,
    video_storyboard as video_storyboard,
    video_subtitles as video_subtitles,
    video_thumbnail as video_thumbnail,
    video_watermark as video_watermark,
)
from .limits import (
    MAX_BATCH_SIZE,
    MAX_CONCURRENCY,
    MAX_CRF,
    MAX_EXPORT_FRAMES_FPS,
    MAX_FREQUENCY,
    MAX_PORT,
    MAX_RESOLUTION,
    MIN_CRF,
    MIN_FREQUENCY,
    MIN_PORT,
)
from .validation import (
    VALID_AUDIO_EFFECT_TYPES,
    VALID_AUDIO_PRESETS,
    VALID_AUDIO_SEQUENCE_TYPES,
    VALID_CODECS,
    VALID_COLOR_GRADE_STYLES,
    VALID_DEMUCS_MODELS,
    VALID_LAYOUTS,
    VALID_MOGRAPH_STYLES,
    VALID_PRESETS,
    VALID_REMOTION_TEMPLATES,
    VALID_SPATIAL_METHODS,
    VALID_UPSCALE_MODELS,
    VALID_WAVEFORMS,
    VALID_WHISPER_MODELS,
)

# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def video_filter(
    input_path: str,
    filter_type: str,
    params: dict[str, Any] | None = None,
    output_path: str | None = None,
    crf: int | None = None,
    preset: str | None = None,
) -> dict[str, Any]:
    """Apply a visual filter to a video.

    Args:
        input_path: Absolute path to the input video.
        filter_type: Filter type (blur, sharpen, brightness, contrast, saturation, grayscale, sepia, invert, vignette, color_preset).
        params: Optional filter parameters (e.g. radius for blur, preset for color_preset).
        output_path: Where to save the output. Auto-generated if omitted.
        crf: Override CRF value (0-51, lower = better quality). Default 23.
        preset: Override FFmpeg encoding preset (ultrafast, fast, medium, slow, veryslow).
    """
    if crf is not None and not (0 <= crf <= 51):
        return _error_result(
            MCPVideoError(f"crf must be 0-51, got {crf}", error_type="validation_error", code="invalid_parameter")
        )
    if preset is not None and preset not in VALID_PRESETS:
        return _error_result(
            MCPVideoError(f"Invalid preset: {preset}", error_type="validation_error", code="invalid_parameter")
        )
    try:
        return _result(
            apply_filter(
                input_path,
                filter_type=filter_type,
                params=params,
                output_path=output_path,
                crf=crf,
                preset=preset,
            )
        )
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_reverse(
    input_path: str,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Reverse video and audio playback so it plays backwards.

    Args:
        input_path: Absolute path to the input video.
        output_path: Where to save the output. Auto-generated if omitted.
    """
    try:
        return _result(reverse(input_path, output_path=output_path))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_chroma_key(
    input_path: str,
    color: str = "0x00FF00",
    similarity: float = 0.01,
    blend: float = 0.0,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Remove a solid color background (green screen / chroma key).

    Args:
        input_path: Absolute path to the input video.
        color: Color to make transparent in hex format (default green: 0x00FF00).
        similarity: How similar colors need to be to be keyed out (0.0-1.0, default 0.01).
        blend: How much to blend the keyed color (default 0.0).
        output_path: Where to save the output. Auto-generated if omitted.
    """
    try:
        _validate_chroma_color(color)
    except MCPVideoError as e:
        return _error_result(e)
    if not 0 <= similarity <= 1:
        return _error_result(
            MCPVideoError(
                f"similarity must be between 0 and 1, got {similarity}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if not 0 <= blend <= 1:
        return _error_result(
            MCPVideoError(
                f"blend must be between 0 and 1, got {blend}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    try:
        return _result(chroma_key(input_path, color=color, similarity=similarity, blend=blend, output_path=output_path))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_blur(
    input_path: str,
    radius: int = 5,
    strength: int = 1,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Apply blur effect to a video.

    Args:
        input_path: Absolute path to the input video.
        radius: Blur radius in pixels (default 5).
        strength: Blur strength (default 1).
        output_path: Where to save the output. Auto-generated if omitted.
    """
    try:
        return _result(
            apply_filter(
                input_path,
                filter_type="blur",
                params={"radius": radius, "strength": strength},
                output_path=output_path,
            )
        )
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_color_grade(
    input_path: str,
    preset: str = "warm",
    output_path: str | None = None,
) -> dict[str, Any]:
    """Apply a color grading preset to a video.

    Args:
        input_path: Absolute path to the input video.
        preset: Color preset (warm, cool, vintage, cinematic, noir).
        output_path: Where to save the output. Auto-generated if omitted.
    """
    try:
        return _result(
            apply_filter(
                input_path,
                filter_type="color_preset",
                params={"preset": preset},
                output_path=output_path,
            )
        )
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_normalize_audio(
    input_path: str,
    target_lufs: float = -16.0,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Normalize audio loudness to a target LUFS level.

    Common presets: -16 (YouTube), -23 (EBU R128/broadcast), -14 (Apple/Spotify).

    Args:
        input_path: Absolute path to the input video.
        target_lufs: Target integrated loudness in LUFS (default -16 for YouTube).
        output_path: Where to save the output. Auto-generated if omitted.
    """
    try:
        if not -70 <= target_lufs <= -5:
            return _error_result(
                MCPVideoError(
                    f"target_lufs must be between -70 and -5, got {target_lufs}",
                    error_type="validation_error",
                    code="invalid_parameter",
                )
            )
        return _result(normalize_audio(input_path, target_lufs=target_lufs, output_path=output_path))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_overlay(
    background_path: str,
    overlay_path: str,
    position: str | dict = "top-right",
    width: int | None = None,
    height: int | None = None,
    opacity: float = 0.8,
    start_time: float | None = None,
    duration: float | None = None,
    output_path: str | None = None,
    crf: int | None = None,
    preset: str | None = None,
) -> dict[str, Any]:
    """Picture-in-picture: overlay a video on top of another.

    Args:
        background_path: Absolute path to the background video.
        overlay_path: Absolute path to the overlay video.
        position: Position on screen. Named (top-left, etc.), pixel {"x": 100, "y": 50}, or percentage {"x_pct": 0.5, "y_pct": 0.5}.
        width: Width to scale the overlay to (pixels).
        height: Height to scale the overlay to (pixels).
        opacity: Overlay opacity (0.0 to 1.0).
        start_time: When the overlay appears (seconds).
        duration: How long the overlay is visible (seconds).
        output_path: Where to save the output. Auto-generated if omitted.
        crf: Override CRF value (0-51, lower = better quality). Default 23.
        preset: Override FFmpeg encoding preset (ultrafast, fast, medium, slow, veryslow).
    """
    if width is not None and width <= 0:
        return _error_result(
            MCPVideoError(
                f"width must be positive, got {width}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if height is not None and height <= 0:
        return _error_result(
            MCPVideoError(
                f"height must be positive, got {height}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if crf is not None and not (0 <= crf <= 51):
        return _error_result(
            MCPVideoError(f"crf must be 0-51, got {crf}", error_type="validation_error", code="invalid_parameter")
        )
    if preset is not None and preset not in VALID_PRESETS:
        return _error_result(
            MCPVideoError(f"Invalid preset: {preset}", error_type="validation_error", code="invalid_parameter")
        )
    try:
        if not 0 <= opacity <= 1:
            return _error_result(
                MCPVideoError(
                    f"opacity must be between 0 and 1, got {opacity}",
                    error_type="validation_error",
                    code="invalid_parameter",
                )
            )
        return _result(
            overlay_video(
                background_path,
                overlay_path=overlay_path,
                position=position,
                width=width,
                height=height,
                opacity=opacity,
                start_time=start_time,
                duration=duration,
                output_path=output_path,
                crf=crf,
                preset=preset,
            )
        )
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_split_screen(
    left_path: str,
    right_path: str,
    layout: str = "side-by-side",
    output_path: str | None = None,
) -> dict[str, Any]:
    """Place two videos side by side or top/bottom.

    Args:
        left_path: Absolute path to the first video.
        right_path: Absolute path to the second video.
        layout: Layout type (side-by-side or top-bottom).
        output_path: Where to save the output. Auto-generated if omitted.
    """
    if layout not in VALID_LAYOUTS:
        return _error_result(
            MCPVideoError(
                f"Invalid layout: must be one of {sorted(VALID_LAYOUTS)}, got '{layout}'",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    try:
        return _result(split_screen(left_path, right_path=right_path, layout=layout, output_path=output_path))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_detect_scenes(
    input_path: str,
    threshold: float = 0.3,
    min_scene_duration: float = 1.0,
) -> dict[str, Any]:
    """Detect scene changes in a video.

    Args:
        input_path: Absolute path to the input video.
        threshold: Scene detection sensitivity (0.0-1.0, lower = more sensitive, default 0.3).
        min_scene_duration: Minimum scene duration in seconds (default 1.0).
    """
    try:
        if not 0 <= threshold <= 1:
            return _error_result(
                MCPVideoError(
                    f"threshold must be between 0 and 1, got {threshold}",
                    error_type="validation_error",
                    code="invalid_parameter",
                )
            )
        if min_scene_duration <= 0:
            return _error_result(
                MCPVideoError(
                    f"min_scene_duration must be positive, got {min_scene_duration}",
                    error_type="validation_error",
                    code="invalid_parameter",
                )
            )
        return _result(detect_scenes(input_path, threshold=threshold, min_scene_duration=min_scene_duration))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_create_from_images(
    images: list[str],
    output_path: str | None = None,
    fps: float = 30.0,
) -> dict[str, Any]:
    """Create a video from a sequence of images.

    Args:
        images: List of absolute paths to image files (in order).
        output_path: Where to save the output video. Auto-generated if omitted.
        fps: Frames per second for the output video (default 30.0).
    """
    try:
        if fps <= 0 or fps > MAX_EXPORT_FRAMES_FPS:
            return _error_result(
                MCPVideoError(
                    f"fps must be between 1 and {MAX_EXPORT_FRAMES_FPS}, got {fps}",
                    error_type="validation_error",
                    code="invalid_parameter",
                )
            )
        return _result(create_from_images(images, output_path=output_path, fps=fps))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_export_frames(
    input_path: str,
    output_dir: str | None = None,
    fps: float = 1.0,
    format: str = "jpg",
) -> dict[str, Any]:
    """Export frames from a video as individual images.

    Args:
        input_path: Absolute path to the input video.
        output_dir: Directory for extracted frames. Auto-generated if omitted.
        fps: Frames per second to extract (1.0 = 1 frame per second, default 1.0).
        format: Output image format (jpg or png, default jpg).
    """
    if fps <= 0:
        return _error_result(
            MCPVideoError(
                f"fps must be positive, got {fps}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if fps > MAX_EXPORT_FRAMES_FPS:
        return _error_result(
            MCPVideoError(
                f"FPS {fps} exceeds maximum of {MAX_EXPORT_FRAMES_FPS}",
                error_type="validation_error",
                code="fps_too_high",
            )
        )
    try:
        return _result(export_frames(input_path, output_dir=output_dir, fps=fps, format=format))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_generate_subtitles(
    entries: list[dict],
    input_path: str,
    burn: bool = False,
) -> dict[str, Any]:
    """Generate SRT subtitles from text entries and optionally burn into video.

    Args:
        entries: List of subtitle entries with keys: start (float), end (float), text (str).
        input_path: Absolute path to the input video.
        burn: If True, burn subtitles into the video (default False).
    """
    if not isinstance(entries, list) or len(entries) == 0:
        return _error_result(
            MCPVideoError(
                "entries must be a non-empty list",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    try:
        return _result(generate_subtitles(entries, input_path, burn=burn))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_compare_quality(
    original_path: str,
    distorted_path: str,
    metrics: list[str] | None = None,
) -> dict[str, Any]:
    """Compare video quality between original and processed versions.

    Args:
        original_path: Absolute path to the original/reference video.
        distorted_path: Absolute path to the processed/distorted video.
        metrics: Metrics to compute (default: ['psnr', 'ssim']).
    """
    try:
        return _result(compare_quality(original_path, distorted_path, metrics=metrics))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_read_metadata(
    input_path: str,
) -> dict[str, Any]:
    """Read metadata tags from a video/audio file.

    Args:
        input_path: Absolute path to the video or audio file.
    """
    try:
        return _result(read_metadata(input_path))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_write_metadata(
    input_path: str,
    metadata: dict[str, str],
    output_path: str | None = None,
) -> dict[str, Any]:
    """Write metadata tags to a video/audio file.

    Args:
        input_path: Absolute path to the input file.
        metadata: Dict of tag key-value pairs (e.g. {'title': 'My Video', 'artist': 'Me'}).
        output_path: Where to save the output. Auto-generated if omitted.
    """
    try:
        return _result(write_metadata(input_path, metadata=metadata, output_path=output_path))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_stabilize(
    input_path: str,
    smoothing: float = 15,
    zooming: float = 0,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Stabilize a shaky video using motion vector analysis.

    Args:
        input_path: Absolute path to the input video.
        smoothing: Smoothing strength (default 15, higher = more stable).
        zooming: Zoom percentage to avoid black borders (default 0).
        output_path: Where to save the output. Auto-generated if omitted.
    """
    try:
        if smoothing < 0:
            return _error_result(
                MCPVideoError(
                    f"smoothing must be non-negative, got {smoothing}",
                    error_type="validation_error",
                    code="invalid_parameter",
                )
            )
        if zooming < 0:
            return _error_result(
                MCPVideoError(
                    f"zooming must be non-negative, got {zooming}",
                    error_type="validation_error",
                    code="invalid_parameter",
                )
            )
        return _result(stabilize(input_path, smoothing=smoothing, zooming=zooming, output_path=output_path))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_apply_mask(
    input_path: str,
    mask_path: str,
    feather: int = 5,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Apply an image mask to a video with edge feathering.

    Args:
        input_path: Absolute path to the input video.
        mask_path: Absolute path to the mask image (white = visible, black = transparent).
        feather: Feather/blur amount at mask edges in pixels (default 5).
        output_path: Where to save the output. Auto-generated if omitted.
    """
    try:
        if feather < 0:
            return _error_result(
                MCPVideoError(
                    f"feather must be non-negative, got {feather}",
                    error_type="validation_error",
                    code="invalid_parameter",
                )
            )
        return _result(apply_mask(input_path, mask_path=mask_path, feather=feather, output_path=output_path))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_audio_waveform(
    input_path: str,
    bins: int = 50,
) -> dict[str, Any]:
    """Extract audio waveform data (peaks and silence regions).

    Args:
        input_path: Absolute path to the input video/audio file.
        bins: Number of time segments to analyze (default 50).
    """
    try:
        if bins < 1 or bins > 1000:
            return _error_result(
                MCPVideoError(
                    f"bins must be between 1 and 1000, got {bins}",
                    error_type="validation_error",
                    code="invalid_parameter",
                )
            )
        return _result(audio_waveform(input_path, bins=bins))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


from .engine import video_batch as _video_batch  # noqa: E402


@mcp.tool()
def video_batch(
    inputs: list[str],
    operation: str,
    params: dict[str, Any] | None = None,
    output_dir: str | None = None,
) -> dict[str, Any]:
    """Apply the same operation to multiple video files.

    Args:
        inputs: List of absolute paths to input video files.
        operation: Operation (trim, resize, convert, filter, blur, color_grade, watermark, speed, fade, normalize_audio).
        params: Parameters for the operation.
        output_dir: Directory for output files. Auto-generated if omitted.
    """
    VALID_BATCH_OPERATIONS = {
        "trim",
        "resize",
        "convert",
        "filter",
        "blur",
        "color_grade",
        "watermark",
        "speed",
        "fade",
        "normalize_audio",
    }
    if operation not in VALID_BATCH_OPERATIONS:
        return _error_result(
            MCPVideoError(
                f"Unknown operation '{operation}'. Valid operations: {sorted(VALID_BATCH_OPERATIONS)}",
                error_type="validation_error",
                code="invalid_operation",
            )
        )
    if len(inputs) > MAX_BATCH_SIZE:
        return _error_result(
            MCPVideoError(
                f"Batch size {len(inputs)} exceeds maximum of {MAX_BATCH_SIZE}",
                error_type="validation_error",
                code="batch_too_large",
            )
        )
    try:
        return _result(_video_batch(inputs, operation, params, output_dir))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return {"success": False, "error": {"type": "internal_error", "code": "unexpected_error", "message": str(e)}}


@mcp.tool()
def video_extract_frame(
    input_path: str,
    timestamp: float | None = None,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Extract a single frame from a video. Alias for video_thumbnail.

    Args:
        input_path: Absolute path to the input video.
        timestamp: Time in seconds to extract frame. Defaults to 10% of video duration.
        output_path: Where to save the frame image. Auto-generated if omitted.
    """
    try:
        return _result(thumbnail(input_path, timestamp=timestamp, output_path=output_path))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


# ---------------------------------------------------------------------------
# Image Analysis Tools
# ---------------------------------------------------------------------------


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
        from .image_engine import analyze_product

        return _result(analyze_product(image_path, use_ai=use_ai, n_colors=n_colors))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


# ---------------------------------------------------------------------------
# Remotion Integration Tools
# ---------------------------------------------------------------------------


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
    try:
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
    if port < MIN_PORT or port > MAX_PORT:
        return _error_result(
            MCPVideoError(
                f"Invalid port: must be {MIN_PORT}-{MAX_PORT}, got {port}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    try:
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
    try:
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
    if not re.match(r"^[a-zA-Z0-9_-]+$", slug):
        return _error_result(
            MCPVideoError(
                "Invalid slug: must match ^[a-zA-Z0-9_-]+$", error_type="validation_error", code="invalid_parameter"
            )
        )
    try:
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
    try:
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
    if not isinstance(post_process, list) or len(post_process) < 1:
        return _error_result(
            MCPVideoError(
                "Invalid post_process: must be a non-empty list",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    try:
        from .remotion_engine import render_and_post

        return _result(render_and_post(project_path, composition_id, post_process, output_path=output_path))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


# ---------------------------------------------------------------------------
# Audio Synthesis Tools (P1 Features)
# ---------------------------------------------------------------------------


@mcp.tool()
def audio_synthesize(
    output_path: str,
    waveform: str = "sine",
    frequency: float = 440.0,
    duration: float = 1.0,
    volume: float = 0.5,
    effects: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate audio procedurally using synthesis.

    Creates WAV files from scratch using mathematical waveforms. No external audio
    files needed. Supports envelopes, reverb, filtering, and fade effects.

    Args:
        output_path: Absolute path for the output WAV file.
        waveform: Waveform type (sine, square, sawtooth, triangle, noise). Default sine.
        frequency: Base frequency in Hz. Default 440 (A4 note).
        duration: Duration in seconds. Default 1.0.
        volume: Amplitude 0-1. Default 0.5.
        effects: Optional effects dict with keys:
            - envelope: {"attack", "decay", "sustain", "release"} in seconds
            - fade_in: Fade in duration in seconds
            - fade_out: Fade out duration in seconds
            - reverb: {"room_size", "damping", "wet_level"}
            - lowpass: Cutoff frequency in Hz

    Returns:
        Dict with success status and output_path.
    """
    if waveform not in VALID_WAVEFORMS:
        return _error_result(
            MCPVideoError(
                f"Invalid waveform: must be one of {sorted(VALID_WAVEFORMS)}, got '{waveform}'",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if frequency < MIN_FREQUENCY or frequency > MAX_FREQUENCY:
        return _error_result(
            MCPVideoError(
                f"Invalid frequency: must be {MIN_FREQUENCY}-{MAX_FREQUENCY}, got {frequency}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if duration <= 0:
        return _error_result(
            MCPVideoError(
                f"Invalid duration: must be > 0, got {duration}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if volume < 0 or volume > 1:
        return _error_result(
            MCPVideoError(
                f"Invalid volume: must be 0-1, got {volume}", error_type="validation_error", code="invalid_parameter"
            )
        )
    try:
        from .audio_engine import audio_synthesize as _synth

        return _result(
            _synth(
                output=output_path,
                waveform=waveform,
                frequency=frequency,
                duration=duration,
                volume=volume,
                effects=effects,
            )
        )
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def audio_preset(
    preset: str,
    output_path: str,
    pitch: str = "mid",
    duration: float | None = None,
    intensity: float = 0.5,
) -> dict[str, Any]:
    """Generate preset sound design elements.

    Pre-configured sound effects for common use cases. No external audio files needed.

    Available presets:
    - UI: ui-blip, ui-click, ui-tap, ui-whoosh-up, ui-whoosh-down
    - Ambient: drone-low, drone-mid, drone-tech
    - Notifications: chime-success, chime-error, chime-notification
    - Data: typing, scan, processing, data-flow

    Args:
        preset: Preset name from the list above.
        output_path: Absolute path for the output WAV file.
        pitch: Pitch variation (low, mid, high). Default mid.
        duration: Override default duration (seconds).
        intensity: Effect intensity 0-1. Default 0.5.

    Returns:
        Dict with success status and output_path.
    """
    if preset not in VALID_AUDIO_PRESETS:
        return _error_result(
            MCPVideoError(
                f"Invalid preset: must be one of {sorted(VALID_AUDIO_PRESETS)}, got '{preset}'",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if pitch not in {"low", "mid", "high"}:
        return _error_result(
            MCPVideoError(
                f"Invalid pitch: must be one of ['high', 'low', 'mid'], got '{pitch}'",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if intensity < 0 or intensity > 1:
        return _error_result(
            MCPVideoError(
                f"Invalid intensity: must be 0-1, got {intensity}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if duration is not None and duration <= 0:
        return _error_result(
            MCPVideoError(
                f"Invalid duration: must be > 0, got {duration}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    try:
        from .audio_engine import audio_preset as _preset

        return _result(
            _preset(
                preset=preset,
                output=output_path,
                pitch=pitch,
                duration=duration,
                intensity=intensity,
            )
        )
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def audio_sequence(
    sequence: list[dict[str, Any]],
    output_path: str,
) -> dict[str, Any]:
    """Compose multiple audio events into a timed sequence.

    Creates a layered audio track from multiple timed sound events.

    Args:
        sequence: List of audio events, each with:
            - type: "tone", "preset", or "whoosh"
            - at: Start time in seconds
            - duration: Event duration in seconds
            - freq/frequency: For tones (Hz)
            - name: For presets (preset name)
            - volume: 0-1 amplitude
            - waveform: For tones (sine, square, etc.)
        output_path: Absolute path for the output WAV file.

    Returns:
        Dict with success status and output_path.
    """
    if not isinstance(sequence, list) or len(sequence) < 1:
        return _error_result(
            MCPVideoError(
                "Invalid sequence: must be a non-empty list", error_type="validation_error", code="invalid_parameter"
            )
        )
    for i, event in enumerate(sequence):
        if not isinstance(event, dict):
            return _error_result(
                MCPVideoError(
                    f"Invalid sequence[{i}]: must be a dict", error_type="validation_error", code="invalid_parameter"
                )
            )
        evt_type = event.get("type")
        if evt_type not in VALID_AUDIO_SEQUENCE_TYPES:
            return _error_result(
                MCPVideoError(
                    f"Invalid sequence[{i}].type: must be one of {sorted(VALID_AUDIO_SEQUENCE_TYPES)}, got '{evt_type}'",
                    error_type="validation_error",
                    code="invalid_parameter",
                )
            )
        evt_at = event.get("at")
        if not isinstance(evt_at, (int, float)):
            return _error_result(
                MCPVideoError(
                    f"Invalid sequence[{i}].at: must be numeric, got {type(evt_at).__name__}",
                    error_type="validation_error",
                    code="invalid_parameter",
                )
            )
        evt_dur = event.get("duration")
        if evt_dur is not None and evt_dur <= 0:
            return _error_result(
                MCPVideoError(
                    f"Invalid sequence[{i}].duration: must be > 0, got {evt_dur}",
                    error_type="validation_error",
                    code="invalid_parameter",
                )
            )
    try:
        from .audio_engine import audio_sequence as _sequence

        return _result(_sequence(sequence=sequence, output=output_path))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def audio_compose(
    tracks: list[dict[str, Any]],
    duration: float,
    output_path: str,
) -> dict[str, Any]:
    """Layer multiple audio tracks with volume mixing.

    Mix multiple WAV files together with individual volume control.

    Args:
        tracks: List of track configs with:
            - file: Absolute path to WAV file
            - volume: Volume multiplier 0-1
            - start: Start time offset in seconds
            - loop: Whether to loop the track (default false)
        duration: Total output duration in seconds.
        output_path: Absolute path for the output WAV file.

    Returns:
        Dict with success status and output_path.
    """
    if duration <= 0:
        return _error_result(
            MCPVideoError(
                f"Invalid duration: must be > 0, got {duration}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if not isinstance(tracks, list) or len(tracks) < 1:
        return _error_result(
            MCPVideoError(
                "Invalid tracks: must be a non-empty list", error_type="validation_error", code="invalid_parameter"
            )
        )
    for i, track in enumerate(tracks):
        if not isinstance(track, dict):
            return _error_result(
                MCPVideoError(
                    f"Invalid tracks[{i}]: must be a dict", error_type="validation_error", code="invalid_parameter"
                )
            )
        if not isinstance(track.get("file"), str):
            return _error_result(
                MCPVideoError(
                    f"Invalid tracks[{i}].file: must be a string",
                    error_type="validation_error",
                    code="invalid_parameter",
                )
            )
        vol = track.get("volume", 1.0)
        if vol < 0 or vol > 1:
            return _error_result(
                MCPVideoError(
                    f"Invalid tracks[{i}].volume: must be 0-1, got {vol}",
                    error_type="validation_error",
                    code="invalid_parameter",
                )
            )
    try:
        from .audio_engine import audio_compose as _compose

        return _result(_compose(tracks=tracks, duration=duration, output=output_path))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def audio_effects(
    input_path: str,
    output_path: str,
    effects: list[dict[str, Any]],
) -> dict[str, Any]:
    """Apply audio effects chain to a WAV file.

    Process audio through a chain of effects like reverb, filtering, normalization.

    Args:
        input_path: Absolute path to input WAV file.
        output_path: Absolute path for output WAV file.
        effects: List of effect configs with:
            - type: "lowpass", "reverb", "normalize", "fade"
            - Additional params per effect type

    Returns:
        Dict with success status and output_path.
    """
    if not isinstance(effects, list) or len(effects) < 1:
        return _error_result(
            MCPVideoError(
                "Invalid effects: must be a non-empty list", error_type="validation_error", code="invalid_parameter"
            )
        )
    for i, effect in enumerate(effects):
        if not isinstance(effect, dict):
            return _error_result(
                MCPVideoError(
                    f"Invalid effects[{i}]: must be a dict", error_type="validation_error", code="invalid_parameter"
                )
            )
        eff_type = effect.get("type")
        if eff_type not in VALID_AUDIO_EFFECT_TYPES:
            return _error_result(
                MCPVideoError(
                    f"Invalid effects[{i}].type: must be one of {sorted(VALID_AUDIO_EFFECT_TYPES)}, got '{eff_type}'",
                    error_type="validation_error",
                    code="invalid_parameter",
                )
            )
    try:
        from .audio_engine import audio_effects as _effects

        return _result(_effects(input_path=input_path, output=output_path, effects=effects))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_add_generated_audio(
    input_path: str,
    audio_config: dict[str, Any],
    output_path: str,
) -> dict[str, Any]:
    """Add procedurally generated audio to a video.

    One-shot convenience function to generate and add audio to video.

    Args:
        input_path: Absolute path to input video.
        audio_config: Configuration dict with:
            - drone: {"frequency", "volume"} for background tone
            - events: List of timed sound events
        output_path: Absolute path for output video.

    Returns:
        Dict with success status and output_path.
    """
    try:
        if not isinstance(audio_config, dict) or not audio_config:
            return _error_result(ValueError("audio_config must be a non-empty dict"))
        from .audio_engine import add_generated_audio as _add_gen_audio

        return _result(_add_gen_audio(input_path, audio_config, output_path))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


# ---------------------------------------------------------------------------
# Visual Effects Tools (P1 Features)
# ---------------------------------------------------------------------------


@mcp.tool()
def effect_vignette(
    input_path: str,
    output_path: str,
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

        return _result(_vignette(input_path, output_path, intensity, radius, smoothness))
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
    output_path: str,
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

        return _result(_text(input_path, text, output_path, animation, font, size, color, position, start, duration))
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
    output_path: str,
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

        return _result(transition_glitch(clip1_path, clip2_path, output_path, duration, intensity))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return {"success": False, "error": {"type": "internal_error", "code": "unexpected_error", "message": str(e)}}


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
        return {"success": False, "error": {"type": "internal_error", "code": "unexpected_error", "message": str(e)}}


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
        return {"success": False, "error": {"type": "internal_error", "code": "unexpected_error", "message": str(e)}}


# ---------------------------------------------------------------------------
# AI Feature Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def video_ai_remove_silence(
    input_path: str,
    output_path: str,
    silence_threshold: float = -50,
    min_silence_duration: float = 0.5,
    keep_margin: float = 0.1,
) -> dict[str, Any]:
    """Remove silent sections from video."""
    if not -70 <= silence_threshold <= 0:
        return _error_result(
            MCPVideoError(
                f"silence_threshold must be between -70 and 0, got {silence_threshold}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if min_silence_duration <= 0:
        return _error_result(
            MCPVideoError(
                f"min_silence_duration must be positive, got {min_silence_duration}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if keep_margin < 0:
        return _error_result(
            MCPVideoError(
                f"keep_margin must be non-negative, got {keep_margin}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    try:
        from .ai_engine import ai_remove_silence

        return _result(ai_remove_silence(input_path, output_path, silence_threshold, min_silence_duration, keep_margin))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return {"success": False, "error": {"type": "internal_error", "code": "unexpected_error", "message": str(e)}}


@mcp.tool()
def video_ai_transcribe(
    input_path: str,
    output_srt: str | None = None,
    model: str = "base",
    language: str | None = None,
) -> dict[str, Any]:
    """Transcribe speech to text using Whisper."""
    if model not in VALID_WHISPER_MODELS:
        return _error_result(
            MCPVideoError(
                f"Invalid model: must be one of {sorted(VALID_WHISPER_MODELS)}, got '{model}'",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    try:
        from .ai_engine import ai_transcribe

        return _result(ai_transcribe(input_path, output_srt, model, language))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return {"success": False, "error": {"type": "internal_error", "code": "unexpected_error", "message": str(e)}}


@mcp.tool()
def video_analyze(
    input_path: str,
    whisper_model: str = "base",
    language: str | None = None,
    scene_threshold: float = 0.3,
    include_transcript: bool = True,
    include_scenes: bool = True,
    include_audio: bool = True,
    include_quality: bool = True,
    include_chapters: bool = True,
    include_colors: bool = True,
    output_srt: str | None = None,
    output_txt: str | None = None,
    output_md: str | None = None,
    output_json: str | None = None,
) -> dict[str, Any]:
    """Comprehensive video analysis — transcript, metadata, scenes, audio, quality, chapters, colors.

    Accepts a local file path or an HTTP/HTTPS URL. Direct video URLs
    (e.g. https://example.com/clip.mp4) are downloaded automatically.
    Streaming-platform URLs (YouTube, Vimeo, TikTok, Twitter/X, Instagram,
    Twitch, …) require yt-dlp (pip install yt-dlp).
    Each sub-analysis is independent so one failure will not abort the others.

    Args:
        input_path: Local path or HTTP/HTTPS URL to the video.
        whisper_model: Whisper model size (tiny, base, small, medium, large, turbo).
        language: Language code for transcription (auto-detect if None).
        scene_threshold: Scene change sensitivity 0.0-1.0.
        include_transcript: Run speech-to-text via Whisper (requires openai-whisper).
        include_scenes: Detect scene changes and boundaries.
        include_audio: Analyse audio waveform, peaks, and silence regions.
        include_quality: Run visual quality check.
        include_chapters: Auto-generate chapter markers from scene changes.
        include_colors: Extract dominant colors and extended metadata.
        output_srt: Optional path to write SRT subtitle file.
        output_txt: Optional path to write plain-text transcript.
        output_md: Optional path to write Markdown transcript with timestamps.
        output_json: Optional path to write full JSON transcript data.
    """
    if whisper_model not in VALID_WHISPER_MODELS:
        return _error_result(
            MCPVideoError(
                f"Invalid model: must be one of {sorted(VALID_WHISPER_MODELS)}, got '{whisper_model}'",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if not 0.0 <= scene_threshold <= 1.0:
        return _error_result(
            MCPVideoError(
                f"scene_threshold must be between 0.0 and 1.0, got {scene_threshold}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    try:
        from .ai_engine import analyze_video

        return analyze_video(
            input_path,
            whisper_model=whisper_model,
            language=language,
            scene_threshold=scene_threshold,
            include_transcript=include_transcript,
            include_scenes=include_scenes,
            include_audio=include_audio,
            include_quality=include_quality,
            include_chapters=include_chapters,
            include_colors=include_colors,
            output_srt=output_srt,
            output_txt=output_txt,
            output_md=output_md,
            output_json=output_json,
        )
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return {"success": False, "error": {"type": "internal_error", "code": "unexpected_error", "message": str(e)}}


@mcp.tool()
def video_ai_scene_detect(
    input_path: str,
    threshold: float = 0.3,
    use_ai: bool = False,
) -> dict[str, Any]:
    """Detect scene changes in video."""
    if not 0.0 <= threshold <= 1.0:
        return _error_result(
            MCPVideoError(
                f"threshold must be between 0.0 and 1.0, got {threshold}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    try:
        from .ai_engine import ai_scene_detect

        return _result(ai_scene_detect(input_path, threshold, use_ai))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return {"success": False, "error": {"type": "internal_error", "code": "unexpected_error", "message": str(e)}}


@mcp.tool()
def video_ai_stem_separation(
    input_path: str,
    output_dir: str,
    stems: list[str] | None = None,
    model: str = "htdemucs",
) -> dict[str, Any]:
    """Separate audio into stems using Demucs."""
    if model not in VALID_DEMUCS_MODELS:
        return _error_result(
            MCPVideoError(
                f"Invalid model: must be one of {sorted(VALID_DEMUCS_MODELS)}, got '{model}'",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if stems is not None and not isinstance(stems, list):
        return _error_result(
            MCPVideoError(
                f"stems must be a list, got {type(stems).__name__}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    try:
        from .ai_engine import ai_stem_separation

        return _result(ai_stem_separation(input_path, output_dir, stems, model))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return {"success": False, "error": {"type": "internal_error", "code": "unexpected_error", "message": str(e)}}


@mcp.tool()
def video_ai_upscale(
    input_path: str,
    output_path: str,
    scale: int = 2,
    model: str = "realesrgan",
) -> dict[str, Any]:
    """Upscale video using AI super-resolution."""
    if scale not in {2, 4}:
        return _error_result(
            MCPVideoError(
                f"scale must be 2 or 4, got {scale}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if model not in VALID_UPSCALE_MODELS:
        return _error_result(
            MCPVideoError(
                f"Invalid model: must be one of {sorted(VALID_UPSCALE_MODELS)}, got '{model}'",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    try:
        from .ai_engine import ai_upscale

        return _result(ai_upscale(input_path, output_path, scale, model))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return {"success": False, "error": {"type": "internal_error", "code": "unexpected_error", "message": str(e)}}


@mcp.tool()
def video_ai_color_grade(
    input_path: str,
    output_path: str,
    reference_path: str | None = None,
    style: str = "auto",
) -> dict[str, Any]:
    """Auto color grade video."""
    if style not in VALID_COLOR_GRADE_STYLES:
        return _error_result(
            MCPVideoError(
                f"Invalid style: must be one of {sorted(VALID_COLOR_GRADE_STYLES)}, got '{style}'",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    try:
        from .ai_engine import ai_color_grade

        return _result(ai_color_grade(input_path, output_path, reference_path, style))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return {"success": False, "error": {"type": "internal_error", "code": "unexpected_error", "message": str(e)}}


@mcp.tool()
def video_audio_spatial(
    input_path: str,
    output_path: str,
    positions: list[dict],
    method: str = "hrtf",
) -> dict[str, Any]:
    """Apply 3D spatial audio positioning."""
    if method not in VALID_SPATIAL_METHODS:
        return _error_result(
            MCPVideoError(
                f"Invalid method: must be one of {sorted(VALID_SPATIAL_METHODS)}, got '{method}'",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if not isinstance(positions, list) or len(positions) == 0:
        return _error_result(
            MCPVideoError(
                "positions must be a non-empty list",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    try:
        from .ai_engine import audio_spatial

        return _result(audio_spatial(input_path, output_path, positions, method))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return {"success": False, "error": {"type": "internal_error", "code": "unexpected_error", "message": str(e)}}


@mcp.tool()
def video_quality_check(
    input_path: str,
    fail_on_warning: bool = False,
) -> dict[str, Any]:
    """Run visual quality checks on a video.

    Analyzes brightness, contrast, saturation, audio levels,
    and color balance. Returns quality scores and recommendations.

    Args:
        input_path: Absolute path to video file
        fail_on_warning: If True, treat warnings as failures
    """
    try:
        from .quality_guardrails import quality_check

        return _result(quality_check(input_path, fail_on_warning))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return {"success": False, "error": {"type": "internal_error", "code": "unexpected_error", "message": str(e)}}


@mcp.tool()
def video_design_quality_check(
    input_path: str,
    auto_fix: bool = False,
    strict: bool = False,
) -> dict[str, Any]:
    """Run comprehensive design quality analysis on a video.

    Checks layout, typography, color, motion, and composition quality.
    Can automatically fix issues where possible.

    Args:
        input_path: Absolute path to video file
        auto_fix: If True, automatically apply fixes
        strict: If True, treat warnings as errors
    """
    try:
        from .design_quality import design_quality_check

        return _result(design_quality_check(input_path, auto_fix=auto_fix, strict=strict))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return {"success": False, "error": {"type": "internal_error", "code": "unexpected_error", "message": str(e)}}


@mcp.tool()
def video_fix_design_issues(
    input_path: str,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Auto-fix design issues in a video.

    Applies automatic fixes for brightness, contrast, saturation,
    and audio level issues.

    Args:
        input_path: Absolute path to input video
        output_path: Absolute path for output (auto-generated if omitted)
    """
    try:
        from .design_quality import fix_design_issues

        return _result(fix_design_issues(input_path, output_path))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return {"success": False, "error": {"type": "internal_error", "code": "unexpected_error", "message": str(e)}}
