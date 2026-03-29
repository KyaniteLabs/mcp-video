"""Pydantic models for mcp-video operations."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


# --- Video metadata ---

class VideoInfo(BaseModel):
    """Metadata about a video file."""

    path: str
    duration: float
    width: int
    height: int
    fps: float
    codec: str
    audio_codec: str | None = None
    audio_sample_rate: int | None = None
    bitrate: int | None = None
    size_bytes: int | None = None
    format: str | None = None

    @property
    def resolution(self) -> str:
        return f"{self.width}x{self.height}"

    @property
    def aspect_ratio(self) -> str:
        from math import gcd
        g = gcd(self.width, self.height)
        return f"{self.width // g}:{self.height // g}"

    @property
    def size_mb(self) -> float | None:
        if self.size_bytes is not None:
            return round(self.size_bytes / (1024 * 1024), 2)
        return None


# --- Operation results ---

class EditResult(BaseModel):
    """Result of a video editing operation."""

    success: bool = True
    output_path: str
    duration: float | None = None
    resolution: str | None = None
    size_mb: float | None = None
    format: str | None = None
    operation: str | None = None
    progress: float | None = Field(default=None, description="Final progress percentage (0-100)")
    thumbnail_base64: str | None = Field(default=None, description="Base64-encoded JPEG thumbnail of the first frame")


class ErrorResult(BaseModel):
    """Structured error result returned to agents."""

    success: Literal[False] = False
    error: dict[str, Any]


class StoryboardResult(BaseModel):
    """Result of storyboard generation."""

    success: bool = True
    frames: list[str] = Field(description="Paths to extracted frame images")
    grid: str | None = Field(default=None, description="Path to storyboard grid image")
    count: int


class ThumbnailResult(BaseModel):
    """Result of thumbnail extraction."""

    success: bool = True
    frame_path: str
    timestamp: float


# --- Quality settings ---

QualityLevel = Literal["low", "medium", "high", "ultra"]

QUALITY_PRESETS: dict[QualityLevel, dict[str, Any]] = {
    "low": {"crf": 35, "preset": "fast", "max_height": 480},
    "medium": {"crf": 28, "preset": "medium", "max_height": 720},
    "high": {"crf": 23, "preset": "slow", "max_height": 1080},
    "ultra": {"crf": 18, "preset": "veryslow", "max_height": 1080},
}

PREVIEW_PRESETS: dict[str, Any] = {
    "crf": 35,
    "preset": "ultrafast",
    "scale_factor": 4,  # 1/4 resolution
}

# --- Aspect ratio presets ---

ASPECT_RATIOS: dict[str, tuple[int, int]] = {
    "16:9": (1920, 1080),
    "9:16": (1080, 1920),
    "1:1": (1080, 1080),
    "4:3": (1440, 1080),
    "4:5": (1080, 1350),
    "21:9": (2560, 1080),
}

# --- Text positioning ---

Position = Literal[
    "top-left", "top-center", "top-right",
    "center-left", "center", "center-right",
    "bottom-left", "bottom-center", "bottom-right",
]

# --- Transition types ---

TransitionType = Literal["fade", "dissolve", "wipe-left", "wipe-right", "wipe-up", "wipe-down"]

# --- Filter types ---

FilterType = Literal[
    "blur", "sharpen", "brightness", "contrast", "saturation",
    "grayscale", "sepia", "invert", "vignette", "color_preset",
]

ColorPreset = Literal["warm", "cool", "vintage", "cinematic", "noir"]

# --- Split layout ---

SplitLayout = Literal["side-by-side", "top-bottom"]

# --- Format types ---

ExportFormat = Literal["mp4", "webm", "gif", "mov"]

# --- Timeline DSL models ---

class TimelineClip(BaseModel):
    """A single clip in a timeline track."""

    source: str
    start: float = 0.0
    duration: float | None = None
    trim_start: float = 0.0
    trim_end: float | None = None
    volume: float = 1.0
    fade_in: float = 0.0
    fade_out: float = 0.0


class TimelineTransition(BaseModel):
    """A transition between two clips."""

    after_clip: int
    type: TransitionType = "fade"
    duration: float = 1.0


class TimelineTextElement(BaseModel):
    """A text overlay element in a timeline."""

    text: str
    start: float = 0.0
    duration: float | None = None
    position: Position = "top-center"
    style: dict[str, Any] = Field(default_factory=lambda: {
        "font": "Arial",
        "size": 48,
        "color": "white",
        "shadow": True,
    })


class TimelineTrack(BaseModel):
    """A track in the timeline (video, audio, or text)."""

    type: Literal["video", "audio", "text"]
    clips: list[TimelineClip] = Field(default_factory=list)
    transitions: list[TimelineTransition] = Field(default_factory=list)
    elements: list[TimelineTextElement] = Field(default_factory=list)


class TimelineExport(BaseModel):
    """Export settings for a timeline render."""

    format: ExportFormat = "mp4"
    quality: QualityLevel = "high"


class Timeline(BaseModel):
    """Full timeline specification for complex edits."""

    width: int = 1920
    height: int = 1080
    duration: float | None = None
    tracks: list[TimelineTrack] = Field(default_factory=list)
    export: TimelineExport = Field(default_factory=TimelineExport)


# --- Watermark settings ---

class WatermarkSettings(BaseModel):
    """Settings for watermark overlay."""

    image_path: str
    position: Position = "bottom-right"
    opacity: float = 0.7
    margin: int = 20
