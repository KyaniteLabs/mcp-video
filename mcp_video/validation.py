"""Centralized validation helpers and constants for mcp-video."""

from __future__ import annotations

from .errors import MCPVideoError
from .limits import *  # noqa: F403 — re-export all limit constants


# ---------------------------------------------------------------------------
# Validation constants — allowed values for various parameters
# ---------------------------------------------------------------------------

VALID_FORMATS = {"mp4", "webm", "gif", "mov"}
VALID_AUDIO_FORMATS = {"mp3", "aac", "wav", "ogg", "flac"}
VALID_PRESETS = {"ultrafast", "fast", "medium", "slow", "veryslow"}
VALID_CODECS = {"h264", "h265", "vp8", "vp9", "prores", "gif"}
VALID_XFADE_TRANSITIONS = {
    "fade", "dissolve", "wipeleft", "wiperight", "slideleft", "slideright",
    "slideup", "slidedown", "circlecrop", "radial",
    "smoothleft", "smoothright", "smoothup", "smoothdown",
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
    "ui-blip", "ui-click", "ui-tap", "ui-whoosh-up", "ui-whoosh-down",
    "drone-low", "drone-mid", "drone-tech",
    "chime-success", "chime-error", "chime-notification",
    "data-flow", "typing", "scan", "processing",
}
