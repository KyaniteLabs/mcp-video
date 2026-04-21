"""Media MCP video tool registrations."""

from __future__ import annotations

import os
from typing import Any

from .engine import (
    crop,
    edit_timeline,
    export_video,
    extract_audio,
    fade,
    preview,
    rotate,
    storyboard,
    subtitles,
    thumbnail,
    watermark,
)
from .errors import MCPVideoError
from .server_app import _error_result, _result, mcp
from .validation import VALID_AUDIO_FORMATS, VALID_FORMATS, VALID_PRESETS
from .ffmpeg_helpers import _validate_input_path


@mcp.tool()
def video_thumbnail(
    input_path: str,
    timestamp: float | None = None,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Extract a single frame (thumbnail) from a video.

    Args:
        input_path: Absolute path to the input video.
        timestamp: Time in seconds to extract frame. Defaults to 10% of video duration.
        output_path: Where to save the frame image. Auto-generated if omitted.
    """
    try:
        _validate_input_path(input_path)
        return _result(thumbnail(input_path, timestamp=timestamp, output_path=output_path))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_preview(
    input_path: str,
    output_path: str | None = None,
    scale_factor: int = 4,
) -> dict[str, Any]:
    """Generate a fast low-resolution preview for quick review.

    Args:
        input_path: Absolute path to the input video.
        output_path: Where to save the preview. Auto-generated if omitted.
        scale_factor: Downscale factor (4 = 1/4 resolution).
    """
    try:
        _validate_input_path(input_path)
        MAX_SCALE_FACTOR = 16
        if scale_factor < 2:
            return _error_result(
                MCPVideoError(
                    f"scale_factor must be at least 2, got {scale_factor}",
                    error_type="validation_error",
                    code="invalid_parameter",
                )
            )
        if scale_factor > MAX_SCALE_FACTOR:
            return _error_result(
                MCPVideoError(
                    f"scale_factor must be at most {MAX_SCALE_FACTOR}, got {scale_factor}",
                    error_type="validation_error",
                    code="invalid_parameter",
                )
            )
        return _result(preview(input_path, output_path=output_path, scale_factor=scale_factor))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_storyboard(
    input_path: str,
    output_dir: str | None = None,
    frame_count: int = 8,
) -> dict[str, Any]:
    """Extract key frames and create a storyboard grid for human review.

    Args:
        input_path: Absolute path to the input video.
        output_dir: Directory to save frames. Auto-generated if omitted.
        frame_count: Number of key frames to extract.
    """
    try:
        _validate_input_path(input_path)
        MAX_FRAME_COUNT = 100
        if frame_count is not None and (frame_count < 1 or frame_count > MAX_FRAME_COUNT):
            return _error_result(
                MCPVideoError(
                    f"frame_count must be between 1 and {MAX_FRAME_COUNT}, got {frame_count}",
                    error_type="validation_error",
                    code="invalid_parameter",
                )
            )
        return _result(storyboard(input_path, output_dir=output_dir, frame_count=frame_count))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_subtitles(
    input_path: str,
    subtitle_path: str,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Burn subtitles (SRT/VTT) into a video.

    Args:
        input_path: Absolute path to the input video.
        subtitle_path: Absolute path to the subtitle file (.srt or .vtt).
        output_path: Where to save the output. Auto-generated if omitted.
    """
    try:
        _validate_input_path(input_path)
        _validate_input_path(subtitle_path)
        return _result(subtitles(input_path, subtitle_path=subtitle_path, output_path=output_path))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_watermark(
    input_path: str,
    image_path: str,
    position: str | dict = "bottom-right",
    opacity: float = 0.7,
    margin: int = 20,
    output_path: str | None = None,
    crf: int | None = None,
    preset: str | None = None,
) -> dict[str, Any]:
    """Add an image watermark to a video.

    Args:
        input_path: Absolute path to the input video.
        image_path: Absolute path to the watermark image (PNG with transparency recommended).
        position: Position on screen. Named (top-left, etc.), pixel {"x": 100, "y": 50}, or percentage {"x_pct": 0.5, "y_pct": 0.5}.
        opacity: Watermark opacity (0.0 to 1.0).
        margin: Margin from edge in pixels.
        output_path: Where to save the output. Auto-generated if omitted.
        crf: Override CRF value (0-51, lower = better quality). Default 23.
        preset: Override FFmpeg encoding preset (ultrafast, fast, medium, slow, veryslow).
    """
    if not 0 <= opacity <= 1:
        return _error_result(
            MCPVideoError(
                f"opacity must be between 0 and 1, got {opacity}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if margin < 0:
        return _error_result(
            MCPVideoError(
                f"margin must be non-negative, got {margin}",
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
        _validate_input_path(input_path)
        _validate_input_path(image_path)
        return _result(
            watermark(
                input_path,
                image_path=image_path,
                position=position,
                opacity=opacity,
                margin=margin,
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
def video_export(
    input_path: str,
    output_path: str | None = None,
    quality: str = "high",
    format: str = "mp4",
) -> dict[str, Any]:
    """Render and export a video with quality and format settings.

    Args:
        input_path: Absolute path to the input video.
        output_path: Where to save the output. Auto-generated if omitted.
        quality: Quality preset (low, medium, high, ultra).
        format: Output format (mp4, webm, gif, mov).
    """
    if format not in VALID_FORMATS:
        return _error_result(
            MCPVideoError(
                f"Invalid format: {format}. Must be one of {sorted(VALID_FORMATS)}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    try:
        return _result(
            export_video(
                input_path,
                output_path=output_path,
                quality=quality,
                format=format,
            )
        )
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_crop(
    input_path: str,
    width: int,
    height: int,
    x: int | None = None,
    y: int | None = None,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Crop a video to a rectangular region.

    Args:
        input_path: Absolute path to the input video.
        width: Width of the crop region in pixels.
        height: Height of the crop region in pixels.
        x: X offset (defaults to center).
        y: Y offset (defaults to center).
        output_path: Where to save the output. Auto-generated if omitted.
    """
    try:
        _validate_input_path(input_path)
        return _result(crop(input_path, width=width, height=height, x=x, y=y, output_path=output_path))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_rotate(
    input_path: str,
    angle: int = 0,
    flip_horizontal: bool = False,
    flip_vertical: bool = False,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Rotate and/or flip a video.

    Args:
        input_path: Absolute path to the input video.
        angle: Rotation angle (0, 90, 180, 270 degrees).
        flip_horizontal: Mirror the video horizontally.
        flip_vertical: Mirror the video vertically.
        output_path: Where to save the output. Auto-generated if omitted.
    """
    try:
        return _result(
            rotate(
                input_path,
                angle=angle,
                flip_horizontal=flip_horizontal,
                flip_vertical=flip_vertical,
                output_path=output_path,
            )
        )
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_fade(
    input_path: str,
    fade_in: float = 0.0,
    fade_out: float = 0.0,
    output_path: str | None = None,
    crf: int | None = None,
    preset: str | None = None,
) -> dict[str, Any]:
    """Add fade in/out effect to a video.

    Args:
        input_path: Absolute path to the input video.
        fade_in: Fade in duration in seconds (from black).
        fade_out: Fade out duration in seconds (to black).
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
        _validate_input_path(input_path)
        if fade_in < 0:
            return _error_result(
                MCPVideoError(
                    f"fade_in must be non-negative, got {fade_in}",
                    error_type="validation_error",
                    code="invalid_parameter",
                )
            )
        if fade_out < 0:
            return _error_result(
                MCPVideoError(
                    f"fade_out must be non-negative, got {fade_out}",
                    error_type="validation_error",
                    code="invalid_parameter",
                )
            )
        return _result(
            fade(
                input_path,
                fade_in=fade_in,
                fade_out=fade_out,
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
def video_edit(
    timeline: dict[str, Any] | str,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Execute a full timeline-based edit from a JSON specification.

    The timeline JSON describes video clips, audio tracks, text overlays,
    image overlays, transitions, and export settings in a single operation.

    Image overlays are applied in a single filtergraph pass (no multiple re-encodes).

    Args:
        timeline: JSON object with keys: width, height, tracks (video/audio/text/image), export.
            Can also be a JSON string or a path to a .json file.
            Image overlays in tracks: {"type": "image", "images": [{"source": "logo.png", "position": "top-right", "width": 200, "opacity": 0.8}]}
        output_path: Where to save the final video. Auto-generated if omitted.
    """
    parsed_timeline = timeline
    if isinstance(timeline, str):
        import json as _json

        timeline_str = timeline.strip()
        # Try parsing as inline JSON first
        try:
            parsed_timeline = _json.loads(timeline_str)
        except _json.JSONDecodeError:
            # Try reading as a file path
            if os.path.isfile(timeline_str):
                try:
                    with open(timeline_str, encoding="utf-8") as f:
                        parsed_timeline = _json.load(f)
                except (_json.JSONDecodeError, OSError) as exc:
                    return _error_result(
                        MCPVideoError(
                            f"Invalid timeline JSON file: {timeline_str} — {exc}",
                            error_type="validation_error",
                            code="invalid_json",
                        )
                    )
            else:
                return _error_result(
                    MCPVideoError(
                        f"timeline must be a dict, valid JSON string, or path to a .json file. Got: {timeline_str[:100]}",
                        error_type="validation_error",
                        code="invalid_parameter",
                    )
                )
    if not isinstance(parsed_timeline, dict):
        return _error_result(
            MCPVideoError(
                f"timeline must be a dict or JSON object. Got: {type(parsed_timeline).__name__}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    try:
        return _result(edit_timeline(parsed_timeline, output_path=output_path))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return _error_result(e)


@mcp.tool()
def video_extract_audio(
    input_path: str,
    output_path: str | None = None,
    format: str = "mp3",
) -> dict[str, Any]:
    """Extract the audio track from a video file.

    Args:
        input_path: Absolute path to the input video.
        output_path: Where to save the audio file. Auto-generated if omitted.
        format: Audio format (mp3, aac, wav, ogg, flac).
    """
    if format not in VALID_AUDIO_FORMATS:
        return _error_result(
            MCPVideoError(
                f"Invalid audio format: {format}. Must be one of {sorted(VALID_AUDIO_FORMATS)}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    try:
        _validate_input_path(input_path)
        result = extract_audio(input_path, output_path=output_path, format=format)
        if not os.path.isfile(result):
            return _error_result(
                MCPVideoError(
                    f"Audio extraction completed but output file not found: {result}",
                    error_type="processing_error",
                    code="missing_output",
                )
            )
        size_mb = os.path.getsize(result) / (1024 * 1024)
        return {
            "success": True,
            "output_path": result,
            "size_mb": round(size_mb, 2),
            "format": format,
            "operation": "extract_audio",
        }
    except MCPVideoError as e:
        return _error_result(e)
    except OSError as e:
        return _error_result(
            MCPVideoError(
                f"File error during audio extraction: {e}",
                error_type="processing_error",
                code="file_error",
            )
        )
    except Exception as e:
        return _error_result(e)
