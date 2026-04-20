"""CLI handlers for image analysis commands."""

from __future__ import annotations

from typing import Any

from rich.panel import Panel
from rich.table import Table

from .common import _with_spinner, output_json
from .formatting import console


def handle_image_commands(args: Any, *, use_json: bool) -> bool:
    """Handle image analysis commands extracted from the main dispatcher."""
    if args.command == "image-extract-colors":
        from ..image_engine import extract_colors

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
        return True

    if args.command == "image-generate-palette":
        from ..image_engine import generate_palette

        result = _with_spinner(
            "Generating palette...", generate_palette, args.input, harmony=args.harmony, n_colors=args.n_colors
        )
        if use_json:
            output_json(result.model_dump() if hasattr(result, "model_dump") else result)
        else:
            data = result.model_dump() if hasattr(result, "model_dump") else result
            table = Table(title=f"Color Palette ({args.harmony})")
            table.add_column("Role", style="bold cyan")
            table.add_column("Hex")
            table.add_row("Base", data.get("base_color", "N/A"))
            palette = data.get("palette", {})
            if isinstance(palette, dict):
                for name, info in palette.items():
                    table.add_row(name, info.get("hex", "N/A") if isinstance(info, dict) else str(info))
            console.print(table)
        return True

    if args.command == "image-analyze-product":
        from ..image_engine import analyze_product

        result = _with_spinner(
            "Analyzing product...", analyze_product, args.input, use_ai=args.use_ai, n_colors=args.n_colors
        )
        if use_json:
            output_json(result.model_dump() if hasattr(result, "model_dump") else result)
        else:
            data = result.model_dump() if hasattr(result, "model_dump") else result
            lines = []
            colors = data.get("colors", [])
            if colors:
                lines.append("[bold green]Colors:[/bold green]")
                for c in colors[:5]:
                    lines.append(
                        f"  {c.get('hex', '')} ({c.get('css_name', '')}) - {c.get('coverage_pct', 0):.1f}%"
                    )
            desc = data.get("description")
            if desc:
                lines.append(f"\n[bold green]AI Description:[/bold green] {desc}")
            console.print(Panel("\n".join(lines), border_style="green", title="Product Analysis"))
        return True

    return False
