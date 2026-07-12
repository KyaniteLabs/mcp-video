"""Descriptor-aware render primitives for governed salvage recipes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from kinocut.defaults import DEFAULT_SALVAGE_FREEZE_CODEC, DEFAULT_SALVAGE_FREEZE_PIXEL_FORMAT
from kinocut.engine_probe import _build_video_info
from kinocut.errors import InputFileError, MCPVideoError, ProcessingError
from kinocut.ffmpeg_helpers import (
    _build_ffmpeg_cmd,
    _escape_ffmpeg_filter_value,
    _run_ffmpeg,
    _run_ffprobe_json,
    _validate_output_path,
)
from kinocut.models import VideoInfo


def _invalid_policy(message: str) -> MCPVideoError:
    return MCPVideoError(message, error_type="validation_error", code="invalid_salvage_policy")


def _probe_source(path: Path, *, pass_fds: tuple[int, ...]) -> VideoInfo:
    """Probe one already-verified held descriptor without reopening ambient state."""

    try:
        data = _run_ffprobe_json(str(path), pass_fds=pass_fds)
    except ProcessingError as exc:
        raise InputFileError(str(path), "Not a valid video file") from exc
    return _build_video_info(str(path), data)


def _trim_source(
    source: Path,
    output: Path,
    *,
    start: float,
    duration: float,
    pass_fds: tuple[int, ...],
) -> None:
    """Accurately trim a descriptor-backed source into a private output."""

    _validate_output_path(str(output))
    args = ["-i", str(source)]
    if start:
        args.extend(["-ss", str(start)])
    args.extend(["-t", str(duration), *_build_ffmpeg_cmd(output_path=str(output))])
    _run_ffmpeg(args, pass_fds=pass_fds)


def _render(
    recipe: str,
    policy: dict[str, Any],
    source: Path,
    output: Path,
    *,
    pass_fds: tuple[int, ...] = (),
) -> None:
    """Render one recipe while keeping descriptor-backed input inherited."""

    if recipe == "clean_edges":
        duration = _probe_source(source, pass_fds=pass_fds).duration - policy["trim_start"] - policy["trim_end"]
        if duration <= 0:
            raise _invalid_policy("trim removes the complete source")
        _trim_source(
            source,
            output,
            start=policy["trim_start"],
            duration=duration,
            pass_fds=pass_fds,
        )
    elif recipe == "region_crop":
        _render_region_crop(policy, source, output, pass_fds=pass_fds)
    elif recipe == "still_frame":
        _render_still(source, output, policy["timestamp"], pass_fds=pass_fds)
    elif recipe == "freeze_extension":
        _render_freeze(source, output, policy["extension_seconds"], pass_fds=pass_fds)
    else:
        _render_background_plate(source, output, policy["region"], pass_fds=pass_fds)


def _render_region_crop(policy: dict[str, Any], source: Path, output: Path, *, pass_fds: tuple[int, ...]) -> None:
    info, region = _probe_source(source, pass_fds=pass_fds), policy["region"]
    width, height = round(info.width * region["width"]), round(info.height * region["height"])
    x, y = round(info.width * region["x"]), round(info.height * region["y"])
    _validate_output_path(str(output))
    _run_ffmpeg(
        _build_ffmpeg_cmd(
            str(source),
            output_path=str(output),
            video_filter=_crop_filter(width, height, x, y),
            audio_codec="copy",
        ),
        pass_fds=pass_fds,
    )


def _render_still(source: Path, output: Path, timestamp: float, *, pass_fds: tuple[int, ...]) -> None:
    if timestamp >= _probe_source(source, pass_fds=pass_fds).duration:
        raise _invalid_policy("still timestamp is outside the source")
    _run_ffmpeg(
        ["-ss", str(timestamp), "-i", str(source), "-frames:v", "1", str(output)],
        pass_fds=pass_fds,
    )


def _render_freeze(source: Path, output: Path, extension: float, *, pass_fds: tuple[int, ...]) -> None:
    duration = _probe_source(source, pass_fds=pass_fds).duration + extension
    safe_extension = _escape_ffmpeg_filter_value(str(extension))
    _run_ffmpeg(
        [
            "-i",
            str(source),
            "-vf",
            f"tpad=stop_mode=clone:stop_duration={safe_extension}",
            "-t",
            str(duration),
            "-an",
            "-c:v",
            DEFAULT_SALVAGE_FREEZE_CODEC,
            "-pix_fmt",
            DEFAULT_SALVAGE_FREEZE_PIXEL_FORMAT,
            str(output),
        ],
        pass_fds=pass_fds,
    )


def _render_background_plate(
    source: Path, output: Path, region: dict[str, float], *, pass_fds: tuple[int, ...]
) -> None:
    info = _probe_source(source, pass_fds=pass_fds)
    width, height = round(info.width * region["width"]), round(info.height * region["height"])
    x, y = round(info.width * region["x"]), round(info.height * region["y"])
    _run_ffmpeg(
        [
            "-i",
            str(source),
            "-vf",
            _crop_filter(width, height, x, y),
            "-an",
            "-c:v",
            DEFAULT_SALVAGE_FREEZE_CODEC,
            "-pix_fmt",
            DEFAULT_SALVAGE_FREEZE_PIXEL_FORMAT,
            str(output),
        ],
        pass_fds=pass_fds,
    )


def _crop_filter(width: int, height: int, x: int, y: int) -> str:
    values = (_escape_ffmpeg_filter_value(str(value)) for value in (width, height, x, y))
    safe_width, safe_height, safe_x, safe_y = values
    return f"crop={safe_width}:{safe_height}:{safe_x}:{safe_y}"
