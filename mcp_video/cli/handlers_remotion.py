"""CLI handlers for Remotion commands."""

from __future__ import annotations

from typing import Any

from rich.panel import Panel
from rich.table import Table

from .common import _parse_json_arg, _with_spinner, output_json
from .formatting import console


def handle_remotion_commands(args: Any, *, use_json: bool) -> bool:
    """Handle Remotion commands extracted from the main dispatcher."""
    if args.command == "remotion-render":
        from ..remotion_engine import render_composition

        props = _parse_json_arg(args.props, "props", json_mode=use_json) if args.props else None
        result = _with_spinner(
            f"Rendering {args.composition_id}...",
            render_composition,
            args.project_path,
            args.composition_id,
            output_path=args.output,
            codec=args.codec,
            crf=args.crf,
            width=args.width,
            height=args.height,
            fps=args.fps,
            concurrency=args.concurrency,
            frames=args.frames,
            props=props,
            scale=args.scale,
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
        return True

    if args.command == "remotion-compositions":
        from ..remotion_engine import list_compositions

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
        return True

    if args.command == "remotion-studio":
        from ..remotion_engine import launch_studio

        result = _with_spinner(
            "Launching Remotion Studio...",
            launch_studio,
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
                    f"[bold green]Studio running:[/bold green] {data.get('url', 'N/A')}\n"
                    f"[bold green]Port:[/bold green] {data.get('port', 'N/A')}\n"
                    f"[bold green]Project:[/bold green] {data.get('project_path', 'N/A')}",
                    border_style="green",
                    title="Remotion Studio",
                )
            )
        return True

    if args.command == "remotion-still":
        from ..remotion_engine import render_still

        result = _with_spinner(
            f"Rendering still frame {args.frame}...",
            render_still,
            args.project_path,
            args.composition_id,
            output_path=args.output,
            frame=args.frame,
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
        return True

    if args.command == "remotion-create":
        from ..remotion_engine import create_project

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
        return True

    if args.command == "remotion-scaffold":
        from ..remotion_engine import scaffold_composition

        spec = _parse_json_arg(args.spec, "spec", json_mode=use_json)
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
        return True

    if args.command == "remotion-validate":
        from ..remotion_engine import validate_project

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
            console.print(
                Panel(
                    "\n".join(lines),
                    border_style="green" if data.get("valid") else "red",
                    title="Remotion Validate",
                )
            )
        return True

    if args.command == "remotion-pipeline":
        from ..remotion_engine import render_pipeline

        post_process = _parse_json_arg(args.post_process, "post-process", json_mode=use_json)
        result = _with_spinner(
            f"Running pipeline for {args.composition_id}...",
            render_pipeline,
            args.project_path,
            args.composition_id,
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
        return True

    return False
