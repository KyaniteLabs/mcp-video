"""mcp-video Python client — clean API for programmatic video editing."""

from __future__ import annotations

from typing import Any, Literal

from .engine import (
    add_audio as _add_audio,
    add_text as _add_text,
    apply_filter as _apply_filter,
    apply_mask as _apply_mask,
    audio_waveform as _audio_waveform,
    compare_quality as _compare_quality,
    convert as _convert,
    create_from_images as _create_from_images,
    crop as _crop,
    detect_scenes as _detect_scenes,
    edit_timeline as _edit_timeline,
    export_frames as _export_frames,
    export_video as _export_video,
    extract_audio as _extract_audio,
    fade as _fade,
    generate_subtitles as _generate_subtitles,
    merge as _merge,
    normalize_audio as _normalize_audio,
    overlay_video as _overlay_video,
    preview as _preview,
    probe as _probe,
    read_metadata as _read_metadata,
    resize as _resize,
    rotate as _rotate,
    split_screen as _split_screen,
    stabilize as _stabilize,
    storyboard as _storyboard,
    subtitles as _subtitles,
    speed as _speed,
    thumbnail as _thumbnail,
    trim as _trim,
    watermark as _watermark,
    write_metadata as _write_metadata,
)
from .models import (
    EditResult,
    ExportFormat,
    ImageSequenceResult,
    MetadataResult,
    Position,
    QualityLevel,
    QualityMetricsResult,
    SceneDetectionResult,
    StoryboardResult,
    SubtitleResult,
    ThumbnailResult,
    VideoInfo,
    WaveformResult,
)


class Client:
    """mcp-video client for programmatic video editing.

    Usage:
        from mcp_video import Client
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
            transitions: Transition types applied between each clip pair.
                One per boundary (len = len(clips)-1). If fewer provided,
                the last type is repeated. Example: ["fade", "dissolve", "fade"].
            transition_duration: Duration of each transition in seconds.
        """
        return _merge(clips, output_path=output, transitions=transitions, transition_duration=transition_duration)

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
        crf: int | None = None,
        preset: str | None = None,
    ) -> EditResult:
        """Overlay text on a video."""
        return _add_text(
            video, text=text, position=position, font=font,
            size=size, color=color, shadow=shadow,
            start_time=start_time, duration=duration,
            output_path=output, crf=crf, preset=preset,
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
        two_pass: bool = False,
        target_bitrate: int | None = None,
    ) -> EditResult:
        """Convert video to a different format."""
        return _convert(video, format=format, quality=quality, output_path=output, two_pass=two_pass, target_bitrate=target_bitrate)

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

    def extract_frame(
        self,
        video: str,
        timestamp: float | None = None,
        output: str | None = None,
    ) -> ThumbnailResult:
        """Extract a frame from a video. Alias for thumbnail()."""
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
        crf: int | None = None,
        preset: str | None = None,
    ) -> EditResult:
        """Add image watermark."""
        return _watermark(
            video, image_path=image, position=position,
            opacity=opacity, margin=margin, output_path=output,
            crf=crf, preset=preset,
        )

    def crop(
        self,
        video: str,
        width: int,
        height: int,
        x: int | None = None,
        y: int | None = None,
        output: str | None = None,
    ) -> EditResult:
        """Crop a video to a rectangular region."""
        return _crop(video, width=width, height=height, x=x, y=y, output_path=output)

    def rotate(
        self,
        video: str,
        angle: int = 0,
        flip_horizontal: bool = False,
        flip_vertical: bool = False,
        output: str | None = None,
    ) -> EditResult:
        """Rotate and/or flip a video."""
        return _rotate(video, angle=angle, flip_horizontal=flip_horizontal, flip_vertical=flip_vertical, output_path=output)

    def fade(
        self,
        video: str,
        fade_in: float = 0.0,
        fade_out: float = 0.0,
        output: str | None = None,
        crf: int | None = None,
        preset: str | None = None,
    ) -> EditResult:
        """Add fade in/out effect to a video."""
        return _fade(
            video, fade_in=fade_in, fade_out=fade_out,
            output_path=output, crf=crf, preset=preset,
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
        return _edit_timeline(timeline, output_path=output)

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

    def filter(
        self,
        video: str,
        filter_type: str,
        params: dict | None = None,
        output: str | None = None,
        crf: int | None = None,
        preset: str | None = None,
    ) -> EditResult:
        """Apply a visual filter to a video."""
        return _apply_filter(
            video, filter_type=filter_type, params=params,
            output_path=output, crf=crf, preset=preset,
        )

    def blur(
        self,
        video: str,
        radius: int = 5,
        strength: int = 1,
        output: str | None = None,
    ) -> EditResult:
        """Apply blur effect to a video."""
        return _apply_filter(
            video, filter_type="blur",
            params={"radius": radius, "strength": strength},
            output_path=output,
        )

    def reverse(
        self,
        video: str,
        output: str | None = None,
    ) -> EditResult:
        """Reverse video and audio playback."""
        return self._run_tool("video_reverse", input_path=video, output_path=output)

    def chroma_key(
        self,
        video: str,
        color: str = "0x00FF00",
        similarity: float = 0.01,
        blend: float = 0.0,
        output: str | None = None,
    ) -> EditResult:
        """Remove a solid color background (green screen / chroma key)."""
        return self._run_tool("video_chroma_key", input_path=video, color=color, similarity=similarity, blend=blend, output_path=output)

    def color_grade(
        self,
        video: str,
        preset: str = "warm",
        output: str | None = None,
    ) -> EditResult:
        """Apply a color grading preset to a video."""
        return _apply_filter(
            video, filter_type="color_preset",
            params={"preset": preset},
            output_path=output,
        )

    def normalize_audio(
        self,
        video: str,
        target_lufs: float = -16.0,
        output: str | None = None,
    ) -> EditResult:
        """Normalize audio loudness to a target LUFS level."""
        return _normalize_audio(video, target_lufs=target_lufs, output_path=output)

    def overlay_video(
        self,
        background: str,
        overlay: str,
        position: str = "top-right",
        width: int | None = None,
        height: int | None = None,
        opacity: float = 0.8,
        start_time: float | None = None,
        duration: float | None = None,
        output: str | None = None,
        crf: int | None = None,
        preset: str | None = None,
    ) -> EditResult:
        """Picture-in-picture: overlay a video on top of another."""
        return _overlay_video(
            background, overlay_path=overlay, position=position,
            width=width, height=height, opacity=opacity,
            start_time=start_time, duration=duration,
            output_path=output, crf=crf, preset=preset,
        )

    def split_screen(
        self,
        left: str,
        right: str,
        layout: str = "side-by-side",
        output: str | None = None,
    ) -> EditResult:
        """Place two videos side by side or top/bottom."""
        return _split_screen(left, right_path=right, layout=layout, output_path=output)

    def detect_scenes(
        self,
        video: str,
        threshold: float = 0.3,
        min_scene_duration: float = 1.0,
    ) -> SceneDetectionResult:
        """Detect scene changes in a video."""
        return _detect_scenes(video, threshold=threshold, min_scene_duration=min_scene_duration)

    def create_from_images(
        self,
        images: list[str],
        output: str | None = None,
        fps: float = 30.0,
    ) -> EditResult:
        """Create a video from a sequence of images."""
        return _create_from_images(images, output_path=output, fps=fps)

    def export_frames(
        self,
        video: str,
        output_dir: str | None = None,
        fps: float = 1.0,
        format: str = "jpg",
    ) -> ImageSequenceResult:
        """Export frames from a video as images."""
        return _export_frames(video, output_dir=output_dir, fps=fps, format=format)

    def generate_subtitles(
        self,
        video: str,
        entries: list[dict],
        burn: bool = False,
    ) -> SubtitleResult:
        """Generate SRT subtitles from text entries and optionally burn into video."""
        return _generate_subtitles(entries, video, burn=burn)

    def audio_waveform(
        self,
        video: str,
        bins: int = 50,
    ) -> WaveformResult:
        """Extract audio waveform data (peaks and silence regions)."""
        return _audio_waveform(video, bins=bins)

    def compare_quality(
        self,
        original: str,
        distorted: str,
        metrics: list[str] | None = None,
    ) -> QualityMetricsResult:
        """Compare video quality between original and processed versions."""
        return _compare_quality(original, distorted, metrics=metrics)

    def read_metadata(
        self,
        video: str,
    ) -> MetadataResult:
        """Read metadata tags from a video/audio file."""
        return _read_metadata(video)

    def write_metadata(
        self,
        video: str,
        metadata: dict[str, str],
        output: str | None = None,
    ) -> EditResult:
        """Write metadata tags to a video/audio file."""
        return _write_metadata(video, metadata=metadata, output_path=output)

    def stabilize(
        self,
        video: str,
        smoothing: float = 15,
        zooming: float = 0,
        output: str | None = None,
    ) -> EditResult:
        """Stabilize a shaky video."""
        return _stabilize(video, smoothing=smoothing, zooming=zooming, output_path=output)

    def apply_mask(
        self,
        video: str,
        mask: str,
        feather: int = 5,
        output: str | None = None,
    ) -> EditResult:
        """Apply an image mask to a video with edge feathering."""
        return _apply_mask(video, mask_path=mask, feather=feather, output_path=output)

    def batch(
        self,
        inputs: list[str],
        operation: str,
        params: dict | None = None,
    ) -> dict:
        """Apply the same operation to multiple video files."""
        from .engine import video_batch
        return video_batch(inputs, operation=operation, params=params)


# Fix the circular import for resize
from .engine import resize as _resize
