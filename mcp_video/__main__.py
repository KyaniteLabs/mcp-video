"""mcp-video CLI entry point."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

console = Console()
err_console = Console(stderr=True)


def _format_info_text(info: Any) -> None:
    """Display video info as a rich table."""
    table = Table(title="Video Info", show_header=False, border_style="blue")
    table.add_column("Property", style="bold cyan", no_wrap=True)
    table.add_column("Value")
    table.add_row("Path", str(getattr(info, "path", "N/A")))
    table.add_row("Duration", f"{getattr(info, 'duration', 0):.2f}s")
    table.add_row("Resolution", getattr(info, "resolution", "N/A"))
    table.add_row("Aspect Ratio", getattr(info, "aspect_ratio", "N/A"))
    table.add_row("FPS", str(getattr(info, "fps", "N/A")))
    table.add_row("Video Codec", getattr(info, "codec", "N/A"))
    table.add_row("Audio Codec", getattr(info, "audio_codec", "N/A"))
    table.add_row("Size", f"{getattr(info, 'size_mb', 0):.2f} MB")
    table.add_row("Format", getattr(info, "format", "N/A"))
    console.print(table)


def _format_edit_text(result: Any) -> None:
    """Display edit result as a success panel."""
    data = result.model_dump() if hasattr(result, "model_dump") else result
    lines = [
        f"[bold green]Operation:[/bold green] {data.get('operation', 'N/A')}",
        f"[bold green]Output:[/bold green] {data.get('output_path', 'N/A')}",
    ]
    if data.get("duration") is not None:
        lines.append(f"[bold green]Duration:[/bold green] {data['duration']:.2f}s")
    if data.get("resolution"):
        lines.append(f"[bold green]Resolution:[/bold green] {data['resolution']}")
    if data.get("size_mb") is not None:
        lines.append(f"[bold green]Size:[/bold green] {data['size_mb']:.2f} MB")
    if data.get("format"):
        lines.append(f"[bold green]Format:[/bold green] {data['format']}")
    console.print(Panel("\n".join(lines), border_style="green", title="Done"))


def _format_storyboard_text(result: Any) -> None:
    """Display storyboard result."""
    data = result.model_dump() if hasattr(result, "model_dump") else result
    frames = data.get("frames", [])
    grid = data.get("grid")
    lines = [
        f"[bold green]Frames:[/bold green] {data.get('count', len(frames))}",
    ]
    if frames:
        lines.append(f"[bold green]Output dir:[/bold green] {frames[0].rsplit('/', 1)[0] if '/' in frames[0] else '.'}")
    if grid:
        lines.append(f"[bold green]Grid:[/bold green] {grid}")
    console.print(Panel("\n".join(lines), border_style="green", title="Storyboard"))


def _format_batch_text(result: dict) -> None:
    """Display batch result as a table."""
    table = Table(title="Batch Results")
    table.add_column("File", style="cyan")
    table.add_column("Status")
    table.add_column("Output")
    for r in result.get("results", []):
        status = "[green]OK[/green]" if r.get("success") else f"[red]{r.get('error', 'Failed')}[/red]"
        table.add_row(r.get("input", "N/A"), status, r.get("output_path", "-"))
    console.print(table)
    summary = f"[bold]{result['succeeded']}/{result['total']} succeeded[/bold]"
    if result.get("failed"):
        summary += f", [red]{result['failed']} failed[/red]"
    console.print(summary)


def _format_extract_audio_text(result: Any) -> None:
    """Display extract-audio result."""
    console.print(Panel(f"[bold green]Audio extracted:[/bold green] {result}", border_style="green", title="Done"))


def _format_error(e: Exception) -> None:
    """Display error in a styled panel."""
    from .errors import MCPVideoError
    if isinstance(e, MCPVideoError):
        data = e.to_dict()
        msg = data.get("message", str(e))
        code = data.get("code", "")
        action = data.get("suggested_action", {})
        lines = [f"[bold red]{msg}[/bold red]"]
        if code:
            lines.append(f"[dim]Code: {code}[/dim]")
        if isinstance(action, dict) and action.get("description"):
            lines.append(f"\n[yellow]Suggested fix:[/yellow] {action['description']}")
        err_console.print(Panel("\n".join(lines), border_style="red", title="Error"))
    else:
        err_console.print(Panel(f"[bold red]{e}[/bold red]", border_style="red", title="Error"))


def _with_spinner(label: str, fn, *args, **kwargs):
    """Run an engine function with a rich spinner."""
    with Progress(
        SpinnerColumn(),
        TextColumn(f"[progress.description]{label}"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task(description=label, total=None)
        return fn(*args, **kwargs)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="mcp-video",
        description="mcp-video — Video editing for AI agents (and humans)",
    )
    parser.add_argument(
        "--mcp",
        action="store_true",
        help="Run as MCP server (default mode)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version and exit",
    )
    subparsers = parser.add_subparsers(dest="command", help="CLI commands")

    # info
    info_p = subparsers.add_parser("info", help="Get video metadata")
    info_p.add_argument("input", help="Input video file")

    # trim
    trim_p = subparsers.add_parser("trim", help="Trim a video")
    trim_p.add_argument("input", help="Input video file")
    trim_p.add_argument("-s", "--start", default="0", help="Start time")
    trim_p.add_argument("-d", "--duration", help="Duration")
    trim_p.add_argument("-e", "--end", help="End time")
    trim_p.add_argument("-o", "--output", help="Output file path")

    # merge
    merge_p = subparsers.add_parser("merge", help="Merge multiple clips")
    merge_p.add_argument("inputs", nargs="+", help="Input video files")
    merge_p.add_argument("-t", "--transition", default=None, choices=["fade", "dissolve", "wipe-left", "wipe-right", "wipe-up", "wipe-down"])
    merge_p.add_argument("--transitions", nargs="+", choices=["fade", "dissolve", "wipe-left", "wipe-right", "wipe-up", "wipe-down"], help="Per-pair transition types (overrides --transition)")
    merge_p.add_argument("-td", "--transition-duration", type=float, default=1.0, help="Transition duration in seconds")
    merge_p.add_argument("-o", "--output", help="Output file path")

    # add_text
    text_p = subparsers.add_parser("add-text", help="Overlay text on a video")
    text_p.add_argument("input", help="Input video file")
    text_p.add_argument("text", help="Text to overlay")
    text_p.add_argument("-p", "--position", default="top-center", choices=["top-left", "top-center", "top-right", "center-left", "center", "center-right", "bottom-left", "bottom-center", "bottom-right"])
    text_p.add_argument("--font", help="Path to font file")
    text_p.add_argument("--size", type=int, default=48, help="Font size in pixels")
    text_p.add_argument("--color", default="white", help="Text color")
    text_p.add_argument("--no-shadow", action="store_true", help="Disable text shadow")
    text_p.add_argument("--start-time", type=float, help="When text appears (seconds)")
    text_p.add_argument("--duration", type=float, help="How long text is visible (seconds)")
    text_p.add_argument("-o", "--output", help="Output file path")

    # add_audio
    audio_p = subparsers.add_parser("add-audio", help="Add or replace audio track")
    audio_p.add_argument("video", help="Input video file")
    audio_p.add_argument("audio", help="Audio file (MP3, WAV, etc.)")
    audio_p.add_argument("-v", "--volume", type=float, default=1.0, help="Audio volume (0.0-2.0)")
    audio_p.add_argument("--fade-in", type=float, default=0.0, help="Fade in duration")
    audio_p.add_argument("--fade-out", type=float, default=0.0, help="Fade out duration")
    audio_p.add_argument("--mix", action="store_true", help="Mix with existing audio instead of replacing")
    audio_p.add_argument("--start-time", type=float, help="When audio starts (seconds)")
    audio_p.add_argument("-o", "--output", help="Output file path")

    # resize
    resize_p = subparsers.add_parser("resize", help="Resize a video")
    resize_p.add_argument("input", help="Input video file")
    resize_p.add_argument("-w", "--width", type=int, help="Target width")
    resize_p.add_argument("--height", type=int, help="Target height")
    resize_p.add_argument("-a", "--aspect-ratio", choices=["16:9", "9:16", "1:1", "4:3", "4:5", "21:9"], help="Preset aspect ratio")
    resize_p.add_argument("-q", "--quality", default="high", choices=["low", "medium", "high", "ultra"])
    resize_p.add_argument("-o", "--output", help="Output file path")

    # speed
    speed_p = subparsers.add_parser("speed", help="Change playback speed")
    speed_p.add_argument("input", help="Input video file")
    speed_p.add_argument("-f", "--factor", type=float, default=1.0, help="Speed multiplier (0.5=slow, 2.0=fast)")
    speed_p.add_argument("-o", "--output", help="Output file path")

    # convert
    convert_p = subparsers.add_parser("convert", help="Convert video format")
    convert_p.add_argument("input", help="Input video file")
    convert_p.add_argument("-f", "--format", "--fmt", dest="fmt", default="mp4", choices=["mp4", "webm", "gif", "mov"], help="Output format")
    convert_p.add_argument("-q", "--quality", default="high", choices=["low", "medium", "high", "ultra"])
    convert_p.add_argument("-o", "--output", help="Output file path")

    # thumbnail
    thumb_p = subparsers.add_parser("thumbnail", help="Extract a single frame")
    thumb_p.add_argument("input", help="Input video file")
    thumb_p.add_argument("-t", "--timestamp", type=float, help="Time in seconds (default: 10%% of duration)")
    thumb_p.add_argument("-o", "--output", help="Output image path")

    # preview
    preview_p = subparsers.add_parser("preview", help="Generate a fast low-res preview")
    preview_p.add_argument("input", help="Input video file")
    preview_p.add_argument("-o", "--output", help="Output file path")
    preview_p.add_argument("-s", "--scale", type=int, default=4, help="Downscale factor (default: 4)")

    # storyboard
    storyboard_p = subparsers.add_parser("storyboard", help="Extract key frames as storyboard")
    storyboard_p.add_argument("input", help="Input video file")
    storyboard_p.add_argument("-o", "--output-dir", help="Output directory")
    storyboard_p.add_argument("-n", "--frames", type=int, default=8, help="Number of frames (default: 8)")

    # subtitles
    subs_p = subparsers.add_parser("subtitles", help="Burn subtitles into video")
    subs_p.add_argument("input", help="Input video file")
    subs_p.add_argument("subtitle", help="Subtitle file (.srt or .vtt)")
    subs_p.add_argument("-o", "--output", help="Output file path")

    # watermark
    wm_p = subparsers.add_parser("watermark", help="Add image watermark")
    wm_p.add_argument("input", help="Input video file")
    wm_p.add_argument("image", help="Watermark image (PNG recommended)")
    wm_p.add_argument("-p", "--position", default="bottom-right", choices=["top-left", "top-center", "top-right", "center-left", "center", "bottom-left", "bottom-center", "bottom-right"])
    wm_p.add_argument("--opacity", type=float, default=0.7, help="Watermark opacity (0.0-1.0)")
    wm_p.add_argument("--margin", type=int, default=20, help="Margin from edge in pixels")
    wm_p.add_argument("-o", "--output", help="Output file path")

    # crop
    crop_p = subparsers.add_parser("crop", help="Crop a video to a region")
    crop_p.add_argument("input", help="Input video file")
    crop_p.add_argument("-w", "--width", type=int, required=True, help="Crop width in pixels")
    crop_p.add_argument("--height", type=int, required=True, help="Crop height in pixels")
    crop_p.add_argument("-x", type=int, default=None, help="X offset (default: center)")
    crop_p.add_argument("-y", type=int, default=None, help="Y offset (default: center)")
    crop_p.add_argument("-o", "--output", help="Output file path")

    # rotate
    rotate_p = subparsers.add_parser("rotate", help="Rotate and/or flip a video")
    rotate_p.add_argument("input", help="Input video file")
    rotate_p.add_argument("-a", "--angle", type=int, default=0, choices=[0, 90, 180, 270], help="Rotation angle in degrees")
    rotate_p.add_argument("--flip-h", action="store_true", help="Flip horizontally")
    rotate_p.add_argument("--flip-v", action="store_true", help="Flip vertically")
    rotate_p.add_argument("-o", "--output", help="Output file path")

    # fade
    fade_p = subparsers.add_parser("fade", help="Add fade in/out to video")
    fade_p.add_argument("input", help="Input video file")
    fade_p.add_argument("--fade-in", type=float, default=0.0, help="Fade in duration (seconds)")
    fade_p.add_argument("--fade-out", type=float, default=0.0, help="Fade out duration (seconds)")
    fade_p.add_argument("-o", "--output", help="Output file path")

    # export
    export_p = subparsers.add_parser("export", help="Export video with quality settings")
    export_p.add_argument("input", help="Input video file")
    export_p.add_argument("-q", "--quality", default="high", choices=["low", "medium", "high", "ultra"])
    export_p.add_argument("-f", "--format", "--fmt", dest="fmt", default="mp4", choices=["mp4", "webm", "gif", "mov"], help="Output format")
    export_p.add_argument("-o", "--output", help="Output file path")

    # extract_audio
    extract_p = subparsers.add_parser("extract-audio", help="Extract audio from video")
    extract_p.add_argument("input", help="Input video file")
    extract_p.add_argument("-f", "--format", "--fmt", dest="audio_format", default="mp3", choices=["mp3", "aac", "wav", "ogg", "flac"])
    extract_p.add_argument("-o", "--output", help="Output audio file path")

    # edit (timeline)
    edit_p = subparsers.add_parser("edit", help="Execute timeline-based edit from JSON")
    edit_p.add_argument("timeline", help="Path to timeline JSON file")
    edit_p.add_argument("-o", "--output", help="Output file path")

    # filter
    filter_p = subparsers.add_parser("filter", help="Apply a visual filter")
    filter_p.add_argument("input", help="Input video file")
    filter_p.add_argument("-t", "--type", dest="filter_type", required=True, choices=["blur", "sharpen", "brightness", "contrast", "saturation", "grayscale", "sepia", "invert", "vignette", "color_preset", "denoise", "deinterlace"], help="Filter type")
    filter_p.add_argument("--params", help="Filter parameters as JSON")
    filter_p.add_argument("-o", "--output", help="Output file path")

    # blur (convenience)
    blur_p = subparsers.add_parser("blur", help="Apply blur effect")
    blur_p.add_argument("input", help="Input video file")
    blur_p.add_argument("-r", "--radius", type=int, default=5, help="Blur radius (default: 5)")
    blur_p.add_argument("-s", "--strength", type=int, default=1, help="Blur strength (default: 1)")
    blur_p.add_argument("-o", "--output", help="Output file path")

    # reverse
    reverse_p = subparsers.add_parser("reverse", help="Reverse video playback")
    reverse_p.add_argument("input", help="Input video file")
    reverse_p.add_argument("-o", "--output", help="Output file path")

    # chroma-key
    chroma_p = subparsers.add_parser("chroma-key", help="Remove solid color background (green screen)")
    chroma_p.add_argument("input", help="Input video file")
    chroma_p.add_argument("--color", default="0x00FF00", help="Color to remove in hex (default: 0x00FF00 for green)")
    chroma_p.add_argument("--similarity", type=float, default=0.01, help="Color similarity threshold (default: 0.01)")
    chroma_p.add_argument("--blend", type=float, default=0.0, help="Blend amount (default: 0.0)")
    chroma_p.add_argument("-o", "--output", help="Output file path")

    # color-grade (convenience)
    grade_p = subparsers.add_parser("color-grade", help="Apply color grading preset")
    grade_p.add_argument("input", help="Input video file")
    grade_p.add_argument("-p", "--preset", default="warm", choices=["warm", "cool", "vintage", "cinematic", "noir"], help="Color preset")
    grade_p.add_argument("-o", "--output", help="Output file path")

    # normalize-audio
    norm_p = subparsers.add_parser("normalize-audio", help="Normalize audio loudness")
    norm_p.add_argument("input", help="Input video file")
    norm_p.add_argument("-l", "--lufs", type=float, default=-16.0, help="Target LUFS (default: -16 for YouTube)")
    norm_p.add_argument("-o", "--output", help="Output file path")

    # overlay-video
    overlay_p = subparsers.add_parser("overlay-video", help="Picture-in-picture overlay")
    overlay_p.add_argument("background", help="Background video file")
    overlay_p.add_argument("overlay", help="Overlay video file")
    overlay_p.add_argument("-p", "--position", default="top-right", choices=["top-left", "top-center", "top-right", "center-left", "center", "center-right", "bottom-left", "bottom-center", "bottom-right"])
    overlay_p.add_argument("-w", "--width", type=int, help="Overlay width")
    overlay_p.add_argument("--height", type=int, help="Overlay height")
    overlay_p.add_argument("--opacity", type=float, default=0.8, help="Overlay opacity (0.0-1.0)")
    overlay_p.add_argument("--start-time", type=float, help="When overlay appears (seconds)")
    overlay_p.add_argument("--duration", type=float, help="How long overlay is visible (seconds)")
    overlay_p.add_argument("-o", "--output", help="Output file path")

    # split-screen
    split_p = subparsers.add_parser("split-screen", help="Place two videos side by side or top/bottom")
    split_p.add_argument("left", help="First video file")
    split_p.add_argument("right", help="Second video file")
    split_p.add_argument("-l", "--layout", default="side-by-side", choices=["side-by-side", "top-bottom"], help="Layout type")
    split_p.add_argument("-o", "--output", help="Output file path")

    # batch
    batch_p = subparsers.add_parser("batch", help="Apply operation to multiple files")
    batch_p.add_argument("inputs", nargs="+", help="Input video files")
    batch_p.add_argument("-o", "--output-dir", help="Output directory for processed files")
    batch_p.add_argument("--operation", required=True, choices=["trim", "resize", "convert", "filter", "blur", "color_grade", "watermark", "speed", "fade", "normalize_audio"], help="Operation to apply")
    batch_p.add_argument("--params", help="Operation parameters as JSON")

    # detect-scenes
    scenes_p = subparsers.add_parser("detect-scenes", help="Detect scene changes in a video")
    scenes_p.add_argument("input", help="Input video file")
    scenes_p.add_argument("-t", "--threshold", type=float, default=0.3, help="Detection sensitivity (0.0-1.0, default: 0.3)")
    scenes_p.add_argument("--min-duration", type=float, default=1.0, help="Minimum scene duration in seconds (default: 1.0)")

    # create-from-images
    imgseq_p = subparsers.add_parser("create-from-images", help="Create video from image sequence")
    imgseq_p.add_argument("inputs", nargs="+", help="Input image files")
    imgseq_p.add_argument("-f", "--fps", type=float, default=30.0, help="Frames per second (default: 30)")
    imgseq_p.add_argument("-o", "--output", help="Output video file path")

    # export-frames
    frames_p = subparsers.add_parser("export-frames", help="Export video frames as images")
    frames_p.add_argument("input", help="Input video file")
    frames_p.add_argument("-o", "--output-dir", help="Output directory for frames")
    frames_p.add_argument("-f", "--fps", type=float, default=1.0, help="Frames per second to extract (default: 1)")
    frames_p.add_argument("--format", default="jpg", choices=["jpg", "png"], help="Image format (default: jpg)")

    # compare-quality
    quality_p = subparsers.add_parser("compare-quality", help="Compare video quality between two files")
    quality_p.add_argument("original", help="Original/reference video file")
    quality_p.add_argument("distorted", help="Processed/distorted video file")
    quality_p.add_argument("--metrics", nargs="+", choices=["psnr", "ssim"], help="Metrics to compute (default: psnr ssim)")

    # read-metadata
    read_meta_p = subparsers.add_parser("read-metadata", help="Read metadata tags from a file")
    read_meta_p.add_argument("input", help="Input video/audio file")

    # write-metadata
    write_meta_p = subparsers.add_parser("write-metadata", help="Write metadata tags to a file")
    write_meta_p.add_argument("input", help="Input video/audio file")
    write_meta_p.add_argument("--tags", required=True, help="Metadata as JSON, e.g. '{\"title\": \"My Video\"}'")
    write_meta_p.add_argument("-o", "--output", help="Output file path")

    # stabilize
    stab_p = subparsers.add_parser("stabilize", help="Stabilize a shaky video")
    stab_p.add_argument("input", help="Input video file")
    stab_p.add_argument("-s", "--smoothing", type=float, default=15, help="Smoothing strength (default: 15)")
    stab_p.add_argument("-z", "--zooming", type=float, default=0, help="Zoom to avoid black borders (default: 0)")
    stab_p.add_argument("-o", "--output", help="Output file path")

    # apply-mask
    mask_p = subparsers.add_parser("apply-mask", help="Apply an image mask to a video")
    mask_p.add_argument("input", help="Input video file")
    mask_p.add_argument("mask", help="Mask image file (white=visible, black=transparent)")
    mask_p.add_argument("--feather", type=int, default=5, help="Edge feather in pixels (default: 5)")
    mask_p.add_argument("-o", "--output", help="Output file path")

    # audio-waveform
    waveform_p = subparsers.add_parser("audio-waveform", help="Extract audio waveform data")
    waveform_p.add_argument("input", help="Input video/audio file")
    waveform_p.add_argument("-b", "--bins", type=int, default=50, help="Number of time segments (default: 50)")
    waveform_p.add_argument("-o", "--output", help="Output file path (optional, data is returned as JSON)")

    # generate-subtitles
    gen_subs_p = subparsers.add_parser("generate-subtitles", help="Generate SRT subtitles from text entries")
    gen_subs_p.add_argument("input", help="Input video file")
    gen_subs_p.add_argument("--entries", required=True, help="Subtitle entries as JSON: '[{\"start\":0,\"end\":2,\"text\":\"Hello\"}]'")
    gen_subs_p.add_argument("--burn", action="store_true", help="Burn subtitles into video")
    gen_subs_p.add_argument("-o", "--output", help="Output directory/path (default: auto-generated)")

    # templates (list available templates)
    subparsers.add_parser("templates", help="List available video templates")

    # template (apply a template)
    template_p = subparsers.add_parser("template", help="Apply a video template")
    template_p.add_argument("name", choices=["tiktok", "youtube-shorts", "instagram-reel", "youtube", "instagram-post"], help="Template name")
    template_p.add_argument("input", help="Input video file")
    template_p.add_argument("--caption", help="Caption text (for tiktok, instagram)")
    template_p.add_argument("--title", help="Title text (for youtube-shorts, youtube)")
    template_p.add_argument("--music", help="Background music file")
    template_p.add_argument("--outro", help="Outro video file (for youtube)")
    template_p.add_argument("-o", "--output", help="Output file path")

    # ------------------------------------------------------------------
    # Remotion commands
    # ------------------------------------------------------------------

    # remotion-render
    remotion_render_p = subparsers.add_parser("remotion-render", help="Render a Remotion composition to video")
    remotion_render_p.add_argument("project_path", help="Path to Remotion project")
    remotion_render_p.add_argument("composition_id", help="Composition ID to render")
    remotion_render_p.add_argument("-o", "--output", help="Output video file path")
    remotion_render_p.add_argument("--codec", default="h264", choices=["h264", "h265", "vp8", "vp9", "prores", "gif"], help="Video codec (default: h264)")
    remotion_render_p.add_argument("--crf", type=int, default=18, help="CRF quality (default: 18)")
    remotion_render_p.add_argument("--width", type=int, help="Output width in pixels")
    remotion_render_p.add_argument("--height", type=int, help="Output height in pixels")
    remotion_render_p.add_argument("--fps", type=float, default=30.0, help="Frames per second (default: 30)")
    remotion_render_p.add_argument("--concurrency", type=int, default=1, help="Number of concurrent render threads")
    remotion_render_p.add_argument("--frames", help="Frame range (e.g. '0-90' or '10-50')")
    remotion_render_p.add_argument("--props", help="Input props as JSON")
    remotion_render_p.add_argument("--scale", type=float, default=1.0, help="Render scale factor")

    # remotion-compositions
    remotion_comps_p = subparsers.add_parser("remotion-compositions", help="List compositions in a Remotion project")
    remotion_comps_p.add_argument("project_path", help="Path to Remotion project")
    remotion_comps_p.add_argument("--composition-id", help="Filter by specific composition ID")
    remotion_comps_p.add_argument("--json", action="store_true", help="Output raw JSON")
    remotion_comps_p.add_argument("-o", "--output", help="Output file path")

    # remotion-studio
    remotion_studio_p = subparsers.add_parser("remotion-studio", help="Launch Remotion Studio for live preview")
    remotion_studio_p.add_argument("project_path", help="Path to Remotion project")
    remotion_studio_p.add_argument("-p", "--port", type=int, default=3000, help="Studio port (default: 3000)")
    remotion_studio_p.add_argument("--json", action="store_true", help="Output raw JSON")

    # remotion-still
    remotion_still_p = subparsers.add_parser("remotion-still", help="Render a single frame as image")
    remotion_still_p.add_argument("project_path", help="Path to Remotion project")
    remotion_still_p.add_argument("composition_id", help="Composition ID to render")
    remotion_still_p.add_argument("-o", "--output", help="Output image file path")
    remotion_still_p.add_argument("--frame", type=int, default=0, help="Frame number to render (default: 0)")
    remotion_still_p.add_argument("--image-format", default="png", choices=["png", "jpeg", "webp"], help="Image format (default: png)")

    # remotion-create
    remotion_create_p = subparsers.add_parser("remotion-create", help="Scaffold a new Remotion project")
    remotion_create_p.add_argument("name", help="Project name")
    remotion_create_p.add_argument("-d", "--output-dir", help="Output directory (default: current directory)")
    remotion_create_p.add_argument("-t", "--template", default="blank", choices=["blank", "hello-world"], help="Project template (default: blank)")

    # remotion-scaffold
    remotion_scaffold_p = subparsers.add_parser("remotion-scaffold", help="Generate composition from spec")
    remotion_scaffold_p.add_argument("project_path", help="Path to Remotion project")
    remotion_scaffold_p.add_argument("--spec", required=True, help="Composition spec as JSON")
    remotion_scaffold_p.add_argument("--slug", required=True, help="Slug for the composition (used for filenames)")

    # remotion-validate
    remotion_validate_p = subparsers.add_parser("remotion-validate", help="Validate a Remotion project")
    remotion_validate_p.add_argument("project_path", help="Path to Remotion project")
    remotion_validate_p.add_argument("--composition-id", help="Specific composition ID to validate")

    # remotion-pipeline
    remotion_pipeline_p = subparsers.add_parser("remotion-pipeline", help="Render + post-process in one step")
    remotion_pipeline_p.add_argument("project_path", help="Path to Remotion project")
    remotion_pipeline_p.add_argument("composition_id", help="Composition ID to render")
    remotion_pipeline_p.add_argument("--post-process", required=True, help="Post-processing operations as JSON list")
    remotion_pipeline_p.add_argument("-o", "--output", help="Final output file path")

    # ------------------------------------------------------------------
    # Effect commands
    # ------------------------------------------------------------------

    # effect-vignette
    vig_p = subparsers.add_parser("effect-vignette", help="Apply vignette effect (darkened edges)")
    vig_p.add_argument("input", help="Input video file")
    vig_p.add_argument("-o", "--output", help="Output file path")
    vig_p.add_argument("-i", "--intensity", type=float, default=0.5, help="Darkness amount 0-1 (default: 0.5)")
    vig_p.add_argument("-r", "--radius", type=float, default=0.8, help="Vignette radius 0-1 (default: 0.8)")
    vig_p.add_argument("-s", "--smoothness", type=float, default=0.5, help="Edge softness 0-1 (default: 0.5)")

    # effect-glow
    glow_p = subparsers.add_parser("effect-glow", help="Apply bloom/glow effect to highlights")
    glow_p.add_argument("input", help="Input video file")
    glow_p.add_argument("-o", "--output", help="Output file path")
    glow_p.add_argument("-i", "--intensity", type=float, default=0.5, help="Glow strength 0-1 (default: 0.5)")
    glow_p.add_argument("-r", "--radius", type=int, default=10, help="Blur radius in pixels (default: 10)")
    glow_p.add_argument("-t", "--threshold", type=float, default=0.7, help="Brightness threshold 0-1 (default: 0.7)")

    # effect-noise
    noise_p = subparsers.add_parser("effect-noise", help="Apply film grain or digital noise")
    noise_p.add_argument("input", help="Input video file")
    noise_p.add_argument("-o", "--output", help="Output file path")
    noise_p.add_argument("-i", "--intensity", type=float, default=0.05, help="Noise amount 0-1 (default: 0.05)")
    noise_p.add_argument("-m", "--mode", default="film", choices=["film", "digital", "color"], help="Noise type (default: film)")
    noise_p.add_argument("--static", action="store_true", help="Use static noise instead of animated")

    # effect-scanlines
    scan_p = subparsers.add_parser("effect-scanlines", help="Apply CRT-style scanlines overlay")
    scan_p.add_argument("input", help="Input video file")
    scan_p.add_argument("-o", "--output", help="Output file path")
    scan_p.add_argument("--line-height", type=int, default=2, help="Pixels per scanline (default: 2)")
    scan_p.add_argument("--opacity", type=float, default=0.3, help="Line opacity 0-1 (default: 0.3)")
    scan_p.add_argument("--flicker", type=float, default=0.1, help="Brightness variation 0-1 (default: 0.1)")

    # effect-chromatic-aberration
    chroma_p = subparsers.add_parser("effect-chromatic-aberration", help="Apply RGB channel separation")
    chroma_p.add_argument("input", help="Input video file")
    chroma_p.add_argument("-o", "--output", help="Output file path")
    chroma_p.add_argument("-i", "--intensity", type=float, default=2.0, help="Pixel offset amount (default: 2.0)")
    chroma_p.add_argument("-a", "--angle", type=float, default=0, help="Separation direction in degrees (default: 0)")

    # ------------------------------------------------------------------
    # Transition commands
    # ------------------------------------------------------------------

    # transition-glitch
    tglitch_p = subparsers.add_parser("transition-glitch", help="Apply glitch transition between two clips")
    tglitch_p.add_argument("clip1", help="First video clip")
    tglitch_p.add_argument("clip2", help="Second video clip")
    tglitch_p.add_argument("-o", "--output", help="Output file path")
    tglitch_p.add_argument("-d", "--duration", type=float, default=0.5, help="Transition duration in seconds (default: 0.5)")
    tglitch_p.add_argument("-i", "--intensity", type=float, default=0.3, help="Glitch intensity 0-1 (default: 0.3)")

    # transition-morph
    tmorph_p = subparsers.add_parser("transition-morph", help="Apply morph transition between two clips")
    tmorph_p.add_argument("clip1", help="First video clip")
    tmorph_p.add_argument("clip2", help="Second video clip")
    tmorph_p.add_argument("-o", "--output", help="Output file path")
    tmorph_p.add_argument("-d", "--duration", type=float, default=0.6, help="Transition duration in seconds (default: 0.6)")
    tmorph_p.add_argument("--mesh-size", type=int, default=10, help="Mesh warp intensity (default: 10)")

    # transition-pixelate
    tpxl_p = subparsers.add_parser("transition-pixelate", help="Apply pixelate transition between two clips")
    tpxl_p.add_argument("clip1", help="First video clip")
    tpxl_p.add_argument("clip2", help="Second video clip")
    tpxl_p.add_argument("-o", "--output", help="Output file path")
    tpxl_p.add_argument("-d", "--duration", type=float, default=0.4, help="Transition duration in seconds (default: 0.4)")
    tpxl_p.add_argument("--pixel-size", type=int, default=50, help="Pixel size (default: 50)")

    # ------------------------------------------------------------------
    # AI commands
    # ------------------------------------------------------------------

    # video-ai-transcribe
    aitrans_p = subparsers.add_parser("video-ai-transcribe", help="Transcribe speech to text using Whisper")
    aitrans_p.add_argument("input", help="Input video file")
    aitrans_p.add_argument("-o", "--output", help="Output SRT file path")
    aitrans_p.add_argument("--model", default="base", choices=["tiny", "base", "small", "medium", "large"], help="Whisper model (default: base)")
    aitrans_p.add_argument("--language", help="Language code (auto-detect if omitted)")

    # video-ai-upscale
    aiup_p = subparsers.add_parser("video-ai-upscale", help="Upscale video using AI super-resolution")
    aiup_p.add_argument("input", help="Input video file")
    aiup_p.add_argument("-o", "--output", help="Output file path")
    aiup_p.add_argument("-s", "--scale", type=int, default=2, choices=[2, 4], help="Upscale factor (default: 2)")
    aiup_p.add_argument("--model", default="realesrgan", help="Model name (default: realesrgan)")

    # video-ai-stem-separation
    aistem_p = subparsers.add_parser("video-ai-stem-separation", help="Separate audio into stems using Demucs")
    aistem_p.add_argument("input", help="Input video file")
    aistem_p.add_argument("-o", "--output-dir", required=True, help="Output directory for stem files")
    aistem_p.add_argument("--stems", nargs="+", help="Stems to extract (default: vocals drums bass other)")
    aistem_p.add_argument("--model", default="htdemucs", help="Demucs model (default: htdemucs)")

    # video-ai-scene-detect
    aiscene_p = subparsers.add_parser("video-ai-scene-detect", help="Detect scene changes using perceptual hashing")
    aiscene_p.add_argument("input", help="Input video file")
    aiscene_p.add_argument("-t", "--threshold", type=float, default=0.3, help="Detection threshold (default: 0.3)")
    aiscene_p.add_argument("--use-ai", action="store_true", help="Use perceptual hashing for better accuracy")

    # video-ai-color-grade
    aigrade_p = subparsers.add_parser("video-ai-color-grade", help="Auto color grade video")
    aigrade_p.add_argument("input", help="Input video file")
    aigrade_p.add_argument("-o", "--output", help="Output file path")
    aigrade_p.add_argument("--reference", help="Reference video for color matching")
    aigrade_p.add_argument("--style", default="auto", choices=["auto", "cinematic", "vintage", "warm", "cool", "dramatic"], help="Color style (default: auto)")

    # video-ai-remove-silence
    airms_p = subparsers.add_parser("video-ai-remove-silence", help="Remove silent sections from video")
    airms_p.add_argument("input", help="Input video file")
    airms_p.add_argument("-o", "--output", help="Output file path")
    airms_p.add_argument("--silence-threshold", type=float, default=-50, help="Silence threshold in dB (default: -50)")
    airms_p.add_argument("--min-silence-duration", type=float, default=0.5, help="Min silence duration in seconds (default: 0.5)")
    airms_p.add_argument("--keep-margin", type=float, default=0.1, help="Keep margin around silence in seconds (default: 0.1)")

    # ------------------------------------------------------------------
    # Audio synthesis commands
    # ------------------------------------------------------------------

    # audio-synthesize
    asynth_p = subparsers.add_parser("audio-synthesize", help="Generate audio using waveform synthesis")
    asynth_p.add_argument("-o", "--output", required=True, help="Output WAV file path")
    asynth_p.add_argument("-w", "--waveform", default="sine", choices=["sine", "square", "sawtooth", "triangle", "noise"], help="Waveform type (default: sine)")
    asynth_p.add_argument("-f", "--frequency", type=float, default=440.0, help="Frequency in Hz (default: 440)")
    asynth_p.add_argument("-d", "--duration", type=float, default=1.0, help="Duration in seconds (default: 1.0)")
    asynth_p.add_argument("-v", "--volume", type=float, default=0.5, help="Volume 0-1 (default: 0.5)")
    asynth_p.add_argument("--effects", help="Effects as JSON, e.g. '{\"reverb\": {\"room_size\": 0.5}}'")

    # audio-compose
    acomp_p = subparsers.add_parser("audio-compose", help="Layer multiple audio tracks with mixing")
    acomp_p.add_argument("-o", "--output", required=True, help="Output WAV file path")
    acomp_p.add_argument("-d", "--duration", type=float, required=True, help="Total duration in seconds")
    acomp_p.add_argument("--tracks", required=True, help="Tracks as JSON: [{'file': 'a.wav', 'volume': 0.5, 'start': 0}]")

    # audio-preset
    apreset_p = subparsers.add_parser("audio-preset", help="Generate preset sound design elements")
    apreset_p.add_argument("preset", help="Preset name: ui-blip, ui-click, ui-tap, ui-whoosh-up, ui-whoosh-down, drone-low, drone-mid, drone-tech, drone-ominous, chime-success, chime-error, chime-notification, typing, scan, processing, data-flow, upload, download")
    apreset_p.add_argument("-o", "--output", required=True, help="Output WAV file path")
    apreset_p.add_argument("--pitch", default="mid", choices=["low", "mid", "high"], help="Pitch variation (default: mid)")
    apreset_p.add_argument("-d", "--duration", type=float, help="Override default duration (seconds)")
    apreset_p.add_argument("-i", "--intensity", type=float, default=0.5, help="Effect intensity 0-1 (default: 0.5)")

    # audio-sequence
    aseq_p = subparsers.add_parser("audio-sequence", help="Compose audio events into a timed sequence")
    aseq_p.add_argument("-o", "--output", required=True, help="Output WAV file path")
    aseq_p.add_argument("--sequence", required=True, help="Sequence as JSON: [{'type': 'tone', 'at': 0, 'duration': 1, 'freq': 440}]")

    # audio-effects
    aefx_p = subparsers.add_parser("audio-effects", help="Apply audio effects chain to a WAV file")
    aefx_p.add_argument("input", help="Input WAV file")
    aefx_p.add_argument("-o", "--output", required=True, help="Output WAV file path")
    aefx_p.add_argument("--effects", required=True, help="Effects as JSON: [{'type': 'lowpass', 'cutoff': 1000}]")

    # ------------------------------------------------------------------
    # Motion graphics commands
    # ------------------------------------------------------------------

    # video-text-animated
    tanim_p = subparsers.add_parser("video-text-animated", help="Add animated text to video")
    tanim_p.add_argument("input", help="Input video file")
    tanim_p.add_argument("text", help="Text to display")
    tanim_p.add_argument("-o", "--output", help="Output file path")
    tanim_p.add_argument("-a", "--animation", default="fade", choices=["fade", "slide-up", "typewriter", "glitch"], help="Animation type (default: fade)")
    tanim_p.add_argument("--font", default="Arial", help="Font family (default: Arial)")
    tanim_p.add_argument("--size", type=int, default=48, help="Font size in pixels (default: 48)")
    tanim_p.add_argument("--color", default="white", help="Text color (default: white)")
    tanim_p.add_argument("-p", "--position", default="center", choices=["center", "top", "bottom", "top-left", "top-right", "bottom-left", "bottom-right"], help="Text position (default: center)")
    tanim_p.add_argument("--start", type=float, default=0, help="Start time in seconds (default: 0)")
    tanim_p.add_argument("--duration", type=float, default=3.0, help="Display duration in seconds (default: 3.0)")

    # video-mograph-count
    mcount_p = subparsers.add_parser("video-mograph-count", help="Generate animated number counter video")
    mcount_p.add_argument("start", type=int, help="Starting number")
    mcount_p.add_argument("end", type=int, help="Ending number")
    mcount_p.add_argument("-d", "--duration", type=float, required=True, help="Animation duration in seconds")
    mcount_p.add_argument("-o", "--output", required=True, help="Output video file path")
    mcount_p.add_argument("--style", help="Style as JSON: {\"font\": \"Arial\", \"size\": 160, \"color\": \"white\"}")
    mcount_p.add_argument("--fps", type=int, default=30, help="Frame rate (default: 30)")

    # video-mograph-progress
    mprog_p = subparsers.add_parser("video-mograph-progress", help="Generate progress bar / loading animation")
    mprog_p.add_argument("-d", "--duration", type=float, required=True, help="Animation duration in seconds")
    mprog_p.add_argument("-o", "--output", required=True, help="Output video file path")
    mprog_p.add_argument("--style", default="bar", choices=["bar", "circle", "dots"], help="Progress style (default: bar)")
    mprog_p.add_argument("--color", default="#CCFF00", help="Progress color hex (default: #CCFF00)")
    mprog_p.add_argument("--track-color", default="#333333", help="Track background color hex (default: #333333)")
    mprog_p.add_argument("--fps", type=int, default=30, help="Frame rate (default: 30)")

    # ------------------------------------------------------------------
    # Layout commands
    # ------------------------------------------------------------------

    # video-layout-grid
    lgrid_p = subparsers.add_parser("video-layout-grid", help="Arrange multiple videos in a grid")
    lgrid_p.add_argument("inputs", nargs="+", help="Input video files")
    lgrid_p.add_argument("-l", "--layout", default="2x2", choices=["2x2", "3x1", "1x3", "2x3"], help="Grid layout (default: 2x2)")
    lgrid_p.add_argument("-o", "--output", required=True, help="Output file path")
    lgrid_p.add_argument("--gap", type=int, default=10, help="Gap between clips in pixels (default: 10)")
    lgrid_p.add_argument("--padding", type=int, default=20, help="Padding around grid in pixels (default: 20)")
    lgrid_p.add_argument("--background", default="#141414", help="Background color hex (default: #141414)")

    # video-layout-pip
    lpip_p = subparsers.add_parser("video-layout-pip", help="Picture-in-picture overlay with border")
    lpip_p.add_argument("main", help="Main video file")
    lpip_p.add_argument("pip", help="Picture-in-picture video file")
    lpip_p.add_argument("-o", "--output", required=True, help="Output file path")
    lpip_p.add_argument("-p", "--position", default="bottom-right", choices=["top-left", "top-right", "bottom-left", "bottom-right"], help="PIP position (default: bottom-right)")
    lpip_p.add_argument("-s", "--size", type=float, default=0.25, help="PIP size as fraction of main 0-1 (default: 0.25)")
    lpip_p.add_argument("--margin", type=int, default=20, help="Margin from edges in pixels (default: 20)")
    lpip_p.add_argument("--border", action="store_true", default=True, help="Add border around PIP (default: True)")
    lpip_p.add_argument("--no-border", dest="border", action="store_false", help="Disable border around PIP")
    lpip_p.add_argument("--border-color", default="#CCFF00", help="Border color hex (default: #CCFF00)")
    lpip_p.add_argument("--border-width", type=int, default=2, help="Border width in pixels (default: 2)")

    # ------------------------------------------------------------------
    # Audio-Video commands
    # ------------------------------------------------------------------

    # video-add-generated-audio
    addgen_p = subparsers.add_parser("video-add-generated-audio", help="Add procedurally generated audio to video")
    addgen_p.add_argument("input", help="Input video file")
    addgen_p.add_argument("--audio-config", required=True, help="Audio config as JSON: {\"drone\": {\"frequency\": 100}, \"events\": [...]}")
    addgen_p.add_argument("-o", "--output", help="Output file path")

    # video-audio-spatial
    aspat_p = subparsers.add_parser("video-audio-spatial", help="Apply 3D spatial audio positioning")
    aspat_p.add_argument("input", help="Input video file")
    aspat_p.add_argument("-o", "--output", help="Output file path")
    aspat_p.add_argument("--positions", required=True, help="Positions as JSON: [{\"time\": 0, \"azimuth\": 0, \"elevation\": 0}]")
    aspat_p.add_argument("--method", default="hrtf", choices=["hrtf", "vbap", "simple"], help="Spatialization method (default: hrtf)")

    # ------------------------------------------------------------------
    # Quality / Info commands
    # ------------------------------------------------------------------

    # video-auto-chapters
    achap_p = subparsers.add_parser("video-auto-chapters", help="Auto-detect scene changes and create chapters")
    achap_p.add_argument("input", help="Input video file")
    achap_p.add_argument("-t", "--threshold", type=float, default=0.3, help="Scene detection threshold (default: 0.3)")

    # video-extract-frame
    eframe_p = subparsers.add_parser("video-extract-frame", help="Extract a single frame (alias for thumbnail)")
    eframe_p.add_argument("input", help="Input video file")
    eframe_p.add_argument("-t", "--timestamp", type=float, help="Time in seconds (default: 10%% of duration)")
    eframe_p.add_argument("-o", "--output", help="Output image path")

    # video-info-detailed
    idetail_p = subparsers.add_parser("video-info-detailed", help="Get extended video metadata with scene detection")
    idetail_p.add_argument("input", help="Input video file")

    # video-quality-check
    qcheck_p = subparsers.add_parser("video-quality-check", help="Run visual quality checks on a video")
    qcheck_p.add_argument("input", help="Input video file")
    qcheck_p.add_argument("--fail-on-warning", action="store_true", help="Treat warnings as failures")

    # video-design-quality-check
    dqcheck_p = subparsers.add_parser("video-design-quality-check", help="Run design quality analysis on a video")
    dqcheck_p.add_argument("input", help="Input video file")
    dqcheck_p.add_argument("--auto-fix", action="store_true", help="Automatically fix issues where possible")
    dqcheck_p.add_argument("--strict", action="store_true", help="Treat warnings as errors")

    # video-fix-design-issues
    dfix_p = subparsers.add_parser("video-fix-design-issues", help="Auto-fix design issues in a video")
    dfix_p.add_argument("input", help="Input video file")
    dfix_p.add_argument("-o", "--output", help="Output file path (auto-generated if omitted)")

    # ------------------------------------------------------------------
    # Image analysis commands
    # ------------------------------------------------------------------

    # image-extract-colors
    imgcol_p = subparsers.add_parser("image-extract-colors", help="Extract dominant colors from an image")
    imgcol_p.add_argument("input", help="Input image file")
    imgcol_p.add_argument("-n", "--n-colors", type=int, default=5, help="Number of colors to extract (default: 5, max: 20)")

    # image-generate-palette
    imgpal_p = subparsers.add_parser("image-generate-palette", help="Generate color harmony palette from image")
    imgpal_p.add_argument("input", help="Input image file")
    imgpal_p.add_argument("--harmony", default="complementary", choices=["complementary", "analogous", "triadic", "split_complementary"], help="Harmony type (default: complementary)")
    imgpal_p.add_argument("-n", "--n-colors", type=int, default=5, help="Number of base colors (default: 5, max: 20)")

    # image-analyze-product
    imgprod_p = subparsers.add_parser("image-analyze-product", help="Analyze a product image (colors + optional AI description)")
    imgprod_p.add_argument("input", help="Input image file")
    imgprod_p.add_argument("--use-ai", action="store_true", help="Use Claude Vision for description (requires ANTHROPIC_API_KEY)")
    imgprod_p.add_argument("-n", "--n-colors", type=int, default=5, help="Number of colors to extract (default: 5, max: 20)")

    args = parser.parse_args()

    # --version
    if args.version:
        from . import __version__
        console.print(f"mcp-video [bold]{__version__}[/bold]")
        return

    # Default mode: run MCP server
    if args.mcp or args.command is None:
        try:
            from .server import mcp
            mcp.run()
        except ImportError:
            err_console.print(
                "[red]MCP mode requires the 'mcp' package.[/red]\n"
                "Install with: [bold]pip install 'mcp-video[mcp]'[/bold]",
            )
            sys.exit(1)
        return

    use_json = args.format == "json"

    # Helper to output result
    def output_json(data: Any) -> None:
        if hasattr(data, "model_dump"):
            data = data.model_dump()
        print(json.dumps(data, indent=2))

    # CLI commands
    try:
        if args.command == "info":
            from .engine import probe
            info = probe(args.input)
            if use_json:
                output_json(info)
            else:
                _format_info_text(info)

        elif args.command == "trim":
            from .engine import trim
            result = _with_spinner("Trimming...", trim, args.input, start=args.start, duration=args.duration, end=args.end, output_path=args.output)
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "merge":
            from .engine import merge
            result = _with_spinner("Merging...", merge, args.inputs, output_path=args.output, transition=args.transition, transitions=args.transitions, transition_duration=args.transition_duration)
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "add-text":
            from .engine import add_text
            result = _with_spinner("Adding text...", add_text,
                args.input, text=args.text, position=args.position,
                font=args.font, size=args.size, color=args.color,
                shadow=not args.no_shadow,
                start_time=args.start_time, duration=args.duration,
                output_path=args.output,
            )
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "add-audio":
            from .engine import add_audio
            result = _with_spinner("Adding audio...", add_audio,
                args.video, args.audio, volume=args.volume,
                fade_in=args.fade_in, fade_out=args.fade_out,
                mix=args.mix, start_time=args.start_time,
                output_path=args.output,
            )
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "resize":
            from .engine import resize
            result = _with_spinner("Resizing...", resize,
                args.input, width=args.width, height=args.height,
                aspect_ratio=args.aspect_ratio, quality=args.quality,
                output_path=args.output,
            )
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "speed":
            from .engine import speed
            result = _with_spinner("Changing speed...", speed, args.input, factor=args.factor, output_path=args.output)
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "convert":
            from .engine import convert
            result = _with_spinner("Converting...", convert, args.input, format=args.fmt, quality=args.quality, output_path=args.output)
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "thumbnail":
            from .engine import thumbnail
            result = thumbnail(args.input, timestamp=args.timestamp, output_path=args.output)
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "preview":
            from .engine import preview
            result = _with_spinner("Generating preview...", preview, args.input, output_path=args.output, scale_factor=args.scale)
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "storyboard":
            from .engine import storyboard
            result = _with_spinner("Extracting storyboard...", storyboard, args.input, output_dir=args.output_dir, frame_count=args.frames)
            if use_json:
                output_json(result)
            else:
                _format_storyboard_text(result)

        elif args.command == "subtitles":
            from .engine import subtitles
            result = _with_spinner("Burning subtitles...", subtitles, args.input, subtitle_path=args.subtitle, output_path=args.output)
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "watermark":
            from .engine import watermark
            result = _with_spinner("Adding watermark...", watermark,
                args.input, image_path=args.image, position=args.position,
                opacity=args.opacity, margin=args.margin,
                output_path=args.output,
            )
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "crop":
            from .engine import crop
            result = _with_spinner("Cropping...", crop, args.input, width=args.width, height=args.height, x=args.x, y=args.y, output_path=args.output)
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "rotate":
            from .engine import rotate
            result = _with_spinner("Rotating...", rotate, args.input, angle=args.angle, flip_horizontal=args.flip_h, flip_vertical=args.flip_v, output_path=args.output)
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "fade":
            from .engine import fade
            result = _with_spinner("Applying fade...", fade, args.input, fade_in=args.fade_in, fade_out=args.fade_out, output_path=args.output)
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "export":
            from .engine import export_video
            result = _with_spinner("Exporting...", export_video, args.input, quality=args.quality, format=args.fmt, output_path=args.output)
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "extract-audio":
            from .engine import extract_audio
            result = _with_spinner("Extracting audio...", extract_audio, args.input, output_path=args.output, format=args.audio_format)
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                _format_extract_audio_text(result)

        elif args.command == "edit":
            from .models import Timeline
            with open(args.timeline) as f:
                tl = Timeline.model_validate(json.load(f))
            from .engine import edit_timeline
            result = _with_spinner("Editing timeline...", edit_timeline, tl, output_path=args.output)
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "filter":
            from .engine import apply_filter
            params = json.loads(args.params) if args.params else {}
            result = _with_spinner("Applying filter...", apply_filter, args.input, filter_type=args.filter_type, params=params, output_path=args.output)
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "blur":
            from .engine import apply_filter
            result = _with_spinner("Applying blur...", apply_filter, args.input, filter_type="blur", params={"radius": args.radius, "strength": args.strength}, output_path=args.output)
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "reverse":
            from .engine import reverse
            result = _with_spinner("Reversing...", reverse, args.input, output_path=args.output)
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "chroma-key":
            from .engine import chroma_key
            result = _with_spinner("Removing green screen...", chroma_key, args.input, color=args.color, similarity=args.similarity, blend=args.blend, output_path=args.output)
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "color-grade":
            from .engine import apply_filter
            result = _with_spinner("Applying color grade...", apply_filter, args.input, filter_type="color_preset", params={"preset": args.preset}, output_path=args.output)
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "normalize-audio":
            from .engine import normalize_audio
            result = _with_spinner("Normalizing audio...", normalize_audio, args.input, target_lufs=args.lufs, output_path=args.output)
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "overlay-video":
            from .engine import overlay_video
            result = _with_spinner("Compositing overlay...", overlay_video,
                args.background, overlay_path=args.overlay, position=args.position,
                width=args.width, height=args.height, opacity=args.opacity,
                start_time=args.start_time, duration=args.duration,
                output_path=args.output,
            )
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "split-screen":
            from .engine import split_screen
            result = _with_spinner("Creating split screen...", split_screen, args.left, right_path=args.right, layout=args.layout, output_path=args.output)
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "batch":
            from .engine import video_batch
            params = json.loads(args.params) if args.params else {}
            result = video_batch(args.inputs, operation=args.operation, params=params, output_dir=args.output_dir)
            if use_json:
                print(json.dumps(result, indent=2))
            else:
                _format_batch_text(result)

        elif args.command == "detect-scenes":
            from .engine import detect_scenes
            result = _with_spinner("Detecting scenes...", detect_scenes, args.input, threshold=args.threshold, min_scene_duration=args.min_duration)
            if use_json:
                output_json(result)
            else:
                data = result.model_dump()
                table = Table(title="Scene Detection")
                table.add_column("#", style="bold", justify="right")
                table.add_column("Start", style="cyan")
                table.add_column("End", style="cyan")
                table.add_column("Frames")
                for i, scene in enumerate(data.get("scenes", []), 1):
                    table.add_row(str(i), f"{scene['start']:.2f}s", f"{scene['end']:.2f}s", f"{scene['start_frame']}-{scene['end_frame']}")
                console.print(table)
                console.print(f"[bold]{data.get('scene_count', 0)} scenes detected[/bold] in {data.get('duration', 0):.2f}s")

        elif args.command == "create-from-images":
            from .engine import create_from_images
            result = _with_spinner("Creating video from images...", create_from_images, args.inputs, output_path=args.output, fps=args.fps)
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "export-frames":
            from .engine import export_frames
            result = _with_spinner("Exporting frames...", export_frames, args.input, output_dir=args.output_dir, fps=args.fps, format=args.format)
            if use_json:
                output_json(result)
            else:
                data = result.model_dump()
                lines = [
                    f"[bold green]Frames:[/bold green] {data.get('frame_count', 0)}",
                    f"[bold green]Format:[/bold green] {args.format}",
                    f"[bold green]FPS:[/bold green] {data.get('fps', 0)}",
                ]
                if data.get("frame_paths"):
                    lines.append(f"[bold green]Output dir:[/bold green] {data['frame_paths'][0].rsplit('/', 1)[0]}")
                console.print(Panel("\n".join(lines), border_style="green", title="Frames Exported"))

        elif args.command == "compare-quality":
            from .engine import compare_quality
            metrics = args.metrics if args.metrics else None
            result = _with_spinner("Comparing quality...", compare_quality, args.original, args.distorted, metrics=metrics)
            if use_json:
                output_json(result)
            else:
                data = result.model_dump()
                table = Table(title="Quality Metrics")
                table.add_column("Metric", style="bold cyan")
                table.add_column("Value")
                for k, v in data.get("metrics", {}).items():
                    table.add_row(k.upper(), f"{v:.4f}")
                quality = data.get("overall_quality", "unknown")
                quality_style = {"high": "green", "medium": "yellow", "low": "red"}.get(quality, "white")
                table.add_row("Overall", f"[{quality_style}]{quality}[/{quality_style}]")
                console.print(table)

        elif args.command == "read-metadata":
            from .engine import read_metadata
            result = read_metadata(args.input)
            if use_json:
                output_json(result)
            else:
                data = result.model_dump()
                table = Table(title="Metadata")
                table.add_column("Field", style="bold cyan")
                table.add_column("Value")
                for field in ["title", "artist", "album", "comment", "date"]:
                    val = data.get(field)
                    if val:
                        table.add_row(field.capitalize(), val)
                for k, v in data.get("tags", {}).items():
                    table.add_row(k, str(v))
                if not data.get("title") and not data.get("tags"):
                    console.print("[yellow]No metadata found.[/yellow]")
                else:
                    console.print(table)

        elif args.command == "write-metadata":
            from .engine import write_metadata
            tags = json.loads(args.tags)
            result = _with_spinner("Writing metadata...", write_metadata, args.input, metadata=tags, output_path=args.output)
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "stabilize":
            from .engine import stabilize
            result = _with_spinner("Stabilizing...", stabilize, args.input, smoothing=args.smoothing, zooming=args.zooming, output_path=args.output)
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "apply-mask":
            from .engine import apply_mask
            result = _with_spinner("Applying mask...", apply_mask, args.input, mask_path=args.mask, feather=args.feather, output_path=args.output)
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "audio-waveform":
            from .engine import audio_waveform
            result = _with_spinner("Extracting waveform...", audio_waveform, args.input, bins=args.bins)
            if use_json:
                output_json(result)
            else:
                data = result.model_dump()
                table = Table(title="Audio Waveform")
                table.add_column("Property", style="bold cyan")
                table.add_column("Value")
                table.add_row("Duration", f"{data.get('duration', 0):.2f}s")
                table.add_row("Mean Level", f"{data.get('mean_level', 0):.1f} dB")
                table.add_row("Max Level", f"{data.get('max_level', 0):.1f} dB")
                table.add_row("Min Level", f"{data.get('min_level', 0):.1f} dB")
                silence_count = len(data.get('silence_regions', []))
                table.add_row("Silence Regions", str(silence_count))
                console.print(table)

        elif args.command == "generate-subtitles":
            from .engine import generate_subtitles
            entries = json.loads(args.entries)
            result = _with_spinner("Generating subtitles...", generate_subtitles, entries, args.input, burn=args.burn, output_path=args.output)
            if use_json:
                output_json(result)
            else:
                data = result.model_dump()
                lines = [
                    f"[bold green]Entries:[/bold green] {data.get('entry_count', 0)}",
                    f"[bold green]SRT Path:[/bold green] {data.get('srt_path', 'N/A')}",
                ]
                if data.get('video_path'):
                    lines.append(f"[bold green]Video Path:[/bold green] {data['video_path']}")
                console.print(Panel("\n".join(lines), border_style="green", title="Subtitles Generated"))

        elif args.command == "templates":
            from .templates import TEMPLATES
            descriptions = {
                "tiktok": "TikTok (9:16, 1080x1920) — vertical video with optional caption and music",
                "youtube-shorts": "YouTube Shorts (9:16) — title at top, vertical video",
                "instagram-reel": "Instagram Reel (9:16) — caption at bottom, vertical video",
                "youtube": "YouTube (16:9, 1920x1080) — horizontal video with title card and outro",
                "instagram-post": "Instagram Post (1:1, 1080x1080) — square video with caption",
            }
            if use_json:
                output_json({"templates": {name: descriptions.get(name, "") for name in TEMPLATES}})
            else:
                table = Table(title="Available Templates")
                table.add_column("Name", style="bold cyan")
                table.add_column("Description")
                for name in TEMPLATES:
                    table.add_row(name, descriptions.get(name, ""))
                console.print(table)

        elif args.command == "template":
            from .templates import TEMPLATES
            from .engine import edit_timeline
            template_fn = TEMPLATES[args.name]
            kwargs: dict[str, Any] = {"video_path": args.input, "output_path": args.output}
            if args.caption:
                kwargs["caption"] = args.caption
            if args.title:
                kwargs["title"] = args.title
            if args.music:
                kwargs["music_path"] = args.music
            if args.outro:
                kwargs["outro_path"] = args.outro
            timeline = template_fn(**kwargs)
            result = _with_spinner(f"Applying {args.name} template...", edit_timeline, timeline, output_path=args.output)
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        # ------------------------------------------------------------------
        # Remotion commands
        # ------------------------------------------------------------------

        elif args.command == "remotion-render":
            from .remotion_engine import render_composition
            props = json.loads(args.props) if args.props else None
            result = _with_spinner(
                f"Rendering {args.composition_id}...",
                render_composition,
                args.project_path, args.composition_id,
                output_path=args.output, codec=args.codec, crf=args.crf,
                width=args.width, height=args.height, fps=args.fps,
                concurrency=args.concurrency, frames=args.frames,
                props=props, scale=args.scale,
            )
            if use_json:
                output_json(result)
            else:
                data = result.model_dump()
                lines = [
                    f"[bold green]Composition:[/bold green] {args.composition_id}",
                    f"[bold green]Output:[/bold green] {data.get('output_path', 'N/A')}",
                ]
                if data.get("resolution"):
                    lines.append(f"[bold green]Resolution:[/bold green] {data['resolution']}")
                if data.get("codec"):
                    lines.append(f"[bold green]Codec:[/bold green] {data['codec']}")
                if data.get("size_mb") is not None:
                    lines.append(f"[bold green]Size:[/bold green] {data['size_mb']:.2f} MB")
                if data.get("render_time") is not None:
                    lines.append(f"[bold green]Render time:[/bold green] {data['render_time']:.1f}s")
                console.print(Panel("\n".join(lines), border_style="green", title="Remotion Render"))

        elif args.command == "remotion-compositions":
            from .remotion_engine import list_compositions
            result = _with_spinner(
                "Listing compositions...",
                list_compositions,
                args.project_path,
                composition_id=args.composition_id,
            )
            if use_json or args.json:
                output_json(result)
            else:
                data = result.model_dump()
                table = Table(title=f"Compositions — {args.project_path}")
                table.add_column("ID", style="bold cyan")
                table.add_column("Width")
                table.add_column("Height")
                table.add_column("FPS")
                table.add_column("Frames")
                for comp in data.get("compositions", []):
                    table.add_row(
                        comp.get("id", ""),
                        str(comp.get("width", "")),
                        str(comp.get("height", "")),
                        str(comp.get("fps", "")),
                        str(comp.get("duration_in_frames", "")),
                    )
                console.print(table)

        elif args.command == "remotion-studio":
            from .remotion_engine import launch_studio
            result = _with_spinner(
                "Launching Remotion Studio...",
                launch_studio,
                args.project_path,
                port=args.port,
            )
            if use_json or args.json:
                output_json(result)
            else:
                data = result.model_dump()
                console.print(Panel(
                    f"[bold green]Studio running:[/bold green] {data.get('url', 'N/A')}\n"
                    f"[bold green]Port:[/bold green] {data.get('port', 'N/A')}\n"
                    f"[bold green]Project:[/bold green] {data.get('project_path', 'N/A')}",
                    border_style="green",
                    title="Remotion Studio",
                ))

        elif args.command == "remotion-still":
            from .remotion_engine import render_still
            result = _with_spinner(
                f"Rendering still frame {args.frame}...",
                render_still,
                args.project_path, args.composition_id,
                output_path=args.output, frame=args.frame,
                image_format=args.image_format,
            )
            if use_json:
                output_json(result)
            else:
                data = result.model_dump()
                lines = [
                    f"[bold green]Composition:[/bold green] {args.composition_id}",
                    f"[bold green]Frame:[/bold green] {data.get('frame', 0)}",
                    f"[bold green]Output:[/bold green] {data.get('output_path', 'N/A')}",
                ]
                if data.get("resolution"):
                    lines.append(f"[bold green]Resolution:[/bold green] {data['resolution']}")
                console.print(Panel("\n".join(lines), border_style="green", title="Remotion Still"))

        elif args.command == "remotion-create":
            from .remotion_engine import create_project
            result = _with_spinner(
                f"Creating project '{args.name}'...",
                create_project,
                args.name,
                output_dir=args.output_dir,
                template=args.template,
            )
            if use_json:
                output_json(result)
            else:
                data = result.model_dump()
                lines = [
                    f"[bold green]Project:[/bold green] {data.get('project_path', 'N/A')}",
                    f"[bold green]Template:[/bold green] {data.get('template', 'N/A')}",
                ]
                if data.get("files"):
                    lines.append(f"[bold green]Files created:[/bold green] {len(data['files'])}")
                console.print(Panel("\n".join(lines), border_style="green", title="Remotion Project Created"))

        elif args.command == "remotion-scaffold":
            from .remotion_engine import scaffold_composition
            spec = json.loads(args.spec)
            result = _with_spinner(
                f"Scaffolding '{args.slug}'...",
                scaffold_composition,
                args.project_path,
                spec=spec,
                slug=args.slug,
            )
            if use_json:
                output_json(result)
            else:
                data = result.model_dump()
                lines = [
                    f"[bold green]Project:[/bold green] {data.get('project_path', 'N/A')}",
                    f"[bold green]Slug:[/bold green] {data.get('slug', 'N/A')}",
                ]
                if data.get("files"):
                    lines.append(f"[bold green]Files created:[/bold green] {len(data['files'])}")
                console.print(Panel("\n".join(lines), border_style="green", title="Remotion Scaffold"))

        elif args.command == "remotion-validate":
            from .remotion_engine import validate_project
            result = _with_spinner(
                "Validating project...",
                validate_project,
                args.project_path,
                composition_id=args.composition_id,
            )
            if use_json:
                output_json(result)
            else:
                data = result.model_dump()
                status = "[green]Valid[/green]" if data.get("valid") else "[red]Invalid[/red]"
                lines = [
                    f"[bold green]Project:[/bold green] {data.get('project_path', 'N/A')}",
                    f"[bold green]Status:[/bold green] {status}",
                ]
                if data.get("issues"):
                    lines.append(f"[red]Issues ({len(data['issues'])}):[/red]")
                    for issue in data["issues"]:
                        lines.append(f"  - {issue}")
                if data.get("warnings"):
                    lines.append(f"[yellow]Warnings ({len(data['warnings'])}):[/yellow]")
                    for warning in data["warnings"]:
                        lines.append(f"  - {warning}")
                console.print(Panel("\n".join(lines), border_style="green" if data.get("valid") else "red", title="Remotion Validate"))

        elif args.command == "remotion-pipeline":
            from .remotion_engine import render_pipeline
            post_process = json.loads(args.post_process)
            result = _with_spinner(
                f"Running pipeline for {args.composition_id}...",
                render_pipeline,
                args.project_path, args.composition_id,
                post_process=post_process,
                output_path=args.output,
            )
            if use_json:
                output_json(result)
            else:
                data = result.model_dump()
                lines = [
                    f"[bold green]Composition:[/bold green] {args.composition_id}",
                    f"[bold green]Remotion output:[/bold green] {data.get('remotion_output', 'N/A')}",
                    f"[bold green]Final output:[/bold green] {data.get('final_output', 'N/A')}",
                ]
                if data.get("operations"):
                    lines.append(f"[bold green]Post-process ops:[/bold green] {', '.join(data['operations'])}")
                console.print(Panel("\n".join(lines), border_style="green", title="Remotion Pipeline"))

        # ------------------------------------------------------------------
        # Effect commands
        # ------------------------------------------------------------------

        elif args.command == "effect-vignette":
            from .effects_engine import effect_vignette
            result = _with_spinner("Applying vignette...", effect_vignette, args.input, args.output,
                                   intensity=args.intensity, radius=args.radius, smoothness=args.smoothness)
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(Panel(f"[bold green]Vignette applied:[/bold green] {result}", border_style="green", title="Done"))

        elif args.command == "effect-glow":
            from .effects_engine import effect_glow
            result = _with_spinner("Applying glow...", effect_glow, args.input, args.output,
                                   intensity=args.intensity, radius=args.radius, threshold=args.threshold)
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(Panel(f"[bold green]Glow applied:[/bold green] {result}", border_style="green", title="Done"))

        elif args.command == "effect-noise":
            from .effects_engine import effect_noise
            result = _with_spinner("Applying noise...", effect_noise, args.input, args.output,
                                   intensity=args.intensity, mode=args.mode, animated=not args.static)
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(Panel(f"[bold green]Noise applied:[/bold green] {result}", border_style="green", title="Done"))

        elif args.command == "effect-scanlines":
            from .effects_engine import effect_scanlines
            result = _with_spinner("Applying scanlines...", effect_scanlines, args.input, args.output,
                                   line_height=args.line_height, opacity=args.opacity, flicker=args.flicker)
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(Panel(f"[bold green]Scanlines applied:[/bold green] {result}", border_style="green", title="Done"))

        elif args.command == "effect-chromatic-aberration":
            from .effects_engine import effect_chromatic_aberration
            result = _with_spinner("Applying chromatic aberration...", effect_chromatic_aberration,
                                   args.input, args.output, intensity=args.intensity, angle=args.angle)
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(Panel(f"[bold green]Chromatic aberration applied:[/bold green] {result}", border_style="green", title="Done"))

        # ------------------------------------------------------------------
        # Transition commands
        # ------------------------------------------------------------------

        elif args.command == "transition-glitch":
            from .transitions_engine import transition_glitch
            result = _with_spinner("Applying glitch transition...", transition_glitch,
                                   args.clip1, args.clip2, args.output,
                                   duration=args.duration, intensity=args.intensity)
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(Panel(f"[bold green]Glitch transition:[/bold green] {result}", border_style="green", title="Done"))

        elif args.command == "transition-morph":
            from .transitions_engine import transition_morph
            result = _with_spinner("Applying morph transition...", transition_morph,
                                   args.clip1, args.clip2, args.output,
                                   duration=args.duration, mesh_size=args.mesh_size)
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(Panel(f"[bold green]Morph transition:[/bold green] {result}", border_style="green", title="Done"))

        elif args.command == "transition-pixelate":
            from .transitions_engine import transition_pixelate
            result = _with_spinner("Applying pixelate transition...", transition_pixelate,
                                   args.clip1, args.clip2, args.output,
                                   duration=args.duration, pixel_size=args.pixel_size)
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(Panel(f"[bold green]Pixelate transition:[/bold green] {result}", border_style="green", title="Done"))

        # ------------------------------------------------------------------
        # AI commands
        # ------------------------------------------------------------------

        elif args.command == "video-ai-transcribe":
            from .ai_engine import ai_transcribe
            result = _with_spinner("Transcribing...", ai_transcribe, args.input,
                                   output_srt=args.output, model=args.model, language=args.language)
            if use_json:
                output_json(result)
            else:
                data = result if isinstance(result, dict) else {"success": True}
                text = data.get("text", "")
                srt = data.get("srt_path", args.output or "N/A")
                lines = [f"[bold green]SRT:[/bold green] {srt}"]
                if text:
                    lines.append(f"[bold green]Preview:[/bold green] {text[:200]}...")
                console.print(Panel("\n".join(lines), border_style="green", title="Transcription"))

        elif args.command == "video-ai-upscale":
            from .ai_engine import ai_upscale
            result = _with_spinner("Upscaling...", ai_upscale, args.input, args.output,
                                   scale=args.scale, model=args.model)
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(Panel(f"[bold green]Upscaled ({args.scale}x):[/bold green] {result}", border_style="green", title="Done"))

        elif args.command == "video-ai-stem-separation":
            from .ai_engine import ai_stem_separation
            result = _with_spinner("Separating stems...", ai_stem_separation, args.input,
                                   args.output_dir, stems=args.stems, model=args.model)
            if use_json:
                output_json(result)
            else:
                data = result if isinstance(result, dict) else {}
                lines = []
                for stem, path in data.items():
                    lines.append(f"[bold green]{stem}:[/bold green] {path}")
                console.print(Panel("\n".join(lines), border_style="green", title="Stem Separation"))

        elif args.command == "video-ai-scene-detect":
            from .ai_engine import ai_scene_detect
            result = _with_spinner("Detecting scenes (AI)...", ai_scene_detect, args.input,
                                   threshold=args.threshold, use_ai=args.use_ai)
            if use_json:
                output_json(result if isinstance(result, dict) else {"scenes": result})
            else:
                scenes = result if isinstance(result, list) else result.get("scenes", [])
                table = Table(title="AI Scene Detection")
                table.add_column("#", style="bold", justify="right")
                table.add_column("Start", style="cyan")
                table.add_column("End", style="cyan")
                table.add_column("Confidence")
                for i, scene in enumerate(scenes, 1):
                    if isinstance(scene, dict):
                        table.add_row(str(i), f"{scene.get('start', 0):.2f}s", f"{scene.get('end', 0):.2f}s", f"{scene.get('confidence', 0):.2f}")
                    else:
                        table.add_row(str(i), str(scene))
                console.print(table)
                console.print(f"[bold]{len(scenes)} scenes detected[/bold]")

        elif args.command == "video-ai-color-grade":
            from .ai_engine import ai_color_grade
            result = _with_spinner("Color grading...", ai_color_grade, args.input, args.output,
                                   reference=args.reference, style=args.style)
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(Panel(f"[bold green]Color graded ({args.style}):[/bold green] {result}", border_style="green", title="Done"))

        elif args.command == "video-ai-remove-silence":
            from .ai_engine import ai_remove_silence
            result = _with_spinner("Removing silence...", ai_remove_silence, args.input, args.output,
                                   silence_threshold=args.silence_threshold,
                                   min_silence_duration=args.min_silence_duration,
                                   keep_margin=args.keep_margin)
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(Panel(f"[bold green]Silence removed:[/bold green] {result}", border_style="green", title="Done"))

        # ------------------------------------------------------------------
        # Audio synthesis commands
        # ------------------------------------------------------------------

        elif args.command == "audio-synthesize":
            from .audio_engine import audio_synthesize
            effects = json.loads(args.effects) if args.effects else None
            result = _with_spinner("Synthesizing audio...", audio_synthesize, args.output,
                                   waveform=args.waveform, frequency=args.frequency,
                                   duration=args.duration, volume=args.volume, effects=effects)
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(Panel(f"[bold green]Audio synthesized:[/bold green] {result}", border_style="green", title="Done"))

        elif args.command == "audio-compose":
            from .audio_engine import audio_compose
            tracks = json.loads(args.tracks)
            result = _with_spinner("Composing audio...", audio_compose, tracks, args.duration, args.output)
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(Panel(f"[bold green]Audio composed:[/bold green] {result}", border_style="green", title="Done"))

        elif args.command == "audio-preset":
            from .audio_engine import audio_preset
            result = _with_spinner(f"Generating preset '{args.preset}'...", audio_preset,
                                   args.preset, args.output, pitch=args.pitch,
                                   duration=args.duration, intensity=args.intensity)
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(Panel(f"[bold green]Preset '{args.preset}':[/bold green] {result}", border_style="green", title="Done"))

        elif args.command == "audio-sequence":
            from .audio_engine import audio_sequence
            sequence = json.loads(args.sequence)
            result = _with_spinner("Composing audio sequence...", audio_sequence, sequence, args.output)
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(Panel(f"[bold green]Audio sequence:[/bold green] {result}", border_style="green", title="Done"))

        elif args.command == "audio-effects":
            from .audio_engine import audio_effects
            effects = json.loads(args.effects)
            result = _with_spinner("Applying audio effects...", audio_effects, args.input, args.output, effects)
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(Panel(f"[bold green]Audio effects applied:[/bold green] {result}", border_style="green", title="Done"))

        # ------------------------------------------------------------------
        # Motion graphics commands
        # ------------------------------------------------------------------

        elif args.command == "video-text-animated":
            from .effects_engine import text_animated
            result = _with_spinner("Adding animated text...", text_animated,
                                   args.input, args.text, args.output,
                                   animation=args.animation, font=args.font, size=args.size,
                                   color=args.color, position=args.position,
                                   start=args.start, duration=args.duration)
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(Panel(f"[bold green]Animated text ({args.animation}):[/bold green] {result}", border_style="green", title="Done"))

        elif args.command == "video-mograph-count":
            from .effects_engine import mograph_count
            style = json.loads(args.style) if args.style else None
            result = _with_spinner("Generating counter...", mograph_count,
                                   args.start, args.end, args.duration, args.output,
                                   style=style, fps=args.fps)
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(Panel(f"[bold green]Counter ({args.start}-{args.end}):[/bold green] {result}", border_style="green", title="Done"))

        elif args.command == "video-mograph-progress":
            from .effects_engine import mograph_progress
            result = _with_spinner("Generating progress animation...", mograph_progress,
                                   args.duration, args.output, style=args.style,
                                   color=args.color, track_color=args.track_color, fps=args.fps)
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(Panel(f"[bold green]Progress bar ({args.style}):[/bold green] {result}", border_style="green", title="Done"))

        # ------------------------------------------------------------------
        # Layout commands
        # ------------------------------------------------------------------

        elif args.command == "video-layout-grid":
            from .effects_engine import layout_grid
            result = _with_spinner("Creating grid layout...", layout_grid,
                                   args.inputs, args.layout, args.output,
                                   gap=args.gap, padding=args.padding, background=args.background)
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(Panel(f"[bold green]Grid layout ({args.layout}):[/bold green] {result}", border_style="green", title="Done"))

        elif args.command == "video-layout-pip":
            from .effects_engine import layout_pip
            result = _with_spinner("Creating PIP layout...", layout_pip,
                                   args.main, args.pip, args.output,
                                   position=args.position, size=args.size,
                                   margin=args.margin, border=args.border,
                                   border_color=args.border_color, border_width=args.border_width)
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(Panel(f"[bold green]PIP ({args.position}):[/bold green] {result}", border_style="green", title="Done"))

        # ------------------------------------------------------------------
        # Audio-Video commands
        # ------------------------------------------------------------------

        elif args.command == "video-add-generated-audio":
            from .audio_engine import add_generated_audio
            audio_config = json.loads(args.audio_config)
            result = _with_spinner("Adding generated audio...", add_generated_audio,
                                   args.input, audio_config, args.output)
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(Panel(f"[bold green]Generated audio added:[/bold green] {result}", border_style="green", title="Done"))

        elif args.command == "video-audio-spatial":
            from .ai_engine import audio_spatial
            positions = json.loads(args.positions)
            result = _with_spinner("Applying spatial audio...", audio_spatial,
                                   args.input, args.output, positions=positions, method=args.method)
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(Panel(f"[bold green]Spatial audio ({args.method}):[/bold green] {result}", border_style="green", title="Done"))

        # ------------------------------------------------------------------
        # Quality / Info commands
        # ------------------------------------------------------------------

        elif args.command == "video-auto-chapters":
            from .effects_engine import auto_chapters
            result = _with_spinner("Detecting chapters...", auto_chapters, args.input, threshold=args.threshold)
            if use_json:
                output_json({"chapters": [{"timestamp": t, "description": d} for t, d in result]})
            else:
                table = Table(title="Auto Chapters")
                table.add_column("#", style="bold", justify="right")
                table.add_column("Timestamp", style="cyan")
                table.add_column("Description")
                for i, (ts, desc) in enumerate(result, 1):
                    table.add_row(str(i), f"{ts:.2f}s", desc)
                console.print(table)
                console.print(f"[bold]{len(result)} chapters detected[/bold]")

        elif args.command == "video-extract-frame":
            from .engine import thumbnail
            result = _with_spinner("Extracting frame...", thumbnail, args.input, timestamp=args.timestamp, output_path=args.output)
            if use_json:
                output_json(result)
            else:
                data = result.model_dump() if hasattr(result, "model_dump") else result
                console.print(Panel(f"[bold green]Frame extracted:[/bold green] {data.get('output_path', 'N/A')}", border_style="green", title="Done"))

        elif args.command == "video-info-detailed":
            from .effects_engine import video_info_detailed
            result = _with_spinner("Getting detailed info...", video_info_detailed, args.input)
            if use_json:
                output_json(result)
            else:
                table = Table(title="Detailed Video Info")
                table.add_column("Property", style="bold cyan", no_wrap=True)
                table.add_column("Value")
                table.add_row("Duration", f"{result.get('duration', 0):.2f}s")
                table.add_row("FPS", str(result.get("fps", "N/A")))
                table.add_row("Resolution", f"{result.get('resolution', 'N/A')}")
                table.add_row("Bitrate", f"{result.get('bitrate', 0) // 1000} kbps")
                table.add_row("Has Audio", str(result.get("has_audio", False)))
                table.add_row("Scene Changes", str(len(result.get("scene_changes", []))))
                for i, ts in enumerate(result.get("scene_changes", []), 1):
                    table.add_row(f"  Scene {i}", f"{ts:.2f}s")
                console.print(table)

        elif args.command == "video-quality-check":
            from .quality_guardrails import quality_check
            result = _with_spinner("Running quality check...", quality_check, args.input, fail_on_warning=args.fail_on_warning)
            if use_json:
                output_json(result)
            else:
                data = result if isinstance(result, dict) else {}
                table = Table(title="Quality Check")
                table.add_column("Check", style="bold cyan")
                table.add_column("Status")
                table.add_column("Value")
                for check, info in data.get("checks", {}).items():
                    status = "[green]PASS[/green]" if info.get("passed") else "[red]FAIL[/red]"
                    table.add_row(check, status, str(info.get("value", "")))
                overall = "[green]PASS[/green]" if data.get("passed") else "[red]FAIL[/red]"
                console.print(table)
                console.print(f"[bold]Overall: {overall}[/bold]")

        elif args.command == "video-design-quality-check":
            from .design_quality import design_quality_check
            result = _with_spinner("Running design quality check...", design_quality_check,
                                   args.input, auto_fix=args.auto_fix, strict=args.strict)
            if use_json:
                output_json(result.model_dump() if hasattr(result, "model_dump") else result)
            else:
                data = result.model_dump() if hasattr(result, "model_dump") else result
                score = data.get("overall_score", "N/A")
                issues = data.get("issues", [])
                warnings = data.get("warnings", [])
                lines = [f"[bold green]Score:[/bold green] {score}"]
                if issues:
                    lines.append(f"[red]Issues ({len(issues)}):[/red]")
                    for issue in issues[:5]:
                        lines.append(f"  - {issue}")
                if warnings:
                    lines.append(f"[yellow]Warnings ({len(warnings)}):[/yellow]")
                    for w in warnings[:5]:
                        lines.append(f"  - {w}")
                console.print(Panel("\n".join(lines), border_style="green", title="Design Quality"))

        elif args.command == "video-fix-design-issues":
            from .design_quality import fix_design_issues
            result = _with_spinner("Fixing design issues...", fix_design_issues, args.input, args.output)
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(Panel(f"[bold green]Design fixed:[/bold green] {result}", border_style="green", title="Done"))

        # ------------------------------------------------------------------
        # Image analysis commands
        # ------------------------------------------------------------------

        elif args.command == "image-extract-colors":
            from .image_engine import extract_colors
            result = _with_spinner("Extracting colors...", extract_colors, args.input, n_colors=args.n_colors)
            if use_json:
                output_json(result.model_dump() if hasattr(result, "model_dump") else result)
            else:
                data = result.model_dump() if hasattr(result, "model_dump") else result
                table = Table(title="Dominant Colors")
                table.add_column("Color", style="bold cyan")
                table.add_column("Hex")
                table.add_column("RGB")
                table.add_column("CSS Name")
                table.add_column("Coverage")
                for c in data.get("colors", []):
                    table.add_row(
                        c.get("css_name", ""),
                        c.get("hex", ""),
                        str(c.get("rgb", "")),
                        c.get("css_name", ""),
                        f"{c.get('coverage_pct', 0):.1f}%",
                    )
                console.print(table)

        elif args.command == "image-generate-palette":
            from .image_engine import generate_palette
            result = _with_spinner("Generating palette...", generate_palette, args.input,
                                   harmony=args.harmony, n_colors=args.n_colors)
            if use_json:
                output_json(result.model_dump() if hasattr(result, "model_dump") else result)
            else:
                data = result.model_dump() if hasattr(result, "model_dump") else result
                table = Table(title=f"Color Palette ({args.harmony})")
                table.add_column("Role", style="bold cyan")
                table.add_column("Hex")
                table.add_row("Base", data.get("base_color", "N/A"))
                for name, info in data.get("palette", {}).items():
                    table.add_row(name, info.get("hex", "N/A") if isinstance(info, dict) else str(info))
                console.print(table)

        elif args.command == "image-analyze-product":
            from .image_engine import analyze_product
            result = _with_spinner("Analyzing product...", analyze_product, args.input,
                                   use_ai=args.use_ai, n_colors=args.n_colors)
            if use_json:
                output_json(result.model_dump() if hasattr(result, "model_dump") else result)
            else:
                data = result.model_dump() if hasattr(result, "model_dump") else result
                lines = []
                colors = data.get("colors", [])
                if colors:
                    lines.append("[bold green]Colors:[/bold green]")
                    for c in colors[:5]:
                        lines.append(f"  {c.get('hex', '')} ({c.get('css_name', '')}) - {c.get('coverage_pct', 0):.1f}%")
                desc = data.get("description")
                if desc:
                    lines.append(f"\n[bold green]AI Description:[/bold green] {desc}")
                console.print(Panel("\n".join(lines), border_style="green", title="Product Analysis"))

    except Exception as e:
        if use_json:
            from .errors import MCPVideoError
            if isinstance(e, MCPVideoError):
                print(json.dumps({"success": False, "error": e.to_dict()}, indent=2), file=sys.stderr)
            else:
                print(json.dumps({"success": False, "error": {"type": "unknown", "message": str(e)}}, indent=2), file=sys.stderr)
        else:
            _format_error(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
