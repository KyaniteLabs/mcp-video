"""Merge operations for the FFmpeg engine."""

from __future__ import annotations

import os
import shutil
import tempfile

from .engine_probe import get_duration, probe
from .engine_runtime_utils import _auto_output, _movflags_args, _run_ffmpeg, _timed_operation, _validate_input
from .errors import InputFileError, MCPVideoError
from .models import EditResult


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

    with _timed_operation() as timing:
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
        elapsed_ms=timing["elapsed_ms"],
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
