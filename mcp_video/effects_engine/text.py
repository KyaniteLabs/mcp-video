"""Video effects and filters engine.

Visual effects using FFmpeg filters and PIL for custom processing.
"""

from __future__ import annotations

import logging
import os
import tempfile
import textwrap
from pathlib import Path
from typing import Any

from ..defaults import DEFAULT_SAFE_SUBTITLE_FONT_SIZE, DEFAULT_SUBTITLE_MAX_CHARS_PER_LINE, DEFAULT_SUBTITLE_MAX_LINES
from ..errors import InputFileError
from ..ffmpeg_helpers import _validate_input_path, _validate_output_path, _run_ffmpeg, _escape_ffmpeg_filter_value

logger = logging.getLogger(__name__)


def _wrap_subtitle_text_for_safe_area(
    text: str,
    max_chars_per_line: int = DEFAULT_SUBTITLE_MAX_CHARS_PER_LINE,
    max_lines: int = DEFAULT_SUBTITLE_MAX_LINES,
) -> str:
    """Wrap subtitle dialogue into a bounded safe-area block."""
    lines = textwrap.wrap(
        " ".join(text.split()),
        width=max_chars_per_line,
        break_long_words=False,
        break_on_hyphens=False,
    )
    if len(lines) > max_lines:
        kept = lines[:max_lines]
        kept[-1] = kept[-1].rstrip(" .,:;") + "…"
        return "\n".join(kept)
    return "\n".join(lines)


def _is_subtitle_timing_line(line: str) -> bool:
    return "-->" in line


def _is_srt_index_line(line: str) -> bool:
    return line.strip().isdigit()


def _is_webvtt_metadata_block(lines: list[str]) -> bool:
    first = lines[0].strip() if lines else ""
    if first == "WEBVTT":
        return True
    if first.startswith("NOTE"):
        return True
    return first in {"STYLE", "REGION"}


def _wrap_subtitle_payload_for_safe_area(
    payload: str,
    max_chars_per_line: int = DEFAULT_SUBTITLE_MAX_CHARS_PER_LINE,
    max_lines: int = DEFAULT_SUBTITLE_MAX_LINES,
) -> str:
    """Wrap SRT/VTT dialogue lines while preserving timing/index lines."""
    blocks = payload.strip().split("\n\n")
    wrapped_blocks: list[str] = []
    for block in blocks:
        lines = block.splitlines()
        if _is_webvtt_metadata_block(lines):
            wrapped_blocks.append(block)
            continue
        header = [line for line in lines if _is_srt_index_line(line) or _is_subtitle_timing_line(line)]
        dialogue = [line for line in lines if line not in header and line.strip() and line.strip() != "WEBVTT"]
        if not dialogue:
            wrapped_blocks.append(block)
            continue
        wrapped = _wrap_subtitle_text_for_safe_area(" ".join(dialogue), max_chars_per_line, max_lines)
        wrapped_blocks.append("\n".join([*header, wrapped]))
    return "\n\n".join(wrapped_blocks) + "\n"


def _prepare_safe_subtitle_file(subtitles: str, max_chars_per_line: int) -> str:
    """Return a wrapped temp subtitle file for SRT/VTT inputs."""
    suffix = Path(subtitles).suffix.lower()
    if suffix not in {".srt", ".vtt"}:
        return subtitles
    source = Path(subtitles).read_text(encoding="utf-8")
    wrapped = _wrap_subtitle_payload_for_safe_area(source, max_chars_per_line=max_chars_per_line)
    with tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8") as tmp:
        tmp.write(wrapped)
        return tmp.name


def _subtitle_filter(
    prepared_subtitles: str, font: str, size: int, color: str, outline: int, outline_color: str
) -> str:
    """Build a safe subtitles filter string."""
    safe_subtitles = _escape_ffmpeg_filter_value(prepared_subtitles)
    safe_font = _escape_ffmpeg_filter_value(font)
    safe_color = _escape_ffmpeg_filter_value(color)
    safe_outline_color = _escape_ffmpeg_filter_value(outline_color)
    return (
        f"subtitles={safe_subtitles}:force_style='"
        f"FontName={safe_font},"
        f"FontSize={size},"
        f"PrimaryColour={safe_color},"
        f"OutlineColour={safe_outline_color},"
        f"Outline={outline},"
        f"BorderStyle=1'"
    )


def text_animated(
    video: str,
    text: str,
    output: str,
    animation: str = "fade",
    font: str = "Arial",
    size: int = 48,
    color: str = "white",
    position: str = "center",
    start: float = 0,
    duration: float = 3.0,
) -> str:
    """Add animated text to video.

    Args:
        video: Input video path
        text: Text to display
        output: Output video path
        animation: "fade", "slide-up", "typewriter", "glitch"
        font: Font family
        size: Font size
        color: Text color
        position: Text position
        start: Start time in seconds
        duration: Display duration

    Returns:
        Path to output video
    """
    # Map positions
    pos_map = {
        "center": "(w-text_w)/2:(h-text_h)/2",
        "top": "(w-text_w)/2:20",
        "bottom": "(w-text_w)/2:h-text_h-20",
        "top-left": "20:20",
        "top-right": "w-text_w-20:20",
        "bottom-left": "20:h-text_h-20",
        "bottom-right": "w-text_w-20:h-text_h-20",
    }
    pos = pos_map.get(position, pos_map["center"])

    # Build animation expression
    fade_start = start
    fade_end = start + 0.5
    fade_out_start = start + duration - 0.5
    fade_out_end = start + duration

    if animation == "fade":
        # Fade in/out opacity
        alpha_expr = (
            f"if(lt(t,{fade_start}),0,"
            f"if(lt(t,{fade_end}),(t-{fade_start})/0.5,"
            f"if(lt(t,{fade_out_start}),1,"
            f"if(lt(t,{fade_out_end}),({fade_out_end}-t)/0.5,0))))"
        )
    elif animation == "slide-up":
        # Slide up from bottom
        y_offset = f"+50*(1-min(1,(t-{start})/0.3))"
        pos = pos.replace("(h-text_h)/2", f"(h-text_h)/2{y_offset}")
        alpha_expr = "1"
    elif animation == "typewriter":
        # True per-character reveal requires multiple drawtext filters with
        # staggered enable times (one per character) — too expensive for
        # arbitrary-length text. Using rapid linear fade-in as approximation:
        # text appears quickly (like a typewriter keystroke burst) then
        # stays visible. Distinct from "fade" which has slow in + slow out.
        # TODO: Implement proper typewriter via overlay clipping mask.
        reveal_duration = min(1.5, duration * 0.5)
        alpha_expr = f"if(lt(t,{start}),0,if(lt(t,{start}+{reveal_duration}),(t-{start})/{reveal_duration},1))"
    elif animation == "glitch":
        # Random glitch opacity
        alpha_expr = "if(random(0)*lt(mod(t,0.2),0.1),0.8,1)"
    else:
        alpha_expr = "1"

    # Escape text for FFmpeg — handle all filter-special characters
    safe_text = _escape_ffmpeg_filter_value(text)
    safe_font = _escape_ffmpeg_filter_value(font) if font is not None else font
    safe_color = _escape_ffmpeg_filter_value(color) if color is not None else color

    filter_complex = (
        f"drawtext=text='{safe_text}':font={safe_font}:fontsize={size}:fontcolor={safe_color}:"
        f"x={pos.split(':')[0]}:y={pos.split(':')[1]}:"
        f"enable='between(t\\,{start}\\,{start + duration})':"
        f"alpha='{alpha_expr}'"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video,
        "-vf",
        filter_complex,
        "-c:v",
        "libx264",
        "-c:a",
        "copy",
        "-pix_fmt",
        "yuv420p",
        "-crf",
        "23",
        output,
    ]

    _run_ffmpeg(cmd)

    return output


def text_subtitles(
    video: str,
    subtitles: str,
    output: str,
    style: dict[str, Any] | None = None,
) -> str:
    """Burn subtitles from SRT/VTT into video with styling.

    Args:
        video: Input video path
        subtitles: Subtitle file path (SRT or VTT)
        output: Output video path
        style: Style dict with keys:
            - font, size, color, outline, outline_color, background, position

    Returns:
        Path to output video
    """
    video = _validate_input_path(video)
    _validate_output_path(output)

    if not os.path.isfile(subtitles):
        raise InputFileError(f"Subtitles file not found: {subtitles}")

    style = style or {}

    # Build subtitle filter options
    font = style.get("font", "Arial")
    unsafe_layout = bool(style.get("allow_unsafe_layout", False))
    size = int(style.get("size", DEFAULT_SAFE_SUBTITLE_FONT_SIZE))
    if not unsafe_layout:
        size = min(size, DEFAULT_SAFE_SUBTITLE_FONT_SIZE)
    color = style.get("color", "white")
    outline = style.get("outline", 2)
    outline_color = style.get("outline_color", "black")
    max_chars_per_line = max(20, min(80, int(style.get("max_chars_per_line", DEFAULT_SUBTITLE_MAX_CHARS_PER_LINE))))

    # Convert hex colors to FFmpeg format
    if color.startswith("#"):
        color = f"0x{color[1:]}"
    if outline_color.startswith("#"):
        outline_color = f"0x{outline_color[1:]}"

    prepared_subtitles = _prepare_safe_subtitle_file(subtitles, max_chars_per_line)
    filter_complex = _subtitle_filter(prepared_subtitles, font, size, color, outline, outline_color)

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video,
        "-vf",
        filter_complex,
        "-c:v",
        "libx264",
        "-c:a",
        "copy",
        "-pix_fmt",
        "yuv420p",
        "-crf",
        "23",
        output,
    ]

    try:
        _run_ffmpeg(cmd)
    finally:
        if prepared_subtitles != subtitles:
            Path(prepared_subtitles).unlink(missing_ok=True)

    return output


# ---------------------------------------------------------------------------
# Motion Graphics
# ---------------------------------------------------------------------------
