"""AgentCut CLI entry point."""

from __future__ import annotations

import argparse
import json
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="agentcut",
        description="AgentCut — Video editing for AI agents",
    )
    parser.add_argument(
        "--mcp",
        action="store_true",
        help="Run as MCP server (default mode)",
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
    convert_p.add_argument("-f", "--format", default="mp4", choices=["mp4", "webm", "gif", "mov"])
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
    export_p.add_argument("-f", "--format", default="mp4", choices=["mp4", "webm", "gif", "mov"])
    export_p.add_argument("-o", "--output", help="Output file path")

    # extract_audio
    extract_p = subparsers.add_parser("extract-audio", help="Extract audio from video")
    extract_p.add_argument("input", help="Input video file")
    extract_p.add_argument("-f", "--format", default="mp3", choices=["mp3", "aac", "wav", "ogg", "flac"])
    extract_p.add_argument("-o", "--output", help="Output audio file path")

    # edit (timeline)
    edit_p = subparsers.add_parser("edit", help="Execute timeline-based edit from JSON")
    edit_p.add_argument("timeline", help="Path to timeline JSON file")
    edit_p.add_argument("-o", "--output", help="Output file path")

    args = parser.parse_args()

    # Default mode: run MCP server
    if args.mcp or args.command is None:
        from .server import mcp
        mcp.run()
        return

    # CLI commands
    try:
        if args.command == "info":
            from .engine import probe
            info = probe(args.input)
            print(json.dumps(info.model_dump(), indent=2))

        elif args.command == "trim":
            from .engine import trim
            result = trim(args.input, start=args.start, duration=args.duration, end=args.end, output_path=args.output)
            print(json.dumps(result.model_dump(), indent=2))

        elif args.command == "merge":
            from .engine import merge
            result = merge(args.inputs, output_path=args.output, transition=args.transition, transitions=args.transitions, transition_duration=args.transition_duration)
            print(json.dumps(result.model_dump(), indent=2))

        elif args.command == "add-text":
            from .engine import add_text
            result = add_text(
                args.input, text=args.text, position=args.position,
                font=args.font, size=args.size, color=args.color,
                shadow=not args.no_shadow,
                start_time=args.start_time, duration=args.duration,
                output_path=args.output,
            )
            print(json.dumps(result.model_dump(), indent=2))

        elif args.command == "add-audio":
            from .engine import add_audio
            result = add_audio(
                args.video, args.audio, volume=args.volume,
                fade_in=args.fade_in, fade_out=args.fade_out,
                mix=args.mix, start_time=args.start_time,
                output_path=args.output,
            )
            print(json.dumps(result.model_dump(), indent=2))

        elif args.command == "resize":
            from .engine import resize
            result = resize(
                args.input, width=args.width, height=args.height,
                aspect_ratio=args.aspect_ratio, quality=args.quality,
                output_path=args.output,
            )
            print(json.dumps(result.model_dump(), indent=2))

        elif args.command == "speed":
            from .engine import speed
            result = speed(args.input, factor=args.factor, output_path=args.output)
            print(json.dumps(result.model_dump(), indent=2))

        elif args.command == "convert":
            from .engine import convert
            result = convert(args.input, format=args.format, quality=args.quality, output_path=args.output)
            print(json.dumps(result.model_dump(), indent=2))

        elif args.command == "thumbnail":
            from .engine import thumbnail
            result = thumbnail(args.input, timestamp=args.timestamp, output_path=args.output)
            print(json.dumps(result.model_dump(), indent=2))

        elif args.command == "preview":
            from .engine import preview
            result = preview(args.input, output_path=args.output, scale_factor=args.scale)
            print(json.dumps(result.model_dump(), indent=2))

        elif args.command == "storyboard":
            from .engine import storyboard
            result = storyboard(args.input, output_dir=args.output_dir, frame_count=args.frames)
            print(json.dumps(result.model_dump(), indent=2))

        elif args.command == "subtitles":
            from .engine import subtitles
            result = subtitles(args.input, subtitle_path=args.subtitle, output_path=args.output)
            print(json.dumps(result.model_dump(), indent=2))

        elif args.command == "watermark":
            from .engine import watermark
            result = watermark(
                args.input, image_path=args.image, position=args.position,
                opacity=args.opacity, margin=args.margin,
                output_path=args.output,
            )
            print(json.dumps(result.model_dump(), indent=2))

        elif args.command == "crop":
            from .engine import crop
            result = crop(args.input, width=args.width, height=args.height, x=args.x, y=args.y, output_path=args.output)
            print(json.dumps(result.model_dump(), indent=2))

        elif args.command == "rotate":
            from .engine import rotate
            result = rotate(args.input, angle=args.angle, flip_horizontal=args.flip_h, flip_vertical=args.flip_v, output_path=args.output)
            print(json.dumps(result.model_dump(), indent=2))

        elif args.command == "fade":
            from .engine import fade
            result = fade(args.input, fade_in=args.fade_in, fade_out=args.fade_out, output_path=args.output)
            print(json.dumps(result.model_dump(), indent=2))

        elif args.command == "export":
            from .engine import export_video
            result = export_video(args.input, quality=args.quality, format=args.format, output_path=args.output)
            print(json.dumps(result.model_dump(), indent=2))

        elif args.command == "extract-audio":
            from .engine import extract_audio
            result = extract_audio(args.input, output_path=args.output, format=args.format)
            print(result)

        elif args.command == "edit":
            from .models import Timeline
            with open(args.timeline) as f:
                tl = Timeline.model_validate(json.load(f))
            from .engine import edit_timeline
            result = edit_timeline(tl, output_path=args.output)
            print(json.dumps(result.model_dump(), indent=2))

    except Exception as e:
        from .errors import AgentCutError
        if isinstance(e, AgentCutError):
            print(json.dumps({"success": False, "error": e.to_dict()}, indent=2), file=sys.stderr)
        else:
            print(json.dumps({"success": False, "error": {"type": "unknown", "message": str(e)}}, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
