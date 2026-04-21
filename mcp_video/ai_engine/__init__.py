"""AI-powered video processing using machine learning models."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from ..errors import InputFileError, MCPVideoError

# Public API re-exports
from .color import ai_color_grade as ai_color_grade
from .download import _resolve_video_source as _resolve_video_source
from .scene import ai_scene_detect as ai_scene_detect
from .silence import ai_remove_silence as ai_remove_silence
from .spatial import audio_spatial as audio_spatial
from .stem import ai_stem_separation as ai_stem_separation
from .transcribe import ai_transcribe as ai_transcribe
from .upscale import ai_upscale as ai_upscale

# Private helper re-exports for tests
from .download import _is_url as _is_url, _url_host as _url_host
import subprocess  # noqa: F401

from .spatial import _azimuth_to_pan as _azimuth_to_pan, _elevation_to_volume as _elevation_to_volume, _standard_scene_detect as _standard_scene_detect
from .upscale import _ai_upscale_opencv as _ai_upscale_opencv
from .download import _is_safe_url as _is_safe_url
from .transcribe import (
    _format_json_transcript as _format_json_transcript,
    _format_md as _format_md,
    _format_srt as _format_srt,
    _format_txt as _format_txt,
)

def analyze_video(
    video: str,
    *,
    whisper_model: str = "base",
    language: str | None = None,
    scene_threshold: float = 0.3,
    include_transcript: bool = True,
    include_scenes: bool = True,
    include_audio: bool = True,
    include_quality: bool = True,
    include_chapters: bool = True,
    include_colors: bool = True,
    output_srt: str | None = None,
    output_txt: str | None = None,
    output_md: str | None = None,
    output_json: str | None = None,
) -> dict[str, Any]:
    """Comprehensive video analysis — transcript, metadata, scenes, audio, quality, chapters, colors.

    Accepts either a **local file path** or an **HTTP/HTTPS URL**.

    For direct video URLs (e.g. ``https://example.com/clip.mp4``) the file is
    downloaded automatically via ``urllib``.  For streaming-platform URLs
    (YouTube, Vimeo, TikTok, Twitter/X, Instagram, Twitch, …) the optional
    ``yt-dlp`` package is used — install it with ``pip install yt-dlp``.

    Each sub-analysis is independent: one failure will not abort the others.

    Args:
        video: Local path **or** HTTP/HTTPS URL to the video.
        whisper_model: Whisper model size (tiny, base, small, medium, large, turbo).
        language: Language code for transcription (auto-detect if None).
        scene_threshold: Scene change sensitivity 0.0-1.0 (lower = more sensitive).
        include_transcript: Run speech-to-text via Whisper (requires openai-whisper).
        include_scenes: Detect scene changes and boundaries.
        include_audio: Analyse audio waveform, peaks, and silence regions.
        include_quality: Run visual quality check (brightness, contrast, saturation, audio levels).
        include_chapters: Auto-generate chapter markers from scene changes.
        include_colors: Extract dominant colors and extended metadata.
        output_srt: Optional path to write SRT subtitle file.
        output_txt: Optional path to write plain-text transcript.
        output_md: Optional path to write Markdown transcript with timestamps.
        output_json: Optional path to write full JSON transcript data.

    Returns:
        Dict with keys: success, video, source_url, metadata, transcript, scenes,
        audio, chapters, colors, quality, errors.
    """
    if "\x00" in video:
        raise InputFileError(video, "Invalid path: contains null bytes")

    # Validate scene_threshold
    if not (0.0 <= scene_threshold <= 1.0):
        raise MCPVideoError(
            f"scene_threshold must be between 0.0 and 1.0, got {scene_threshold}",
            error_type="validation_error",
            code="invalid_parameter",
        )

    # Validate output paths — ensure they don't escape safe directories
    for label, path in [
        ("output_srt", output_srt),
        ("output_txt", output_txt),
        ("output_md", output_md),
        ("output_json", output_json),
    ]:
        if path is not None:
            p = Path(path).resolve()
            # Block writes to system directories
            blocked_prefixes = (
                "/etc/",
                "/usr/",
                "/bin/",
                "/sbin/",
                "/var/",
                "/root/",
                "/boot/",
                "/dev/",
                "/proc/",
                "/sys/",
            )
            if any(str(p).startswith(prefix) for prefix in blocked_prefixes):
                raise MCPVideoError(
                    f"{label} path escapes safe directory: {path}", error_type="validation_error", code="unsafe_path"
                )

    # ── Resolve URL → local file ─────────────────────────────────────────────
    _tmp_dir: str | None = None
    try:
        local_video, _tmp_dir, source_url = _resolve_video_source(video)

        video_path = Path(local_video)
        if not video_path.exists():
            raise InputFileError(str(video_path))

        # Lazy imports — keep optional-dependency pattern consistent with the rest
        from .. import engine as _engine
        from .. import effects_engine as _effects
        from .. import quality_guardrails as _quality

        errors: list[dict[str, str]] = []

        # ── 1. Metadata (always runs) ────────────────────────────────────────
        try:
            info = _engine.probe(str(video_path))
            metadata: dict[str, Any] = {
                "path": str(video_path.resolve()),
                "duration": info.duration,
                "width": info.width,
                "height": info.height,
                "fps": info.fps,
                "codec": info.codec,
                "audio_codec": info.audio_codec,
                "audio_sample_rate": info.audio_sample_rate,
                "bitrate": info.bitrate,
                "size_bytes": info.size_bytes,
                "format": info.format,
            }
        except Exception as exc:
            metadata = {"path": str(video_path.resolve())}
            errors.append({"section": "metadata", "error": str(exc)})

        # ── 2. Transcript ────────────────────────────────────────────────────
        transcript_result: dict[str, Any] | None = None
        if include_transcript:
            try:
                raw = ai_transcribe(
                    str(video_path),
                    output_srt=output_srt,
                    model=whisper_model,
                    language=language,
                )
                segments = raw.get("segments", [])
                txt_path: str | None = None
                md_path: str | None = None
                json_path: str | None = None

                if output_txt:
                    Path(output_txt).write_text(_format_txt(segments), encoding="utf-8")
                    txt_path = output_txt
                if output_md:
                    Path(output_md).write_text(_format_md(segments), encoding="utf-8")
                    md_path = output_md
                if output_json:
                    json_data = _format_json_transcript(
                        raw.get("transcript", ""),
                        segments,
                        raw.get("language", "unknown"),
                    )
                    Path(output_json).write_text(
                        json.dumps(json_data, indent=2, ensure_ascii=False),
                        encoding="utf-8",
                    )
                    json_path = output_json

                transcript_result = {
                    "text": raw.get("transcript", ""),
                    "language": raw.get("language", "unknown"),
                    "segments": segments,
                    "srt_path": output_srt,
                    "txt_path": txt_path,
                    "md_path": md_path,
                    "json_path": json_path,
                }
            except RuntimeError as exc:
                # Whisper not installed — record gracefully
                errors.append({"section": "transcript", "error": str(exc)})
            except Exception as exc:
                errors.append({"section": "transcript", "error": str(exc)})

        # ── 3. Scenes ────────────────────────────────────────────────────────
        scenes_result: list[dict] | None = None
        if include_scenes:
            try:
                scene_det = _engine.detect_scenes(str(video_path), threshold=scene_threshold)
                scenes_result = scene_det.scenes
            except Exception as exc:
                errors.append({"section": "scenes", "error": str(exc)})

        # ── 4. Audio waveform ────────────────────────────────────────────────
        audio_result: dict[str, Any] | None = None
        if include_audio:
            try:
                waveform = _engine.audio_waveform(str(video_path))
                audio_result = {
                    "duration": waveform.duration,
                    "peaks": waveform.peaks,
                    "mean_level": waveform.mean_level,
                    "max_level": waveform.max_level,
                    "min_level": waveform.min_level,
                    "silence_regions": waveform.silence_regions,
                }
            except Exception as exc:
                errors.append({"section": "audio", "error": str(exc)})

        # ── 5. Chapters ──────────────────────────────────────────────────────
        chapters_result: list[dict] | None = None
        if include_chapters:
            try:
                raw_chapters = _effects.auto_chapters(str(video_path), threshold=scene_threshold)
                chapters_result = [{"timestamp": ts, "title": title} for ts, title in raw_chapters]
            except Exception as exc:
                errors.append({"section": "chapters", "error": str(exc)})

        # ── 6. Colors / extended info ────────────────────────────────────────
        # NOTE: Dominant color extraction is not yet implemented in effects_engine.
        # video_info_detailed() returns an empty list for dominant_colors.
        # Leaving this section as a placeholder — remove include_colors flag
        # and this block when colors are actually implemented.
        colors_result: list[Any] | None = None
        if include_colors:
            errors.append({"section": "colors", "error": "Color extraction not yet implemented"})

        # ── 7. Quality ───────────────────────────────────────────────────────
        quality_result: dict[str, Any] | None = None
        if include_quality:
            try:
                quality_result = _quality.quality_check(str(video_path))
            except Exception as exc:
                errors.append({"section": "quality", "error": str(exc)})

        return {
            "success": True,
            "video": str(video_path.resolve()),
            "source_url": source_url,
            "metadata": metadata,
            "transcript": transcript_result,
            "scenes": scenes_result,
            "audio": audio_result,
            "chapters": chapters_result,
            "colors": colors_result,
            "quality": quality_result,
            "errors": errors,
        }

    finally:
        # Clean up downloaded temp directory (if input was a URL)
        if _tmp_dir is not None:
            shutil.rmtree(_tmp_dir, ignore_errors=True)
