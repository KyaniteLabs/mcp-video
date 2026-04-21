"""Video effects and filters engine.

Visual effects using FFmpeg filters and PIL for custom processing.
"""

from __future__ import annotations

# Re-exports for backward compatibility
from .core import (
    effect_chromatic_aberration,
    effect_glow,
    effect_noise,
    effect_scanlines,
    effect_vignette,
)
from .layout import layout_grid, layout_pip
from .mograph import mograph_count, mograph_progress
from .text import text_animated, text_subtitles
from .utility import auto_chapters, video_info_detailed
