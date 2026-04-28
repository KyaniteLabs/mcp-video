"""CLI handlers for Hyperframes commands."""

from __future__ import annotations

from typing import Any

from rich.panel import Panel
from rich.table import Table

from .common import _parse_json_arg, _with_spinner, output_json
from .formatting import console


def handle_hyperframes_commands(args: Any, *, use_json: bool) -> bool:
    """Handle Hyperframes commands extracted from the main dispatcher."""
    if args.command == "hyperframes-render":
        from ..hyperframes_engine import render

        result = _with_spinner(
            f"Rendering {args.project_path}...",
            render,
            args.project_path,
            output_path=args.output,
            fps=args.fps,
            width=args.width,
            height=args.height,
            quality=args.quality,
            format=args.format,
            workers=args.workers,
            crf=args.crf,
        )
        if use_json:
            output_json(result)
        else:
            data = result.model_dump()
            lines = [
                f"[bold green]Project:[/bold green] {args.project_path}",
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
            console.print(Panel("\n".join(lines), border_style="green", title="Hyperframes Render"))
        return True

    if args.command == "hyperframes-compositions":
        from ..hyperframes_engine import compositions

        result = _with_spinner(
            "Listing compositions...",
            compositions,
            args.project_path,
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
        return True

    if args.command == "hyperframes-preview":
        from ..hyperframes_engine import preview

        result = _with_spinner(
            "Launching Hyperframes preview...",
            preview,
            args.project_path,
            port=args.port,
        )
        if use_json or args.json:
            output_json(result)
        else:
            data = (
                result.model_dump() if hasattr(result, "model_dump") else (result if isinstance(result, dict) else {})
            )
            console.print(
                Panel(
                    f"[bold green]Preview running:[/bold green] {data.get('url', 'N/A')}\n"
                    f"[bold green]Port:[/bold green] {data.get('port', 'N/A')}\n"
                    f"[bold green]Project:[/bold green] {data.get('project_path', 'N/A')}",
                    border_style="green",
                    title="Hyperframes Preview",
                )
            )
        return True

    if args.command == "hyperframes-still":
        from ..hyperframes_engine import still

        result = _with_spinner(
            f"Rendering still frame {args.frame}...",
            still,
            args.project_path,
            output_path=args.output,
            frame=args.frame,
        )
        if use_json:
            output_json(result)
        else:
            data = result.model_dump()
            lines = [
                f"[bold green]Project:[/bold green] {args.project_path}",
                f"[bold green]Frame:[/bold green] {data.get('frame', 0)}",
                f"[bold green]Output:[/bold green] {data.get('output_path', 'N/A')}",
            ]
            if data.get("resolution"):
                lines.append(f"[bold green]Resolution:[/bold green] {data['resolution']}")
            console.print(Panel("\n".join(lines), border_style="green", title="Hyperframes Still"))
        return True

    if args.command == "hyperframes-init":
        from ..hyperframes_engine import create_project

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
            console.print(Panel("\n".join(lines), border_style="green", title="Hyperframes Project Created"))
        return True

    if args.command == "hyperframes-add-block":
        from ..hyperframes_engine import add_block

        result = _with_spinner(
            f"Adding block '{args.block_name}'...",
            add_block,
            args.project_path,
            args.block_name,
        )
        if use_json:
            output_json(result)
        else:
            data = result.model_dump()
            lines = [
                f"[bold green]Project:[/bold green] {data.get('project_path', 'N/A')}",
                f"[bold green]Block:[/bold green] {data.get('block_name', 'N/A')}",
            ]
            if data.get("files_added"):
                lines.append(f"[bold green]Files added:[/bold green] {len(data['files_added'])}")
            console.print(Panel("\n".join(lines), border_style="green", title="Hyperframes Block Added"))
        return True

    if args.command == "hyperframes-validate":
        from ..hyperframes_engine import validate

        result = _with_spinner(
            "Validating project...",
            validate,
            args.project_path,
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
            console.print(
                Panel(
                    "\n".join(lines),
                    border_style="green" if data.get("valid") else "red",
                    title="Hyperframes Validate",
                )
            )
        return True

    if args.command == "hyperframes-pipeline":
        from ..hyperframes_engine import render_and_post

        post_process = _parse_json_arg(args.post_process, "post-process", json_mode=use_json)
        result = _with_spinner(
            f"Running pipeline for {args.project_path}...",
            render_and_post,
            args.project_path,
            post_process=post_process,
            output_path=args.output,
        )
        if use_json:
            output_json(result)
        else:
            data = result.model_dump()
            lines = [
                f"[bold green]Project:[/bold green] {args.project_path}",
                f"[bold green]Hyperframes output:[/bold green] {data.get('hyperframes_output', 'N/A')}",
                f"[bold green]Final output:[/bold green] {data.get('final_output', 'N/A')}",
            ]
            if data.get("operations"):
                lines.append(f"[bold green]Post-process ops:[/bold green] {', '.join(data['operations'])}")
            console.print(Panel("\n".join(lines), border_style="green", title="Hyperframes Pipeline"))
        return True

    return False
