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
    elapsed_ms: float | None = Field(default=None, description="Wall-clock processing time in milliseconds")


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


class SubtitleResult(BaseModel):
    """Result of subtitle generation."""

    success: bool = True
    srt_path: str | None = Field(default=None, description="Path to generated SRT file")
    video_path: str | None = Field(default=None, description="Path to burned-in video (if burn=True)")
    entry_count: int


class WaveformResult(BaseModel):
    """Result of audio waveform extraction.

    The synthetic field indicates whether the peak data was synthetically
    generated due to astats filter failure (True) or extracted from actual
    audio analysis (False).
    """

    success: bool = True
    duration: float
    peaks: list[dict] = Field(description="List of {time, level} data points")
    mean_level: float
    max_level: float
    min_level: float
    silence_regions: list[dict] = Field(description="List of {start, end} silence regions")
    synthetic: bool = Field(
        default=False, description="True if data was synthetically generated due to analysis failure"
    )


class SceneDetectionResult(BaseModel):
    """Result of scene detection."""

    success: bool = True
    scenes: list[dict] = Field(description="List of {start, end, start_frame, end_frame} dicts")
    scene_count: int
    duration: float


class ImageSequenceResult(BaseModel):
    """Result of image sequence operations."""

    success: bool = True
    frame_paths: list[str] = Field(description="Paths to extracted/generated frame images")
    frame_count: int
    fps: float


class QualityMetricsResult(BaseModel):
    """Result of quality comparison between two videos."""

    success: bool = True
    metrics: dict[str, float] = Field(description="Metric scores, e.g. {'psnr': 42.5, 'ssim': 0.95}")
    overall_quality: str = Field(description="Quality assessment: high, medium, or low")


class MetadataResult(BaseModel):
    """Result of metadata read operation."""

    success: bool = True
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    comment: str | None = None
    date: str | None = None
    tags: dict[str, str] = Field(default_factory=dict, description="All metadata tags")


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

NamedPosition = Literal[
    "top-left",
    "top-center",
    "top-right",
    "center-left",
    "center",
    "center-right",
    "bottom-left",
    "bottom-center",
    "bottom-right",
]

# Position can be a named position string, pixel coordinates, or percentage coordinates
Position = NamedPosition | dict[str, float]

# --- Transition types ---

TransitionType = Literal["fade", "dissolve", "wipe-left", "wipe-right", "wipe-up", "wipe-down"]

# --- Filter types ---

FilterType = Literal[
    "blur",
    "sharpen",
    "brightness",
    "contrast",
    "saturation",
    "grayscale",
    "sepia",
    "invert",
    "vignette",
    "color_preset",
    "denoise",
    "deinterlace",
    "ken_burns",
    "reverb",
    "compressor",
    "pitch_shift",
    "noise_reduction",
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
    style: dict[str, Any] = Field(
        default_factory=lambda: {
            "font": "Arial",
            "size": 48,
            "color": "white",
            "shadow": True,
        }
    )


class TimelineImageOverlay(BaseModel):
    """An image overlay element in a timeline."""

    source: str
    position: Position = "center"
    x: int | None = None
    y: int | None = None
    width: int | None = None
    height: int | None = None
    opacity: float = 1.0
    start: float = 0.0
    duration: float | None = None


class TimelineTrack(BaseModel):
    """A track in the timeline (video, audio, text, or image)."""

    type: Literal["video", "audio", "text", "image"]
    clips: list[TimelineClip] = Field(default_factory=list)
    transitions: list[TimelineTransition] = Field(default_factory=list)
    elements: list[TimelineTextElement] = Field(default_factory=list)
    images: list[TimelineImageOverlay] = Field(default_factory=list)


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
