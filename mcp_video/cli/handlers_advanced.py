"""CLI handlers for quality, info, and advanced analysis commands."""

from __future__ import annotations

from typing import Any

from rich.panel import Panel
from rich.table import Table

from .common import _with_spinner, output_json
from .formatting import _format_thumbnail_text, console


def handle_advanced_commands(args: Any, *, use_json: bool) -> bool:
    """Handle quality, info, and advanced analysis commands extracted from the main dispatcher."""
    if args.command == "video-auto-chapters":
        from ..effects_engine import auto_chapters

        result = _with_spinner("Detecting chapters...", auto_chapters, args.input, threshold=args.threshold)
        if use_json:
            output_json(
                {
                    "chapters": [
                        {
                            "timestamp": (c[0] if isinstance(c, (list, tuple)) else c.get("timestamp", "")),
                            "description": (c[1] if isinstance(c, (list, tuple)) else c.get("description", "")),
                        }
                        for c in result
                    ]
                }
            )
        else:
            table = Table(title="Auto Chapters")
            table.add_column("#", style="bold", justify="right")
            table.add_column("Timestamp", style="cyan")
            table.add_column("Description")
            for i, chapter in enumerate(result, 1):
                if isinstance(chapter, (list, tuple)):
                    ts, desc = chapter
                else:
                    ts = chapter.get("timestamp", "")
                    desc = chapter.get("description", "")
                table.add_row(str(i), f"{ts:.2f}s", desc)
            console.print(table)
            console.print(f"[bold]{len(result)} chapters detected[/bold]")
        return True

    if args.command == "video-extract-frame":
        from ..engine import thumbnail

        result = _with_spinner(
            "Extracting frame...", thumbnail, args.input, timestamp=args.timestamp, output_path=args.output
        )
        if use_json:
            output_json(result)
        else:
            _format_thumbnail_text(result)
        return True

    if args.command == "video-info-detailed":
        from ..effects_engine import video_info_detailed

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
            table.add_row("Bitrate", f"{(result.get('bitrate') or 0) // 1000} kbps")
            table.add_row("Has Audio", str(result.get("has_audio", False)))
            table.add_row("Scene Changes", str(len(result.get("scene_changes", []))))
            for i, ts in enumerate(result.get("scene_changes", []), 1):
                table.add_row(f"  Scene {i}", f"{ts:.2f}s")
            console.print(table)
        return True

    if args.command == "video-quality-check":
        from ..quality_guardrails import quality_check

        result = _with_spinner(
            "Running quality check...", quality_check, args.input, fail_on_warning=args.fail_on_warning
        )
        if use_json:
            output_json(result)
        else:
            data = result if isinstance(result, dict) else {}
            table = Table(title="Quality Check")
            table.add_column("Check", style="bold cyan")
            table.add_column("Status")
            table.add_column("Value")
            checks = data.get("checks", {})
            if isinstance(checks, dict):
                for check, info in checks.items():
                    status = "[green]PASS[/green]" if info.get("passed") else "[red]FAIL[/red]"
                    table.add_row(check, status, str(info.get("value", "")))
            overall = "[green]PASS[/green]" if data.get("passed") else "[red]FAIL[/red]"
            console.print(table)
            console.print(f"[bold]Overall: {overall}[/bold]")
        return True

    if args.command == "video-design-quality-check":
        from ..design_quality import design_quality_check

        result = _with_spinner(
            "Running design quality check...",
            design_quality_check,
            args.input,
            auto_fix=args.auto_fix,
            strict=args.strict,
        )
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
        return True

    if args.command == "video-fix-design-issues":
        from ..design_quality import fix_design_issues

        result = _with_spinner("Fixing design issues...", fix_design_issues, args.input, args.output)
        if use_json:
            output_json({"success": True, "output_path": result})
        else:
            console.print(
                Panel(f"[bold green]Design fixed:[/bold green] {result}", border_style="green", title="Done")
            )
        return True

    return False
