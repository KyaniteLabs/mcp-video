"""Centralized validation helpers and constants for mcp-video."""

from __future__ import annotations

from .errors import MCPVideoError
from .limits import *  # noqa: F403 — re-export all limit constants


# ---------------------------------------------------------------------------
# Validation helpers — all raise MCPVideoError with validation metadata
# ---------------------------------------------------------------------------


def _validate_ffmpeg_param(
    value,
    name,
    min_val=None,
    max_val=None,
    allowed_types=(int, float),
):
    """Validate a numeric FFmpeg parameter. Returns float(value)."""
    if not isinstance(value, allowed_types):
        raise MCPVideoError(
            f"Invalid {name}: expected {allowed_types}, got {type(value).__name__}",
            error_type="validation_error",
            code="invalid_parameter",
        )
    val = float(value)
    if min_val is not None and val < min_val:
        raise MCPVideoError(
            f"Invalid {name}: must be >= {min_val}, got {val}",
            error_type="validation_error",
            code="invalid_parameter",
        )
    if max_val is not None and val > max_val:
        raise MCPVideoError(
            f"Invalid {name}: must be <= {max_val}, got {val}",
            error_type="validation_error",
            code="invalid_parameter",
        )
    return val


def _validate_enum(value, name, allowed):
    """Validate value is in allowed set."""
    if value not in allowed:
        raise MCPVideoError(
            f"Invalid {name}: must be one of {sorted(allowed)}, got '{value}'",
            error_type="validation_error",
            code="invalid_parameter",
        )


def _validate_ffmpeg_string(value, name):
    """Reject FFmpeg filter-breaking characters: ; and null byte."""
    if not isinstance(value, str):
        raise MCPVideoError(
            f"Invalid {name}: must be a string",
            error_type="validation_error",
            code="invalid_parameter",
        )
    for ch in (";", "\x00"):
        if ch in value:
            raise MCPVideoError(
                f"Invalid {name}: contains forbidden character",
                error_type="validation_error",
                code="invalid_parameter",
            )


def _validate_output_path(path, name):
    """Basic output path validation — no null bytes, must be string."""
    if not isinstance(path, str) or "\x00" in path:
        raise MCPVideoError(
            f"Invalid {name}: path contains null bytes or is not a string",
            error_type="validation_error",
            code="invalid_parameter",
        )


def _validate_list(value, name, min_length=1):
    """Validate value is a list with optional minimum length."""
    if not isinstance(value, list):
        raise MCPVideoError(
            f"Invalid {name}: must be a list, got {type(value).__name__}",
            error_type="validation_error",
            code="invalid_parameter",
        )
    if len(value) < min_length:
        raise MCPVideoError(
            f"Invalid {name}: must have at least {min_length} items, got {len(value)}",
            error_type="validation_error",
            code="invalid_parameter",
        )
    return value


def _validate_dict(value, name, required_keys=None):
    """Validate value is a dict with optional required keys."""
    if not isinstance(value, dict):
        raise MCPVideoError(
            f"Invalid {name}: must be a dict, got {type(value).__name__}",
            error_type="validation_error",
            code="invalid_parameter",
        )
    if required_keys:
        missing = [k for k in required_keys if k not in value]
        if missing:
            raise MCPVideoError(
                f"Invalid {name}: missing required keys {missing}",
                error_type="validation_error",
                code="invalid_parameter",
            )
    return value


# ---------------------------------------------------------------------------
# Validation constants — allowed values for various parameters
# ---------------------------------------------------------------------------

VALID_FORMATS = {"mp4", "webm", "gif", "mov"}
VALID_AUDIO_FORMATS = {"mp3", "aac", "wav", "ogg", "flac"}
VALID_PRESETS = {"ultrafast", "fast", "medium", "slow", "veryslow"}
VALID_CODECS = {"h264", "h265", "vp8", "vp9", "prores", "gif"}
VALID_XFADE_TRANSITIONS = {
    "fade",
    "dissolve",
    "wipeleft",
    "wiperight",
    "slideleft",
    "slideright",
    "slideup",
    "slidedown",
    "circlecrop",
    "radial",
    "smoothleft",
    "smoothright",
    "smoothup",
    "smoothdown",
}
VALID_WAVEFORMS = {"sine", "square", "sawtooth", "triangle", "noise"}
VALID_AUDIO_EFFECT_TYPES = {"lowpass", "reverb", "normalize", "fade"}
VALID_SPATIAL_METHODS = {"hrtf", "panning"}
VALID_MOGRAPH_STYLES = {"bar", "circle", "dots"}
VALID_LAYOUTS = {"side-by-side", "top-bottom"}
VALID_REMOTION_TEMPLATES = {"blank", "hello-world"}
VALID_WHISPER_MODELS = {"tiny", "base", "small", "medium", "large", "turbo"}
VALID_DEMUCS_MODELS = {"htdemucs", "htdemucs_ft", "mdx", "mdx_extra", "mdx_extra_q"}
VALID_UPSCALE_MODELS = {"realesrgan", "bsrgan", "swinir"}
VALID_COLOR_GRADE_STYLES = {"auto", "warm", "cool", "vintage", "cinematic", "noir"}
VALID_AUDIO_SEQUENCE_TYPES = {"tone", "preset", "whoosh"}
VALID_AUDIO_PRESETS = {
    "ui-blip",
    "ui-click",
    "ui-tap",
    "ui-whoosh-up",
    "ui-whoosh-down",
    "drone-low",
    "drone-mid",
    "drone-tech",
    "chime-success",
    "chime-error",
    "chime-notification",
    "data-flow",
    "typing",
    "scan",
    "processing",
}


def get_valid_audio_presets():
    """Return the set of valid audio preset names.

    Lazily imports from audio_engine to avoid circular imports.
    Falls back to a hardcoded set if audio_engine is unavailable.
    """
    try:
        from .audio_engine import audio_preset  # noqa: F401

        # The presets dict is local to audio_preset(), so we use the
        # known set documented in its docstring.
        return {
            "ui-blip",
            "ui-click",
            "ui-tap",
            "ui-whoosh-up",
            "ui-whoosh-down",
            "drone-low",
            "drone-mid",
            "drone-tech",
            "chime-success",
            "chime-error",
            "chime-notification",
            "typing",
            "scan",
            "processing",
            "data-flow",
        }
    except ImportError:
        return {
            "ui-blip",
            "ui-click",
            "ui-tap",
            "ui-whoosh-up",
            "ui-whoosh-down",
            "drone-low",
            "drone-mid",
            "drone-tech",
            "chime-success",
            "chime-error",
            "chime-notification",
            "typing",
            "scan",
            "processing",
            "data-flow",
        }
