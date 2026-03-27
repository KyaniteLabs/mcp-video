"""mcp-video MCP server — exposes video editing tools for AI agents."""

from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from .engine import (
    add_audio,
    add_text,
    apply_filter,
    apply_mask,
    audio_waveform,
    chroma_key,
    compare_quality,
    convert,
    create_from_images,
    crop,
    detect_scenes,
    edit_timeline,
    export_frames,
    export_video,
    extract_audio,
    fade,
    generate_subtitles,
    merge,
    normalize_audio,
    overlay_video,
    preview,
    probe,
    read_metadata,
    resize,
    reverse,
    rotate,
    split_screen,
    stabilize,
    storyboard,
    subtitles,
    speed,
    thumbnail,
    trim,
    watermark,
    write_metadata,
)
from .errors import MCPVideoError
from .models import (
    ExportFormat,
    FilterType,
    Position,
    QualityLevel,
    SplitLayout,
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
        transition: Single transition type for all clip pairs (fade, dissolve, wipe-*).
        transitions: Per-pair transition types. Overrides transition if both provided.
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
    position: str | dict = "top-center",
    font: str | None = None,
    size: int = 48,
    color: str = "white",
    shadow: bool = True,
    start_time: float | None = None,
    duration: float | None = None,
    output_path: str | None = None,
    crf: int | None = None,
    preset: str | None = None,
) -> dict[str, Any]:
    """Overlay text on a video (titles, captions, watermarks).

    Args:
        input_path: Absolute path to the input video.
        text: Text to overlay.
        position: Position on screen. Named (top-left, top-center, etc.), pixel {"x": 100, "y": 50}, or percentage {"x_pct": 0.5, "y_pct": 0.5}.
        font: Path to font file. Uses system default if omitted.
        size: Font size in pixels.
        color: Text color (CSS color name or hex).
        shadow: Add text shadow for readability.
        start_time: When the text appears (seconds). Null = always visible.
        duration: How long text is visible (seconds). Requires start_time.
        output_path: Where to save the output. Auto-generated if omitted.
        crf: Override CRF value (0-51, lower = better quality). Default 23.
        preset: Override FFmpeg encoding preset (ultrafast, fast, medium, slow, veryslow).
    """
    try:
        return _result(add_text(
            input_path, text=text, position=position, font=font,
            size=size, color=color, shadow=shadow,
            start_time=start_time, duration=duration,
            output_path=output_path, crf=crf, preset=preset,
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
    try:
        return _result(watermark(
            input_path, image_path=image_path, position=position,
            opacity=opacity, margin=margin, output_path=output_path,
            crf=crf, preset=preset,
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
    try:
        return _result(fade(
            input_path, fade_in=fade_in, fade_out=fade_out,
            output_path=output_path, crf=crf, preset=preset,
        ))
    except MCPVideoError as e:
        return _error_result(e)


@mcp.tool()
def video_edit(
    timeline: dict[str, Any],
    output_path: str | None = None,
) -> dict[str, Any]:
    """Execute a full timeline-based edit from a JSON specification.

    The timeline JSON describes video clips, audio tracks, text overlays,
    image overlays, transitions, and export settings in a single operation.

    Image overlays are applied in a single filtergraph pass (no multiple re-encodes).

    Args:
        timeline: JSON object with keys: width, height, tracks (video/audio/text/image), export.
            Image overlays in tracks: {"type": "image", "images": [{"source": "logo.png", "position": "top-right", "width": 200, "opacity": 0.8}]}
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
    try:
        return _result(apply_filter(
            input_path, filter_type=filter_type, params=params,
            output_path=output_path, crf=crf, preset=preset,
        ))
    except MCPVideoError as e:
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
        return _result(chroma_key(input_path, color=color, similarity=similarity, blend=blend, output_path=output_path))
    except MCPVideoError as e:
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
        return _result(apply_filter(
            input_path, filter_type="blur",
            params={"radius": radius, "strength": strength},
            output_path=output_path,
        ))
    except MCPVideoError as e:
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
        return _result(apply_filter(
            input_path, filter_type="color_preset",
            params={"preset": preset},
            output_path=output_path,
        ))
    except MCPVideoError as e:
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
        return _result(normalize_audio(input_path, target_lufs=target_lufs, output_path=output_path))
    except MCPVideoError as e:
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
    try:
        return _result(overlay_video(
            background_path, overlay_path=overlay_path, position=position,
            width=width, height=height, opacity=opacity,
            start_time=start_time, duration=duration,
            output_path=output_path, crf=crf, preset=preset,
        ))
    except MCPVideoError as e:
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
    try:
        return _result(split_screen(left_path, right_path=right_path, layout=layout, output_path=output_path))
    except MCPVideoError as e:
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
        return _result(detect_scenes(input_path, threshold=threshold, min_scene_duration=min_scene_duration))
    except MCPVideoError as e:
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
        return _result(create_from_images(images, output_path=output_path, fps=fps))
    except MCPVideoError as e:
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
    try:
        return _result(export_frames(input_path, output_dir=output_dir, fps=fps, format=format))
    except MCPVideoError as e:
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
    try:
        return _result(generate_subtitles(entries, input_path, burn=burn))
    except MCPVideoError as e:
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
        return _result(stabilize(input_path, smoothing=smoothing, zooming=zooming, output_path=output_path))
    except MCPVideoError as e:
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
        return _result(apply_mask(input_path, mask_path=mask_path, feather=feather, output_path=output_path))
    except MCPVideoError as e:
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
        return _result(audio_waveform(input_path, bins=bins))
    except MCPVideoError as e:
        return _error_result(e)


from .engine import video_batch as _video_batch


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
    return _video_batch(inputs, operation, params, output_dir)


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
    try:
        from .remotion_engine import render
        return _result(render(project_path, composition_id, output_path=output_path, codec=codec, crf=crf, width=width, height=height, fps=fps, concurrency=concurrency, frames=frames, props=props, scale=scale))
    except MCPVideoError as e:
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
    try:
        from .remotion_engine import studio
        return _result(studio(project_path, port=port))
    except MCPVideoError as e:
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
        return _result(still(project_path, composition_id, output_path=output_path, frame=frame, image_format=image_format))
    except MCPVideoError as e:
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
    try:
        from .remotion_engine import create_project
        return _result(create_project(name, output_dir=output_dir, template=template))
    except MCPVideoError as e:
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
    try:
        from .remotion_engine import scaffold_template
        return _result(scaffold_template(project_path, spec, slug))
    except MCPVideoError as e:
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
    try:
        from .remotion_engine import render_and_post
        return _result(render_and_post(project_path, composition_id, post_process, output_path=output_path))
    except MCPVideoError as e:
        return _error_result(e)
