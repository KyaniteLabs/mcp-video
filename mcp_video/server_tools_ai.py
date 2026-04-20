"""MCP tool registrations for AI analysis and quality guardrails."""

from __future__ import annotations

from typing import Any

from .errors import MCPVideoError
from .server_app import _error_result, _result, mcp
from .ffmpeg_helpers import _validate_input_path
from .validation import (
    VALID_COLOR_GRADE_STYLES,
    VALID_DEMUCS_MODELS,
    VALID_UPSCALE_MODELS,
    VALID_WHISPER_MODELS,
)

# ---------------------------------------------------------------------------
# AI Feature Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def video_ai_remove_silence(
    input_path: str,
    output_path: str,
    silence_threshold: float = -50,
    min_silence_duration: float = 0.5,
    keep_margin: float = 0.1,
) -> dict[str, Any]:
    """Remove silent sections from video."""
    if not -70 <= silence_threshold <= 0:
        return _error_result(
            MCPVideoError(
                f"silence_threshold must be between -70 and 0, got {silence_threshold}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if min_silence_duration <= 0:
        return _error_result(
            MCPVideoError(
                f"min_silence_duration must be positive, got {min_silence_duration}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if keep_margin < 0:
        return _error_result(
            MCPVideoError(
                f"keep_margin must be non-negative, got {keep_margin}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    try:
        _validate_input_path(input_path)
        from .ai_engine import ai_remove_silence

        return _result(ai_remove_silence(input_path, output_path, silence_threshold, min_silence_duration, keep_margin))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return {"success": False, "error": {"type": "internal_error", "code": "unexpected_error", "message": str(e)}}


@mcp.tool()
def video_ai_transcribe(
    input_path: str,
    output_srt: str | None = None,
    model: str = "base",
    language: str | None = None,
) -> dict[str, Any]:
    """Transcribe speech to text using Whisper."""
    if model not in VALID_WHISPER_MODELS:
        return _error_result(
            MCPVideoError(
                f"Invalid model: must be one of {sorted(VALID_WHISPER_MODELS)}, got '{model}'",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    try:
        _validate_input_path(input_path)
        from .ai_engine import ai_transcribe

        return _result(ai_transcribe(input_path, output_srt, model, language))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return {"success": False, "error": {"type": "internal_error", "code": "unexpected_error", "message": str(e)}}


@mcp.tool()
def video_analyze(
    input_path: str,
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

    Accepts a local file path or an HTTP/HTTPS URL. Direct video URLs
    (e.g. https://example.com/clip.mp4) are downloaded automatically.
    Streaming-platform URLs (YouTube, Vimeo, TikTok, Twitter/X, Instagram,
    Twitch, …) require yt-dlp (pip install yt-dlp).
    Each sub-analysis is independent so one failure will not abort the others.

    Args:
        input_path: Local path or HTTP/HTTPS URL to the video.
        whisper_model: Whisper model size (tiny, base, small, medium, large, turbo).
        language: Language code for transcription (auto-detect if None).
        scene_threshold: Scene change sensitivity 0.0-1.0.
        include_transcript: Run speech-to-text via Whisper (requires openai-whisper).
        include_scenes: Detect scene changes and boundaries.
        include_audio: Analyse audio waveform, peaks, and silence regions.
        include_quality: Run visual quality check.
        include_chapters: Auto-generate chapter markers from scene changes.
        include_colors: Extract dominant colors and extended metadata.
        output_srt: Optional path to write SRT subtitle file.
        output_txt: Optional path to write plain-text transcript.
        output_md: Optional path to write Markdown transcript with timestamps.
        output_json: Optional path to write full JSON transcript data.
    """
    if whisper_model not in VALID_WHISPER_MODELS:
        return _error_result(
            MCPVideoError(
                f"Invalid model: must be one of {sorted(VALID_WHISPER_MODELS)}, got '{whisper_model}'",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if not 0.0 <= scene_threshold <= 1.0:
        return _error_result(
            MCPVideoError(
                f"scene_threshold must be between 0.0 and 1.0, got {scene_threshold}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    try:
        _validate_input_path(input_path)
        from .ai_engine import analyze_video

        return analyze_video(
            input_path,
            whisper_model=whisper_model,
            language=language,
            scene_threshold=scene_threshold,
            include_transcript=include_transcript,
            include_scenes=include_scenes,
            include_audio=include_audio,
            include_quality=include_quality,
            include_chapters=include_chapters,
            include_colors=include_colors,
            output_srt=output_srt,
            output_txt=output_txt,
            output_md=output_md,
            output_json=output_json,
        )
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return {"success": False, "error": {"type": "internal_error", "code": "unexpected_error", "message": str(e)}}


@mcp.tool()
def video_ai_scene_detect(
    input_path: str,
    threshold: float = 0.3,
    use_ai: bool = False,
) -> dict[str, Any]:
    """Detect scene changes in video."""
    if not 0.0 <= threshold <= 1.0:
        return _error_result(
            MCPVideoError(
                f"threshold must be between 0.0 and 1.0, got {threshold}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    try:
        _validate_input_path(input_path)
        from .ai_engine import ai_scene_detect

        return _result(ai_scene_detect(input_path, threshold, use_ai))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return {"success": False, "error": {"type": "internal_error", "code": "unexpected_error", "message": str(e)}}


@mcp.tool()
def video_ai_stem_separation(
    input_path: str,
    output_dir: str,
    stems: list[str] | None = None,
    model: str = "htdemucs",
) -> dict[str, Any]:
    """Separate audio into stems using Demucs."""
    if model not in VALID_DEMUCS_MODELS:
        return _error_result(
            MCPVideoError(
                f"Invalid model: must be one of {sorted(VALID_DEMUCS_MODELS)}, got '{model}'",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if stems is not None and not isinstance(stems, list):
        return _error_result(
            MCPVideoError(
                f"stems must be a list, got {type(stems).__name__}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    try:
        _validate_input_path(input_path)
        from .ai_engine import ai_stem_separation

        return _result(ai_stem_separation(input_path, output_dir, stems, model))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return {"success": False, "error": {"type": "internal_error", "code": "unexpected_error", "message": str(e)}}


@mcp.tool()
def video_ai_upscale(
    input_path: str,
    output_path: str,
    scale: int = 2,
    model: str = "realesrgan",
) -> dict[str, Any]:
    """Upscale video using AI super-resolution."""
    if scale not in {2, 4}:
        return _error_result(
            MCPVideoError(
                f"scale must be 2 or 4, got {scale}",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    if model not in VALID_UPSCALE_MODELS:
        return _error_result(
            MCPVideoError(
                f"Invalid model: must be one of {sorted(VALID_UPSCALE_MODELS)}, got '{model}'",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    try:
        _validate_input_path(input_path)
        from .ai_engine import ai_upscale

        return _result(ai_upscale(input_path, output_path, scale, model))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return {"success": False, "error": {"type": "internal_error", "code": "unexpected_error", "message": str(e)}}


@mcp.tool()
def video_ai_color_grade(
    input_path: str,
    output_path: str,
    reference_path: str | None = None,
    style: str = "auto",
) -> dict[str, Any]:
    """Auto color grade video."""
    if style not in VALID_COLOR_GRADE_STYLES:
        return _error_result(
            MCPVideoError(
                f"Invalid style: must be one of {sorted(VALID_COLOR_GRADE_STYLES)}, got '{style}'",
                error_type="validation_error",
                code="invalid_parameter",
            )
        )
    try:
        _validate_input_path(input_path)
        _validate_input_path(reference_path)
        from .ai_engine import ai_color_grade

        return _result(ai_color_grade(input_path, output_path, reference_path, style))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return {"success": False, "error": {"type": "internal_error", "code": "unexpected_error", "message": str(e)}}


@mcp.tool()
def video_quality_check(
    input_path: str,
    fail_on_warning: bool = False,
) -> dict[str, Any]:
    """Run visual quality checks on a video.

    Analyzes brightness, contrast, saturation, audio levels,
    and color balance. Returns quality scores and recommendations.

    Args:
        input_path: Absolute path to video file
        fail_on_warning: If True, treat warnings as failures
    """
    try:
        _validate_input_path(input_path)
        from .quality_guardrails import quality_check

        return _result(quality_check(input_path, fail_on_warning))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return {"success": False, "error": {"type": "internal_error", "code": "unexpected_error", "message": str(e)}}


@mcp.tool()
def video_design_quality_check(
    input_path: str,
    auto_fix: bool = False,
    strict: bool = False,
) -> dict[str, Any]:
    """Run comprehensive design quality analysis on a video.

    Checks layout, typography, color, motion, and composition quality.
    Can automatically fix issues where possible.

    Args:
        input_path: Absolute path to video file
        auto_fix: If True, automatically apply fixes
        strict: If True, treat warnings as errors
    """
    try:
        _validate_input_path(input_path)
        from .design_quality import design_quality_check

        return _result(design_quality_check(input_path, auto_fix=auto_fix, strict=strict))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return {"success": False, "error": {"type": "internal_error", "code": "unexpected_error", "message": str(e)}}


@mcp.tool()
def video_fix_design_issues(
    input_path: str,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Auto-fix design issues in a video.

    Applies automatic fixes for brightness, contrast, saturation,
    and audio level issues.

    Args:
        input_path: Absolute path to input video
        output_path: Absolute path for output (auto-generated if omitted)
    """
    try:
        _validate_input_path(input_path)
        from .design_quality import fix_design_issues

        return _result(fix_design_issues(input_path, output_path))
    except MCPVideoError as e:
        return _error_result(e)
    except Exception as e:
        return {"success": False, "error": {"type": "internal_error", "code": "unexpected_error", "message": str(e)}}
