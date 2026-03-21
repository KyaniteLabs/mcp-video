"""AgentCut Python client — clean API for programmatic video editing."""

from __future__ import annotations

from typing import Any, Literal

from .engine import (
    add_audio as _add_audio,
    add_text as _add_text,
    convert as _convert,
    edit_timeline as _edit_timeline,
    export_video as _export_video,
    extract_audio as _extract_audio,
    merge as _merge,
    preview as _preview,
    probe as _probe,
    storyboard as _storyboard,
    subtitles as _subtitles,
    speed as _speed,
    thumbnail as _thumbnail,
    trim as _trim,
    watermark as _watermark,
)
from .models import (
    EditResult,
    ExportFormat,
    Position,
    QualityLevel,
    StoryboardResult,
    ThumbnailResult,
    Timeline,
    VideoInfo,
)


class Client:
    """AgentCut client for programmatic video editing.

    Usage:
        from agentcut import Client
        editor = Client()

        result = editor.trim("input.mp4", start="00:00:30", duration="00:00:15")
        print(result.output_path)
    """

    def info(self, input_path: str) -> VideoInfo:
        """Get metadata about a video file."""
        return _probe(input_path)

    def trim(
        self,
        input: str,
        start: str | float = 0,
        duration: str | float | None = None,
        end: str | float | None = None,
        output: str | None = None,
    ) -> EditResult:
        """Trim a clip by start time and duration."""
        return _trim(input, start=start, duration=duration, end=end, output_path=output)

    def merge(
        self,
        clips: list[str],
        output: str | None = None,
        transitions: list[str] | None = None,
        transition_duration: float = 1.0,
    ) -> EditResult:
        """Merge multiple clips into one video.

        Args:
            clips: List of video file paths.
            output: Output file path.
            transitions: List of transition types (applied between each clip pair).
                Note: the underlying merge() function applies a single transition
                type between all clips. If multiple transitions are provided,
                the first one is used.
            transition_duration: Duration of each transition in seconds.
        """
        transition = transitions[0] if transitions else None
        return _merge(clips, output_path=output, transition=transition, transition_duration=transition_duration)

    def add_text(
        self,
        video: str,
        text: str,
        position: str = "top-center",
        font: str | None = None,
        size: int = 48,
        color: str = "white",
        shadow: bool = True,
        start_time: float | None = None,
        duration: float | None = None,
        output: str | None = None,
    ) -> EditResult:
        """Overlay text on a video."""
        return _add_text(
            video, text=text, position=position, font=font,
            size=size, color=color, shadow=shadow,
            start_time=start_time, duration=duration,
            output_path=output,
        )

    def add_audio(
        self,
        video: str,
        audio: str,
        volume: float = 1.0,
        fade_in: float = 0.0,
        fade_out: float = 0.0,
        mix: bool = False,
        start_time: float | None = None,
        output: str | None = None,
    ) -> EditResult:
        """Add or replace audio track."""
        return _add_audio(
            video, audio_path=audio, volume=volume,
            fade_in=fade_in, fade_out=fade_out, mix=mix,
            start_time=start_time, output_path=output,
        )

    def resize(
        self,
        video: str,
        width: int | None = None,
        height: int | None = None,
        aspect_ratio: str | None = None,
        quality: str = "high",
        output: str | None = None,
    ) -> EditResult:
        """Resize a video or change aspect ratio."""
        return _resize(
            video, width=width, height=height,
            aspect_ratio=aspect_ratio, quality=quality,
            output_path=output,
        )

    def convert(
        self,
        video: str,
        format: str = "mp4",
        quality: str = "high",
        output: str | None = None,
    ) -> EditResult:
        """Convert video to a different format."""
        return _convert(video, format=format, quality=quality, output_path=output)

    def speed(
        self,
        video: str,
        factor: float = 1.0,
        output: str | None = None,
    ) -> EditResult:
        """Change playback speed."""
        return _speed(video, factor=factor, output_path=output)

    def thumbnail(
        self,
        video: str,
        timestamp: float | None = None,
        output: str | None = None,
    ) -> ThumbnailResult:
        """Extract a frame from a video."""
        return _thumbnail(video, timestamp=timestamp, output_path=output)

    def preview(
        self,
        video: str,
        output: str | None = None,
        scale_factor: int = 4,
    ) -> EditResult:
        """Generate a fast low-res preview."""
        return _preview(video, output_path=output, scale_factor=scale_factor)

    def storyboard(
        self,
        video: str,
        output_dir: str | None = None,
        frame_count: int = 8,
    ) -> StoryboardResult:
        """Extract key frames as storyboard for human review."""
        return _storyboard(video, output_dir=output_dir, frame_count=frame_count)

    def subtitles(
        self,
        video: str,
        subtitle_file: str,
        output: str | None = None,
    ) -> EditResult:
        """Burn subtitles into a video."""
        return _subtitles(video, subtitle_path=subtitle_file, output_path=output)

    def watermark(
        self,
        video: str,
        image: str,
        position: str = "bottom-right",
        opacity: float = 0.7,
        margin: int = 20,
        output: str | None = None,
    ) -> EditResult:
        """Add image watermark."""
        return _watermark(
            video, image_path=image, position=position,
            opacity=opacity, margin=margin, output_path=output,
        )

    def export(
        self,
        video: str,
        output: str | None = None,
        quality: str = "high",
        format: str = "mp4",
    ) -> EditResult:
        """Render final video with quality settings."""
        return _export_video(video, output_path=output, quality=quality, format=format)

    def edit(self, timeline: dict[str, Any], output: str | None = None) -> EditResult:
        """Execute a full timeline-based edit from JSON."""
        tl = Timeline.model_validate(timeline)
        return _edit_timeline(tl, output_path=output)

    def extract_audio(
        self,
        video: str,
        output: str | None = None,
        format: str = "mp3",
    ) -> EditResult:
        """Extract audio track from video."""
        result_path = _extract_audio(video, output_path=output, format=format)
        return EditResult(
            output_path=result_path,
            operation="extract_audio",
            format=format,
        )


# Fix the circular import for resize
from .engine import resize as _resize
