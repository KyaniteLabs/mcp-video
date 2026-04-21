"""CLI handlers for media processing commands."""

from __future__ import annotations

import json
from typing import Any

from rich.panel import Panel
from rich.table import Table

from .common import _parse_json_arg, _with_spinner, output_json
from .formatting import _format_batch_text, _format_edit_text, console


def handle_media_commands(args: Any, *, use_json: bool) -> bool:
    """Handle media processing commands extracted from the main dispatcher."""
    if args.command == "filter":
        from ..engine import apply_filter

        params = _parse_json_arg(args.params, "params", json_mode=use_json) if args.params else {}
        result = _with_spinner(
            "Applying filter...",
            apply_filter,
            args.input,
            filter_type=args.filter_type,
            params=params,
            output_path=args.output,
            crf=args.crf,
            preset=args.preset,
        )
        if use_json:
            output_json(result)
        else:
            _format_edit_text(result)
        return True

    if args.command == "blur":
        from ..engine import apply_filter

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
        return True

    if args.command == "reverse":
        from ..engine import reverse

        result = _with_spinner("Reversing...", reverse, args.input, output_path=args.output)
        if use_json:
            output_json(result)
        else:
            _format_edit_text(result)
        return True

    if args.command == "chroma-key":
        from ..engine import chroma_key

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
        return True

    if args.command == "color-grade":
        from ..engine import apply_filter

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
        return True

    if args.command == "normalize-audio":
        from ..engine import normalize_audio

        norm_kwargs = {"target_lufs": args.lufs, "output_path": args.output}
        if args.lra is not None:
            norm_kwargs["lra"] = args.lra
        result = _with_spinner("Normalizing audio...", normalize_audio, args.input, **norm_kwargs)
        if use_json:
            output_json(result)
        else:
            _format_edit_text(result)
        return True

    if args.command == "overlay-video":
        from ..engine import overlay_video

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
            crf=args.crf,
            preset=args.preset,
        )
        if use_json:
            output_json(result)
        else:
            _format_edit_text(result)
        return True

    if args.command == "split-screen":
        from ..engine import split_screen

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
        return True

    if args.command == "batch":
        from ..engine import video_batch

        params = _parse_json_arg(args.params, "params", json_mode=use_json) if args.params else {}
        result = video_batch(args.inputs, operation=args.operation, params=params, output_dir=args.output_dir)
        if use_json:
            print(json.dumps(result, indent=2))
        else:
            _format_batch_text(result)
        return True

    if args.command == "detect-scenes":
        from ..engine import detect_scenes

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
        return True

    if args.command == "create-from-images":
        from ..engine import create_from_images

        result = _with_spinner(
            "Creating video from images...", create_from_images, args.inputs, output_path=args.output, fps=args.fps
        )
        if use_json:
            output_json(result)
        else:
            _format_edit_text(result)
        return True

    if args.command == "export-frames":
        from ..engine import export_frames

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
        return True

    if args.command == "compare-quality":
        from ..engine import compare_quality

        metrics = args.metrics if args.metrics else None
        result = _with_spinner("Comparing quality...", compare_quality, args.original, args.distorted, metrics=metrics)
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
        return True

    if args.command == "read-metadata":
        from ..engine import read_metadata

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
        return True

    if args.command == "write-metadata":
        from ..engine import write_metadata

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
        return True

    if args.command == "stabilize":
        from ..engine import stabilize

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
        return True

    if args.command == "apply-mask":
        from ..engine import apply_mask

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
        return True

    if args.command == "audio-waveform":
        from ..engine import audio_waveform

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
        return True

    if args.command == "generate-subtitles":
        from ..engine import generate_subtitles

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
        return True

    if args.command == "templates":
        from ..templates import TEMPLATES

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
        return True

    if args.command == "template":
        from ..engine import edit_timeline
        from ..templates import TEMPLATES

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
        result = _with_spinner(f"Applying {args.name} template...", edit_timeline, timeline, output_path=args.output)
        if use_json:
            output_json(result)
        else:
            _format_edit_text(result)
        return True

    return False
