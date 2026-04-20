"""CLI handlers for AI-powered video commands."""

from __future__ import annotations

from typing import Any

from rich.panel import Panel
from rich.table import Table

from .common import _with_spinner, output_json
from .formatting import console


def handle_ai_commands(args: Any, *, use_json: bool) -> bool:
    """Handle AI video commands extracted from the main dispatcher."""
    if args.command == "video-ai-transcribe":
        from ..ai_engine import ai_transcribe

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
        return True

    if args.command == "video-analyze":
        from ..ai_engine import analyze_video

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
        return True

    if args.command == "video-ai-upscale":
        from ..ai_engine import ai_upscale

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
        return True

    if args.command == "video-ai-stem-separation":
        from ..ai_engine import ai_stem_separation

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
        return True

    if args.command == "video-ai-scene-detect":
        from ..ai_engine import ai_scene_detect

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
        return True

    if args.command == "video-ai-color-grade":
        from ..ai_engine import ai_color_grade

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
        return True

    if args.command == "video-ai-remove-silence":
        from ..ai_engine import ai_remove_silence

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
        return True

    return False
