"""mcp-video CLI entry point."""

from __future__ import annotations

import json
import sys
from typing import Any

from rich.panel import Panel
from rich.table import Table

from .cli.common import _auto_output, _parse_json_arg, _with_spinner, output_json
from .cli.handlers_core import handle_initial_command
from .cli.parser import build_parser
from .cli.formatting import (
    _format_batch_text,
    _format_edit_text,
    _format_error,
    _format_extract_audio_text,
    _format_storyboard_text,
    _format_thumbnail_text,
    console,
    err_console,
)


def main() -> None:
    parser = build_parser()
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

    # CLI commands
    try:
        if handle_initial_command(args, use_json=use_json):
            return

        if args.command == "trim":
            from .engine import trim

            result = _with_spinner(
                "Trimming...",
                trim,
                args.input,
                start=args.start,
                duration=args.duration,
                end=args.end,
                output_path=args.output,
            )
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "merge":
            from .engine import merge

            result = _with_spinner(
                "Merging...",
                merge,
                args.inputs,
                output_path=args.output,
                transition=args.transition,
                transitions=args.transitions,
                transition_duration=args.transition_duration,
            )
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "add-text":
            from .engine import add_text

            result = _with_spinner(
                "Adding text...",
                add_text,
                args.input,
                text=args.text,
                position=args.position,
                font=args.font,
                size=args.size,
                color=args.color,
                shadow=not args.no_shadow,
                start_time=args.start_time,
                duration=args.duration,
                output_path=args.output,
            )
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "add-audio":
            from .engine import add_audio

            result = _with_spinner(
                "Adding audio...",
                add_audio,
                args.video,
                args.audio,
                volume=args.volume,
                fade_in=args.fade_in,
                fade_out=args.fade_out,
                mix=args.mix,
                start_time=args.start_time,
                output_path=args.output,
            )
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "resize":
            from .engine import resize

            result = _with_spinner(
                "Resizing...",
                resize,
                args.input,
                width=args.width,
                height=args.height,
                aspect_ratio=args.aspect_ratio,
                quality=args.quality,
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

            result = _with_spinner(
                "Converting...", convert, args.input, format=args.fmt, quality=args.quality, output_path=args.output
            )
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

            result = _with_spinner(
                "Generating preview...", preview, args.input, output_path=args.output, scale_factor=args.scale
            )
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "storyboard":
            from .engine import storyboard

            result = _with_spinner(
                "Extracting storyboard...", storyboard, args.input, output_dir=args.output_dir, frame_count=args.frames
            )
            if use_json:
                output_json(result)
            else:
                _format_storyboard_text(result)

        elif args.command == "subtitles":
            from .engine import subtitles

            result = _with_spinner(
                "Burning subtitles...", subtitles, args.input, subtitle_path=args.subtitle, output_path=args.output
            )
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "watermark":
            from .engine import watermark

            result = _with_spinner(
                "Adding watermark...",
                watermark,
                args.input,
                image_path=args.image,
                position=args.position,
                opacity=args.opacity,
                margin=args.margin,
                output_path=args.output,
            )
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "crop":
            from .engine import crop

            result = _with_spinner(
                "Cropping...",
                crop,
                args.input,
                width=args.width,
                height=args.height,
                x=args.x,
                y=args.y,
                output_path=args.output,
            )
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "rotate":
            from .engine import rotate

            result = _with_spinner(
                "Rotating...",
                rotate,
                args.input,
                angle=args.angle,
                flip_horizontal=args.flip_h,
                flip_vertical=args.flip_v,
                output_path=args.output,
            )
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "fade":
            from .engine import fade

            result = _with_spinner(
                "Applying fade...",
                fade,
                args.input,
                fade_in=args.fade_in,
                fade_out=args.fade_out,
                output_path=args.output,
            )
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "export":
            from .engine import export_video

            result = _with_spinner(
                "Exporting...", export_video, args.input, quality=args.quality, format=args.fmt, output_path=args.output
            )
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "extract-audio":
            from .engine import extract_audio

            result = _with_spinner(
                "Extracting audio...", extract_audio, args.input, output_path=args.output, format=args.audio_format
            )
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                _format_extract_audio_text(result)

        elif args.command == "edit":
            from .models import Timeline

            timeline_arg = args.timeline.strip()
            if timeline_arg.startswith(("{", "[")):
                tl = Timeline.model_validate(_parse_json_arg(timeline_arg, "timeline", json_mode=use_json))
            else:
                with open(timeline_arg) as f:
                    tl = Timeline.model_validate(json.load(f))
            from .engine import edit_timeline

            result = _with_spinner("Editing timeline...", edit_timeline, tl, output_path=args.output)
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "filter":
            from .engine import apply_filter

            params = _parse_json_arg(args.params, "params", json_mode=use_json) if args.params else {}
            result = _with_spinner(
                "Applying filter...",
                apply_filter,
                args.input,
                filter_type=args.filter_type,
                params=params,
                output_path=args.output,
            )
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "blur":
            from .engine import apply_filter

            result = _with_spinner(
                "Applying blur...",
                apply_filter,
                args.input,
                filter_type="blur",
                params={"radius": args.radius, "strength": args.strength},
                output_path=args.output,
            )
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "reverse":
            from .engine import reverse

            result = _with_spinner("Reversing...", reverse, args.input, output_path=args.output)
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "chroma-key":
            from .engine import chroma_key

            result = _with_spinner(
                "Removing green screen...",
                chroma_key,
                args.input,
                color=args.color,
                similarity=args.similarity,
                blend=args.blend,
                output_path=args.output,
            )
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "color-grade":
            from .engine import apply_filter

            result = _with_spinner(
                "Applying color grade...",
                apply_filter,
                args.input,
                filter_type="color_preset",
                params={"preset": args.preset},
                output_path=args.output,
            )
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "normalize-audio":
            from .engine import normalize_audio

            result = _with_spinner(
                "Normalizing audio...", normalize_audio, args.input, target_lufs=args.lufs, output_path=args.output
            )
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "overlay-video":
            from .engine import overlay_video

            result = _with_spinner(
                "Compositing overlay...",
                overlay_video,
                args.background,
                overlay_path=args.overlay,
                position=args.position,
                width=args.width,
                height=args.height,
                opacity=args.opacity,
                start_time=args.start_time,
                duration=args.duration,
                output_path=args.output,
            )
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "split-screen":
            from .engine import split_screen

            result = _with_spinner(
                "Creating split screen...",
                split_screen,
                args.left,
                right_path=args.right,
                layout=args.layout,
                output_path=args.output,
            )
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "batch":
            from .engine import video_batch

            params = _parse_json_arg(args.params, "params", json_mode=use_json) if args.params else {}
            result = video_batch(args.inputs, operation=args.operation, params=params, output_dir=args.output_dir)
            if use_json:
                print(json.dumps(result, indent=2))
            else:
                _format_batch_text(result)

        elif args.command == "detect-scenes":
            from .engine import detect_scenes

            result = _with_spinner(
                "Detecting scenes...",
                detect_scenes,
                args.input,
                threshold=args.threshold,
                min_scene_duration=args.min_duration,
            )
            if use_json:
                output_json(result)
            else:
                data = result.model_dump()
                table = Table(title="Scene Detection")
                table.add_column("#", style="bold", justify="right")
                table.add_column("Start", style="cyan")
                table.add_column("End", style="cyan")
                table.add_column("Frames")
                for i, scene in enumerate(data.get("scenes", []), 1):
                    table.add_row(
                        str(i),
                        f"{scene['start']:.2f}s",
                        f"{scene['end']:.2f}s",
                        f"{scene['start_frame']}-{scene['end_frame']}",
                    )
                console.print(table)
                console.print(
                    f"[bold]{data.get('scene_count', 0)} scenes detected[/bold] in {data.get('duration', 0):.2f}s"
                )

        elif args.command == "create-from-images":
            from .engine import create_from_images

            result = _with_spinner(
                "Creating video from images...", create_from_images, args.inputs, output_path=args.output, fps=args.fps
            )
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "export-frames":
            from .engine import export_frames

            fmt = "mjpeg" if args.image_format == "jpg" else args.image_format
            result = _with_spinner(
                "Exporting frames...", export_frames, args.input, output_dir=args.output_dir, fps=args.fps, format=fmt
            )
            if use_json:
                output_json(result)
            else:
                data = result.model_dump()
                lines = [
                    f"[bold green]Frames:[/bold green] {data.get('frame_count', 0)}",
                    f"[bold green]Format:[/bold green] {args.image_format}",
                    f"[bold green]FPS:[/bold green] {data.get('fps', 0)}",
                ]
                if data.get("frame_paths"):
                    lines.append(f"[bold green]Output dir:[/bold green] {data['frame_paths'][0].rsplit('/', 1)[0]}")
                console.print(Panel("\n".join(lines), border_style="green", title="Frames Exported"))

        elif args.command == "compare-quality":
            from .engine import compare_quality

            metrics = args.metrics if args.metrics else None
            result = _with_spinner(
                "Comparing quality...", compare_quality, args.original, args.distorted, metrics=metrics
            )
            if use_json:
                output_json(result)
            else:
                data = result.model_dump()
                table = Table(title="Quality Metrics")
                table.add_column("Metric", style="bold cyan")
                table.add_column("Value")
                for k, v in data.get("metrics", {}).items():
                    table.add_row(k.upper(), f"{v:.4f}")
                quality = data.get("overall_quality", "unknown")
                quality_style = {"high": "green", "medium": "yellow", "low": "red"}.get(quality, "white")
                table.add_row("Overall", f"[{quality_style}]{quality}[/{quality_style}]")
                console.print(table)

        elif args.command == "read-metadata":
            from .engine import read_metadata

            result = read_metadata(args.input)
            if use_json:
                output_json(result)
            else:
                data = result.model_dump()
                table = Table(title="Metadata")
                table.add_column("Field", style="bold cyan")
                table.add_column("Value")
                for field in ["title", "artist", "album", "comment", "date"]:
                    val = data.get(field)
                    if val:
                        table.add_row(field.capitalize(), val)
                for k, v in data.get("tags", {}).items():
                    table.add_row(k, str(v))
                if not data.get("title") and not data.get("tags"):
                    console.print("[yellow]No metadata found.[/yellow]")
                else:
                    console.print(table)

        elif args.command == "write-metadata":
            from .engine import write_metadata

            try:
                tags = json.loads(args.tags)
            except json.JSONDecodeError as e:
                console.print(f"[bold red]Invalid JSON in --tags: {e}[/bold red]")
                raise SystemExit(1) from None
            result = _with_spinner(
                "Writing metadata...", write_metadata, args.input, metadata=tags, output_path=args.output
            )
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "stabilize":
            from .engine import stabilize

            result = _with_spinner(
                "Stabilizing...",
                stabilize,
                args.input,
                smoothing=args.smoothing,
                zooming=args.zooming,
                output_path=args.output,
            )
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "apply-mask":
            from .engine import apply_mask

            result = _with_spinner(
                "Applying mask...",
                apply_mask,
                args.input,
                mask_path=args.mask,
                feather=args.feather,
                output_path=args.output,
            )
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        elif args.command == "audio-waveform":
            from .engine import audio_waveform

            result = _with_spinner("Extracting waveform...", audio_waveform, args.input, bins=args.bins)
            if use_json:
                output_json(result)
            else:
                data = result.model_dump()
                table = Table(title="Audio Waveform")
                table.add_column("Property", style="bold cyan")
                table.add_column("Value")
                table.add_row("Duration", f"{data.get('duration', 0):.2f}s")
                table.add_row("Mean Level", f"{data.get('mean_level', 0):.1f} dB")
                table.add_row("Max Level", f"{data.get('max_level', 0):.1f} dB")
                table.add_row("Min Level", f"{data.get('min_level', 0):.1f} dB")
                silence_count = len(data.get("silence_regions", []))
                table.add_row("Silence Regions", str(silence_count))
                console.print(table)

        elif args.command == "generate-subtitles":
            from .engine import generate_subtitles

            entries = _parse_json_arg(args.entries, "entries", json_mode=use_json)
            result = _with_spinner(
                "Generating subtitles...",
                generate_subtitles,
                entries,
                args.input,
                burn=args.burn,
                output_path=args.output,
            )
            if use_json:
                output_json(result)
            else:
                data = result.model_dump()
                lines = [
                    f"[bold green]Entries:[/bold green] {data.get('entry_count', 0)}",
                    f"[bold green]SRT Path:[/bold green] {data.get('srt_path', 'N/A')}",
                ]
                if data.get("video_path"):
                    lines.append(f"[bold green]Video Path:[/bold green] {data['video_path']}")
                console.print(Panel("\n".join(lines), border_style="green", title="Subtitles Generated"))

        elif args.command == "templates":
            from .templates import TEMPLATES

            descriptions = {
                "tiktok": "TikTok (9:16, 1080x1920) — vertical video with optional caption and music",
                "youtube-shorts": "YouTube Shorts (9:16) — title at top, vertical video",
                "instagram-reel": "Instagram Reel (9:16) — caption at bottom, vertical video",
                "youtube": "YouTube (16:9, 1920x1080) — horizontal video with title card and outro",
                "instagram-post": "Instagram Post (1:1, 1080x1080) — square video with caption",
            }
            if use_json:
                output_json({"success": True, "templates": {name: descriptions.get(name, "") for name in TEMPLATES}})
            else:
                table = Table(title="Available Templates")
                table.add_column("Name", style="bold cyan")
                table.add_column("Description")
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
            result = _with_spinner(
                f"Applying {args.name} template...", edit_timeline, timeline, output_path=args.output
            )
            if use_json:
                output_json(result)
            else:
                _format_edit_text(result)

        # ------------------------------------------------------------------
        # Remotion commands
        # ------------------------------------------------------------------

        elif args.command == "remotion-render":
            from .remotion_engine import render_composition

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

        elif args.command == "remotion-compositions":
            from .remotion_engine import list_compositions

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

        elif args.command == "remotion-studio":
            from .remotion_engine import launch_studio

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
                    result.model_dump()
                    if hasattr(result, "model_dump")
                    else (result if isinstance(result, dict) else {})
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

        elif args.command == "remotion-still":
            from .remotion_engine import render_still

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

        elif args.command == "remotion-create":
            from .remotion_engine import create_project

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

        elif args.command == "remotion-scaffold":
            from .remotion_engine import scaffold_composition

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

        elif args.command == "remotion-validate":
            from .remotion_engine import validate_project

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

        elif args.command == "remotion-pipeline":
            from .remotion_engine import render_pipeline

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

        # ------------------------------------------------------------------
        # Effect commands
        # ------------------------------------------------------------------

        elif args.command == "effect-vignette":
            from .effects_engine import effect_vignette

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
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(
                    Panel(f"[bold green]Vignette applied:[/bold green] {result}", border_style="green", title="Done")
                )

        elif args.command == "effect-glow":
            from .effects_engine import effect_glow

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
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(
                    Panel(f"[bold green]Glow applied:[/bold green] {result}", border_style="green", title="Done")
                )

        elif args.command == "effect-noise":
            from .effects_engine import effect_noise

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
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(
                    Panel(f"[bold green]Noise applied:[/bold green] {result}", border_style="green", title="Done")
                )

        elif args.command == "effect-scanlines":
            from .effects_engine import effect_scanlines

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
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(
                    Panel(f"[bold green]Scanlines applied:[/bold green] {result}", border_style="green", title="Done")
                )

        elif args.command == "effect-chromatic-aberration":
            from .effects_engine import effect_chromatic_aberration

            out = args.output or _auto_output(args.input, "chromatic")
            result = _with_spinner(
                "Applying chromatic aberration...",
                effect_chromatic_aberration,
                args.input,
                out,
                intensity=args.intensity,
                angle=args.angle,
            )
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(
                    Panel(
                        f"[bold green]Chromatic aberration applied:[/bold green] {result}",
                        border_style="green",
                        title="Done",
                    )
                )

        # ------------------------------------------------------------------
        # Transition commands
        # ------------------------------------------------------------------

        elif args.command == "transition-glitch":
            from .transitions_engine import transition_glitch

            result = _with_spinner(
                "Applying glitch transition...",
                transition_glitch,
                args.clip1,
                args.clip2,
                args.output,
                duration=args.duration,
                intensity=args.intensity,
            )
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(
                    Panel(f"[bold green]Glitch transition:[/bold green] {result}", border_style="green", title="Done")
                )

        elif args.command == "transition-morph":
            from .transitions_engine import transition_morph

            result = _with_spinner(
                "Applying morph transition...",
                transition_morph,
                args.clip1,
                args.clip2,
                args.output,
                duration=args.duration,
                mesh_size=args.mesh_size,
            )
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(
                    Panel(f"[bold green]Morph transition:[/bold green] {result}", border_style="green", title="Done")
                )

        elif args.command == "transition-pixelate":
            from .transitions_engine import transition_pixelate

            result = _with_spinner(
                "Applying pixelate transition...",
                transition_pixelate,
                args.clip1,
                args.clip2,
                args.output,
                duration=args.duration,
                pixel_size=args.pixel_size,
            )
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(
                    Panel(f"[bold green]Pixelate transition:[/bold green] {result}", border_style="green", title="Done")
                )

        # ------------------------------------------------------------------
        # AI commands
        # ------------------------------------------------------------------

        elif args.command == "video-ai-transcribe":
            from .ai_engine import ai_transcribe

            result = _with_spinner(
                "Transcribing...",
                ai_transcribe,
                args.input,
                output_srt=args.output,
                model=args.model,
                language=args.language,
            )
            if use_json:
                output_json(result)
            else:
                data = result if isinstance(result, dict) else {"success": True}
                text = data.get("text", "")
                srt = data.get("srt_path", args.output or "N/A")
                lines = [f"[bold green]SRT:[/bold green] {srt}"]
                if text:
                    lines.append(f"[bold green]Preview:[/bold green] {text[:200]}...")
                console.print(Panel("\n".join(lines), border_style="green", title="Transcription"))

        elif args.command == "video-analyze":
            from .ai_engine import analyze_video

            result = _with_spinner(
                "Analysing video...",
                analyze_video,
                args.input,
                whisper_model=args.model,
                language=args.language,
                scene_threshold=args.scene_threshold,
                include_transcript=not args.no_transcript,
                include_scenes=not args.no_scenes,
                include_audio=not args.no_audio,
                include_quality=not args.no_quality,
                include_chapters=not args.no_chapters,
                include_colors=not args.no_colors,
                output_srt=args.output_srt,
                output_txt=args.output_txt,
                output_md=args.output_md,
                output_json=args.output_json,
            )
            if use_json:
                output_json(result)
            else:
                # Metadata panel
                meta = result.get("metadata", {})
                meta_lines = []
                if meta.get("duration"):
                    meta_lines.append(f"[bold]Duration:[/bold] {meta['duration']:.2f}s")
                if meta.get("width") and meta.get("height"):
                    meta_lines.append(f"[bold]Resolution:[/bold] {meta['width']}x{meta['height']}")
                if meta.get("fps"):
                    meta_lines.append(f"[bold]FPS:[/bold] {meta['fps']:.2f}")
                if meta.get("codec"):
                    meta_lines.append(f"[bold]Video codec:[/bold] {meta['codec']}")
                if meta.get("audio_codec"):
                    meta_lines.append(f"[bold]Audio codec:[/bold] {meta['audio_codec']}")
                if meta.get("size_bytes"):
                    meta_lines.append(f"[bold]Size:[/bold] {meta['size_bytes'] // 1024:,} KB")
                console.print(
                    Panel("\n".join(meta_lines) or "No metadata", title="[cyan]Metadata[/cyan]", border_style="cyan")
                )

                # Transcript panel
                transcript = result.get("transcript")
                if transcript:
                    text = transcript.get("text", "")
                    lang = transcript.get("language", "unknown")
                    segs = len(transcript.get("segments", []))
                    preview = text[:300] + ("..." if len(text) > 300 else "")
                    t_lines = [
                        f"[bold]Language:[/bold] {lang}",
                        f"[bold]Segments:[/bold] {segs}",
                        f"[bold]Preview:[/bold] {preview}",
                    ]
                    if transcript.get("srt_path"):
                        t_lines.append(f"[bold]SRT:[/bold] {transcript['srt_path']}")
                    if transcript.get("txt_path"):
                        t_lines.append(f"[bold]TXT:[/bold] {transcript['txt_path']}")
                    if transcript.get("md_path"):
                        t_lines.append(f"[bold]Markdown:[/bold] {transcript['md_path']}")
                    if transcript.get("json_path"):
                        t_lines.append(f"[bold]JSON:[/bold] {transcript['json_path']}")
                    console.print(Panel("\n".join(t_lines), title="[green]Transcript[/green]", border_style="green"))
                elif not args.no_transcript:
                    console.print(
                        Panel(
                            "[yellow]Transcript unavailable (Whisper not installed?)[/yellow]",
                            title="Transcript",
                            border_style="yellow",
                        )
                    )

                # Scenes panel
                scenes = result.get("scenes")
                if scenes is not None:
                    table = Table(title="Scenes", show_header=True, header_style="bold magenta")
                    table.add_column("#", style="dim", width=4)
                    table.add_column("Start", justify="right")
                    table.add_column("End", justify="right")
                    for i, sc in enumerate(scenes[:20], 1):
                        table.add_row(str(i), f"{sc.get('start', 0):.2f}s", f"{sc.get('end', 0):.2f}s")
                    if len(scenes) > 20:
                        table.add_row("...", f"+{len(scenes) - 20} more", "")
                    console.print(table)

                # Chapters panel
                chapters = result.get("chapters")
                if chapters:
                    ch_lines = [f"[bold]{ch['title']}[/bold] @ {ch['timestamp']:.2f}s" for ch in chapters[:10]]
                    console.print(Panel("\n".join(ch_lines), title="[blue]Chapters[/blue]", border_style="blue"))

                # Audio panel
                audio = result.get("audio")
                if audio:
                    a_lines = [
                        f"[bold]Mean level:[/bold] {audio.get('mean_level', 'N/A')} dBFS",
                        f"[bold]Max level:[/bold] {audio.get('max_level', 'N/A')} dBFS",
                        f"[bold]Silence regions:[/bold] {len(audio.get('silence_regions', []))}",
                    ]
                    console.print(Panel("\n".join(a_lines), title="[yellow]Audio[/yellow]", border_style="yellow"))

                # Quality panel
                quality = result.get("quality")
                if quality:
                    score = quality.get("overall_score", "N/A")
                    console.print(
                        Panel(
                            f"[bold]Overall score:[/bold] {score}/100",
                            title="[magenta]Quality[/magenta]",
                            border_style="magenta",
                        )
                    )

                # Errors panel
                errors = result.get("errors", [])
                if errors:
                    err_lines = [f"[red]{e['section']}:[/red] {e['error']}" for e in errors]
                    console.print(Panel("\n".join(err_lines), title="[red]Warnings / Errors[/red]", border_style="red"))

        elif args.command == "video-ai-upscale":
            from .ai_engine import ai_upscale

            result = _with_spinner(
                "Upscaling...", ai_upscale, args.input, args.output, scale=args.scale, model=args.model
            )
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(
                    Panel(
                        f"[bold green]Upscaled ({args.scale}x):[/bold green] {result}",
                        border_style="green",
                        title="Done",
                    )
                )

        elif args.command == "video-ai-stem-separation":
            from .ai_engine import ai_stem_separation

            result = _with_spinner(
                "Separating stems...",
                ai_stem_separation,
                args.input,
                args.output_dir,
                stems=args.stems,
                model=args.model,
            )
            if use_json:
                output_json(result)
            else:
                data = result if isinstance(result, dict) else {}
                lines = []
                if isinstance(data, dict):
                    for stem, path in data.items():
                        lines.append(f"[bold green]{stem}:[/bold green] {path}")
                if not lines:
                    lines.append("[dim]No stems found[/dim]")
                console.print(Panel("\n".join(lines), border_style="green", title="Stem Separation"))

        elif args.command == "video-ai-scene-detect":
            from .ai_engine import ai_scene_detect

            result = _with_spinner(
                "Detecting scenes (AI)...", ai_scene_detect, args.input, threshold=args.threshold, use_ai=args.use_ai
            )
            if use_json:
                output_json(result if isinstance(result, dict) else {"scenes": result})
            else:
                scenes = result if isinstance(result, list) else result.get("scenes", [])
                table = Table(title="AI Scene Detection")
                table.add_column("#", style="bold", justify="right")
                table.add_column("Start", style="cyan")
                table.add_column("End", style="cyan")
                table.add_column("Confidence")
                for i, scene in enumerate(scenes, 1):
                    if isinstance(scene, dict):
                        table.add_row(
                            str(i),
                            f"{scene.get('start', 0):.2f}s",
                            f"{scene.get('end', 0):.2f}s",
                            f"{scene.get('confidence', 0):.2f}",
                        )
                    else:
                        table.add_row(str(i), str(scene))
                console.print(table)
                console.print(f"[bold]{len(scenes)} scenes detected[/bold]")

        elif args.command == "video-ai-color-grade":
            from .ai_engine import ai_color_grade

            result = _with_spinner(
                "Color grading...", ai_color_grade, args.input, args.output, reference=args.reference, style=args.style
            )
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(
                    Panel(
                        f"[bold green]Color graded ({args.style}):[/bold green] {result}",
                        border_style="green",
                        title="Done",
                    )
                )

        elif args.command == "video-ai-remove-silence":
            from .ai_engine import ai_remove_silence

            result = _with_spinner(
                "Removing silence...",
                ai_remove_silence,
                args.input,
                args.output,
                silence_threshold=args.silence_threshold,
                min_silence_duration=args.min_silence_duration,
                keep_margin=args.keep_margin,
            )
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(
                    Panel(f"[bold green]Silence removed:[/bold green] {result}", border_style="green", title="Done")
                )

        # ------------------------------------------------------------------
        # Audio synthesis commands
        # ------------------------------------------------------------------

        elif args.command == "audio-synthesize":
            from .audio_engine import audio_synthesize

            effects = _parse_json_arg(args.effects, "effects", json_mode=use_json) if args.effects else None
            result = _with_spinner(
                "Synthesizing audio...",
                audio_synthesize,
                args.output,
                waveform=args.waveform,
                frequency=args.frequency,
                duration=args.duration,
                volume=args.volume,
                effects=effects,
            )
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(
                    Panel(f"[bold green]Audio synthesized:[/bold green] {result}", border_style="green", title="Done")
                )

        elif args.command == "audio-compose":
            from .audio_engine import audio_compose

            tracks = _parse_json_arg(args.tracks, "tracks", json_mode=use_json)
            result = _with_spinner("Composing audio...", audio_compose, tracks, args.duration, args.output)
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(
                    Panel(f"[bold green]Audio composed:[/bold green] {result}", border_style="green", title="Done")
                )

        elif args.command == "audio-preset":
            from .audio_engine import audio_preset

            result = _with_spinner(
                f"Generating preset '{args.preset}'...",
                audio_preset,
                args.preset,
                args.output,
                pitch=args.pitch,
                duration=args.duration,
                intensity=args.intensity,
            )
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(
                    Panel(
                        f"[bold green]Preset '{args.preset}':[/bold green] {result}", border_style="green", title="Done"
                    )
                )

        elif args.command == "audio-sequence":
            from .audio_engine import audio_sequence

            sequence = _parse_json_arg(args.sequence, "sequence", json_mode=use_json)
            result = _with_spinner("Composing audio sequence...", audio_sequence, sequence, args.output)
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(
                    Panel(f"[bold green]Audio sequence:[/bold green] {result}", border_style="green", title="Done")
                )

        elif args.command == "audio-effects":
            from .audio_engine import audio_effects

            effects = _parse_json_arg(args.effects, "effects", json_mode=use_json)
            result = _with_spinner("Applying audio effects...", audio_effects, args.input, args.output, effects)
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(
                    Panel(
                        f"[bold green]Audio effects applied:[/bold green] {result}", border_style="green", title="Done"
                    )
                )

        # ------------------------------------------------------------------
        # Motion graphics commands
        # ------------------------------------------------------------------

        elif args.command == "video-text-animated":
            from .effects_engine import text_animated

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
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(
                    Panel(
                        f"[bold green]Animated text ({args.animation}):[/bold green] {result}",
                        border_style="green",
                        title="Done",
                    )
                )

        elif args.command == "video-mograph-count":
            from .effects_engine import mograph_count

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
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(
                    Panel(
                        f"[bold green]Counter ({args.start}-{args.end}):[/bold green] {result}",
                        border_style="green",
                        title="Done",
                    )
                )

        elif args.command == "video-mograph-progress":
            from .effects_engine import mograph_progress

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
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(
                    Panel(
                        f"[bold green]Progress bar ({args.style}):[/bold green] {result}",
                        border_style="green",
                        title="Done",
                    )
                )

        # ------------------------------------------------------------------
        # Layout commands
        # ------------------------------------------------------------------

        elif args.command == "video-layout-grid":
            from .effects_engine import layout_grid

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
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(
                    Panel(
                        f"[bold green]Grid layout ({args.layout}):[/bold green] {result}",
                        border_style="green",
                        title="Done",
                    )
                )

        elif args.command == "video-layout-pip":
            from .effects_engine import layout_pip

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
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(
                    Panel(
                        f"[bold green]PIP ({args.position}):[/bold green] {result}", border_style="green", title="Done"
                    )
                )

        # ------------------------------------------------------------------
        # Audio-Video commands
        # ------------------------------------------------------------------

        elif args.command == "video-add-generated-audio":
            from .audio_engine import add_generated_audio

            audio_config = _parse_json_arg(args.audio_config, "audio-config", json_mode=use_json)
            result = _with_spinner(
                "Adding generated audio...", add_generated_audio, args.input, audio_config, args.output
            )
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(
                    Panel(
                        f"[bold green]Generated audio added:[/bold green] {result}", border_style="green", title="Done"
                    )
                )

        elif args.command == "video-audio-spatial":
            from .ai_engine import audio_spatial

            positions = _parse_json_arg(args.positions, "positions", json_mode=use_json)
            result = _with_spinner(
                "Applying spatial audio...",
                audio_spatial,
                args.input,
                args.output,
                positions=positions,
                method=args.method,
            )
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(
                    Panel(
                        f"[bold green]Spatial audio ({args.method}):[/bold green] {result}",
                        border_style="green",
                        title="Done",
                    )
                )

        # ------------------------------------------------------------------
        # Quality / Info commands
        # ------------------------------------------------------------------

        elif args.command == "video-auto-chapters":
            from .effects_engine import auto_chapters

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

        elif args.command == "video-extract-frame":
            from .engine import thumbnail

            result = _with_spinner(
                "Extracting frame...", thumbnail, args.input, timestamp=args.timestamp, output_path=args.output
            )
            if use_json:
                output_json(result)
            else:
                _format_thumbnail_text(result)

        elif args.command == "video-info-detailed":
            from .effects_engine import video_info_detailed

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

        elif args.command == "video-quality-check":
            from .quality_guardrails import quality_check

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

        elif args.command == "video-design-quality-check":
            from .design_quality import design_quality_check

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

        elif args.command == "video-fix-design-issues":
            from .design_quality import fix_design_issues

            result = _with_spinner("Fixing design issues...", fix_design_issues, args.input, args.output)
            if use_json:
                output_json({"success": True, "output_path": result})
            else:
                console.print(
                    Panel(f"[bold green]Design fixed:[/bold green] {result}", border_style="green", title="Done")
                )

        # ------------------------------------------------------------------
        # Image analysis commands
        # ------------------------------------------------------------------

        elif args.command == "image-extract-colors":
            from .image_engine import extract_colors

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

        elif args.command == "image-generate-palette":
            from .image_engine import generate_palette

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

        elif args.command == "image-analyze-product":
            from .image_engine import analyze_product

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

    except Exception as e:
        if use_json:
            from .errors import MCPVideoError

            if isinstance(e, MCPVideoError):
                try:
                    err_data = e.to_dict()
                except Exception:
                    err_data = {"type": "internal_error", "code": "to_dict_failed", "message": str(e)}
                print(json.dumps({"success": False, "error": err_data}, indent=2), file=sys.stderr)
            else:
                print(
                    json.dumps({"success": False, "error": {"type": "unknown", "message": str(e)}}, indent=2),
                    file=sys.stderr,
                )
        else:
            _format_error(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
