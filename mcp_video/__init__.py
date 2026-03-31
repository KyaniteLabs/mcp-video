"""mcp-video — Video editing MCP server for AI agents."""

__version__ = "1.1.0"

from .client import Client
from .ai_engine import (
    ai_remove_silence,
    ai_color_grade,
    ai_transcribe,
    ai_scene_detect,
    ai_stem_separation,
    ai_upscale,
    audio_spatial,
)
from .audio_engine import (
    audio_synthesize,
    audio_preset,
    audio_sequence,
    audio_compose,
    audio_effects,
    add_generated_audio,
)
from .effects_engine import (
    effect_vignette,
    effect_chromatic_aberration,
    effect_scanlines,
    effect_noise,
    effect_glow,
    layout_grid,
    layout_pip,
    text_animated,
    text_subtitles,
    mograph_count,
    mograph_progress,
    video_info_detailed,
    auto_chapters,
)
from .transitions_engine import (
    transition_glitch,
    transition_pixelate,
    transition_morph,
)

from .quality_guardrails import quality_check, VisualQualityGuardrails, QualityReport
from .design_quality import (
    design_quality_check,
    fix_design_issues,
    DesignQualityGuardrails,
    DesignQualityReport,
    DesignIssue,
)

__all__ = [
    "Client",
    # Audio synthesis
    "audio_synthesize",
    "audio_preset",
    "audio_sequence",
    "audio_compose",
    "audio_effects",
    "add_generated_audio",
    # Visual effects
    "effect_vignette",
    "effect_chromatic_aberration",
    "effect_scanlines",
    "effect_noise",
    "effect_glow",
    # Layout
    "layout_grid",
    "layout_pip",
    # Text
    "text_animated",
    "text_subtitles",
    # Motion graphics
    "mograph_count",
    "mograph_progress",
    # Utility
    "video_info_detailed",
    "auto_chapters",
    # NEW: Transitions
    "transition_glitch",
    "transition_pixelate",
    "transition_morph",
    # NEW: AI Features
    "ai_remove_silence",
    "ai_transcribe",
    "ai_scene_detect",
    "ai_stem_separation",
    "ai_upscale",
    "ai_color_grade",
    "audio_spatial",
    # NEW: Quality Guardrails
    "quality_check",
    "VisualQualityGuardrails",
    "QualityReport",
    # NEW: Design Quality
    "design_quality_check",
    "fix_design_issues",
    "DesignQualityGuardrails",
    "DesignQualityReport",
    "DesignIssue",
]
