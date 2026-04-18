"""CLI handlers for motion graphics and layout commands."""

from __future__ import annotations

from typing import Any

from rich.panel import Panel

from .common import _parse_json_arg, _with_spinner, output_json
from .formatting import console


def _print_output(label: str, result: str, *, use_json: bool) -> None:
    if use_json:
        output_json({"success": True, "output_path": result})
    else:
        console.print(Panel(f"[bold green]{label}:[/bold green] {result}", border_style="green", title="Done"))


def handle_composition_command(args: Any, *, use_json: bool) -> bool:
    """Handle motion graphics and layout commands extracted from main."""
    if args.command == "video-text-animated":
        from ..effects_engine import text_animated

        result = _with_spinner(
            "Adding animated text...",
            text_animated,
            args.input,
            args.text,
            args.output,
            animation=args.animation,
            font=args.font,
            size=args.size,
            color=args.color,
            position=args.position,
            start=args.start,
            duration=args.duration,
        )
        _print_output(f"Animated text ({args.animation})", result, use_json=use_json)
        return True

    if args.command == "video-mograph-count":
        from ..effects_engine import mograph_count

        style = _parse_json_arg(args.style, "style", json_mode=use_json) if args.style else None
        result = _with_spinner(
            "Generating counter...",
            mograph_count,
            args.start,
            args.end,
            args.duration,
            args.output,
            style=style,
            fps=args.fps,
        )
        _print_output(f"Counter ({args.start}-{args.end})", result, use_json=use_json)
        return True

    if args.command == "video-mograph-progress":
        from ..effects_engine import mograph_progress

        result = _with_spinner(
            "Generating progress animation...",
            mograph_progress,
            args.duration,
            args.output,
            style=args.style,
            color=args.color,
            track_color=args.track_color,
            fps=args.fps,
        )
        _print_output(f"Progress bar ({args.style})", result, use_json=use_json)
        return True

    if args.command == "video-layout-grid":
        from ..effects_engine import layout_grid

        result = _with_spinner(
            "Creating grid layout...",
            layout_grid,
            args.inputs,
            args.layout,
            args.output,
            gap=args.gap,
            padding=args.padding,
            background=args.background,
        )
        _print_output(f"Grid layout ({args.layout})", result, use_json=use_json)
        return True

    if args.command == "video-layout-pip":
        from ..effects_engine import layout_pip

        result = _with_spinner(
            "Creating PIP layout...",
            layout_pip,
            args.main,
            args.pip,
            args.output,
            position=args.position,
            size=args.size,
            margin=args.margin,
            border=args.border,
            border_color=args.border_color,
            border_width=args.border_width,
            rounded_corners=args.rounded_corners,
        )
        _print_output(f"PIP ({args.position})", result, use_json=use_json)
        return True

    return False
