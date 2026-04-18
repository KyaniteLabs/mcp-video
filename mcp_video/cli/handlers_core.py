"""Core CLI command handlers."""

from __future__ import annotations

from typing import Any

from .common import _with_spinner, output_json
from .formatting import (
    _format_doctor_text,
    _format_edit_text,
    _format_info_text,
    _format_storyboard_text,
    _format_thumbnail_text,
)


def handle_initial_command(args: Any, *, use_json: bool) -> bool:
    """Handle initial low-risk commands extracted from ``__main__``.

    Returns True when a command was handled and no further dispatch is needed.
    """
    if args.command == "doctor":
        from ..doctor import run_diagnostics

        report = run_diagnostics()
        if use_json or args.json:
            output_json(report)
        else:
            _format_doctor_text(report)
        return True

    if args.command == "info":
        from ..engine import probe

        info = probe(args.input)
        if use_json:
            info_dict = info.model_dump() if hasattr(info, "model_dump") else info
            output_json({"success": True, "data": info_dict})
        else:
            _format_info_text(info)
        return True

    if args.command == "extract-frame":
        from ..engine import thumbnail

        result = _with_spinner(
            "Extracting frame...", thumbnail, args.input, timestamp=args.timestamp, output_path=args.output
        )
        if use_json:
            result_dict = result.model_dump() if hasattr(result, "model_dump") else result
            output_json({"success": True, **result_dict})
        else:
            _format_thumbnail_text(result)
        return True

    if args.command == "trim":
        from ..engine import trim

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
        return True

    if args.command == "merge":
        from ..engine import merge

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
        return True

    if args.command == "add-text":
        from ..engine import add_text

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
        return True

    if args.command == "add-audio":
        from ..engine import add_audio

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
        return True

    if args.command == "resize":
        from ..engine import resize

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
        return True

    if args.command == "speed":
        from ..engine import speed

        result = _with_spinner("Changing speed...", speed, args.input, factor=args.factor, output_path=args.output)
        if use_json:
            output_json(result)
        else:
            _format_edit_text(result)
        return True

    if args.command == "convert":
        from ..engine import convert

        result = _with_spinner(
            "Converting...", convert, args.input, format=args.fmt, quality=args.quality, output_path=args.output
        )
        if use_json:
            output_json(result)
        else:
            _format_edit_text(result)
        return True

    if args.command == "thumbnail":
        from ..engine import thumbnail

        result = thumbnail(args.input, timestamp=args.timestamp, output_path=args.output)
        if use_json:
            output_json(result)
        else:
            _format_edit_text(result)
        return True

    if args.command == "preview":
        from ..engine import preview

        result = _with_spinner(
            "Generating preview...", preview, args.input, output_path=args.output, scale_factor=args.scale
        )
        if use_json:
            output_json(result)
        else:
            _format_edit_text(result)
        return True

    if args.command == "storyboard":
        from ..engine import storyboard

        result = _with_spinner(
            "Extracting storyboard...", storyboard, args.input, output_dir=args.output_dir, frame_count=args.frames
        )
        if use_json:
            output_json(result)
        else:
            _format_storyboard_text(result)
        return True

    return False
