"""Runtime helper utilities for the FFmpeg engine."""

from __future__ import annotations

import base64
import os
import re
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from typing import Any

from .errors import (
    FFmpegNotFoundError,
    FFprobeNotFoundError,
    InputFileError,
    MCPVideoError,
    parse_ffmpeg_error,
)
from .limits import DEFAULT_CRF, DEFAULT_FFMPEG_TIMEOUT, DEFAULT_PRESET
from .models import NamedPosition, Position

# ---------------------------------------------------------------------------
# FFmpeg / FFprobe availability
# ---------------------------------------------------------------------------


def _find_executable(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise FFmpegNotFoundError() if name == "ffmpeg" else FFprobeNotFoundError()
    return path


_FFMPEG = _FFPROBE = ""
_AVAILABLE_FILTERS: set[str] | None = None


def _ffmpeg() -> str:
    global _FFMPEG
    if not _FFMPEG:
        _FFMPEG = _find_executable("ffmpeg")
    return _FFMPEG


def _ffprobe() -> str:
    global _FFPROBE
    if not _FFPROBE:
        _FFPROBE = _find_executable("ffprobe")
    return _FFPROBE


def _check_filter_available(name: str) -> bool:
    """Check if an FFmpeg filter is available."""
    global _AVAILABLE_FILTERS
    if _AVAILABLE_FILTERS is None:
        proc = subprocess.run(
            [_ffmpeg(), "-filters"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        _AVAILABLE_FILTERS = set()
        for line in proc.stdout.split("\n"):
            parts = line.strip().split()
            if len(parts) >= 3 and "->" in parts[2]:
                _AVAILABLE_FILTERS.add(parts[1])
    return name in _AVAILABLE_FILTERS


def _require_filter(name: str, feature: str) -> None:
    """Raise an error if a required FFmpeg filter is not available."""
    if not _check_filter_available(name):
        raise MCPVideoError(
            f"FFmpeg filter '{name}' is not available. {feature} requires FFmpeg "
            f"to be compiled with additional libraries.\n"
            f"Install with: brew install ffmpeg (macOS) or rebuild FFmpeg with "
            f"libfreetype/libass support.",
            error_type="dependency_error",
            code=f"missing_filter_{name}",
            suggested_action={
                "auto_fix": False,
                "description": f"Reinstall FFmpeg with {name} support. On macOS: brew reinstall ffmpeg",
            },
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _validate_input(path: str) -> None:
    if "\x00" in path:
        raise InputFileError(path, "Path contains null bytes")
    if not os.path.isfile(path):
        raise InputFileError(path)


def _sanitize_ffmpeg_number(value: Any, name: str) -> float:
    """Ensure a value is numeric before FFmpeg interpolation. Returns float(value)."""
    try:
        return float(value)
    except (TypeError, ValueError):
        raise MCPVideoError(
            f"Invalid {name}: expected number, got {type(value).__name__}",
            error_type="validation_error",
            code="invalid_parameter",
        ) from None


_CSS_COLOR_NAMES = frozenset(
    {
        "white",
        "black",
        "red",
        "green",
        "blue",
        "yellow",
        "cyan",
        "magenta",
        "orange",
        "purple",
        "pink",
        "brown",
        "gray",
        "grey",
        "silver",
        "gold",
        "navy",
        "teal",
        "maroon",
        "olive",
        "lime",
        "aqua",
        "fuchsia",
        "indigo",
        "violet",
        "coral",
        "salmon",
        "tomato",
        "khaki",
        "lavender",
        "turquoise",
        "tan",
        "wheat",
        "ivory",
        "beige",
        "linen",
        "snow",
        "mintcream",
        "azure",
        "aliceblue",
        "ghostwhite",
        "honeydew",
        "seashell",
        "whitesmoke",
        "oldlace",
        "floralwhite",
        "cornsilk",
        "lemonchiffon",
        "lightyellow",
        "lightcyan",
        "paleturquoise",
        "powderblue",
        "lightblue",
        "skyblue",
        "lightskyblue",
        "steelblue",
        "dodgerblue",
        "deepskyblue",
        "cornflowerblue",
        "royalblue",
        "mediumblue",
        "darkblue",
        "midnightblue",
        "slateblue",
        "darkslateblue",
        "mediumpurple",
        "blueviolet",
        "darkviolet",
        "darkorchid",
        "mediumorchid",
        "orchid",
        "plum",
        "mediumvioletred",
        "palevioletred",
        "hotpink",
        "deeppink",
        "lightpink",
        "rosybrown",
        "indianred",
        "firebrick",
        "darkred",
        "crimson",
        "orangered",
        "lightsalmon",
        "darksalmon",
        "lightcoral",
        "peachpuff",
        "bisque",
        "moccasin",
        "navajowhite",
        "sandybrown",
        "chocolate",
        "saddlebrown",
        "sienna",
        "burlywood",
        "peru",
        "darkgoldenrod",
        "goldenrod",
        "lightgoldenrod",
        "darkkhaki",
        "chartreuse",
        "greenyellow",
        "springgreen",
        "mediumspringgreen",
        "lawngreen",
        "darkgreen",
        "forestgreen",
        "seagreen",
        "darkseagreen",
        "lightgreen",
        "palegreen",
        "limegreen",
    }
)

_HEX_COLOR_RE = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
_FFMPEG_SPECIAL_CHARS = set(":=;'[]\\")


def _validate_color(color: str) -> None:
    """Validate a color value to prevent FFmpeg filter injection.

    Accepts CSS named colors (whitelist) and hex colors (#RGB, #RRGGBB, #RRGGBBAA).
    Rejects anything containing FFmpeg special characters.
    """
    if not isinstance(color, str):
        raise MCPVideoError(
            "invalid_color: value must be a string",
            error_type="validation_error",
            code="invalid_color",
        )
    if any(c in _FFMPEG_SPECIAL_CHARS for c in color):
        raise MCPVideoError(
            "invalid_color: contains FFmpeg special characters",
            error_type="validation_error",
            code="invalid_color",
        )
    if color.lower() in _CSS_COLOR_NAMES:
        return
    if _HEX_COLOR_RE.match(color):
        return
    raise MCPVideoError(
        "invalid_color: not a recognized CSS name or hex color",
        error_type="validation_error",
        code="invalid_color",
    )


def _validate_chroma_color(color: str) -> None:
    """Validate a chroma-key color in FFmpeg 0xRRGGBB hex format.

    Ensures the value is exactly 7 characters (``0x`` prefix + 6 hex digits)
    and contains only legal hex characters to prevent FFmpeg filter injection.
    """
    if not isinstance(color, str) or len(color) != 8 or not color.startswith("0x"):
        raise MCPVideoError(
            "color must be in 0xRRGGBB format (e.g. 0x00FF00)",
            error_type="validation_error",
            code="invalid_parameter",
        )
    hex_part = color[2:]
    if not all(c in "0123456789abcdefABCDEF" for c in hex_part):
        raise MCPVideoError(
            "color must contain only hex characters (0-9, a-f, A-F) after 0x prefix",
            error_type="validation_error",
            code="invalid_parameter",
        )


def _auto_output(input_path: str, suffix: str = "edited", ext: str | None = None) -> str:
    base, original_ext = os.path.splitext(input_path)
    ext = ext or original_ext or ".mp4"
    # Sanitize colons in base path — they break FFmpeg filter syntax
    # and are problematic on Windows
    safe_base = base.replace(":", "_")
    output = f"{safe_base}_{suffix}{ext}"
    # Prevent overwriting the input file
    if output == input_path:
        base_out, ext_out = os.path.splitext(output)
        output = f"{base_out}_2{ext_out}"
    return output


def _auto_output_dir(input_path: str, suffix: str = "output") -> str:
    base, _ = os.path.splitext(input_path)
    safe_base = base.replace(":", "_")
    return f"{safe_base}_{suffix}"


def _run_ffmpeg(args: list[str]) -> subprocess.CompletedProcess[str]:
    cmd = [_ffmpeg(), "-y", *args]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=DEFAULT_FFMPEG_TIMEOUT,
    )
    if proc.returncode != 0:
        raise parse_ffmpeg_error(proc.stderr)
    return proc


def _parse_ffmpeg_time(time_str: str) -> float:
    """Parse FFmpeg time= value (HH:MM:SS.xx) to seconds."""
    m = re.match(r"(\d+):(\d+):(\d+)\.(\d+)", time_str)
    if not m:
        return 0.0
    frac = m.group(4)
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3)) + int(frac) / (10 ** len(frac))


_TIME_RE = re.compile(r"time=(\d+:\d+:\d+\.\d+)")


def _run_ffmpeg_with_progress(
    args: list[str],
    estimated_duration: float | None = None,
    on_progress: Callable[[float], None] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run FFmpeg with real-time progress reporting.

    Parses FFmpeg stderr for time= output and calls on_progress(percent).
    Falls back to _run_ffmpeg if estimated_duration is not provided.
    """
    if estimated_duration is None or estimated_duration <= 0 or on_progress is None:
        return _run_ffmpeg(args)

    cmd = [_ffmpeg(), "-y", *args]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )

    stderr_lines: list[str] = []
    try:
        while True:
            line = proc.stderr.readline()
            if not line:
                break
            stderr_lines.append(line)

            match = _TIME_RE.search(line)
            if match:
                current_time = _parse_ffmpeg_time(match.group(1))
                pct = min(100.0, (current_time / estimated_duration) * 100)
                on_progress(pct)
    finally:
        proc.wait()

    stderr = "".join(stderr_lines)
    if proc.returncode != 0:
        raise parse_ffmpeg_error(stderr)

    # Report 100% on success
    on_progress(100.0)

    return subprocess.CompletedProcess(
        cmd,
        proc.returncode,
        "",
        stderr,
    )


def _generate_thumbnail_base64(video_path: str) -> str | None:
    """Generate a base64-encoded JPEG thumbnail from the first frame of a video.

    Returns base64 string or None if generation fails.
    """
    try:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp_path = tmp.name

        proc = subprocess.run(
            [
                _ffmpeg(),
                "-y",
                "-i",
                video_path,
                "-vframes",
                "1",
                "-q:v",
                "5",
                "-vf",
                "scale=320:-1",
                tmp_path,
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )

        if proc.returncode != 0 or not os.path.isfile(tmp_path):
            return None

        with open(tmp_path, "rb") as f:
            data = f.read()
        os.unlink(tmp_path)
        return base64.b64encode(data).decode("ascii")
    except Exception:
        return None


def _movflags_args(output_path: str) -> list[str]:
    """Return -movflags +faststart only for MP4/MOV containers."""
    ext = os.path.splitext(output_path)[1].lower()
    if ext in (".mp4", ".mov"):
        return ["-movflags", "+faststart"]
    return []


def _quality_args(
    crf: int | None = None,
    preset: str | None = None,
    default_crf: int = DEFAULT_CRF,
    default_preset: str = DEFAULT_PRESET,
) -> list[str]:
    """Build FFmpeg quality args [-preset, X, -crf, Y].

    If crf or preset are provided, they override the defaults.
    """
    return ["-preset", preset or default_preset, "-crf", str(crf if crf is not None else default_crf)]


def _validate_position(position: Position) -> None:
    """Validate position dict values to prevent FFmpeg filter injection.

    Only validates when position is a dict; named strings are safe by design.
    """
    if not isinstance(position, dict):
        return
    if "x_pct" in position and "y_pct" in position:
        for key in ("x_pct", "y_pct"):
            val = position[key]
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                raise MCPVideoError(
                    f"Invalid position: {position}. Must be a named position (top-left, top-center, etc.) or a dict with 'x'/'y' keys",
                    error_type="validation_error",
                    code="invalid_parameter",
                )
            if not (0.0 <= float(val) <= 1.0):
                raise MCPVideoError(
                    f"Invalid position: {position}. Must be a named position (top-left, top-center, etc.) or a dict with 'x'/'y' keys",
                    error_type="validation_error",
                    code="invalid_parameter",
                )
    elif "x" in position and "y" in position:
        for key in ("x", "y"):
            val = position[key]
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                raise MCPVideoError(
                    f"Invalid position: {position}. Must be a named position (top-left, top-center, etc.) or a dict with 'x'/'y' keys",
                    error_type="validation_error",
                    code="invalid_parameter",
                )
    else:
        raise MCPVideoError(
            "Position dict must have 'x'+'y' (pixels) or 'x_pct'+'y_pct' (percentage)",
            code="invalid_position_dict",
        )


def _position_coords(position: Position, width: int = 0, height: int = 0) -> str:
    """Return drawtext x,y expression for a named position or dict coords.

    Accepts:
    - Named positions: "top-left", "top-center", etc.
    - Pixel coordinates: {"x": 100, "y": 50}
    - Percentage: {"x_pct": 0.5, "y_pct": 0.5}
    """
    _validate_position(position)
    if isinstance(position, dict):
        if "x_pct" in position and "y_pct" in position:
            x_pct = position["x_pct"]
            y_pct = position["y_pct"]
            return f"x=w*{x_pct}-text_w/2:y=h*{y_pct}-text_h/2"
        elif "x" in position and "y" in position:
            return f"x={position['x']}:y={position['y']}"
        else:
            raise MCPVideoError(
                "Position dict must have 'x'+'y' (pixels) or 'x_pct'+'y_pct' (percentage)",
                code="invalid_position_dict",
            )

    # These expressions use FFmpeg's text_w/text_h variables
    mapping: dict[NamedPosition, str] = {
        "top-left": "x=10:y=10",
        "top-center": "x=(w-text_w)/2:y=10",
        "top-right": "x=w-text_w-10:y=10",
        "center-left": "x=10:y=(h-text_h)/2",
        "center": "x=(w-text_w)/2:y=(h-text_h)/2",
        "center-right": "x=w-text_w-10:y=(h-text_h)/2",
        "bottom-left": "x=10:y=h-text_h-10",
        "bottom-center": "x=(w-text_w)/2:y=h-text_h-10",
        "bottom-right": "x=w-text_w-10:y=h-text_h-10",
    }
    return mapping.get(position, mapping["center"])


def _resolve_position(
    position: Position,
    position_map: dict[NamedPosition, str],
    default: NamedPosition = "center",
) -> str:
    """Resolve a Position (named or dict) to an FFmpeg overlay coordinate string.

    Used by watermark, overlay_video, and similar overlay-based operations.
    """
    _validate_position(position)
    if isinstance(position, dict):
        if "x_pct" in position and "y_pct" in position:
            x_pct = position["x_pct"]
            y_pct = position["y_pct"]
            return f"(main_w*{x_pct}-overlay_w/2):(main_h*{y_pct}-overlay_h/2)"
        elif "x" in position and "y" in position:
            return f"{position['x']}:{position['y']}"
        else:
            raise MCPVideoError(
                "Position dict must have 'x'+'y' (pixels) or 'x_pct'+'y_pct' (percentage)",
                code="invalid_position_dict",
            )
    return position_map.get(position, position_map[default])


def _default_font() -> str:
    """Return a sensible default font path for the current OS."""
    import platform

    system = platform.system()
    if system == "Darwin":
        return "/System/Library/Fonts/Helvetica.ttc"
    elif system == "Windows":
        return "C\\:/Windows/Fonts/arial.ttf"
    else:
        # Linux — check common locations
        for p in [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        ]:
            if os.path.isfile(p):
                return p
        return "DejaVu Sans"


def _get_video_stream(data: dict) -> dict | None:
    for s in data.get("streams", []):
        if s.get("codec_type") == "video":
            return s
    return None


def _get_audio_stream(data: dict) -> dict | None:
    for s in data.get("streams", []):
        if s.get("codec_type") == "audio":
            return s
    return None


def _has_audio(data: dict) -> bool:
    return _get_audio_stream(data) is not None
