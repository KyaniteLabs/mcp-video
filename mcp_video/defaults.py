"""Default values for mcp-video.

All default constants used across the codebase are centralized here
per AGENTS.md Rule 12.
"""

from __future__ import annotations

# Re-export encoding defaults from limits for backward compatibility
from .limits import DEFAULT_CRF, DEFAULT_FFMPEG_TIMEOUT, DEFAULT_PRESET  # noqa: F401

# Quality presets
DEFAULT_QUALITY = "high"
DEFAULT_FORMAT = "mp4"

# Video dimensions
DEFAULT_FPS = 30
DEFAULT_GIF_FPS = 15
DEFAULT_THUMBNAIL_WIDTH = 320
DEFAULT_STORYBOARD_WIDTH = 480
DEFAULT_STORYBOARD_HEIGHT = 270

# Audio defaults
DEFAULT_SAMPLE_RATE = 44100
DEFAULT_CHANNELS = 1
DEFAULT_AUDIO_CHANNELS = 2
DEFAULT_AUDIO_VOLUME = 0.5
DEFAULT_LUFS_TARGET = -16.0
DEFAULT_LRA_TARGET = 11.0
DEFAULT_AUDIO_BITRATE = "128k"

# Text overlay defaults
DEFAULT_FONT_SIZE = 48
DEFAULT_TEXT_COLOR = "white"
DEFAULT_TEXT_POSITION = "top-center"

# Transition defaults
DEFAULT_TRANSITION_DURATION = 1.0

# Grid/layout defaults
DEFAULT_GRID_CELL_WIDTH = 640
DEFAULT_GRID_CELL_HEIGHT = 480
