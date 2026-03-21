"""mcp-video MCP server — exposes video editing tools for AI agents."""

from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from .engine import (
    add_audio,
    add_text,
    convert,
    crop,
    edit_timeline,
    export_video,
    extract_audio,
    fade,
    merge,
    preview,
    probe,
    resize,
    rotate,
    storyboard,
    subtitles,
    speed,
    thumbnail,
    trim,
    watermark,
)
from .errors import MCPVideoError
from .models import (
    ExportFormat,
    Position,
    QualityLevel,
)

mcp = FastMCP(
    "mcp-video",
    instructions=(
        "mcp-video is a video editing MCP server. Use these tools to trim, merge, "
        "add text overlays, sync audio, resize, convert, and export video files. "
        "All file paths should be absolute. Output files are generated automatically "
        "if no output_path is provided."
    ),
)


def _error_result(err: MCPVideoError) -> dict[str, Any]:
    return {"success": False, "error": err.to_dict()}


def _result(result: Any) -> dict[str, Any]:
    if result is None:
        return {"success": False, "error": {"type": "processing_error", "code": "no_result", "message": "Operation returned no result"}}
    if hasattr(result, "model_dump"):
        data = result.model_dump()
        # Include thumbnail_base64 only if it was generated (keep MCP responses lean)
        if not data.get("thumbnail_base64"):
            data.pop("thumbnail_base64", None)
        return data
    return {"success": True, "output_path": str(result)}


# ---------------------------------------------------------------------------
# MCP Resources
# ---------------------------------------------------------------------------

@mcp.resource("mcp-video://video/{path}/info")
def video_info_resource(path: str) -> str:
    """Get metadata about a video file (duration, resolution, codec, etc.)."""
    try:
        info = probe(path)
        return info.model_dump_json(indent=2)
    except MCPVideoError as e:
        return _error_result(e).__str__()


@mcp.resource("mcp-video://video/{path}/preview")
def video_preview_resource(path: str) -> str:
    """Get a text storyboard description (key frame timestamps)."""
    try:
        info = probe(path)
        frames = []
        dur = info.duration
        count = 8
        for i in range(count):
            ts = dur * (i + 1) / (count + 1)
            frames.append(f"Frame {i+1}: {ts:.1f}s")
        return "\n".join(frames)
    except MCPVideoError as e:
        return _error_result(e).__str__()


@mcp.resource("mcp-video://video/{path}/audio")
def video_audio_resource(path: str) -> str:
    """Extract and describe the audio track of a video."""
    try:
        info = probe(path)
        if info.audio_codec:
            return (
                f"Audio codec: {info.audio_codec}\n"
                f"Sample rate: {info.audio_sample_rate} Hz\n"
                f"Duration: {info.duration:.1f}s"
            )
        return "No audio track found."
    except MCPVideoError as e:
        return _error_result(e).__str__()


@mcp.resource("mcp-video://templates")
def templates_resource() -> str:
    """List available editing templates (aspect ratios, quality presets)."""
    from .models import ASPECT_RATIOS, QUALITY_PRESETS
    import json

    data = {
        "aspect_ratios": {k: f"{v[0]}x{v[1]}" for k, v in ASPECT_RATIOS.items()},
        "quality_presets": {
            k: f"CRF {v['crf']}, preset={v['preset']}, max_height={v['max_height']}"
            for k, v in QUALITY_PRESETS.items()
        },
        "transition_types": ["fade", "dissolve", "wipe-left", "wipe-right", "wipe-up", "wipe-down"],
        "export_formats": ["mp4", "webm", "gif", "mov"],
        "text_positions": [
            "top-left", "top-center", "top-right",
            "center-left", "center", "center-right",
            "bottom-left", "bottom-center", "bottom-right",
        ],
    }
    return json.dumps(data, indent=2)


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def video_info(input_path: str) -> dict[str, Any]:
    """Get metadata about a video file: duration, resolution, codec, fps, size.

    Args:
        input_path: Absolute path to the video file.
    """
    try:
        info = probe(input_path)
        return {"success": True, "info": info.model_dump()}
    except MCPVideoError as e:
        return _error_result(e)


@mcp.tool()
def video_trim(
    input_path: str,
    start: str = "0",
    duration: str | None = None,
    end: str | None = None,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Trim a video clip by start time and duration.

    Args:
        input_path: Absolute path to the input video.
        start: Start timestamp (e.g. '00:02:15' or seconds as string like '10.5').
        duration: Duration to keep (e.g. '00:00:30' or '30'). Exclusive with end.
        end: End timestamp. Exclusive with duration.
        output_path: Where to save the trimmed video. Auto-generated if omitted.
    """
    try:
        return _result(trim(input_path, start=start, duration=duration, end=end, output_path=output_path))
    except MCPVideoError as e:
        return _error_result(e)


@mcp.tool()
def video_merge(
    clips: list[str],
    output_path: str | None = None,
    transition: str | None = None,
    transitions: list[str] | None = None,
    transition_duration: float = 1.0,
) -> dict[str, Any]:
    """Merge multiple video clips into one.

    Args:
        clips: List of absolute paths to video clips to merge (in order).
        output_path: Where to save the merged video. Auto-generated if omitted.
        transition: Single transition type for all clip pairs (fade, dissolve, wipe-left, wipe-right, wipe-up, wipe-down).
        transitions: Per-pair transition types (one per clip boundary). Overrides transition if both provided.
        transition_duration: Duration of each transition in seconds.
    """
    try:
        return _result(merge(clips, output_path=output_path, transition=transition, transitions=transitions, transition_duration=transition_duration))
    except MCPVideoError as e:
        return _error_result(e)


@mcp.tool()
def video_add_text(
    input_path: str,
    text: str,
    position: str = "top-center",
    font: str | None = None,
    size: int = 48,
    color: str = "white",
    shadow: bool = True,
    start_time: float | None = None,
    duration: float | None = None,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Overlay text on a video (titles, captions, watermarks).

    Args:
        input_path: Absolute path to the input video.
        text: Text to overlay.
        position: Position on screen (top-left, top-center, top-right, center-left, center, center-right, bottom-left, bottom-center, bottom-right).
        font: Path to font file. Uses system default if omitted.
        size: Font size in pixels.
        color: Text color (CSS color name or hex).
        shadow: Add text shadow for readability.
        start_time: When the text appears (seconds). Null = always visible.
        duration: How long text is visible (seconds). Requires start_time.
        output_path: Where to save the output. Auto-generated if omitted.
    """
    try:
        return _result(add_text(
            input_path, text=text, position=position, font=font,
            size=size, color=color, shadow=shadow,
            start_time=start_time, duration=duration,
            output_path=output_path,
        ))
    except MCPVideoError as e:
        return _error_result(e)


@mcp.tool()
def video_add_audio(
    video_path: str,
    audio_path: str,
    volume: float = 1.0,
    fade_in: float = 0.0,
    fade_out: float = 0.0,
    mix: bool = False,
    start_time: float | None = None,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Add or replace the audio track of a video.

    Args:
        video_path: Absolute path to the video file.
        audio_path: Absolute path to the audio file (MP3, WAV, etc.).
        volume: Audio volume (0.0 to 2.0, where 1.0 = original).
        fade_in: Fade in duration in seconds.
        fade_out: Fade out duration in seconds.
        mix: If true, mix with existing audio. If false, replace it.
        start_time: When the audio starts playing (seconds).
        output_path: Where to save the output. Auto-generated if omitted.
    """
    try:
        return _result(add_audio(
            video_path, audio_path=audio_path, volume=volume,
            fade_in=fade_in, fade_out=fade_out, mix=mix,
            start_time=start_time, output_path=output_path,
        ))
    except MCPVideoError as e:
        return _error_result(e)


@mcp.tool()
def video_resize(
    input_path: str,
    width: int | None = None,
    height: int | None = None,
    aspect_ratio: str | None = None,
    quality: str = "high",
    output_path: str | None = None,
) -> dict[str, Any]:
    """Resize a video or change its aspect ratio.

    Args:
        input_path: Absolute path to the input video.
        width: Target width in pixels. Use with height.
        height: Target height in pixels. Use with width.
        aspect_ratio: Preset aspect ratio (16:9, 9:16, 1:1, 4:3, 4:5, 21:9). Overrides width/height.
        quality: Quality preset (low, medium, high, ultra).
        output_path: Where to save the output. Auto-generated if omitted.
    """
    try:
        return _result(resize(
            input_path, width=width, height=height,
            aspect_ratio=aspect_ratio, quality=quality,
            output_path=output_path,
        ))
    except MCPVideoError as e:
        return _error_result(e)


@mcp.tool()
def video_convert(
    input_path: str,
    format: str = "mp4",
    quality: str = "high",
    output_path: str | None = None,
) -> dict[str, Any]:
    """Convert a video to a different format.

    Args:
        input_path: Absolute path to the input video.
        format: Target format (mp4, webm, gif, mov).
        quality: Quality preset (low, medium, high, ultra).
        output_path: Where to save the output. Auto-generated if omitted.
    """
    try:
        return _result(convert(
            input_path, format=format, quality=quality,
            output_path=output_path,
        ))
    except MCPVideoError as e:
        return _error_result(e)


@mcp.tool()
def video_speed(
    input_path: str,
    factor: float = 1.0,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Change video playback speed.

    Args:
        input_path: Absolute path to the input video.
        factor: Speed multiplier. 2.0 = 2x faster (time-lapse), 0.5 = half speed (slow-mo).
        output_path: Where to save the output. Auto-generated if omitted.
    """
    try:
        return _result(speed(input_path, factor=factor, output_path=output_path))
    except MCPVideoError as e:
        return _error_result(e)


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
        return _result(thumbnail(input_path, timestamp=timestamp, output_path=output_path))
    except MCPVideoError as e:
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
        if scale_factor < 1:
            return _error_result(MCPVideoError(
                "scale_factor must be at least 1",
                error_type="validation_error",
                code="invalid_scale_factor",
            ))
        return _result(preview(input_path, output_path=output_path, scale_factor=scale_factor))
    except MCPVideoError as e:
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
        if frame_count < 1:
            return _error_result(MCPVideoError(
                "frame_count must be at least 1",
                error_type="validation_error",
                code="invalid_frame_count",
            ))
        return _result(storyboard(input_path, output_dir=output_dir, frame_count=frame_count))
    except MCPVideoError as e:
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
        return _result(subtitles(input_path, subtitle_path=subtitle_path, output_path=output_path))
    except MCPVideoError as e:
        return _error_result(e)


@mcp.tool()
def video_watermark(
    input_path: str,
    image_path: str,
    position: str = "bottom-right",
    opacity: float = 0.7,
    margin: int = 20,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Add an image watermark to a video.

    Args:
        input_path: Absolute path to the input video.
        image_path: Absolute path to the watermark image (PNG with transparency recommended).
        position: Position on screen (top-left, top-center, top-right, center, bottom-left, bottom-center, bottom-right).
        opacity: Watermark opacity (0.0 to 1.0).
        margin: Margin from edge in pixels.
        output_path: Where to save the output. Auto-generated if omitted.
    """
    try:
        return _result(watermark(
            input_path, image_path=image_path, position=position,
            opacity=opacity, margin=margin, output_path=output_path,
        ))
    except MCPVideoError as e:
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
    try:
        return _result(export_video(
            input_path, output_path=output_path,
            quality=quality, format=format,
        ))
    except MCPVideoError as e:
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
        return _result(crop(input_path, width=width, height=height, x=x, y=y, output_path=output_path))
    except MCPVideoError as e:
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
        return _result(rotate(input_path, angle=angle, flip_horizontal=flip_horizontal, flip_vertical=flip_vertical, output_path=output_path))
    except MCPVideoError as e:
        return _error_result(e)


@mcp.tool()
def video_fade(
    input_path: str,
    fade_in: float = 0.0,
    fade_out: float = 0.0,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Add fade in/out effect to a video.

    Args:
        input_path: Absolute path to the input video.
        fade_in: Fade in duration in seconds (from black).
        fade_out: Fade out duration in seconds (to black).
        output_path: Where to save the output. Auto-generated if omitted.
    """
    try:
        return _result(fade(input_path, fade_in=fade_in, fade_out=fade_out, output_path=output_path))
    except MCPVideoError as e:
        return _error_result(e)


@mcp.tool()
def video_edit(
    timeline: dict[str, Any],
    output_path: str | None = None,
) -> dict[str, Any]:
    """Execute a full timeline-based edit from a JSON specification.

    The timeline JSON describes video clips, audio tracks, text overlays,
    transitions, and export settings in a single operation.

    Example timeline:
    {
        "width": 1080,
        "height": 1920,
        "tracks": [
            {
                "type": "video",
                "clips": [
                    {"source": "intro.mp4", "start": 0, "duration": 5},
                    {"source": "main.mp4", "start": 5, "trim_start": 10, "duration": 30}
                ],
                "transitions": [{"after_clip": 0, "type": "fade", "duration": 1.0}]
            },
            {
                "type": "audio",
                "clips": [{"source": "music.mp3", "start": 0, "volume": 0.7}]
            },
            {
                "type": "text",
                "elements": [{"text": "EPISODE 42", "start": 0, "duration": 3, "position": "top-center"}]
            }
        ],
        "export": {"format": "mp4", "quality": "high"}
    }

    Args:
        timeline: JSON object describing the full edit timeline.
        output_path: Where to save the final video. Auto-generated if omitted.
    """
    try:
        return _result(edit_timeline(timeline, output_path=output_path))
    except Exception as e:
        if isinstance(e, MCPVideoError):
            return _error_result(e)
        return _error_result(MCPVideoError(str(e), error_type="validation_error", code="invalid_timeline"))


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
    try:
        result = extract_audio(input_path, output_path=output_path, format=format)
        if not os.path.isfile(result):
            return _error_result(MCPVideoError(
                f"Audio extraction completed but output file not found: {result}",
                error_type="processing_error",
                code="missing_output",
            ))
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
        return _error_result(MCPVideoError(
            f"File error during audio extraction: {e}",
            error_type="processing_error",
            code="file_error",
        ))
