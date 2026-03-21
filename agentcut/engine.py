"""FFmpeg engine — all video processing operations."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .errors import (
    AgentCutError,
    CodecError,
    FFmpegNotFoundError,
    FFprobeNotFoundError,
    InputFileError,
    ProcessingError,
    ResolutionMismatchError,
    parse_ffmpeg_error,
)
from .models import (
    ASPECT_RATIOS,
    PREVIEW_PRESETS,
    QUALITY_PRESETS,
    EditResult,
    ErrorResult,
    ExportFormat,
    Position,
    QualityLevel,
    StoryboardResult,
    ThumbnailResult,
    Timeline,
    TimelineClip,
    VideoInfo,
    WatermarkSettings,
)


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
            capture_output=True, text=True, timeout=10,
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
        raise AgentCutError(
            f"FFmpeg filter '{name}' is not available. {feature} requires FFmpeg "
            f"to be compiled with additional libraries.\n"
            f"Install with: brew install ffmpeg (macOS) or rebuild FFmpeg with "
            f"libfreetype/libass support.",
            error_type="dependency_error",
            code=f"missing_filter_{name}",
            suggested_action={
                "auto_fix": False,
                "description": f"Reinstall FFmpeg with {name} support. "
                               "On macOS: brew reinstall ffmpeg",
            },
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _validate_input(path: str) -> None:
    if not os.path.isfile(path):
        raise InputFileError(path)


def _auto_output(input_path: str, suffix: str = "edited", ext: str | None = None) -> str:
    base, original_ext = os.path.splitext(input_path)
    ext = ext or original_ext or ".mp4"
    # Sanitize colons in base path — they break FFmpeg filter syntax
    # and are problematic on Windows
    safe_base = base.replace(":", "_")
    return f"{safe_base}_{suffix}{ext}"


def _auto_output_dir(input_path: str, suffix: str = "output") -> str:
    base, _ = os.path.splitext(input_path)
    safe_base = base.replace(":", "_")
    return f"{safe_base}_{suffix}"


def _run_ffmpeg(args: list[str]) -> subprocess.CompletedProcess[str]:
    cmd = [_ffmpeg(), "-y"] + args
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=600,  # 10-minute max
    )
    if proc.returncode != 0:
        raise parse_ffmpeg_error(proc.stderr)
    return proc


def _run_ffprobe_json(path: str) -> dict[str, Any]:
    cmd = [
        _ffprobe(),
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if proc.returncode != 0:
        raise InputFileError(path, f"FFprobe failed: {proc.stderr[:200]}")
    return json.loads(proc.stdout)


def _movflags_args(output_path: str) -> list[str]:
    """Return -movflags +faststart only for MP4/MOV containers."""
    ext = os.path.splitext(output_path)[1].lower()
    if ext in (".mp4", ".mov"):
        return ["-movflags", "+faststart"]
    return []


def _position_coords(position: Position, width: int = 0, height: int = 0) -> str:
    """Return drawtext x,y expression for a named position."""
    # These expressions use FFmpeg's text_w/text_h variables
    mapping: dict[Position, str] = {
        "top-left": "x=10:y=10",
        "top-center": "x=(w-text_w)/2:y=10",
        "top-right": f"x=w-text_w-10:y=10",
        "center-left": "x=10:y=(h-text_h)/2",
        "center": "x=(w-text_w)/2:y=(h-text_h)/2",
        "center-right": "x=w-text_w-10:y=(h-text_h)/2",
        "bottom-left": "x=10:y=h-text_h-10",
        "bottom-center": "x=(w-text_w)/2:y=h-text_h-10",
        "bottom-right": "x=w-text_w-10:y=h-text_h-10",
    }
    return mapping.get(position, mapping["center"])


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
    _run_ffmpeg([
        "-i", input_path,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
    ] + _movflags_args(output) + [
        output,
    ])
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
    args.extend([
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
    ] + _movflags_args(output) + [
        output,
    ])
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
    tmpdir = tempfile.mkdtemp(prefix="agentcut_")

    try:
        if needs_normalize:
            for i, clip in enumerate(clips):
                norm_path = os.path.join(tmpdir, f"clip_{i:04d}.mp4")
                _run_ffmpeg([
                    "-i", clip,
                    "-vf", f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                    "-c:a", "aac", "-b:a", "128k",
                    "-r", "30",
                    "-ar", "44100", "-ac", "2",
                    norm_path,
                ])
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
            _run_ffmpeg([
                "-f", "concat", "-safe", "0",
                "-i", concat_file,
                "-c", "copy",
            ] + _movflags_args(output) + [
                output,
            ])

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
            raise AgentCutError(
                f"Transition duration ({transition_duration}s) must be less than "
                f"clip {i+1} duration ({clip_dur:.1f}s)",
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
        filter_parts.append(f"[{in1}][{in2}]xfade=transition={xfade_type}:offset={offsets[i]:.3f}:duration={transition_duration:.3f}[{out}]")
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
        inputs + [
            "-filter_complex", filter_complex,
        ] + map_args + [
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        ] + audio_codec_args + _movflags_args(output) + [
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
) -> EditResult:
    """Overlay text on a video."""
    _validate_input(input_path)
    _require_filter("drawtext", "Text overlay")
    output = output_path or _auto_output(input_path, "titled")

    coords = _position_coords(position)
    fontfile = font or _default_font()

    # Escape FFmpeg drawtext special characters
    # Colons and backslashes must be escaped even inside single quotes
    # because FFmpeg parses filter options as key=value pairs with : delimiters
    escaped_text = text.replace("\\", "\\\\").replace("'", "'\\''").replace(":", "\\:")

    filter_parts = [
        f"drawtext=text='{escaped_text}'",
        f"fontsize={size}",
        f"fontcolor={color}",
        f"fontfile={fontfile}",
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

    _run_ffmpeg([
        "-i", input_path,
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "copy",
    ] + _movflags_args(output) + [
        output,
    ])

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

        filter_complex = (
            f"[0:a]anull[a0];"
            f"{delay}[1:a]{af}[a1];"
            f"[a0][a1]amix=inputs=2:duration=longest[aout]"
        )

        _run_ffmpeg([
            "-i", video_path, "-i", audio_path,
            "-filter_complex", filter_complex,
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "128k",
        ] + _movflags_args(output) + [
            output,
        ])
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

        args.extend([
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "128k",
            "-shortest",
        ] + _movflags_args(output) + [
            output,
        ])
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

    if aspect_ratio and aspect_ratio in ASPECT_RATIOS:
        w, h = ASPECT_RATIOS[aspect_ratio]
    elif aspect_ratio:
        raise AgentCutError(
            f"Unknown aspect ratio: {aspect_ratio}. "
            f"Available: {', '.join(ASPECT_RATIOS.keys())}",
            error_type="input_error",
            code="invalid_aspect_ratio",
        )
    elif width and height:
        w, h = width, height
    elif width:
        info = probe(input_path)
        ratio = info.height / info.width
        w, h = width, int(width * ratio)
    elif height:
        info = probe(input_path)
        ratio = info.width / info.height
        w, h = int(height * ratio), height
    else:
        raise AgentCutError("resize requires width+height, aspect_ratio, or single dimension")

    preset = QUALITY_PRESETS[quality]
    output = output_path or _auto_output(input_path, f"{w}x{h}")

    # Scale to fit within target, then pad to exact dimensions
    vf = (
        f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
        f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black"
    )

    _run_ffmpeg([
        "-i", input_path,
        "-vf", vf,
        "-c:v", "libx264",
        "-crf", str(preset["crf"]),
        "-preset", preset["preset"],
        "-c:a", "aac", "-b:a", "128k",
    ] + _movflags_args(output) + [
        output,
    ])

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
) -> EditResult:
    """Convert video to a different format."""
    _validate_input(input_path)
    preset = QUALITY_PRESETS[quality]
    ext = f".{format}" if not format.startswith(".") else format
    output = output_path or _auto_output(input_path, format, ext=ext)

    if format == "mp4":
        _run_ffmpeg([
            "-i", input_path,
            "-c:v", "libx264",
            "-crf", str(preset["crf"]),
            "-preset", preset["preset"],
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            output,
        ])
    elif format == "webm":
        _run_ffmpeg([
            "-i", input_path,
            "-c:v", "libvpx-vp9",
            "-crf", str(preset["crf"]),
            "-b:v", "0",
            "-c:a", "libopus",
            output,
        ])
    elif format == "mov":
        _run_ffmpeg([
            "-i", input_path,
            "-c:v", "libx264",
            "-crf", str(preset["crf"]),
            "-preset", preset["preset"],
            "-c:a", "pcm_s16le",
            output,
        ])
    elif format == "gif":
        # Two-pass palette-based GIF generation for quality
        tmpdir = tempfile.mkdtemp(prefix="agentcut_gif_")
        try:
            palette = os.path.join(tmpdir, "palette.png")
            _run_ffmpeg([
                "-i", input_path,
                "-vf", "fps=15,scale=480:-1:flags=lanczos,palettegen",
                "-y", palette,
            ])
            _run_ffmpeg([
                "-i", input_path,
                "-i", palette,
                "-lavfi", "fps=15,scale=480:-1:flags=lanczos [x]; [x][1:v] paletteuse",
                "-y", output,
            ])
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
    else:
        raise AgentCutError(f"Unsupported format: {format}", code="unsupported_format")

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
            )
    else:
        size_mb = None

    return EditResult(
        output_path=output,
        size_mb=round(size_mb, 2) if size_mb else None,
        format=format,
        operation="convert",
    )


def speed(
    input_path: str,
    factor: float = 1.0,
    output_path: str | None = None,
) -> EditResult:
    """Change playback speed. factor > 1 = faster, < 1 = slower."""
    _validate_input(input_path)
    if factor <= 0:
        raise AgentCutError("Speed factor must be positive")

    output = output_path or _auto_output(input_path, f"speed_{factor}x")

    # Use setpts for video, atempo for audio
    video_filter = f"setpts={1/factor}*PTS"
    audio_filter = f"atempo={factor}"

    # atempo only supports 0.5 to 100.0; chain if needed
    if factor < 0.5:
        chain_count = 2
        while factor ** (1 / chain_count) < 0.5:
            chain_count += 1
        tempo_val = factor ** (1 / chain_count)
        audio_filter = ",".join([f"atempo={tempo_val}"] * chain_count)
    elif factor > 100:
        chain_count = 2
        while factor ** (1 / chain_count) > 100:
            chain_count += 1
        tempo_val = factor ** (1 / chain_count)
        audio_filter = ",".join([f"atempo={tempo_val}"] * chain_count)

    # Check if input has audio
    info = probe(input_path)
    has_audio = info.audio_codec is not None

    if has_audio:
        _run_ffmpeg([
            "-i", input_path,
            "-filter_complex", f"[0:v]{video_filter}[v];[0:a]{audio_filter}[a]",
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
        ] + _movflags_args(output) + [
            output,
        ])
    else:
        _run_ffmpeg([
            "-i", input_path,
            "-vf", video_filter,
            "-an",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        ] + _movflags_args(output) + [
            output,
        ])

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

    _run_ffmpeg([
        "-ss", str(timestamp),
        "-i", input_path,
        "-vframes", "1",
        "-q:v", "2",
        "-y", output,
    ])

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
        raise AgentCutError("scale_factor must be at least 1", code="invalid_scale_factor")
    info = probe(input_path)

    w = max(info.width // scale_factor, 320)
    h = max(info.height // scale_factor, 240)

    output = output_path or _auto_output(input_path, "preview")

    _run_ffmpeg([
        "-i", input_path,
        "-vf", f"scale={w}:{h}",
        "-c:v", "libx264",
        "-crf", str(PREVIEW_PRESETS["crf"]),
        "-preset", PREVIEW_PRESETS["preset"],
        "-c:a", "aac", "-b:a", "64k", "-ac", "2",
    ] + _movflags_args(output) + [
        output,
    ])

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
        raise AgentCutError("frame_count must be at least 1", code="invalid_frame_count")
    dur = get_duration(input_path)

    out_dir = output_dir or _auto_output_dir(input_path, "storyboard")
    os.makedirs(out_dir, exist_ok=True)

    tmpdir = tempfile.mkdtemp(prefix="agentcut_sb_")
    try:
        frame_paths: list[str] = []
        interval = dur / (frame_count + 1)

        for i in range(frame_count):
            ts = interval * (i + 1)
            frame_name = f"frame_{i + 1:02d}_{ts:.1f}s.jpg"
            frame_path = os.path.join(out_dir, frame_name)

            _run_ffmpeg([
                "-ss", str(ts),
                "-i", input_path,
                "-vframes", "1",
                "-q:v", "2",
                "-y", frame_path,
            ])
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
            for i, fp in enumerate(frame_paths):
                filter_parts.append(f"[{i}:v]scale=480:270:force_original_aspect_ratio=decrease,pad=480:270:(ow-iw)/2:(oh-ih)/2[s{i}]")

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
                _run_ffmpeg(
                    inputs + [
                        "-filter_complex", filter_str,
                        "-map", "[vout]",
                        "-q:v", "2",
                        "-y", grid_path,
                    ]
                )
            except ProcessingError:
                # Grid creation failed — frames are still useful individually
                grid_path = None
        elif len(frame_paths) == 1:
            shutil.copy2(frame_paths[0], grid_path)
        else:
            grid_path = None

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

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
    # subtitles filter uses ':' as key=value separator and '\' for escaping
    escaped_sub_path = subtitle_path.replace("\\", "/").replace("'", "'\\''").replace(":", "\\:").replace("[", "\\[").replace("]", "\\]")
    escaped_style = style.replace("'", "\\'").replace(":", "\\:")

    _run_ffmpeg([
        "-i", input_path,
        "-vf", f"subtitles='{escaped_sub_path}':force_style='{escaped_style}'",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "copy",
    ] + _movflags_args(output) + [
        output,
    ])

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
) -> EditResult:
    """Add an image watermark to a video."""
    _validate_input(input_path)
    _validate_input(image_path)
    output = output_path or _auto_output(input_path, "watermarked")

    # Position expressions for the overlay
    position_map: dict[Position, str] = {
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

    overlay_pos = position_map.get(position, position_map["bottom-right"])
    # Format opacity for FFmpeg (0.0 to 1.0)
    opacity_fmt = f"{opacity:.2f}"

    _run_ffmpeg([
        "-i", input_path, "-i", image_path,
        "-filter_complex",
        f"[1:v]format=rgba,colorchannelmixer=aa={opacity_fmt}[wm];[0:v][wm]overlay={overlay_pos}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "copy",
    ] + _movflags_args(output) + [
        output,
    ])

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
        raise AgentCutError("Crop dimensions must be positive", code="invalid_crop")

    info = probe(input_path)
    if width > info.width or height > info.height:
        raise AgentCutError(
            f"Crop size ({width}x{height}) larger than video ({info.width}x{info.height})",
            code="crop_too_large",
        )

    if x is None:
        x = (info.width - width) // 2
    if y is None:
        y = (info.height - height) // 2

    output = output_path or _auto_output(input_path, f"crop_{width}x{height}")

    _run_ffmpeg([
        "-i", input_path,
        "-vf", f"crop={width}:{height}:{x}:{y}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "copy",
    ] + _movflags_args(output) + [
        output,
    ])

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
        raise AgentCutError("angle must be 0, 90, 180, or 270", code="invalid_angle")
    if angle == 0 and not flip_horizontal and not flip_vertical:
        raise AgentCutError("No rotation or flip specified", code="no_transform")

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

    _run_ffmpeg([
        "-i", input_path,
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
    ] + _movflags_args(output) + [
        output,
    ])

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
) -> EditResult:
    """Add fade in/out effect to a video."""
    _validate_input(input_path)
    if fade_in <= 0 and fade_out <= 0:
        raise AgentCutError("Specify fade_in and/or fade_out > 0", code="no_fade")

    output = output_path or _auto_output(input_path, "faded")
    info = probe(input_path)

    vf_parts: list[str] = []
    if fade_in > 0:
        vf_parts.append(f"fade=t=in:st=0:d={fade_in}")
    if fade_out > 0:
        fade_start = max(0, info.duration - fade_out)
        vf_parts.append(f"fade=t=out:st={fade_start:.3f}:d={fade_out}")

    vf = ",".join(vf_parts)

    _run_ffmpeg([
        "-i", input_path,
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "copy",
    ] + _movflags_args(output) + [
        output,
    ])

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
) -> EditResult:
    """Export a video with specified quality and format settings."""
    _validate_input(input_path)
    return convert(input_path, format=format, quality=quality, output_path=output_path)


# ---------------------------------------------------------------------------
# Timeline-based edit (composite operation)
# ---------------------------------------------------------------------------

def edit_timeline(timeline: Timeline | dict, output_path: str | None = None) -> EditResult:
    """Execute a full timeline-based edit described in JSON."""
    if isinstance(timeline, dict):
        timeline = Timeline.model_validate(timeline)
    tmpdir = tempfile.mkdtemp(prefix="agentcut_timeline_")
    try:
        video_clips: list[str] = []
        audio_clips: list[str] = []

        # Process video tracks
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

            elif track.type == "audio":
                for clip in track.clips:
                    _validate_input(clip.source)
                    audio_clips.append(clip.source)

        if not video_clips:
            raise AgentCutError("Timeline must have at least one video clip")

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
                    transition_list = [t.type.value for t in sorted_trans]
                    trans_duration = sorted_trans[0].duration
                    break
            merge(video_clips, output_path=merged, transitions=transition_list, transition_duration=trans_duration)

        # Apply text overlays
        current = merged
        for track in timeline.tracks:
            if track.type == "text":
                for elem in track.elements:
                    out = os.path.join(tmpdir, f"text_{len(video_clips):04d}.mp4")
                    add_text(
                        current,
                        text=elem.text,
                        position=elem.position,
                        start_time=elem.start,
                        duration=elem.duration,
                        **{k: v for k, v in elem.style.items() if k in ("font", "size", "color")},
                        shadow=elem.style.get("shadow", True),
                        output_path=out,
                    )
                    current = out

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


def extract_audio(
    input_path: str,
    output_path: str | None = None,
    format: str = "mp3",
) -> str:
    """Extract audio track from a video file."""
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
    codec = codec_map.get(format, "libmp3lame")

    _run_ffmpeg([
        "-i", input_path,
        "-vn",
        "-c:a", codec,
        "-b:a", "192k" if format != "wav" else "0",
        "-y", output,
    ])

    return output
