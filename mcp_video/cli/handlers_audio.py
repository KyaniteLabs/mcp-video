"""CLI handlers for audio synthesis and audio-video commands."""

from __future__ import annotations

from typing import Any

from rich.panel import Panel

from .common import _parse_json_arg, _with_spinner, output_json
from .formatting import console


def handle_audio_commands(args: Any, *, use_json: bool) -> bool:
    """Handle audio synthesis and spatial commands extracted from the main dispatcher."""
    if args.command == "audio-synthesize":
        from ..audio_engine import audio_synthesize

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
        return True

    if args.command == "audio-compose":
        from ..audio_engine import audio_compose

        tracks = _parse_json_arg(args.tracks, "tracks", json_mode=use_json)
        result = _with_spinner("Composing audio...", audio_compose, tracks, args.duration, args.output)
        if use_json:
            output_json({"success": True, "output_path": result})
        else:
            console.print(
                Panel(f"[bold green]Audio composed:[/bold green] {result}", border_style="green", title="Done")
            )
        return True

    if args.command == "audio-preset":
        from ..audio_engine import audio_preset

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
        return True

    if args.command == "audio-sequence":
        from ..audio_engine import audio_sequence

        sequence = _parse_json_arg(args.sequence, "sequence", json_mode=use_json)
        result = _with_spinner("Composing audio sequence...", audio_sequence, sequence, args.output)
        if use_json:
            output_json({"success": True, "output_path": result})
        else:
            console.print(
                Panel(f"[bold green]Audio sequence:[/bold green] {result}", border_style="green", title="Done")
            )
        return True

    if args.command == "audio-effects":
        from ..audio_engine import audio_effects

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
        return True

    if args.command == "video-add-generated-audio":
        from ..audio_engine import add_generated_audio

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
        return True

    if args.command == "video-audio-spatial":
        from ..ai_engine import audio_spatial

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
        return True

    return False
