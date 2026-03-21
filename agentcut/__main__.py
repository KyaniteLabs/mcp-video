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

    # preview command
    preview_p = subparsers.add_parser("preview", help="Generate a fast low-res preview")
    preview_p.add_argument("input", help="Input video file")
    preview_p.add_argument("-o", "--output", help="Output file path")
    preview_p.add_argument("-s", "--scale", type=int, default=4, help="Downscale factor (default: 4)")

    # storyboard command
    storyboard_p = subparsers.add_parser("storyboard", help="Extract key frames as storyboard")
    storyboard_p.add_argument("input", help="Input video file")
    storyboard_p.add_argument("-o", "--output-dir", help="Output directory")
    storyboard_p.add_argument("-n", "--frames", type=int, default=8, help="Number of frames (default: 8)")

    # info command
    info_p = subparsers.add_parser("info", help="Get video metadata")
    info_p.add_argument("input", help="Input video file")

    # trim command
    trim_p = subparsers.add_parser("trim", help="Trim a video")
    trim_p.add_argument("input", help="Input video file")
    trim_p.add_argument("-s", "--start", default="0", help="Start time")
    trim_p.add_argument("-d", "--duration", help="Duration")
    trim_p.add_argument("-e", "--end", help="End time")
    trim_p.add_argument("-o", "--output", help="Output file path")

    # convert command
    convert_p = subparsers.add_parser("convert", help="Convert video format")
    convert_p.add_argument("input", help="Input video file")
    convert_p.add_argument("-f", "--format", default="mp4", choices=["mp4", "webm", "gif", "mov"])
    convert_p.add_argument("-q", "--quality", default="high", choices=["low", "medium", "high", "ultra"])
    convert_p.add_argument("-o", "--output", help="Output file path")

    args = parser.parse_args()

    # Default mode: run MCP server
    if args.mcp or args.command is None:
        from .server import mcp
        mcp.run()
        return

    # CLI commands
    try:
        if args.command == "preview":
            from .engine import preview
            result = preview(args.input, output_path=args.output, scale_factor=args.scale)
            print(json.dumps(result.model_dump(), indent=2))

        elif args.command == "storyboard":
            from .engine import storyboard
            result = storyboard(args.input, output_dir=args.output_dir, frame_count=args.frames)
            print(json.dumps(result.model_dump(), indent=2))

        elif args.command == "info":
            from .engine import probe
            info = probe(args.input)
            print(json.dumps(info.model_dump(), indent=2))

        elif args.command == "trim":
            from .engine import trim
            result = trim(args.input, start=args.start, duration=args.duration, end=args.end, output_path=args.output)
            print(json.dumps(result.model_dump(), indent=2))

        elif args.command == "convert":
            from .engine import convert
            result = convert(args.input, format=args.format, quality=args.quality, output_path=args.output)
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
