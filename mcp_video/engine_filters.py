"""Video and audio filter operations for the FFmpeg engine."""

from __future__ import annotations

from typing import Any

from .engine_probe import probe
from .engine_runtime_utils import (
    _auto_output,
    _movflags_args,
    _quality_args,
    _require_filter,
    _run_ffmpeg,
    _sanitize_ffmpeg_number,
)
from .errors import MCPVideoError
from .ffmpeg_helpers import _escape_ffmpeg_filter_value, _validate_input_path
from .models import ColorPreset, EditResult, FilterType


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
    """Build FFmpeg audio filter string for pitch shifting."""
    safe_semitones = _sanitize_ffmpeg_number(semitones, "semitones")
    rate_mult = 2 ** (safe_semitones / 12)
    new_rate = 44100 * rate_mult
    tempo = 1.0 / rate_mult
    if tempo < 0.5:
        chain_count = 2
        while tempo ** (1 / chain_count) < 0.5:
            chain_count += 1
        tempo_val = tempo ** (1 / chain_count)
        atempo_str = ",".join([f"atempo={_safe_filter_number(tempo_val, 'atempo')}"] * chain_count)
    elif tempo > 100:
        chain_count = 2
        while tempo ** (1 / chain_count) > 100:
            chain_count += 1
        tempo_val = tempo ** (1 / chain_count)
        atempo_str = ",".join([f"atempo={_safe_filter_number(tempo_val, 'atempo')}"] * chain_count)
    else:
        atempo_str = f"atempo={_safe_filter_number(tempo, 'atempo')}"
    return f"asetrate={_safe_filter_number(new_rate, 'sample_rate')},aresample=44100,{atempo_str}"


def apply_filter(
    input_path: str,
    filter_type: FilterType,
    params: dict[str, Any] | None = None,
    output_path: str | None = None,
    crf: int | None = None,
    preset: str | None = None,
) -> EditResult:
    """Apply a visual or audio filter to a video."""
    _validate_input_path(input_path)
    params = _sanitize_params(params or {})
    output = output_path or _auto_output(input_path, f"filter_{filter_type}")
    info = probe(input_path)

    filter_map = _filter_map(params, info.width, info.height)
    if filter_type not in filter_map:
        valid = ", ".join(sorted(filter_map))
        raise MCPVideoError(
            f"Unknown filter type '{filter_type}'. Valid types: {valid}",
            error_type="validation_error",
            code="invalid_filter_type",
        )
    filter_name, filter_string, is_audio = filter_map[filter_type]
    _require_filter(filter_name, f"Filter '{filter_type}'")

    if is_audio:
        _run_audio_filter(input_path, filter_type, filter_string, output)
    else:
        _run_video_filter(input_path, filter_string, output, crf, preset)

    result_info = probe(output)
    return EditResult(
        output_path=output,
        duration=result_info.duration,
        resolution=result_info.resolution,
        size_mb=result_info.size_mb,
        format="mp4",
        operation=f"filter_{filter_type}",
    )


def _sanitize_params(params: dict[str, Any]) -> dict[str, Any]:
    sanitized = dict(params)
    for key in sanitized:
        if key != "preset":
            sanitized[key] = _sanitize_ffmpeg_number(sanitized[key], key)
    return sanitized


def _filter_map(params: dict[str, Any], width: int, height: int) -> dict[FilterType, tuple[str, str, bool]]:
    return {
        "blur": ("boxblur", f"boxblur={_param(params, 'radius', 5)}:{_param(params, 'strength', 1)}", False),
        "sharpen": ("unsharp", f"unsharp=5:5:{_param(params, 'amount', 1.0)}:5:5:0.0", False),
        "brightness": ("eq", f"eq=brightness={_param(params, 'level', 0.1)}", False),
        "contrast": ("eq", f"eq=contrast={_param(params, 'level', 1.5)}", False),
        "saturation": ("eq", f"eq=saturation={_param(params, 'level', 1.5)}", False),
        "grayscale": ("hue", "hue=s=0", False),
        "sepia": ("colorchannelmixer", "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131", False),
        "invert": ("negate", "negate", False),
        "vignette": ("vignette", f"vignette=angle={_param(params, 'angle', 'PI/4')}", False),
        "color_preset": ("eq", _get_color_preset_filter(params.get("preset", "warm")), False),
        "denoise": (
            "hqdn3d",
            f"hqdn3d={_param(params, 'luma_spatial', 4)}:{_param(params, 'chroma_spatial', 3)}:{_param(params, 'luma_tmp', 6)}:{_param(params, 'chroma_tmp', 4.5)}",
            False,
        ),
        "deinterlace": ("yadif", "yadif=0:-1:0", False),
        "ken_burns": (
            "zoompan",
            f"zoompan=z='min(zoom+{_param(params, 'zoom_speed', 0.0015)},1.5)':d={_param(params, 'duration', 150)}:x='iw/2-(iw/zoom)/2':y='ih/2-(ih/zoom)/2':s={_safe_filter_int(width, 'width')}x{_safe_filter_int(height, 'height')}",
            False,
        ),
        "reverb": (
            "aecho",
            f"aecho={_param(params, 'in_gain', 0.8)}:{_param(params, 'out_gain', 0.9)}:{_param(params, 'delays', 60)}:{_param(params, 'decay', 0.2)}",
            True,
        ),
        "compressor": (
            "acompressor",
            f"acompressor=threshold={_param(params, 'threshold_db', -20)}dB:ratio={_param(params, 'ratio', 4)}:attack={_param(params, 'attack', 5)}:release={_param(params, 'release', 50)}",
            True,
        ),
        "pitch_shift": ("asetrate", _build_pitch_shift_filter(params.get("semitones", 0)), True),
        "noise_reduction": ("afftdn", f"afftdn=nf={_param(params, 'noise_level', -25)}", True),
    }


def _param(params: dict[str, Any], key: str, default: Any) -> str:
    if key not in params and isinstance(default, str):
        return _escape_ffmpeg_filter_value(default)
    return _safe_filter_number(params.get(key, default), key)


def _safe_filter_number(value: Any, name: str) -> str:
    return _escape_ffmpeg_filter_value(str(_sanitize_ffmpeg_number(value, name)))


def _safe_filter_int(value: Any, name: str) -> str:
    return _escape_ffmpeg_filter_value(str(int(_sanitize_ffmpeg_number(value, name))))


def _run_audio_filter(input_path: str, filter_type: FilterType, filter_string: str, output: str) -> None:
    input_info = probe(input_path)
    if input_info.audio_codec is None:
        raise MCPVideoError(
            f"Audio filter '{filter_type}' requires an audio stream, but this video has none",
            error_type="validation_error",
            code="audio_filter_no_audio",
        )
    _run_filter_ffmpeg(
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


def _run_video_filter(input_path: str, filter_string: str, output: str, crf: int | None, preset: str | None) -> None:
    _run_filter_ffmpeg(
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


def _run_filter_ffmpeg(args: list[str]) -> None:
    """Run an FFmpeg filter command while preserving engine error parsing."""
    _run_ffmpeg(args)
