"""Audio attachment operations for the FFmpeg engine."""

from __future__ import annotations

from .defaults import DEFAULT_AUDIO_BITRATE
from .engine_probe import probe
from .engine_runtime_utils import (
    _auto_output,
    _has_audio,
    _movflags_args,
    _run_ffmpeg,
    _timed_operation,
)
from .ffmpeg_helpers import _validate_input_path, _escape_ffmpeg_filter_value, _run_ffprobe_json
from .models import EditResult


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
    video_path = _validate_input_path(video_path)
    audio_path = _validate_input_path(audio_path)
    output = output_path or _auto_output(video_path, "audio")

    video_info = probe(video_path)

    with _timed_operation() as timing:
        if mix and _has_audio(_run_ffprobe_json(video_path)):
            # Mix new audio with existing audio
            audio_filters: list[str] = []
            if volume != 1.0:
                audio_filters.append(f"volume={_escape_ffmpeg_filter_value(str(volume))}")
            if fade_in > 0:
                audio_filters.append(f"afade=t=in:st=0:d={_escape_ffmpeg_filter_value(str(fade_in))}")
            if fade_out > 0:
                audio_filters.append(
                    f"afade=t=out:st={_escape_ffmpeg_filter_value(str(video_info.duration - fade_out))}:"
                    f"d={_escape_ffmpeg_filter_value(str(fade_out))}"
                )

            af = ",".join(audio_filters) if audio_filters else "anull"

            delay = ""
            if start_time:
                safe_delay = _escape_ffmpeg_filter_value(str(int(start_time * 1000)))
                delay = f"[1:a]adelay={safe_delay}|{safe_delay},"

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
                    DEFAULT_AUDIO_BITRATE,
                    *_movflags_args(output),
                    output,
                ]
            )
        else:
            # Replace audio (or add if no existing audio)
            args = ["-i", video_path, "-i", audio_path]

            if start_time:
                safe_delay = _escape_ffmpeg_filter_value(str(int(start_time * 1000)))
                args.extend(["-filter_complex", f"[1:a]adelay={safe_delay}|{safe_delay}[a]"])
                args.extend(["-map", "0:v:0", "-map", "[a]"])
            else:
                args.extend(["-map", "0:v:0", "-map", "1:a:0"])

            audio_filters = []
            if volume != 1.0:
                audio_filters.append(f"volume={_escape_ffmpeg_filter_value(str(volume))}")
            if fade_in > 0:
                audio_filters.append(f"afade=t=in:st=0:d={_escape_ffmpeg_filter_value(str(fade_in))}")
            if fade_out > 0:
                audio_filters.append(
                    f"afade=t=out:st={_escape_ffmpeg_filter_value(str(video_info.duration - fade_out))}:"
                    f"d={_escape_ffmpeg_filter_value(str(fade_out))}"
                )

            if audio_filters:
                args.extend(["-af", ",".join(audio_filters)])

            args.extend(
                [
                    "-c:v",
                    "copy",
                    "-c:a",
                    "aac",
                    "-b:a",
                    DEFAULT_AUDIO_BITRATE,
                    "-shortest",
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
        operation="add_audio",
        elapsed_ms=timing["elapsed_ms"],
    )
