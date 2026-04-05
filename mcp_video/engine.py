"""FFmpeg engine — all video processing operations."""

from __future__ import annotations

import base64
import os
import re
import shutil
import subprocess
import tempfile
from typing import Any
from collections.abc import Callable

from .errors import (
    MCPVideoError,
    FFmpegNotFoundError,
    FFprobeNotFoundError,
    InputFileError,
    ProcessingError,
    parse_ffmpeg_error,
)
from .models import (
    ASPECT_RATIOS,
    PREVIEW_PRESETS,
    QUALITY_PRESETS,
    ColorPreset,
    EditResult,
    ExportFormat,
    FilterType,
    ImageSequenceResult,
    MetadataResult,
    NamedPosition,
    Position,
    QualityLevel,
    QualityMetricsResult,
    SceneDetectionResult,
    SplitLayout,
    StoryboardResult,
    SubtitleResult,
    ThumbnailResult,
    Timeline,
    TimelineImageOverlay,
    VideoInfo,
    WaveformResult,
)
from .ffmpeg_helpers import _escape_ffmpeg_filter_value, _run_ffprobe_json, _seconds_to_srt_time


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
        timeout=600,  # 10-minute max
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
    default_crf: int = 23,
    default_preset: str = "fast",
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


# ---------------------------------------------------------------------------
# Probe
# ---------------------------------------------------------------------------


def probe(path: str) -> VideoInfo:
    """Get metadata about a video file using ffprobe."""
    _validate_input(path)
    data = _run_ffprobe_json(path)

    vs = _get_video_stream(data)
    if vs is None:
        raise InputFileError(path, "No video stream found")

    # Duration
    duration = float(data.get("format", {}).get("duration", 0) or vs.get("duration", 0))

    # Resolution
    width = int(vs.get("width", 0))
    height = int(vs.get("height", 0))

    # FPS — r_frame_rate is "num/den"
    rfr = vs.get("r_frame_rate", "30/1")
    try:
        if "/" in rfr:
            num, den = rfr.split("/")
            den_val = float(den)
            fps = float(num) / den_val if den_val != 0 else 30.0
        else:
            fps = float(rfr) if float(rfr) != 0 else 30.0
    except (ValueError, ZeroDivisionError):
        fps = 30.0

    # Codecs
    codec = vs.get("codec_name", "unknown")
    audio_s = _get_audio_stream(data)
    audio_codec = audio_s.get("codec_name") if audio_s else None
    audio_sr = int(audio_s.get("sample_rate", 0)) if audio_s else None

    # Bitrate / size
    fmt = data.get("format", {})
    bitrate = int(fmt.get("bit_rate", 0)) or None
    size_bytes = int(fmt.get("size", 0)) or None
    fmt_name = fmt.get("format_name")

    return VideoInfo(
        path=path,
        duration=duration,
        width=width,
        height=height,
        fps=fps,
        codec=codec,
        audio_codec=audio_codec,
        audio_sample_rate=audio_sr,
        bitrate=bitrate,
        size_bytes=size_bytes,
        format=fmt_name,
    )


def get_duration(path: str) -> float:
    """Get duration of a video in seconds."""
    return probe(path).duration


# ---------------------------------------------------------------------------
# Normalize — convert to H.264/AAC for editing
# ---------------------------------------------------------------------------


def normalize(input_path: str, output_path: str | None = None) -> str:
    """Normalize a video to H.264 video + AAC audio for reliable editing."""
    _validate_input(input_path)
    output = output_path or _auto_output(input_path, "normalized")
    _run_ffmpeg(
        [
            "-i",
            input_path,
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            *_movflags_args(output),
            output,
        ]
    )
    return output


# ---------------------------------------------------------------------------
# Core operations
# ---------------------------------------------------------------------------


def trim(
    input_path: str,
    start: str | float = 0,
    duration: str | float | None = None,
    end: str | float | None = None,
    output_path: str | None = None,
) -> EditResult:
    """Trim a video by start time and duration or end time."""
    _validate_input(input_path)
    output = output_path or _auto_output(input_path, "trimmed")

    args = []
    if start:
        args.extend(["-ss", str(start)])
    args.extend(["-i", input_path])
    if duration:
        args.extend(["-t", str(duration)])
    elif end:
        args.extend(["-to", str(end)])
    args.extend(
        [
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            *_movflags_args(output),
            output,
        ]
    )
    _run_ffmpeg(args)

    info = probe(output)
    return EditResult(
        output_path=output,
        duration=info.duration,
        resolution=info.resolution,
        size_mb=info.size_mb,
        format="mp4",
        operation="trim",
    )


def merge(
    clips: list[str],
    output_path: str | None = None,
    transition: str | None = None,
    transitions: list[str] | None = None,
    transition_duration: float = 1.0,
) -> EditResult:
    """Merge multiple clips into one video. Auto-normalizes if needed.

    Args:
        clips: List of video file paths.
        output_path: Output file path.
        transition: Single transition type for all clip pairs (backward compat).
        transitions: Per-pair transition types (one per boundary, len = len(clips)-1).
            If shorter than clip pairs, the last type is repeated.
        transition_duration: Duration of each transition in seconds.
    """
    if not clips:
        raise InputFileError("", "No clips provided for merge")

    for c in clips:
        _validate_input(c)

    # Check if all clips have same resolution — if not, normalize
    infos = [probe(c) for c in clips]
    resolutions = {i.resolution for i in infos}
    codecs = {i.codec for i in infos}

    needs_normalize = len(resolutions) > 1 or len(codecs) > 1
    target_w = max(i.width for i in infos)
    target_h = max(i.height for i in infos)

    working_clips: list[str] = []
    tmpdir = tempfile.mkdtemp(prefix="mcp_video_")

    try:
        if needs_normalize:
            for i, clip in enumerate(clips):
                norm_path = os.path.join(tmpdir, f"clip_{i:04d}.mp4")
                _run_ffmpeg(
                    [
                        "-i",
                        clip,
                        "-vf",
                        f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2",
                        "-c:v",
                        "libx264",
                        "-preset",
                        "fast",
                        "-crf",
                        "23",
                        "-c:a",
                        "aac",
                        "-b:a",
                        "128k",
                        "-r",
                        "30",
                        "-ar",
                        "44100",
                        "-ac",
                        "2",
                        norm_path,
                    ]
                )
                working_clips.append(norm_path)
        else:
            working_clips = list(clips)

        output = output_path or _auto_output(clips[0], "merged")

        # Resolve transition types list
        transition_types: list[str] | None = None
        if transitions and len(working_clips) > 1:
            transition_types = list(transitions)
        elif transition and len(working_clips) > 1:
            transition_types = [transition] * (len(working_clips) - 1)

        if transition_types and len(working_clips) > 1:
            # Use xfade filter for transitions
            _merge_with_transitions(working_clips, output, transition_types, transition_duration)
        else:
            # Simple concat
            concat_file = os.path.join(tmpdir, "concat.txt")
            with open(concat_file, "w") as f:
                for clip in working_clips:
                    # Escape single quotes for FFmpeg concat demuxer
                    abs_path = os.path.abspath(clip).replace("'", "'\\''")
                    f.write(f"file '{abs_path}'\n")
            _run_ffmpeg(
                ["-f", "concat", "-safe", "0", "-i", concat_file, "-c", "copy", *_movflags_args(output), output]
            )

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    info = probe(output)
    return EditResult(
        output_path=output,
        duration=info.duration,
        resolution=info.resolution,
        size_mb=info.size_mb,
        format="mp4",
        operation="merge",
    )


def _merge_with_transitions(
    clips: list[str],
    output: str,
    transition_types: list[str],
    transition_duration: float,
) -> None:
    """Merge clips with xfade transitions between them.

    Args:
        transition_types: One transition type per clip pair (len = len(clips)-1).
            If shorter, the last type is repeated.
    """
    n = len(clips)
    if n < 2:
        _run_ffmpeg(["-i", clips[0], "-c", "copy", output])
        return

    # Pad transition_types if shorter than clip pairs
    pairs = n - 1
    if len(transition_types) < pairs:
        last = transition_types[-1] if transition_types else "fade"
        transition_types = transition_types + [last] * (pairs - len(transition_types))

    # xfade offset calculation
    offsets: list[float] = []
    cumulative = 0.0
    for i in range(pairs):
        clip_dur = get_duration(clips[i])
        if transition_duration >= clip_dur:
            raise MCPVideoError(
                f"Transition duration ({transition_duration}s) must be less than "
                f"clip {i + 1} duration ({clip_dur:.1f}s)",
                code="transition_too_long",
            )
        cumulative += clip_dur - transition_duration
        offsets.append(cumulative)

    # Build complex filter
    inputs = []
    for clip in clips:
        inputs.extend(["-i", clip])

    # Build filter chain with per-pair transition types
    filter_parts = []
    labels: list[str] = []
    for i in range(n):
        labels.append(f"{i}:v")

    for i in range(pairs):
        in1 = labels[i]
        in2 = labels[i + 1]
        out = f"xt{i}" if i < pairs - 1 else "vout"
        xfade_type = transition_types[i].replace("-", "")
        filter_parts.append(
            f"[{in1}][{in2}]xfade=transition={xfade_type}:offset={offsets[i]:.3f}:duration={transition_duration:.3f}[{out}]"
        )
        labels[i + 1] = out

    filter_str = ";".join(filter_parts)

    # Audio: only include if clips have audio streams
    has_audio = any(probe(c).audio_codec is not None for c in clips)
    if has_audio:
        audio_parts = []
        for i in range(n):
            audio_parts.append(f"[{i}:a]")
        audio_filter = "".join(audio_parts) + f"concat=n={n}:v=0:a=1[aout]"
        filter_complex = f"{filter_str};{audio_filter}"
        map_args = ["-map", "[vout]", "-map", "[aout]"]
        audio_codec_args = ["-c:a", "aac", "-b:a", "128k"]
    else:
        filter_complex = filter_str
        map_args = ["-map", "[vout]"]
        audio_codec_args = ["-an"]

    _run_ffmpeg(
        [
            *inputs,
            "-filter_complex",
            filter_complex,
            *map_args,
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "23",
            *audio_codec_args,
            *_movflags_args(output),
            output,
        ]
    )


def add_text(
    input_path: str,
    text: str,
    position: Position = "top-center",
    font: str | None = None,
    size: int = 48,
    color: str = "white",
    shadow: bool = True,
    start_time: float | None = None,
    duration: float | None = None,
    output_path: str | None = None,
    crf: int | None = None,
    preset: str | None = None,
) -> EditResult:
    """Overlay text on a video."""
    _validate_input(input_path)
    _require_filter("drawtext", "Text overlay")
    _validate_color(color)
    output = output_path or _auto_output(input_path, "titled")

    coords = _position_coords(position)
    fontfile = font or _default_font()

    # Validate font file exists when explicitly provided
    if font is not None and not os.path.isfile(fontfile):
        raise FileNotFoundError(f"Font file not found: {fontfile}")

    # Escape font path for FFmpeg filter syntax
    escaped_fontfile = _escape_ffmpeg_filter_value(fontfile)

    # Escape FFmpeg drawtext special characters
    # Colons and backslashes must be escaped even inside single quotes
    # because FFmpeg parses filter options as key=value pairs with : delimiters
    escaped_text = (
        text.replace("\\", "\\\\")
        .replace("'", "'\\''")
        .replace(":", "\\:")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace(";", "\\;")
    )

    filter_parts = [
        f"drawtext=text='{escaped_text}'",
        f"fontsize={size}",
        f"fontcolor={color}",
        f"fontfile={escaped_fontfile}",
        coords,
    ]

    if shadow:
        filter_parts.append("shadowcolor=black@0.5")
        filter_parts.append("shadowx=2")
        filter_parts.append("shadowy=2")

    if start_time is not None and duration is not None:
        filter_parts.append(f"enable='between(t\\,{start_time}\\,{start_time + duration})'")
    elif start_time is not None:
        filter_parts.append(f"enable='gte(t\\,{start_time})'")

    vf = ":".join(filter_parts)

    _run_ffmpeg(
        [
            "-i",
            input_path,
            "-vf",
            vf,
            "-c:v",
            "libx264",
            *_quality_args(crf=crf, preset=preset),
            "-c:a",
            "copy",
            *_movflags_args(output),
            output,
        ]
    )

    info = probe(output)
    return EditResult(
        output_path=output,
        duration=info.duration,
        resolution=info.resolution,
        size_mb=info.size_mb,
        format="mp4",
        operation="add_text",
    )


def add_audio(
    video_path: str,
    audio_path: str,
    volume: float = 1.0,
    fade_in: float = 0.0,
    fade_out: float = 0.0,
    mix: bool = False,
    start_time: float | None = None,
    output_path: str | None = None,
) -> EditResult:
    """Add or replace audio track on a video."""
    _validate_input(video_path)
    _validate_input(audio_path)
    output = output_path or _auto_output(video_path, "audio")

    video_info = probe(video_path)

    if mix and _has_audio(_run_ffprobe_json(video_path)):
        # Mix new audio with existing audio
        audio_filters: list[str] = []
        if volume != 1.0:
            audio_filters.append(f"volume={volume}")
        if fade_in > 0:
            audio_filters.append(f"afade=t=in:st=0:d={fade_in}")
        if fade_out > 0:
            audio_filters.append(f"afade=t=out:st={video_info.duration - fade_out}:d={fade_out}")

        af = ",".join(audio_filters) if audio_filters else "anull"

        delay = ""
        if start_time:
            delay = f"[1:a]adelay={int(start_time * 1000)}|{int(start_time * 1000)},"

        filter_complex = f"[0:a]anull[a0];{delay}[1:a]{af}[a1];[a0][a1]amix=inputs=2:duration=longest[aout]"

        _run_ffmpeg(
            [
                "-i",
                video_path,
                "-i",
                audio_path,
                "-filter_complex",
                filter_complex,
                "-map",
                "0:v",
                "-map",
                "[aout]",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                *_movflags_args(output),
                output,
            ]
        )
    else:
        # Replace audio (or add if no existing audio)
        args = ["-i", video_path, "-i", audio_path]

        if start_time:
            args.extend(["-filter_complex", f"[1:a]adelay={int(start_time * 1000)}|{int(start_time * 1000)}[a]"])
            args.extend(["-map", "0:v:0", "-map", "[a]"])
        else:
            args.extend(["-map", "0:v:0", "-map", "1:a:0"])

        audio_filters = []
        if volume != 1.0:
            audio_filters.append(f"volume={volume}")
        if fade_in > 0:
            audio_filters.append(f"afade=t=in:st=0:d={fade_in}")
        if fade_out > 0:
            audio_filters.append(f"afade=t=out:st={video_info.duration - fade_out}:d={fade_out}")

        if audio_filters:
            args.extend(["-af", ",".join(audio_filters)])

        args.extend(["-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest", *_movflags_args(output), output])
        _run_ffmpeg(args)

    info = probe(output)
    return EditResult(
        output_path=output,
        duration=info.duration,
        resolution=info.resolution,
        size_mb=info.size_mb,
        format="mp4",
        operation="add_audio",
    )


def resize(
    input_path: str,
    width: int | None = None,
    height: int | None = None,
    aspect_ratio: str | None = None,
    quality: QualityLevel = "high",
    output_path: str | None = None,
) -> EditResult:
    """Resize a video. Use aspect_ratio for preset sizes (e.g. '9:16')."""
    _validate_input(input_path)

    info = probe(input_path)
    if info.width == 0 or info.height == 0:
        raise MCPVideoError(
            "Cannot resize: video has zero dimensions",
            error_type="processing_error",
            code="invalid_input",
        )

    if aspect_ratio and aspect_ratio in ASPECT_RATIOS:
        w, h = ASPECT_RATIOS[aspect_ratio]
    elif aspect_ratio:
        raise MCPVideoError(
            f"Unknown aspect ratio: {aspect_ratio}. Available: {', '.join(ASPECT_RATIOS.keys())}",
            error_type="input_error",
            code="invalid_aspect_ratio",
        )
    elif width and height:
        w, h = width, height
    elif width:
        ratio = info.height / info.width
        w, h = width, int(width * ratio)
    elif height:
        ratio = info.width / info.height
        w, h = int(height * ratio), height
    else:
        raise MCPVideoError("resize requires width+height, aspect_ratio, or single dimension")

    preset = QUALITY_PRESETS[quality]
    output = output_path or _auto_output(input_path, f"{w}x{h}")

    # Scale to fit within target, then pad to exact dimensions
    vf = f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black"

    _run_ffmpeg(
        [
            "-i",
            input_path,
            "-vf",
            vf,
            "-c:v",
            "libx264",
            "-crf",
            str(preset["crf"]),
            "-preset",
            preset["preset"],
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            *_movflags_args(output),
            output,
        ]
    )

    info = probe(output)
    return EditResult(
        output_path=output,
        duration=info.duration,
        resolution=info.resolution,
        size_mb=info.size_mb,
        format="mp4",
        operation="resize",
    )


def convert(
    input_path: str,
    format: ExportFormat = "mp4",
    quality: QualityLevel = "high",
    output_path: str | None = None,
    on_progress: Callable[[float], None] | None = None,
    two_pass: bool = False,
    target_bitrate: int | None = None,
) -> EditResult:
    """Convert video to a different format."""
    _validate_input(input_path)

    if two_pass and format not in ("mp4", "mov"):
        raise MCPVideoError(
            f"Two-pass encoding is only supported for mp4 and mov formats, got '{format}'",
            error_type="validation_error",
            code="two_pass_unsupported_format",
        )
    if two_pass and target_bitrate is None:
        raise MCPVideoError(
            "Two-pass encoding requires target_bitrate to be set",
            error_type="validation_error",
            code="two_pass_needs_bitrate",
        )

    preset = QUALITY_PRESETS[quality]
    ext = f".{format}" if not format.startswith(".") else format
    output = output_path or _auto_output(input_path, format, ext=ext)

    # Get input duration for progress estimation
    input_info = probe(input_path)

    if two_pass and target_bitrate:
        # Two-pass encoding for better quality at target bitrate
        passlogdir = tempfile.mkdtemp(prefix="mcp_video_2pass_")
        try:
            passlogfile = os.path.join(passlogdir, "pass")
            _run_ffmpeg(
                [
                    "-i",
                    input_path,
                    "-c:v",
                    "libx264",
                    "-b:v",
                    f"{target_bitrate}k",
                    "-pass",
                    "1",
                    "-passlogfile",
                    passlogfile,
                    "-an",
                    "-f",
                    "null",
                    os.devnull,
                ]
            )
            _run_ffmpeg(
                [
                    "-i",
                    input_path,
                    "-c:v",
                    "libx264",
                    "-b:v",
                    f"{target_bitrate}k",
                    "-pass",
                    "2",
                    "-passlogfile",
                    passlogfile,
                    "-preset",
                    preset["preset"],
                    "-c:a",
                    "aac",
                    "-b:a",
                    "128k",
                    *_movflags_args(output),
                    output,
                ]
            )
        finally:
            shutil.rmtree(passlogdir, ignore_errors=True)
    elif format == "mp4":
        _run_ffmpeg_with_progress(
            [
                "-i",
                input_path,
                "-c:v",
                "libx264",
                "-crf",
                str(preset["crf"]),
                "-preset",
                preset["preset"],
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-movflags",
                "+faststart",
                output,
            ],
            estimated_duration=input_info.duration,
            on_progress=on_progress,
        )
    elif format == "webm":
        _run_ffmpeg_with_progress(
            [
                "-i",
                input_path,
                "-c:v",
                "libvpx-vp9",
                "-crf",
                str(preset["crf"]),
                "-b:v",
                "0",
                "-c:a",
                "libopus",
                output,
            ],
            estimated_duration=input_info.duration,
            on_progress=on_progress,
        )
    elif format == "mov":
        _run_ffmpeg_with_progress(
            [
                "-i",
                input_path,
                "-c:v",
                "libx264",
                "-crf",
                str(preset["crf"]),
                "-preset",
                preset["preset"],
                "-c:a",
                "pcm_s16le",
                output,
            ],
            estimated_duration=input_info.duration,
            on_progress=on_progress,
        )
    elif format == "gif":
        # Two-pass palette-based GIF generation for quality
        # Scale by quality level: low=320, medium=480, high=640, ultra=800
        gif_scale = {"low": 320, "medium": 480, "high": 640, "ultra": 800}
        width = gif_scale.get(quality, 480)
        tmpdir = tempfile.mkdtemp(prefix="mcp_video_gif_")
        try:
            palette = os.path.join(tmpdir, "palette.png")
            _run_ffmpeg(
                [
                    "-i",
                    input_path,
                    "-vf",
                    f"fps=15,scale={width}:-1:flags=lanczos,palettegen",
                    "-y",
                    palette,
                ]
            )
            _run_ffmpeg_with_progress(
                [
                    "-i",
                    input_path,
                    "-i",
                    palette,
                    "-lavfi",
                    f"fps=15,scale={width}:-1:flags=lanczos [x]; [x][1:v] paletteuse",
                    "-y",
                    output,
                ],
                estimated_duration=input_info.duration,
                on_progress=on_progress,
            )
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
    else:
        raise MCPVideoError(f"Unsupported format: {format}", code="unsupported_format")

    thumb_b64 = _generate_thumbnail_base64(output) if format != "gif" else None

    if os.path.isfile(output):
        size_mb = os.path.getsize(output) / (1024 * 1024)
        if format != "gif":
            info = probe(output)
            return EditResult(
                output_path=output,
                duration=info.duration,
                resolution=info.resolution,
                size_mb=round(size_mb, 2),
                format=format,
                operation="convert",
                progress=100.0,
                thumbnail_base64=thumb_b64,
            )
    else:
        size_mb = None

    return EditResult(
        output_path=output,
        size_mb=round(size_mb, 2) if size_mb else None,
        format=format,
        operation="convert",
        progress=100.0,
        thumbnail_base64=thumb_b64,
    )


def speed(
    input_path: str,
    factor: float = 1.0,
    output_path: str | None = None,
) -> EditResult:
    """Change playback speed. factor > 1 = faster, < 1 = slower."""
    _validate_input(input_path)
    if factor <= 0:
        raise MCPVideoError("Speed factor must be positive")

    output = output_path or _auto_output(input_path, f"speed_{factor}x")

    # Use setpts for video, atempo for audio
    video_filter = f"setpts={1 / factor}*PTS"
    audio_filter = f"atempo={factor}"

    # atempo only supports 0.5 to 100.0; chain if needed
    MAX_SPEED_CHAIN_COUNT = 20
    if factor < 0.5:
        chain_count = 2
        while factor ** (1 / chain_count) < 0.5:
            chain_count += 1
            if chain_count > MAX_SPEED_CHAIN_COUNT:
                raise MCPVideoError(
                    "Speed factor too extreme: would require more than 20 atempo filters",
                    error_type="validation_error",
                    code="invalid_parameter",
                )
        tempo_val = factor ** (1 / chain_count)
        audio_filter = ",".join([f"atempo={tempo_val}"] * chain_count)
    elif factor > 100:
        chain_count = 2
        while factor ** (1 / chain_count) > 100:
            chain_count += 1
            if chain_count > MAX_SPEED_CHAIN_COUNT:
                raise MCPVideoError(
                    "Speed factor too extreme: would require more than 20 atempo filters",
                    error_type="validation_error",
                    code="invalid_parameter",
                )
        tempo_val = factor ** (1 / chain_count)
        audio_filter = ",".join([f"atempo={tempo_val}"] * chain_count)

    # Check if input has audio
    info = probe(input_path)
    has_audio = info.audio_codec is not None

    if has_audio:
        _run_ffmpeg(
            [
                "-i",
                input_path,
                "-filter_complex",
                f"[0:v]{video_filter}[v];[0:a]{audio_filter}[a]",
                "-map",
                "[v]",
                "-map",
                "[a]",
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "23",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                *_movflags_args(output),
                output,
            ]
        )
    else:
        _run_ffmpeg(
            [
                "-i",
                input_path,
                "-vf",
                video_filter,
                "-an",
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "23",
                *_movflags_args(output),
                output,
            ]
        )

    info = probe(output)
    return EditResult(
        output_path=output,
        duration=info.duration,
        resolution=info.resolution,
        size_mb=info.size_mb,
        format="mp4",
        operation="speed",
    )


def thumbnail(
    input_path: str,
    timestamp: float | None = None,
    output_path: str | None = None,
) -> ThumbnailResult:
    """Extract a single frame from a video."""
    _validate_input(input_path)

    if timestamp is None:
        # Grab frame at 10% of video duration
        dur = get_duration(input_path)
        timestamp = dur * 0.1
    else:
        # Clamp to valid range
        dur = get_duration(input_path)
        timestamp = min(timestamp, dur * 0.99)

    output = output_path or _auto_output(input_path, f"frame_{timestamp:.1f}s", ext=".jpg")

    _run_ffmpeg(
        [
            "-ss",
            str(timestamp),
            "-i",
            input_path,
            "-vframes",
            "1",
            "-q:v",
            "2",
            "-y",
            output,
        ]
    )

    return ThumbnailResult(
        frame_path=output,
        timestamp=timestamp,
    )


def preview(
    input_path: str,
    output_path: str | None = None,
    scale_factor: int = 4,
) -> EditResult:
    """Generate a fast low-resolution preview for quick review."""
    _validate_input(input_path)
    if scale_factor < 1:
        raise MCPVideoError("scale_factor must be at least 1", code="invalid_scale_factor")
    info = probe(input_path)

    w = max(info.width // scale_factor, 320)
    h = max(info.height // scale_factor, 240)

    output = output_path or _auto_output(input_path, "preview")

    _run_ffmpeg(
        [
            "-i",
            input_path,
            "-vf",
            f"scale={w}:{h}",
            "-c:v",
            "libx264",
            "-crf",
            str(PREVIEW_PRESETS["crf"]),
            "-preset",
            PREVIEW_PRESETS["preset"],
            "-c:a",
            "aac",
            "-b:a",
            "64k",
            "-ac",
            "2",
            *_movflags_args(output),
            output,
        ]
    )

    result_info = probe(output)
    return EditResult(
        output_path=output,
        duration=result_info.duration,
        resolution=result_info.resolution,
        size_mb=result_info.size_mb,
        format="mp4",
        operation="preview",
    )


def storyboard(
    input_path: str,
    output_dir: str | None = None,
    frame_count: int = 8,
) -> StoryboardResult:
    """Extract key frames and create a storyboard grid for human review."""
    _validate_input(input_path)
    if frame_count < 1:
        raise MCPVideoError("frame_count must be at least 1", code="invalid_frame_count")
    dur = get_duration(input_path)

    out_dir = output_dir or _auto_output_dir(input_path, "storyboard")
    os.makedirs(out_dir, exist_ok=True)

    frame_paths: list[str] = []
    interval = dur / (frame_count + 1)

    for i in range(frame_count):
        ts = interval * (i + 1)
        frame_name = f"frame_{i + 1:02d}_{ts:.1f}s.jpg"
        frame_path = os.path.join(out_dir, frame_name)

        _run_ffmpeg(
            [
                "-ss",
                str(ts),
                "-i",
                input_path,
                "-vframes",
                "1",
                "-q:v",
                "2",
                "-y",
                frame_path,
            ]
        )
        frame_paths.append(frame_path)

    # Create storyboard grid using FFmpeg
    grid_path = os.path.join(out_dir, "storyboard_grid.jpg")
    if len(frame_paths) >= 2:
        # Create a grid of frames
        cols = min(4, len(frame_paths))
        rows = (len(frame_paths) + cols - 1) // cols

        # Use FFmpeg to tile the images
        # Build a complex filter for the grid
        inputs = []
        for fp in frame_paths:
            inputs.extend(["-i", fp])

        # Normalize all frames to same size
        filter_parts = []
        for i, _fp in enumerate(frame_paths):
            filter_parts.append(
                f"[{i}:v]scale=480:270:force_original_aspect_ratio=decrease,pad=480:270:(ow-iw)/2:(oh-ih)/2[s{i}]"
            )

        # Stack horizontally first, then vertically
        # Row 0: [s0][s1][s2][s3]hstack=inputs=4[r0]
        # Row 1: [s4][s5][s6][s7]hstack=inputs=4[r1]
        # Final: [r0][r1]vstack=inputs=2[vout]

        row_labels: list[str] = []
        for row in range(rows):
            start = row * cols
            end = min(start + cols, len(frame_paths))
            actual_cols = end - start
            input_labels = "".join(f"[s{j}]" for j in range(start, end))
            row_label = f"r{row}"
            filter_parts.append(f"{input_labels}hstack=inputs={actual_cols}[{row_label}]")
            row_labels.append(f"[{row_label}]")

        vstack_inputs = "".join(row_labels)
        filter_parts.append(f"{vstack_inputs}vstack=inputs={rows}[vout]")

        filter_str = ";".join(filter_parts)

        try:
            _run_ffmpeg([*inputs, "-filter_complex", filter_str, "-map", "[vout]", "-q:v", "2", "-y", grid_path])
        except ProcessingError:
            # Grid creation failed — frames are still useful individually
            grid_path = None
    elif len(frame_paths) == 1:
        shutil.copy2(frame_paths[0], grid_path)
    else:
        grid_path = None

    return StoryboardResult(
        frames=frame_paths,
        grid=grid_path,
        count=len(frame_paths),
    )


def subtitles(
    input_path: str,
    subtitle_path: str,
    output_path: str | None = None,
    style: str = "FontSize=22,PrimaryColour=&Hffffff&,OutlineColour=&H000000&,Outline=2,Shadow=1",
) -> EditResult:
    """Burn subtitles (SRT/VTT) into a video."""
    _validate_input(input_path)
    _validate_input(subtitle_path)
    _require_filter("subtitles", "Subtitle burn-in")
    output = output_path or _auto_output(input_path, "subtitled")

    # Escape special characters for FFmpeg subtitle filter path
    escaped_sub_path = _escape_ffmpeg_filter_value(subtitle_path)
    escaped_style = _escape_ffmpeg_filter_value(style)

    _run_ffmpeg(
        [
            "-i",
            input_path,
            "-vf",
            f"subtitles={escaped_sub_path}:force_style={escaped_style}",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "23",
            "-c:a",
            "copy",
            *_movflags_args(output),
            output,
        ]
    )

    info = probe(output)
    return EditResult(
        output_path=output,
        duration=info.duration,
        resolution=info.resolution,
        size_mb=info.size_mb,
        format="mp4",
        operation="subtitles",
    )


def watermark(
    input_path: str,
    image_path: str,
    position: Position = "bottom-right",
    opacity: float = 0.7,
    margin: int = 20,
    output_path: str | None = None,
    crf: int | None = None,
    preset: str | None = None,
) -> EditResult:
    """Add an image watermark to a video."""
    _validate_input(input_path)
    _validate_input(image_path)
    output = output_path or _auto_output(input_path, "watermarked")

    # Position expressions for the overlay
    position_map: dict[NamedPosition, str] = {
        "top-left": f"{margin}:{margin}",
        "top-center": "(main_w-overlay_w)/2:{margin}",
        "top-right": f"main_w-overlay_w-{margin}:{margin}",
        "center-left": f"{margin}:(main_h-overlay_h)/2",
        "center": "(main_w-overlay_w)/2:(main_h-overlay_h)/2",
        "center-right": f"main_w-overlay_w-{margin}:(main_h-overlay_h)/2",
        "bottom-left": f"{margin}:main_h-overlay_h-{margin}",
        "bottom-center": "(main_w-overlay_w)/2:main_h-overlay_h-{margin}",
        "bottom-right": f"main_w-overlay_w-{margin}:main_h-overlay_h-{margin}",
    }

    overlay_pos = _resolve_position(position, position_map, "bottom-right")
    # Format opacity for FFmpeg (0.0 to 1.0)
    opacity_fmt = f"{opacity:.2f}"

    _run_ffmpeg(
        [
            "-i",
            input_path,
            "-i",
            image_path,
            "-filter_complex",
            f"[1:v]format=rgba,colorchannelmixer=aa={opacity_fmt}[wm];[0:v][wm]overlay={overlay_pos}",
            "-c:v",
            "libx264",
            *_quality_args(crf=crf, preset=preset),
            "-c:a",
            "copy",
            *_movflags_args(output),
            output,
        ]
    )

    info = probe(output)
    return EditResult(
        output_path=output,
        duration=info.duration,
        resolution=info.resolution,
        size_mb=info.size_mb,
        format="mp4",
        operation="watermark",
    )


def crop(
    input_path: str,
    width: int,
    height: int,
    x: int | None = None,
    y: int | None = None,
    output_path: str | None = None,
) -> EditResult:
    """Crop a video to a rectangular region."""
    _validate_input(input_path)
    if width <= 0 or height <= 0:
        raise MCPVideoError("Crop dimensions must be positive", code="invalid_crop")

    info = probe(input_path)
    if width > info.width or height > info.height:
        raise MCPVideoError(
            f"Crop size ({width}x{height}) larger than video ({info.width}x{info.height})",
            code="crop_too_large",
        )

    if x is None:
        x = (info.width - width) // 2
    if y is None:
        y = (info.height - height) // 2

    output = output_path or _auto_output(input_path, f"crop_{width}x{height}")

    _run_ffmpeg(
        [
            "-i",
            input_path,
            "-vf",
            f"crop={width}:{height}:{x}:{y}",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "23",
            "-c:a",
            "copy",
            *_movflags_args(output),
            output,
        ]
    )

    result_info = probe(output)
    return EditResult(
        output_path=output,
        duration=result_info.duration,
        resolution=result_info.resolution,
        size_mb=result_info.size_mb,
        format="mp4",
        operation="crop",
    )


def rotate(
    input_path: str,
    angle: int = 0,
    flip_horizontal: bool = False,
    flip_vertical: bool = False,
    output_path: str | None = None,
) -> EditResult:
    """Rotate and/or flip a video.

    Args:
        angle: Rotation angle (0, 90, 180, 270).
        flip_horizontal: Mirror horizontally.
        flip_vertical: Mirror vertically.
    """
    _validate_input(input_path)

    if angle not in (0, 90, 180, 270):
        raise MCPVideoError("angle must be 0, 90, 180, or 270", code="invalid_angle")
    if angle == 0 and not flip_horizontal and not flip_vertical:
        raise MCPVideoError("No rotation or flip specified", code="no_transform")

    filters: list[str] = []
    if flip_horizontal:
        filters.append("hflip")
    if flip_vertical:
        filters.append("vflip")
    if angle == 90:
        filters.append("transpose=1")
    elif angle == 180:
        filters.append("transpose=1,transpose=1")
    elif angle == 270:
        filters.append("transpose=2")

    vf = ",".join(filters)
    output = output_path or _auto_output(input_path, f"rotated_{angle}")

    _run_ffmpeg(
        [
            "-i",
            input_path,
            "-vf",
            vf,
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            *_movflags_args(output),
            output,
        ]
    )

    result_info = probe(output)
    return EditResult(
        output_path=output,
        duration=result_info.duration,
        resolution=result_info.resolution,
        size_mb=result_info.size_mb,
        format="mp4",
        operation="rotate",
    )


def fade(
    input_path: str,
    fade_in: float = 0.0,
    fade_out: float = 0.0,
    output_path: str | None = None,
    crf: int | None = None,
    preset: str | None = None,
) -> EditResult:
    """Add fade in/out effect to a video."""
    _validate_input(input_path)
    if fade_in <= 0 and fade_out <= 0:
        raise MCPVideoError("Specify fade_in and/or fade_out > 0", code="no_fade")

    output = output_path or _auto_output(input_path, "faded")
    info = probe(input_path)

    vf_parts: list[str] = []
    if fade_in > 0:
        vf_parts.append(f"fade=t=in:st=0:d={fade_in}")
    if fade_out > 0:
        fade_start = max(0, info.duration - fade_out)
        vf_parts.append(f"fade=t=out:st={fade_start:.3f}:d={fade_out}")

    vf = ",".join(vf_parts)

    _run_ffmpeg(
        [
            "-i",
            input_path,
            "-vf",
            vf,
            "-c:v",
            "libx264",
            *_quality_args(crf=crf, preset=preset),
            "-c:a",
            "copy",
            *_movflags_args(output),
            output,
        ]
    )

    result_info = probe(output)
    return EditResult(
        output_path=output,
        duration=result_info.duration,
        resolution=result_info.resolution,
        size_mb=result_info.size_mb,
        format="mp4",
        operation="fade",
    )


def export_video(
    input_path: str,
    output_path: str | None = None,
    quality: QualityLevel = "high",
    format: ExportFormat = "mp4",
    on_progress: Callable[[float], None] | None = None,
    two_pass: bool = False,
    target_bitrate: int | None = None,
) -> EditResult:
    """Export a video with specified quality and format settings."""
    _validate_input(input_path)
    result = convert(
        input_path,
        format=format,
        quality=quality,
        output_path=output_path,
        on_progress=on_progress,
        two_pass=two_pass,
        target_bitrate=target_bitrate,
    )
    result.operation = "export"
    return result


# ---------------------------------------------------------------------------
# Timeline-based edit (composite operation)
# ---------------------------------------------------------------------------


def edit_timeline(timeline: Timeline | dict, output_path: str | None = None) -> EditResult:
    """Execute a full timeline-based edit described in JSON."""
    if isinstance(timeline, dict):
        timeline = Timeline.model_validate(timeline)
    tmpdir = tempfile.mkdtemp(prefix="mcp_video_timeline_")
    try:
        video_clips: list[str] = []
        audio_clips: list[str] = []
        text_elements: list = []
        image_overlays: list[TimelineImageOverlay] = []

        # Collect all elements from tracks
        for track in timeline.tracks:
            if track.type == "video":
                for clip in track.clips:
                    _validate_input(clip.source)
                    # Trim clip if needed
                    if clip.trim_start > 0 or clip.trim_end:
                        trimmed = os.path.join(tmpdir, f"v_{len(video_clips):04d}.mp4")
                        trim_kwargs = {"start": clip.trim_start}
                        if clip.duration:
                            trim_kwargs["duration"] = clip.duration
                        elif clip.trim_end:
                            trim_kwargs["end"] = clip.trim_end
                        result = trim(clip.source, output_path=trimmed, **trim_kwargs)
                        video_clips.append(result.output_path)
                    else:
                        video_clips.append(clip.source)
                text_elements.extend(track.elements)

            elif track.type == "audio":
                for clip in track.clips:
                    _validate_input(clip.source)
                    audio_clips.append(clip.source)

            elif track.type == "text":
                text_elements.extend(track.elements)

            elif track.type == "image":
                for img in track.images:
                    _validate_input(img.source)
                    image_overlays.append(img)

        if not video_clips:
            raise MCPVideoError("Timeline must have at least one video clip")

        # Merge video clips
        if len(video_clips) == 1:
            merged = video_clips[0]
        else:
            merged = os.path.join(tmpdir, "merged.mp4")
            transition_list = None
            trans_duration = 1.0
            for track in timeline.tracks:
                if track.type == "video" and track.transitions:
                    # Sort by after_clip to get correct order
                    sorted_trans = sorted(track.transitions, key=lambda t: t.after_clip)
                    transition_list = [t.type for t in sorted_trans]
                    trans_duration = sorted_trans[0].duration
                    break
            merge(video_clips, output_path=merged, transitions=transition_list, transition_duration=trans_duration)

        # Apply text overlays and image overlays in a single filtergraph pass
        # to avoid multiple re-encodes
        current = merged
        if text_elements or image_overlays:
            composited = os.path.join(tmpdir, "composited.mp4")
            _apply_composite_overlays(
                merged,
                composited,
                text_elements,
                image_overlays,
            )
            current = composited

        # Add audio
        if audio_clips:
            final = os.path.join(tmpdir, "with_audio.mp4")
            add_audio(current, audio_clips[0], output_path=final)
            current = final

        # Resize to timeline dimensions
        if timeline.width and timeline.height:
            info = probe(current)
            if info.width != timeline.width or info.height != timeline.height:
                resized = os.path.join(tmpdir, "resized.mp4")
                resize(current, width=timeline.width, height=timeline.height, output_path=resized)
                current = resized

        # Export — write to a safe location outside tmpdir
        if output_path:
            output = output_path
        else:
            # Use the original video's directory, not tmpdir
            original_source = video_clips[0]
            output = _auto_output(original_source, "timeline", ext=f".{timeline.export.format}")
        result = export_video(
            current,
            output_path=output,
            quality=timeline.export.quality,
            format=timeline.export.format,
        )

        return result

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def _apply_composite_overlays(
    input_path: str,
    output_path: str,
    text_elements: list,
    image_overlays: list[TimelineImageOverlay],
) -> None:
    """Apply text and image overlays in a single FFmpeg filtergraph pass.

    This avoids multiple re-encodes when applying multiple overlays.
    """
    info = probe(input_path)

    # Build filter_complex
    inputs: list[str] = ["-i", input_path]
    filter_parts: list[str] = []
    input_idx = 1  # Next input index (0 is the main video)

    # Named overlay position map (no margin for timeline overlays)
    overlay_position_map: dict[NamedPosition, str] = {
        "top-left": "0:0",
        "top-center": "(main_w-overlay_w)/2:0",
        "top-right": "main_w-overlay_w:0",
        "center-left": "0:(main_h-overlay_h)/2",
        "center": "(main_w-overlay_w)/2:(main_h-overlay_h)/2",
        "center-right": "main_w-overlay_w:(main_h-overlay_h)/2",
        "bottom-left": "0:main_h-overlay_h",
        "bottom-center": "(main_w-overlay_w)/2:main_h-overlay_h",
        "bottom-right": "main_w-overlay_w:main_h-overlay_h",
    }

    # Process image overlays first — they use FFmpeg overlay filter
    prev_label = "0:v"
    for i, img in enumerate(image_overlays):
        img_label = f"img{i}"
        ov_label = f"ov{i}"

        inputs.extend(["-i", img.source])

        # Build scale + opacity chain for this image
        chain_parts: list[str] = []
        if img.width and img.height:
            chain_parts.append(f"scale={img.width}:{img.height}")
        elif img.width:
            chain_parts.append(f"scale={img.width}:-1")
        elif img.height:
            chain_parts.append(f"scale=-1:{img.height}")

        if img.opacity < 1.0:
            chain_parts.append("format=rgba")
            chain_parts.append(f"colorchannelmixer=aa={img.opacity:.2f}")

        chain = ",".join(chain_parts) if chain_parts else "null"
        filter_parts.append(f"[{input_idx}:v]{chain}[{img_label}]")

        # Resolve position
        if isinstance(img.position, dict):
            if "x_pct" in img.position and "y_pct" in img.position:
                pos = f"(main_w*{img.position['x_pct']}-overlay_w/2):(main_h*{img.position['y_pct']}-overlay_h/2)"
            elif "x" in img.position and "y" in img.position:
                pos = f"{img.position['x']}:{img.position['y']}"
            else:
                pos = overlay_position_map["center"]
        elif img.x is not None and img.y is not None:
            pos = f"{img.x}:{img.y}"
        else:
            pos = overlay_position_map.get(img.position, overlay_position_map["center"])

        # Enable expression for timing
        enable_expr = ""
        if img.start is not None or img.duration is not None:
            parts = []
            if img.start is not None and img.duration is not None:
                end = img.start + img.duration
                parts.append(f"between(t,{img.start},{end})")
            elif img.start is not None:
                parts.append(f"gte(t,{img.start})")
            elif img.duration is not None:
                parts.append(f"lte(t,{img.duration})")
            enable_expr = f":enable='{parts[0]}'"

        filter_parts.append(f"[{prev_label}][{img_label}]overlay={pos}{enable_expr}[{ov_label}]")
        prev_label = ov_label
        input_idx += 1

    # Process text overlays — use drawtext on the final video
    # If there were image overlays, we append drawtext to the last overlay output
    # Otherwise we apply directly to the base video
    vf_parts: list[str] = []
    for elem in text_elements:
        fontfile = elem.style.get("font") or _default_font()
        if fontfile is not None:
            fontfile = _escape_ffmpeg_filter_value(fontfile)
        size = elem.style.get("size", 48)
        color = elem.style.get("color", "white")
        _validate_color(color)
        coords = _position_coords(elem.position, info.width, info.height)

        escaped_text = elem.text.replace("\\", "\\\\").replace("'", "'\\''").replace(":", "\\:")

        drawtext_parts = [
            f"drawtext=text='{escaped_text}'",
            f"fontsize={size}",
            f"fontcolor={color}",
            f"fontfile={fontfile}",
            coords,
        ]

        if elem.style.get("shadow", True):
            drawtext_parts.append("shadowcolor=black@0.5")
            drawtext_parts.append("shadowx=2")
            drawtext_parts.append("shadowy=2")

        if elem.start is not None and elem.duration is not None:
            drawtext_parts.append(f"enable='between(t\\,{elem.start}\\,{elem.start + elem.duration})'")
        elif elem.start is not None:
            drawtext_parts.append(f"enable='gte(t\\,{elem.start})'")

        vf_parts.append(":".join(drawtext_parts))

    # Combine: filter_complex for overlays + vf for drawtext
    if image_overlays and vf_parts:
        # Apply drawtext to the last overlay output
        last_label = prev_label
        for vf in vf_parts:
            filter_parts.append(f"[{last_label}]{vf}[vout]")
            last_label = "vout"

        # Final map
        cmd = [
            *inputs,
            "-filter_complex",
            ";".join(filter_parts),
            "-map",
            f"[{last_label}]",
            "-map",
            "0:a?",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "23",
            "-c:a",
            "copy",
            *_movflags_args(output_path),
            output_path,
        ]
        _run_ffmpeg(cmd)

    elif image_overlays:
        # Only image overlays, no text
        cmd = [
            *inputs,
            "-filter_complex",
            ";".join(filter_parts),
            "-map",
            f"[{prev_label}]",
            "-map",
            "0:a?",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "23",
            "-c:a",
            "copy",
            *_movflags_args(output_path),
            output_path,
        ]
        _run_ffmpeg(cmd)

    elif text_elements:
        # Only text overlays (no images) — use -vf
        vf = ",".join(vf_parts)
        _run_ffmpeg(
            [
                *inputs,
                "-vf",
                vf,
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "23",
                "-c:a",
                "copy",
                *_movflags_args(output_path),
                output_path,
            ]
        )


def extract_audio(
    input_path: str,
    output_path: str | None = None,
    format: str = "mp3",
) -> str:
    """Extract audio track from a video file."""
    VALID_AUDIO_FORMATS = {"mp3", "aac", "wav", "ogg", "flac"}
    if format not in VALID_AUDIO_FORMATS:
        raise MCPVideoError(
            f"Invalid audio format: {format}. Must be one of {VALID_AUDIO_FORMATS}",
            error_type="validation_error",
            code="invalid_parameter",
        )
    _validate_input(input_path)
    ext = f".{format}" if not format.startswith(".") else format
    output = output_path or _auto_output(input_path, "audio", ext=ext)

    codec_map = {
        "mp3": "libmp3lame",
        "aac": "aac",
        "wav": "pcm_s16le",
        "ogg": "libvorbis",
        "flac": "flac",
    }
    codec = codec_map[format]

    _run_ffmpeg(
        [
            "-i",
            input_path,
            "-vn",
            "-c:a",
            codec,
            "-b:a",
            "192k" if format != "wav" else "0",
            "-y",
            output,
        ]
    )

    return output


# ---------------------------------------------------------------------------
# Video filters & effects
# ---------------------------------------------------------------------------


def _get_color_preset_filter(preset: ColorPreset) -> str:
    """Return FFmpeg eq filter string for a named color preset."""
    preset_filters: dict[ColorPreset, str] = {
        "warm": "eq=brightness=0.05:saturation=1.3:contrast=1.05",
        "cool": "eq=brightness=0.02:saturation=0.9:contrast=1.05",
        "vintage": "eq=contrast=1.1:brightness=-0.02:saturation=0.7",
        "cinematic": "eq=contrast=1.15:brightness=-0.03:saturation=0.85",
        "noir": "eq=contrast=1.3:brightness=-0.05:saturation=0.0",
    }
    if preset not in preset_filters:
        valid = ", ".join(sorted(preset_filters))
        raise MCPVideoError(
            f"Unknown color preset '{preset}'. Valid presets: {valid}",
            error_type="validation_error",
            code="invalid_color_preset",
        )
    return preset_filters[preset]


def _build_pitch_shift_filter(semitones: float = 0) -> str:
    """Build FFmpeg audio filter string for pitch shifting.

    Args:
        semitones: Number of semitones to shift. Positive = higher, negative = lower.
            Each semitone is a 2^(1/12) ~ 1.0595x multiplier on sample rate.
    """
    rate_mult = 2 ** (semitones / 12)
    new_rate = 44100 * rate_mult
    # atempo compensates for the tempo change caused by sample rate shift,
    # restoring original playback speed (avoids A/V desync)
    tempo = 1.0 / rate_mult
    # atempo supports 0.5-100.0; chain if needed
    if tempo < 0.5:
        chain_count = 2
        while tempo ** (1 / chain_count) < 0.5:
            chain_count += 1
        tempo_val = tempo ** (1 / chain_count)
        atempo_str = ",".join([f"atempo={tempo_val}"] * chain_count)
    elif tempo > 100:
        chain_count = 2
        while tempo ** (1 / chain_count) > 100:
            chain_count += 1
        tempo_val = tempo ** (1 / chain_count)
        atempo_str = ",".join([f"atempo={tempo_val}"] * chain_count)
    else:
        atempo_str = f"atempo={tempo}"
    return f"asetrate={new_rate},aresample=44100,{atempo_str}"


def apply_filter(
    input_path: str,
    filter_type: FilterType,
    params: dict[str, Any] | None = None,
    output_path: str | None = None,
    crf: int | None = None,
    preset: str | None = None,
) -> EditResult:
    """Apply a visual filter to a video.

    Args:
        input_path: Path to the input video.
        filter_type: One of the supported filter types.
        params: Optional parameters for the filter.
        output_path: Where to save the output.
    """
    _validate_input(input_path)
    params = params or {}
    output = output_path or _auto_output(input_path, f"filter_{filter_type}")

    # Sanitize numeric params to prevent injection via non-numeric input.
    # Skip known string params (e.g. "preset" for color_preset filter).
    _STRING_PARAMS = {"preset"}
    for key in params:
        if key not in _STRING_PARAMS:
            params[key] = _sanitize_ffmpeg_number(params[key], key)

    # Probe video dimensions for ken_burns filter
    info = probe(input_path)

    # Build the -vf filter string
    # Audio filters use -af; video filters use -vf.
    # filter_map entries: (filter_name, filter_string, is_audio)
    filter_map: dict[FilterType, tuple[str, str, bool]] = {
        "blur": ("boxblur", f"boxblur={params.get('radius', 5)}:{params.get('strength', 1)}", False),
        "sharpen": ("unsharp", f"unsharp=5:5:{params.get('amount', 1.0)}:5:5:0.0", False),
        "brightness": ("eq", f"eq=brightness={params.get('level', 0.1)}", False),
        "contrast": ("eq", f"eq=contrast={params.get('level', 1.5)}", False),
        "saturation": ("eq", f"eq=saturation={params.get('level', 1.5)}", False),
        "grayscale": ("hue", "hue=s=0", False),
        "sepia": ("colorchannelmixer", "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131", False),
        "invert": ("negate", "negate", False),
        "vignette": ("vignette", f"vignette=angle={params.get('angle', 'PI/4')}", False),
        "color_preset": ("eq", _get_color_preset_filter(params.get("preset", "warm")), False),
        "denoise": (
            "hqdn3d",
            f"hqdn3d={params.get('luma_spatial', 4)}:{params.get('chroma_spatial', 3)}:{params.get('luma_tmp', 6)}:{params.get('chroma_tmp', 4.5)}",
            False,
        ),
        "deinterlace": ("yadif", "yadif=0:-1:0", False),
        "ken_burns": (
            "zoompan",
            f"zoompan=z='min(zoom+{params.get('zoom_speed', 0.0015)},1.5)':d={params.get('duration', 150)}:x='iw/2-(iw/zoom)/2':y='ih/2-(ih/zoom)/2':s={info.width}x{info.height}",
            False,
        ),
        "reverb": (
            "aecho",
            f"aecho={params.get('in_gain', 0.8)}:{params.get('out_gain', 0.9)}:{params.get('delays', 60)}:{params.get('decay', 0.2)}",
            True,
        ),
        "compressor": (
            "acompressor",
            f"acompressor=threshold={params.get('threshold_db', -20)}dB:ratio={params.get('ratio', 4)}:attack={params.get('attack', 5)}:release={params.get('release', 50)}",
            True,
        ),
        "pitch_shift": ("asetrate", _build_pitch_shift_filter(params.get("semitones", 0)), True),
        "noise_reduction": ("afftdn", f"afftdn=nf={params.get('noise_level', -25)}", True),
    }

    if filter_type not in filter_map:
        valid = ", ".join(sorted(filter_map))
        raise MCPVideoError(
            f"Unknown filter type '{filter_type}'. Valid types: {valid}",
            error_type="validation_error",
            code="invalid_filter_type",
        )
    filter_name, filter_string, is_audio = filter_map[filter_type]
    _require_filter(filter_name, f"Filter '{filter_type}'")

    # Audio filters require an audio stream and use -af instead of -vf
    if is_audio:
        input_info = probe(input_path)
        if input_info.audio_codec is None:
            raise MCPVideoError(
                f"Audio filter '{filter_type}' requires an audio stream, but this video has none",
                error_type="validation_error",
                code="audio_filter_no_audio",
            )
        _run_ffmpeg(
            [
                "-i",
                input_path,
                "-af",
                filter_string,
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                *_movflags_args(output),
                output,
            ]
        )
    else:
        _run_ffmpeg(
            [
                "-i",
                input_path,
                "-vf",
                filter_string,
                "-c:v",
                "libx264",
                *_quality_args(crf=crf, preset=preset),
                "-c:a",
                "copy",
                *_movflags_args(output),
                output,
            ]
        )

    info = probe(output)
    return EditResult(
        output_path=output,
        duration=info.duration,
        resolution=info.resolution,
        size_mb=info.size_mb,
        format="mp4",
        operation=f"filter_{filter_type}",
    )


# ---------------------------------------------------------------------------
# Audio normalization
# ---------------------------------------------------------------------------


def normalize_audio(
    input_path: str,
    target_lufs: float = -16.0,
    lra: float = 11.0,
    output_path: str | None = None,
) -> EditResult:
    """Normalize audio loudness to a target LUFS level.

    Args:
        input_path: Path to the input video.
        target_lufs: Target integrated loudness in LUFS. Common values:
            -16 (YouTube), -23 (EBU R128/broadcast), -14 (Apple/Spotify).
        lra: Loudness range target in LU. Default 11.0.
        output_path: Where to save the output.
    """
    _validate_input(input_path)
    if not isinstance(target_lufs, (int, float)) or not (-70 <= target_lufs <= -5):
        raise MCPVideoError(
            f"target_lufs must be -70 to -5, got {target_lufs}", error_type="validation_error", code="invalid_parameter"
        )
    _require_filter("loudnorm", "Audio normalization")
    output = output_path or _auto_output(input_path, "normalized")

    # loudnorm parameters: I=integrated loudness, TP=true peak, LRA=loudness range
    # TP (true peak) should be a fixed value near -1.5 dBTP regardless of target LUFS.
    tp = -1.5

    _run_ffmpeg(
        [
            "-i",
            input_path,
            "-af",
            f"loudnorm=I={target_lufs}:TP={tp}:LRA={lra}",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            *_movflags_args(output),
            output,
        ]
    )

    info = probe(output)
    return EditResult(
        output_path=output,
        duration=info.duration,
        resolution=info.resolution,
        size_mb=info.size_mb,
        format="mp4",
        operation="normalize_audio",
    )


# ---------------------------------------------------------------------------
# Compositing & overlays
# ---------------------------------------------------------------------------


def overlay_video(
    background_path: str,
    overlay_path: str,
    position: Position = "top-right",
    width: int | None = None,
    height: int | None = None,
    opacity: float = 0.8,
    start_time: float | None = None,
    duration: float | None = None,
    output_path: str | None = None,
    crf: int | None = None,
    preset: str | None = None,
) -> EditResult:
    """Picture-in-picture: overlay a video on top of another.

    Args:
        background_path: Path to the background video.
        overlay_path: Path to the overlay video.
        position: Position of the overlay on screen.
        width: Width to scale the overlay to.
        height: Height to scale the overlay to.
        opacity: Opacity of the overlay (0.0 to 1.0).
        start_time: When the overlay appears (seconds).
        duration: How long the overlay is visible (seconds).
        output_path: Where to save the output.
    """
    _validate_input(background_path)
    _validate_input(overlay_path)
    _require_filter("overlay", "Video overlay")
    output = output_path or _auto_output(background_path, "overlay")

    # Build scale filter for overlay
    scale_parts = []
    if width and height:
        scale_parts.append(f"scale={width}:{height}")
    elif width:
        scale_parts.append(f"scale={width}:-1")
    elif height:
        scale_parts.append(f"scale=-1:{height}")
    scale_filter = ",".join(scale_parts) if scale_parts else ""

    # Build the overlay filter chain
    opacity_fmt = f"{opacity:.2f}"
    overlay_chain_parts = ["format=rgba", f"colorchannelmixer=aa={opacity_fmt}"]
    if scale_filter:
        overlay_chain_parts.insert(0, scale_filter)
    overlay_chain = ",".join(overlay_chain_parts)

    # Position map (same as watermark but without margin)
    position_map: dict[NamedPosition, str] = {
        "top-left": "0:0",
        "top-center": "(main_w-overlay_w)/2:0",
        "top-right": "main_w-overlay_w:0",
        "center-left": "0:(main_h-overlay_h)/2",
        "center": "(main_w-overlay_w)/2:(main_h-overlay_h)/2",
        "center-right": "main_w-overlay_w:(main_h-overlay_h)/2",
        "bottom-left": "0:main_h-overlay_h",
        "bottom-center": "(main_w-overlay_w)/2:main_h-overlay_h",
        "bottom-right": "main_w-overlay_w:main_h-overlay_h",
    }
    overlay_pos = _resolve_position(position, position_map, "top-right")

    # Optional enable expression for timing
    enable_expr = ""
    if start_time is not None or duration is not None:
        parts = []
        if start_time is not None and duration is not None:
            end = start_time + duration
            parts.append(f"between(t,{start_time},{end})")
        elif start_time is not None:
            parts.append(f"gte(t,{start_time})")
        elif duration is not None:
            parts.append(f"lte(t,{duration})")
        enable_expr = f":enable='{parts[0]}'"

    filter_complex = f"[1:v]{overlay_chain}[ov];[0:v][ov]overlay={overlay_pos}{enable_expr}"

    _run_ffmpeg(
        [
            "-i",
            background_path,
            "-i",
            overlay_path,
            "-filter_complex",
            filter_complex,
            "-c:v",
            "libx264",
            *_quality_args(crf=crf, preset=preset),
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            *_movflags_args(output),
            output,
        ]
    )

    info = probe(output)
    return EditResult(
        output_path=output,
        duration=info.duration,
        resolution=info.resolution,
        size_mb=info.size_mb,
        format="mp4",
        operation="overlay_video",
    )


def split_screen(
    left_path: str,
    right_path: str,
    layout: SplitLayout = "side-by-side",
    output_path: str | None = None,
) -> EditResult:
    """Place two videos side by side or top/bottom.

    Args:
        left_path: Path to the first video.
        right_path: Path to the second video.
        layout: 'side-by-side' or 'top-bottom'.
        output_path: Where to save the output.
    """
    _validate_input(left_path)
    _validate_input(right_path)
    output = output_path or _auto_output(left_path, f"split_{layout}")

    # Get info about both videos to check if resizing is needed
    left_info = probe(left_path)
    right_info = probe(right_path)

    # Build filter_complex to normalize heights (side-by-side) or widths (top-bottom)
    # Use max dimensions to avoid losing quality when one video is larger
    if layout == "side-by-side":
        target_h = max(left_info.height, right_info.height)
        if left_info.height != right_info.height:
            filter_complex = (
                f"[0:v]scale=-1:{target_h},setsar=1[left];"
                f"[1:v]scale=-1:{target_h},setsar=1[right];"
                f"[left][right]hstack=inputs=2[v]"
            )
        else:
            filter_complex = "[0:v][1:v]hstack=inputs=2[v]"
    else:
        target_w = max(left_info.width, right_info.width)
        if left_info.width != right_info.width:
            filter_complex = (
                f"[0:v]scale={target_w}:-1,setsar=1[top];"
                f"[1:v]scale={target_w}:-1,setsar=1[bottom];"
                f"[top][bottom]vstack=inputs=2[v]"
            )
        else:
            filter_complex = "[0:v][1:v]vstack=inputs=2[v]"

    _run_ffmpeg(
        [
            "-i",
            left_path,
            "-i",
            right_path,
            "-filter_complex",
            filter_complex,
            "-map",
            "[v]",
            "-map",
            "0:a?",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            *_movflags_args(output),
            output,
        ]
    )

    info = probe(output)
    return EditResult(
        output_path=output,
        duration=info.duration,
        resolution=info.resolution,
        size_mb=info.size_mb,
        format="mp4",
        operation=f"split_screen_{layout}",
    )


def reverse(
    input_path: str,
    output_path: str | None = None,
) -> EditResult:
    """Reverse video and audio playback.

    Args:
        input_path: Path to the input video.
        output_path: Where to save the output. Auto-generated if omitted.
    """
    _validate_input(input_path)
    output = output_path or _auto_output(input_path, "reversed")

    input_info = probe(input_path)

    args = ["-i", input_path, "-vf", "reverse"]
    # Only reverse audio if the input has an audio stream
    if input_info.audio_codec:
        args += ["-af", "areverse", "-c:a", "aac", "-b:a", "128k"]
    else:
        args += ["-an"]
    args += ["-c:v", "libx264", "-preset", "fast", "-crf", "23"]

    _run_ffmpeg(
        args
        + _movflags_args(output)
        + [
            output,
        ]
    )

    info = probe(output)
    return EditResult(
        output_path=output,
        duration=info.duration,
        resolution=info.resolution,
        size_mb=info.size_mb,
        format="mp4",
        operation="reverse",
    )


def chroma_key(
    input_path: str,
    color: str = "0x00FF00",
    similarity: float = 0.01,
    blend: float = 0.0,
    output_path: str | None = None,
) -> EditResult:
    """Remove a solid color background (green screen / chroma key).

    Args:
        input_path: Path to the input video.
        color: Color to make transparent (default green: 0x00FF00).
        similarity: How similar colors need to be to be keyed out (default 0.01).
        blend: How much to blend the keyed color (default 0.0).
        output_path: Where to save the output. Auto-generated if omitted.

    Note: Use a .mov output path to preserve the alpha channel (transparent
    background). Non-MOV outputs will encode with libx264 which does not
    support transparency.
    """
    _validate_input(input_path)
    output = output_path or _auto_output(input_path, "chromakey")

    _require_filter("chromakey", "Chroma key filter")

    # Validate color is a safe 0xRRGGBB hex value (prevents FFmpeg filter injection)
    _validate_chroma_color(color)

    # Use MOV with prores_ks (supports alpha) when outputting with transparency
    is_mov = output.lower().endswith(".mov")

    if is_mov:
        vf = f"chromakey=color={color}:similarity={similarity}:blend={blend},format=yuva444p16le"
        codec_args = ["-c:v", "prores_ks", "-pix_fmt", "yuva444p12le"]
    else:
        vf = f"chromakey=color={color}:similarity={similarity}:blend={blend}"
        codec_args = ["-c:v", "libx264", "-preset", "fast", "-crf", "23", "-c:a", "aac", "-b:a", "128k"]

    _run_ffmpeg(["-i", input_path, "-vf", vf, *codec_args, *_movflags_args(output), output])

    info = probe(output)
    return EditResult(
        output_path=output,
        duration=info.duration,
        resolution=info.resolution,
        size_mb=info.size_mb,
        format="mp4",
        operation="chroma_key",
    )


# ---------------------------------------------------------------------------
# Subtitle generation
# ---------------------------------------------------------------------------


def generate_subtitles(
    entries: list[dict],
    input_path: str,
    output_path: str | None = None,
    burn: bool = False,
) -> SubtitleResult:
    """Generate SRT subtitles from text entries and optionally burn into video.

    Args:
        entries: List of dicts with keys: start (float), end (float), text (str).
        input_path: Path to the input video.
        output_path: Base path for output files.
        burn: If True, burn subtitles into the video.
    """
    _validate_input(input_path)
    if not entries:
        raise MCPVideoError(
            "entries cannot be empty",
            error_type="validation_error",
            code="empty_entries",
        )
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict) or "text" not in entry or "start" not in entry or "end" not in entry:
            raise MCPVideoError(
                f"Invalid subtitle entry {i}: must have 'start', 'end', 'text' keys",
                error_type="validation_error",
                code="invalid_parameter",
            )
        start = entry.get("start", 0)
        end = entry.get("end", 0)
        if start >= end:
            raise MCPVideoError(
                f"Entry {i}: start ({start}) must be less than end ({end})",
                error_type="validation_error",
                code="invalid_entry_range",
            )

    # Build SRT content
    srt_lines: list[str] = []
    for i, entry in enumerate(entries, 1):
        start = entry["start"]
        end = entry["end"]
        text = entry["text"]
        srt_lines.append(str(i))
        srt_lines.append(_seconds_to_srt_time(start) + " --> " + _seconds_to_srt_time(end))
        srt_lines.append(text)
        srt_lines.append("")

    srt_content = "\n".join(srt_lines)

    # Write SRT file
    if output_path:
        srt_dir = output_path if os.path.isdir(output_path) else os.path.dirname(output_path) or "."
        os.makedirs(srt_dir, exist_ok=True)
    else:
        srt_dir = _auto_output_dir(input_path, "subtitles")
        os.makedirs(srt_dir, exist_ok=True)

    srt_filename = "subtitles.srt"
    srt_file = os.path.join(srt_dir, srt_filename)
    with open(srt_file, "w", encoding="utf-8") as f:
        f.write(srt_content)

    if burn:
        _require_filter("subtitles", "Subtitle burn-in")
        video_out = os.path.join(srt_dir, "subtitled.mp4")
        escaped_srt = _escape_ffmpeg_filter_value(srt_file)
        _run_ffmpeg(
            [
                "-i",
                input_path,
                "-vf",
                f"subtitles={escaped_srt}",
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "23",
                "-c:a",
                "copy",
                *_movflags_args(video_out),
                video_out,
            ]
        )
        return SubtitleResult(
            srt_path=srt_file,
            video_path=video_out,
            entry_count=len(entries),
        )

    return SubtitleResult(
        srt_path=srt_file,
        entry_count=len(entries),
    )


# ---------------------------------------------------------------------------
# Audio waveform extraction
# ---------------------------------------------------------------------------


def audio_waveform(
    input_path: str,
    bins: int = 50,
) -> WaveformResult:
    """Extract audio waveform data (peaks and silence regions).

    Args:
        input_path: Path to the input video/audio file.
        bins: Number of time segments to analyze (default 50).
    """
    _validate_input(input_path)

    input_info = probe(input_path)
    if input_info.audio_codec is None:
        raise MCPVideoError(
            "Audio waveform extraction requires an audio stream, but this video has none",
            error_type="validation_error",
            code="waveform_no_audio",
        )

    duration = input_info.duration
    segment_duration = duration / bins

    # Use astats filter to get per-segment audio levels
    filter_str = "astats=metadata=1:reset=0,ametadata=1"
    proc = subprocess.run(
        [_ffmpeg(), "-i", input_path, "-af", filter_str, "-f", "null", "-"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    # Parse astats output for RMS level
    peaks: list[dict] = []
    levels: list[float] = []

    for line in proc.stderr.split("\n"):
        line = line.strip()
        if "Parsed_dc" in line or "n_samples" in line:
            continue
        if "RMS_level_dB" in line:
            try:
                # Format: [Parsed_astats_...] RMS_level_dB=...
                parts = line.split("RMS_level_dB=")
                if len(parts) >= 2:
                    val = float(parts[1].split()[0])
                    levels.append(val)
            except (ValueError, IndexError):
                continue

    # If astats didn't produce usable data, return synthetic waveform
    if not levels:
        for i in range(bins):
            t = (i + 0.5) * segment_duration
            peaks.append({"time": round(t, 2), "level": -20.0})

        return WaveformResult(
            duration=duration,
            peaks=peaks,
            mean_level=-20.0,
            max_level=-20.0,
            min_level=-20.0,
            silence_regions=[],
            synthetic=True,
        )

    # Bin the levels into the requested number of segments
    samples_per_bin = max(1, len(levels) // bins)
    binned: list[float] = []
    for i in range(bins):
        start_idx = i * samples_per_bin
        end_idx = min((i + 1) * samples_per_bin, len(levels))
        if start_idx < len(levels):
            bin_avg = sum(levels[start_idx:end_idx]) / (end_idx - start_idx)
            binned.append(bin_avg)

    peaks = []
    for i, level in enumerate(binned):
        t = (i + 0.5) * segment_duration
        peaks.append({"time": round(t, 2), "level": round(level, 1)})

    # Detect silence (below -50 dB)
    silence_threshold = -50.0
    silence_regions: list[dict] = []
    in_silence = False
    silence_start = 0.0
    for i, level in enumerate(binned):
        t = (i + 0.5) * segment_duration
        if level < silence_threshold and not in_silence:
            in_silence = True
            silence_start = t
        elif level >= silence_threshold and in_silence:
            in_silence = False
            silence_regions.append({"start": round(silence_start, 2), "end": round(t, 2)})
    if in_silence:
        silence_regions.append({"start": round(silence_start, 2), "end": round(duration, 2)})

    mean_level = sum(binned) / len(binned) if binned else -60.0
    max_level = max(binned) if binned else -60.0
    min_level = min(binned) if binned else -60.0

    return WaveformResult(
        duration=duration,
        peaks=peaks,
        mean_level=round(mean_level, 1),
        max_level=round(max_level, 1),
        min_level=round(min_level, 1),
        silence_regions=silence_regions,
    )


# ---------------------------------------------------------------------------
# Scene detection
# ---------------------------------------------------------------------------


def detect_scenes(
    input_path: str,
    threshold: float = 0.3,
    min_scene_duration: float = 1.0,
) -> SceneDetectionResult:
    """Detect scene changes in a video.

    Args:
        input_path: Path to the input video.
        threshold: Scene detection sensitivity (0.0-1.0, lower = more sensitive).
        min_scene_duration: Minimum duration of a scene in seconds.
    """
    _validate_input(input_path)
    if not isinstance(threshold, (int, float)) or not (0.0 <= threshold <= 1.0):
        raise MCPVideoError(
            f"threshold must be 0.0-1.0, got {threshold}", error_type="validation_error", code="invalid_parameter"
        )
    info = probe(input_path)
    duration = info.duration

    # Use FFmpeg select filter with scene detection
    proc = subprocess.run(
        [
            _ffmpeg(),
            "-i",
            input_path,
            "-vf",
            f"select='gt(scene,{threshold})',showinfo",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if proc.returncode != 0:
        raise parse_ffmpeg_error(proc.stderr)

    # Parse showinfo output for scene change timestamps
    scene_times: list[float] = []
    for line in proc.stderr.split("\n"):
        if "showinfo" in line and "pts_time:" in line:
            try:
                # Format: [showinfo @ ...] pts_time:X ...
                pts_match = re.search(r"pts_time:(\d+\.?\d*)", line)
                if pts_match:
                    scene_times.append(float(pts_match.group(1)))
            except (ValueError, IndexError):
                continue

    # Build scene list from timestamps
    scenes: list[dict] = []
    prev_time = 0.0
    for t in scene_times:
        if t - prev_time >= min_scene_duration:
            scenes.append(
                {
                    "start": round(prev_time, 2),
                    "end": round(t, 2),
                    "start_frame": round(prev_time * info.fps),
                    "end_frame": round(t * info.fps),
                }
            )
            prev_time = t

    # Add final scene
    if duration - prev_time >= 0.1:
        scenes.append(
            {
                "start": round(prev_time, 2),
                "end": round(duration, 2),
                "start_frame": round(prev_time * info.fps),
                "end_frame": round(duration * info.fps),
            }
        )

    return SceneDetectionResult(
        scenes=scenes,
        scene_count=len(scenes),
        duration=duration,
    )


# ---------------------------------------------------------------------------
# Image sequences
# ---------------------------------------------------------------------------


def create_from_images(
    images: list[str],
    output_path: str | None = None,
    fps: float = 30.0,
) -> EditResult:
    """Create a video from a sequence of images.

    Args:
        images: List of image file paths.
        output_path: Where to save the output video.
        fps: Frames per second for the output video.
    """
    if not images:
        raise MCPVideoError(
            "No images provided",
            error_type="validation_error",
            code="empty_images",
        )
    for img in images:
        if not os.path.isfile(img):
            raise InputFileError(img)

    output = output_path or _auto_output(images[0], "from_images")
    tmpdir = tempfile.mkdtemp(prefix="mcp_video_imgseq_")
    try:
        # Detect if any input is PNG (has alpha channel)
        has_png = any(img.lower().endswith(".png") for img in images)
        img_format = "png" if has_png else "jpg"
        ext = f".{img_format}"

        # Normalize all images to same dimensions first
        normalized: list[str] = []
        for i, img in enumerate(images):
            norm_path = os.path.join(tmpdir, f"img_{i:04d}{ext}")
            if img_format == "png":
                _run_ffmpeg(
                    [
                        "-y",
                        "-i",
                        img,
                        "-vf",
                        "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                        "-c:v",
                        "png",
                        norm_path,
                    ]
                )
            else:
                _run_ffmpeg(
                    [
                        "-y",
                        "-i",
                        img,
                        "-vf",
                        "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                        "-q:v",
                        "2",
                        norm_path,
                    ]
                )
            normalized.append(norm_path)

        # Build concat file
        concat_file = os.path.join(tmpdir, "concat.txt")
        img_duration = 1.0 / fps
        with open(concat_file, "w") as f:
            for img in normalized:
                abs_path = os.path.abspath(img).replace("'", "'\\''")
                f.write(f"file '{abs_path}'\n")
                f.write(f"duration {img_duration}\n")
            abs_last = os.path.abspath(normalized[-1]).replace("'", "'\\''")
            f.write(f"file '{abs_last}'\n")

        _run_ffmpeg(
            [
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                concat_file,
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "23",
                "-pix_fmt",
                "yuv420p",
                *_movflags_args(output),
                output,
            ]
        )
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    result_info = probe(output)
    return EditResult(
        output_path=output,
        duration=result_info.duration,
        resolution=result_info.resolution,
        size_mb=result_info.size_mb,
        format="mp4",
        operation="create_from_images",
    )


def export_frames(
    input_path: str,
    output_dir: str | None = None,
    fps: float = 1.0,
    format: str = "jpg",
) -> ImageSequenceResult:
    """Export frames from a video as individual images.

    Args:
        input_path: Path to the input video.
        output_dir: Directory for extracted frames.
        fps: Frames per second to extract (1.0 = 1 frame per second).
        format: Output image format (jpg, png).
    """
    _validate_input(input_path)
    if format == "mjpeg":
        format = "jpg"
    if format not in ("jpg", "png"):
        raise MCPVideoError(
            f"Invalid format '{format}': must be 'jpg', 'mjpeg' or 'png'",
            error_type="validation_error",
            code="invalid_format",
        )
    probe(input_path)

    out_dir = output_dir or _auto_output_dir(input_path, "frames")
    os.makedirs(out_dir, exist_ok=True)

    ext = format if format.startswith(".") else f".{format}"
    pattern = os.path.join(out_dir, f"frame_%04d{ext}")

    _run_ffmpeg(
        [
            "-i",
            input_path,
            "-vf",
            f"fps={fps}",
            "-q:v",
            "2",
            "-y",
            pattern,
        ]
    )

    # Collect generated frame paths
    frame_paths = sorted(
        [os.path.join(out_dir, f) for f in os.listdir(out_dir) if f.startswith("frame_") and f.endswith(ext)]
    )

    return ImageSequenceResult(
        frame_paths=frame_paths,
        frame_count=len(frame_paths),
        fps=fps,
    )


# ---------------------------------------------------------------------------
# Quality metrics
# ---------------------------------------------------------------------------


def compare_quality(
    original_path: str,
    distorted_path: str,
    metrics: list[str] | None = None,
) -> QualityMetricsResult:
    """Compare video quality between original and distorted versions.

    Args:
        original_path: Path to the original/reference video.
        distorted_path: Path to the distorted/processed video.
        metrics: List of metrics to compute (default: ["psnr", "ssim"]).
    """
    _validate_input(original_path)
    _validate_input(distorted_path)
    metrics = metrics or ["psnr", "ssim"]

    computed: dict[str, float] = {}

    for metric in metrics:
        metric_lower = metric.lower()
        if metric_lower not in ("psnr", "ssim"):
            continue

        try:
            # Get original resolution to scale distorted video to match
            orig_info = probe(original_path)
            target_w = orig_info.width
            target_h = orig_info.height

            # Scale distorted to match original resolution, then compare
            filter_str = f"[1:v]scale={target_w}:{target_h}[scaled];[0:v][scaled]{metric_lower}"
            proc = subprocess.run(
                [
                    _ffmpeg(),
                    "-i",
                    original_path,
                    "-i",
                    distorted_path,
                    "-lavfi",
                    filter_str,
                    "-f",
                    "null",
                    "-",
                ],
                capture_output=True,
                text=True,
                timeout=300,
            )
            if proc.returncode != 0:
                raise ProcessingError(
                    f"ffmpeg -i {original_path} -i {distorted_path} -lavfi {metric_lower}",
                    proc.returncode,
                    proc.stderr[:500],
                )

            # Parse metric value from stderr
            for line in proc.stderr.split("\n"):
                if metric_lower == "psnr" and "average:" in line.lower():
                    try:
                        # Format: [Parsed_psnr ...] average:XX.XX
                        val_match = re.search(r"average:\s*([0-9.]+)", line, re.IGNORECASE)
                        if val_match:
                            computed["psnr"] = float(val_match.group(1))
                    except (ValueError, IndexError):
                        continue
                elif metric_lower == "ssim" and "All:" in line:
                    try:
                        # Format: [Parsed_ssim ...] All:X.XXXXXX
                        val_match = re.search(r"All[:\s]+([0-9.]+)", line)
                        if val_match:
                            computed["ssim"] = float(val_match.group(1))
                    except (ValueError, IndexError):
                        continue
        except Exception as e:
            if isinstance(e, ProcessingError):
                raise
            raise ProcessingError(
                f"ffmpeg -i {original_path} -i {distorted_path} -lavfi {metric_lower}",
                1,
                str(e)[:500],
            ) from e

    # Determine overall quality
    if "ssim" in computed:
        ssim_val = computed["ssim"]
        if ssim_val >= 0.95:
            overall = "high"
        elif ssim_val >= 0.80:
            overall = "medium"
        else:
            overall = "low"
    elif "psnr" in computed:
        psnr_val = computed["psnr"]
        if psnr_val >= 40:
            overall = "high"
        elif psnr_val >= 30:
            overall = "medium"
        else:
            overall = "low"
    else:
        overall = "unknown"

    return QualityMetricsResult(
        metrics=computed,
        overall_quality=overall,
    )


# ---------------------------------------------------------------------------
# Metadata editing
# ---------------------------------------------------------------------------


def read_metadata(input_path: str) -> MetadataResult:
    """Read metadata tags from a video/audio file.

    Args:
        input_path: Path to the input file.
    """
    _validate_input(input_path)
    data = _run_ffprobe_json(input_path)

    # Extract tags from format
    fmt_tags = data.get("format", {}).get("tags", {})
    # Also check stream tags
    stream_tags: dict[str, str] = {}
    for stream in data.get("streams", []):
        for k, v in stream.get("tags", {}).items():
            if k not in stream_tags:
                stream_tags[k] = v

    all_tags = {**stream_tags, **fmt_tags}

    return MetadataResult(
        title=all_tags.pop("title", None),
        artist=all_tags.pop("artist", None),
        album=all_tags.pop("album", None),
        comment=all_tags.pop("comment", None),
        date=all_tags.pop("date", None) or all_tags.pop("creation_time", None),
        tags=all_tags,
    )


def write_metadata(
    input_path: str,
    metadata: dict[str, str],
    output_path: str | None = None,
) -> EditResult:
    """Write metadata tags to a video/audio file.

    Args:
        input_path: Path to the input file.
        metadata: Dict of tag key-value pairs (e.g. {"title": "My Video", "artist": "Me"}).
        output_path: Where to save the output. If None, overwrites in place with a temp file.
    """
    _validate_input(input_path)
    if not metadata:
        raise MCPVideoError(
            "No metadata provided",
            error_type="validation_error",
            code="empty_metadata",
        )

    # Validate metadata keys and values: reject newlines, null bytes, and '=' in keys
    for key, value in metadata.items():
        if "=" in key or "\n" in key or "\0" in key:
            raise MCPVideoError(
                f"Invalid metadata key '{key}': keys cannot contain '=', newline, or null bytes",
                error_type="validation_error",
                code="invalid_metadata_key",
            )
        if "\n" in str(value) or "\0" in str(value):
            raise MCPVideoError(
                f"Invalid metadata value for '{key}': values cannot contain newline or null bytes",
                error_type="validation_error",
                code="invalid_metadata_value",
            )

    output = output_path or _auto_output(input_path, "tagged")

    args = ["-i", input_path]
    for key, value in metadata.items():
        args.extend(["-metadata", f"{key}={value}"])
    args.extend(["-c:v", "copy", "-c:a", "copy", *_movflags_args(output), output])
    _run_ffmpeg(args)

    result_info = probe(output)
    return EditResult(
        output_path=output,
        duration=result_info.duration,
        resolution=result_info.resolution,
        size_mb=result_info.size_mb,
        format=result_info.format,
        operation="write_metadata",
    )


# ---------------------------------------------------------------------------
# Video stabilization
# ---------------------------------------------------------------------------


def stabilize(
    input_path: str,
    smoothing: float = 15,
    zooming: float = 0,
    output_path: str | None = None,
) -> EditResult:
    """Stabilize a shaky video using motion vector analysis.

    Uses vidstab filter (two-pass: detect then transform).

    Args:
        input_path: Path to the input video.
        smoothing: Smoothing strength (default 15, higher = more stable).
        zooming: Zoom percentage to avoid black borders (default 0).
        output_path: Where to save the output.
    """
    _validate_input(input_path)
    _require_filter("vidstabdetect", "Video stabilization")
    output = output_path or _auto_output(input_path, "stabilized")

    tmpdir = tempfile.mkdtemp(prefix="mcp_video_stab_")
    try:
        # Pass 1: detect motion vectors
        vectors_file = os.path.join(tmpdir, "vectors.trf")
        result = subprocess.run(
            [
                _ffmpeg(),
                "-y",
                "-i",
                input_path,
                "-vf",
                "vidstabdetect=shakiness=10:accuracy=15:result=" + vectors_file,
                "-f",
                "null",
                "-",
            ],
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode != 0:
            raise parse_ffmpeg_error(result.stderr)

        # Pass 2: apply stabilization
        _run_ffmpeg(
            [
                "-i",
                input_path,
                "-vf",
                f"vidstabtransform=input={vectors_file}:smoothing={smoothing}:zoom={zooming}:crop=black",
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "23",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                *_movflags_args(output),
                output,
            ]
        )
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    result_info = probe(output)
    return EditResult(
        output_path=output,
        duration=result_info.duration,
        resolution=result_info.resolution,
        size_mb=result_info.size_mb,
        format="mp4",
        operation="stabilize",
    )


# ---------------------------------------------------------------------------
# Advanced masking
# ---------------------------------------------------------------------------


def apply_mask(
    input_path: str,
    mask_path: str,
    feather: int = 5,
    output_path: str | None = None,
) -> EditResult:
    """Apply an image mask to a video with edge feathering.

    Uses alphamerge filter to composite the mask as an alpha channel.

    Args:
        input_path: Path to the input video.
        mask_path: Path to the mask image (white = visible, black = transparent).
        feather: Feather/blur amount at mask edges in pixels (default 5).
        output_path: Where to save the output.
    """
    _validate_input(input_path)
    _validate_input(mask_path)
    _require_filter("alphamerge", "Advanced masking")
    output = output_path or _auto_output(input_path, "masked")

    # Get video dimensions to scale mask
    info = probe(input_path)
    w, h = info.width, info.height

    # Scale mask to video dimensions, convert to alpha, and alphamerge
    if feather > 0:
        filter_complex = (
            f"[1:v]format=gray,scale={w}:{h},colorchannelmixer=aa=1.0,boxblur={feather}[alpha];"
            f"[0:v][alpha]alphamerge,format=yuv420p[out]"
        )
    else:
        filter_complex = (
            f"[1:v]format=gray,scale={w}:{h},colorchannelmixer=aa=1.0[alpha];[0:v][alpha]alphamerge,format=yuv420p[out]"
        )

    _run_ffmpeg(
        [
            "-i",
            input_path,
            "-i",
            mask_path,
            "-filter_complex",
            filter_complex,
            "-map",
            "[out]",
            "-map",
            "0:a?",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "23",
            "-c:a",
            "copy",
            *_movflags_args(output),
            output,
        ]
    )

    result_info = probe(output)
    return EditResult(
        output_path=output,
        duration=result_info.duration,
        resolution=result_info.resolution,
        size_mb=result_info.size_mb,
        format="mp4",
        operation="apply_mask",
    )


# ---------------------------------------------------------------------------
# Batch processing
# ---------------------------------------------------------------------------


def video_batch(
    inputs: list[str],
    operation: str,
    params: dict[str, Any] | None = None,
    output_dir: str | None = None,
) -> dict[str, Any]:
    """Apply the same operation to multiple video files.

    Args:
        inputs: List of absolute paths to input video files.
        operation: Operation (trim, resize, convert, filter, blur, color_grade, watermark, speed, fade, normalize_audio).
        params: Parameters for the operation.
        output_dir: Directory for output files. Auto-generated if omitted.
    """
    if not inputs:
        return {
            "success": False,
            "error": {"type": "input_error", "code": "empty_inputs", "message": "No input files provided"},
        }

    params = params or {}
    results = []
    succeeded = 0
    failed = 0

    for input_path in inputs:
        try:
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            def _batch_output(ext: str | None = None, _input_path: str = input_path) -> str:
                """Generate output path in output_dir, or auto-generate."""
                if output_dir:
                    name = os.path.splitext(os.path.basename(_input_path))[0]
                    ext = ext or ".mp4"
                    return os.path.join(output_dir, f"{name}_{operation}{ext}")
                return None  # let the engine auto-generate

            if operation == "trim":
                result = trim(
                    input_path,
                    start=params.get("start", "0"),
                    duration=params.get("duration"),
                    end=params.get("end"),
                    output_path=_batch_output(),
                )
            elif operation == "resize":
                result = resize(
                    input_path,
                    width=params.get("width"),
                    height=params.get("height"),
                    aspect_ratio=params.get("aspect_ratio"),
                    quality=params.get("quality", "high"),
                    output_path=_batch_output(),
                )
            elif operation == "convert":
                out_ext = f".{params.get('format', 'mp4')}"
                result = convert(
                    input_path,
                    format=params.get("format", "mp4"),
                    quality=params.get("quality", "high"),
                    output_path=_batch_output(out_ext),
                )
            elif operation == "filter":
                result = apply_filter(
                    input_path,
                    filter_type=params.get("filter_type", "blur"),
                    params=params.get("filter_params", {}),
                    output_path=_batch_output(),
                )
            elif operation == "blur":
                result = apply_filter(
                    input_path, filter_type="blur", params=params.get("filter_params", {}), output_path=_batch_output()
                )
            elif operation == "color_grade":
                result = apply_filter(
                    input_path,
                    filter_type="color_preset",
                    params={"preset": params.get("preset", "warm")},
                    output_path=_batch_output(),
                )
            elif operation == "watermark":
                result = watermark(
                    input_path,
                    image_path=params.get("image_path", ""),
                    position=params.get("position", "bottom-right"),
                    opacity=params.get("opacity", 0.7),
                    output_path=_batch_output(),
                )
            elif operation == "speed":
                result = speed(input_path, factor=params.get("factor", 1.0), output_path=_batch_output())
            elif operation == "fade":
                result = fade(
                    input_path,
                    fade_in=params.get("fade_in", 0.5),
                    fade_out=params.get("fade_out", 0.5),
                    output_path=_batch_output(),
                )
            elif operation == "normalize_audio":
                result = normalize_audio(
                    input_path, target_lufs=params.get("target_lufs", -16.0), output_path=_batch_output()
                )
            else:
                results.append({"input": input_path, "success": False, "error": f"Unknown operation: {operation}"})
                failed += 1
                continue

            results.append({"input": input_path, "success": True, "output_path": result.output_path})
            succeeded += 1
        except Exception as e:
            results.append({"input": input_path, "success": False, "error": str(e)})
            failed += 1

    return {
        "success": failed == 0,
        "total": len(inputs),
        "succeeded": succeeded,
        "failed": failed,
        "results": results,
    }
