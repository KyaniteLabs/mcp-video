"""CLI handlers for transition commands."""

from __future__ import annotations

from typing import Any

from rich.panel import Panel

from .common import _with_spinner, output_json
from .formatting import console


def _print_transition_result(label: str, result: str, *, use_json: bool) -> None:
    if use_json:
        output_json({"success": True, "output_path": result})
    else:
        console.print(Panel(f"[bold green]{label}:[/bold green] {result}", border_style="green", title="Done"))


def handle_transition_command(args: Any, *, use_json: bool) -> bool:
    """Handle transition commands extracted from the main dispatcher."""
    if args.command == "transition-glitch":
        from ..transitions_engine import transition_glitch

        result = _with_spinner(
            "Applying glitch transition...",
            transition_glitch,
            args.clip1,
            args.clip2,
            args.output,
            duration=args.duration,
            intensity=args.intensity,
        )
        _print_transition_result("Glitch transition", result, use_json=use_json)
        return True

    if args.command == "transition-morph":
        from ..transitions_engine import transition_morph

        result = _with_spinner(
            "Applying morph transition...",
            transition_morph,
            args.clip1,
            args.clip2,
            args.output,
            duration=args.duration,
            mesh_size=args.mesh_size,
        )
        _print_transition_result("Morph transition", result, use_json=use_json)
        return True

    if args.command == "transition-pixelate":
        from ..transitions_engine import transition_pixelate

        result = _with_spinner(
            "Applying pixelate transition...",
            transition_pixelate,
            args.clip1,
            args.clip2,
            args.output,
            duration=args.duration,
            pixel_size=args.pixel_size,
        )
        _print_transition_result("Pixelate transition", result, use_json=use_json)
        return True

    return False
