"""mcp-video — Video editing MCP server for AI agents."""

__version__ = "1.1.1"

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
    "DesignIssue",
    "DesignQualityGuardrails",
    "DesignQualityReport",
    "QualityReport",
    "VisualQualityGuardrails",
    "add_generated_audio",
    "ai_color_grade",
    # NEW: AI Features
    "ai_remove_silence",
    "ai_scene_detect",
    "ai_stem_separation",
    "ai_transcribe",
    "ai_upscale",
    "audio_compose",
    "audio_effects",
    "audio_preset",
    "audio_sequence",
    "audio_spatial",
    # Audio synthesis
    "audio_synthesize",
    "auto_chapters",
    # NEW: Design Quality
    "design_quality_check",
    "effect_chromatic_aberration",
    "effect_glow",
    "effect_noise",
    "effect_scanlines",
    # Visual effects
    "effect_vignette",
    "fix_design_issues",
    # Layout
    "layout_grid",
    "layout_pip",
    # Motion graphics
    "mograph_count",
    "mograph_progress",
    # NEW: Quality Guardrails
    "quality_check",
    # Text
    "text_animated",
    "text_subtitles",
    # NEW: Transitions
    "transition_glitch",
    "transition_morph",
    "transition_pixelate",
    # Utility
    "video_info_detailed",
]
