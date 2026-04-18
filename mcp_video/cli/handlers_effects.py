"""CLI handlers for visual effect commands."""

from __future__ import annotations

from typing import Any

from rich.panel import Panel

from .common import _auto_output, _with_spinner, output_json
from .formatting import console


def _print_effect_result(label: str, result: str, *, use_json: bool) -> None:
    if use_json:
        output_json({"success": True, "output_path": result})
    else:
        console.print(Panel(f"[bold green]{label} applied:[/bold green] {result}", border_style="green", title="Done"))


def handle_effect_command(args: Any, *, use_json: bool) -> bool:
    """Handle visual effect commands extracted from the main dispatcher."""
    if args.command == "effect-vignette":
        from ..effects_engine import effect_vignette

        out = args.output or _auto_output(args.input, "vignette")
        result = _with_spinner(
            "Applying vignette...",
            effect_vignette,
            args.input,
            out,
            intensity=args.intensity,
            radius=args.radius,
            smoothness=args.smoothness,
        )
        _print_effect_result("Vignette", result, use_json=use_json)
        return True

    if args.command == "effect-glow":
        from ..effects_engine import effect_glow

        out = args.output or _auto_output(args.input, "glow")
        result = _with_spinner(
            "Applying glow...",
            effect_glow,
            args.input,
            out,
            intensity=args.intensity,
            radius=args.radius,
            threshold=args.threshold,
        )
        _print_effect_result("Glow", result, use_json=use_json)
        return True

    if args.command == "effect-noise":
        from ..effects_engine import effect_noise

        out = args.output or _auto_output(args.input, "noise")
        result = _with_spinner(
            "Applying noise...",
            effect_noise,
            args.input,
            out,
            intensity=args.intensity,
            mode=args.mode,
            animated=not args.static,
        )
        _print_effect_result("Noise", result, use_json=use_json)
        return True

    if args.command == "effect-scanlines":
        from ..effects_engine import effect_scanlines

        out = args.output or _auto_output(args.input, "scanlines")
        result = _with_spinner(
            "Applying scanlines...",
            effect_scanlines,
            args.input,
            out,
            line_height=args.line_height,
            opacity=args.opacity,
            flicker=args.flicker,
        )
        _print_effect_result("Scanlines", result, use_json=use_json)
        return True

    if args.command == "effect-chromatic-aberration":
        from ..effects_engine import effect_chromatic_aberration

        out = args.output or _auto_output(args.input, "chromatic")
        result = _with_spinner(
            "Applying chromatic aberration...",
            effect_chromatic_aberration,
            args.input,
            out,
            intensity=args.intensity,
            angle=args.angle,
        )
        _print_effect_result("Chromatic aberration", result, use_json=use_json)
        return True

    return False
