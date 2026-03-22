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
    extract_p.add_argument("-f", "--format", "--fmt", dest="format", default="mp3", choices=["mp3", "aac", "wav", "ogg", "flac"])
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
            result = _with_spinner("Extracting audio...", extract_audio, args.input, output_path=args.output, format=args.format)
            if use_json:
                print(result)
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
            result = reverse(args.input, output_path=args.output)
            print(json.dumps(result.model_dump(), indent=2))

        elif args.command == "chroma-key":
            from .engine import chroma_key
            result = chroma_key(args.input, color=args.color, similarity=args.similarity, blend=args.blend, output_path=args.output)
            print(json.dumps(result.model_dump(), indent=2))

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

        elif args.command == "templates":
            from .templates import TEMPLATES
            table = Table(title="Available Templates")
            table.add_column("Name", style="bold cyan")
            table.add_column("Description")
            descriptions = {
                "tiktok": "TikTok (9:16, 1080x1920) — vertical video with optional caption and music",
                "youtube-shorts": "YouTube Shorts (9:16) — title at top, vertical video",
                "instagram-reel": "Instagram Reel (9:16) — caption at bottom, vertical video",
                "youtube": "YouTube (16:9, 1920x1080) — horizontal video with title card and outro",
                "instagram-post": "Instagram Post (1:1, 1080x1080) — square video with caption",
            }
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
