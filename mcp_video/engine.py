"""FFmpeg engine — all video processing operations."""

from __future__ import annotations

import os
import shutil
import tempfile
from typing import Any
from collections.abc import Callable

from .errors import MCPVideoError
from .models import (
    QUALITY_PRESETS,
    ColorPreset,
    EditResult,
    ExportFormat,
    FilterType,
    NamedPosition,
    QualityLevel,
    Timeline,
    TimelineImageOverlay,
)
from .ffmpeg_helpers import _escape_ffmpeg_filter_value
from .engine_audio_waveform import audio_waveform as audio_waveform
from .engine_audio_ops import add_audio as add_audio
from .engine_audio_normalize import normalize_audio as normalize_audio
from .engine_chroma_key import chroma_key as chroma_key
from .engine_compare_quality import compare_quality as compare_quality
from .engine_crop import crop as crop
from .engine_detect_scenes import detect_scenes as detect_scenes
from .engine_edit import trim as trim
from .engine_export import export_video as export_video
from .engine_extract_audio import extract_audio as extract_audio
from .engine_frames import export_frames as export_frames
from .engine_images import create_from_images as create_from_images
from .engine_mask import apply_mask as _apply_mask
from .engine_merge import merge as merge
from .engine_metadata import read_metadata as read_metadata
from .engine_metadata import write_metadata as write_metadata
from .engine_overlay import overlay_video as _overlay_video
from .engine_preview import preview as preview

# Compatibility re-export: callers still import get_duration from mcp_video.engine.
from .engine_probe import get_duration as get_duration
from .engine_probe import probe as probe
from .engine_resize import resize as resize
from .engine_rotate import rotate as rotate
from .engine_reverse import reverse as reverse
from .engine_fade import fade as fade
from .engine_runtime_utils import (
    _auto_output as _auto_output,
    _auto_output_dir as _auto_output_dir,
    _check_filter_available as _check_filter_available,
    _default_font as _default_font,
    _ffmpeg as _ffmpeg,
    _ffprobe as _ffprobe,
    _generate_thumbnail_base64 as _generate_thumbnail_base64,
    _get_audio_stream as _get_audio_stream,
    _get_video_stream as _get_video_stream,
    _has_audio as _has_audio,
    _movflags_args as _movflags_args,
    _parse_ffmpeg_time as _parse_ffmpeg_time,
    _position_coords as _position_coords,
    _quality_args as _quality_args,
    _require_filter as _require_filter,
    _resolve_position as _resolve_position,
    _run_ffmpeg as _run_ffmpeg,
    _run_ffmpeg_with_progress as _run_ffmpeg_with_progress,
    _sanitize_ffmpeg_number as _sanitize_ffmpeg_number,
    _validate_chroma_color as _validate_chroma_color,
    _validate_color as _validate_color,
    _validate_input as _validate_input,
    _validate_position as _validate_position,
)
from .engine_speed import speed as speed
from .engine_stabilize import stabilize as stabilize
from .engine_storyboard import storyboard as storyboard
from .engine_split_screen import split_screen as _split_screen
from .engine_subtitle_generate import generate_subtitles as generate_subtitles
from .engine_subtitles import subtitles as subtitles
from .engine_text import add_text as add_text
from .engine_thumbnail import thumbnail as thumbnail
from .engine_transcode import normalize as normalize
from .engine_watermark import watermark as watermark

apply_mask = _apply_mask
overlay_video = _overlay_video
split_screen = _split_screen


# ---------------------------------------------------------------------------
# Core operations
# ---------------------------------------------------------------------------


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
# Compositing & overlays
# ---------------------------------------------------------------------------


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
