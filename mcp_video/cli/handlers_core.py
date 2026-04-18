"""Core CLI command handlers."""

from __future__ import annotations

from typing import Any

from .common import _with_spinner, output_json
from .formatting import _format_doctor_text, _format_info_text, _format_thumbnail_text


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

    return False
