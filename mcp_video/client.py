"""mcp-video Python client — clean API for programmatic video editing."""

from __future__ import annotations

from typing import Any, ClassVar, Literal

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
    ImageSequenceResult,
    MetadataResult,
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

    def __enter__(self) -> Client:
        return self

    def __exit__(self, *args: Any) -> None:
        pass

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

    _VALID_FORMATS: ClassVar[set[str]] = {"mp4", "webm", "gif", "mov"}
    _VALID_QUALITIES: ClassVar[set[str]] = {"low", "medium", "high", "ultra"}

    def convert(
        self,
        video: str,
        format: str = "mp4",
        quality: str = "high",
        output: str | None = None,
        two_pass: bool = False,
        target_bitrate: int | None = None,
    ) -> EditResult:
        """Convert video to a different format.

        Args:
            video: Input video path
            format: Output format (mp4, webm, gif, mov). CLI: -f/--format
            quality: Quality preset (low, medium, high, ultra). CLI: -q/--quality
            output: Output file path
            two_pass: Enable two-pass encoding
            target_bitrate: Target bitrate in kbps

        Raises:
            ValueError: If format or quality is invalid
        """
        if format not in self._VALID_FORMATS:
            raise ValueError(f"format must be one of {sorted(self._VALID_FORMATS)}, got {format}")
        if quality not in self._VALID_QUALITIES:
            raise ValueError(f"quality must be one of {sorted(self._VALID_QUALITIES)}, got {quality}")
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
        """Render final video with quality settings.

        Args:
            video: Input video path
            output: Output file path
            quality: Quality preset (low, medium, high, ultra). CLI: -q/--quality
            format: Output format (mp4, webm, gif, mov)

        Raises:
            ValueError: If quality is invalid
        """
        if quality not in self._VALID_QUALITIES:
            raise ValueError(f"quality must be one of {sorted(self._VALID_QUALITIES)}, got {quality}")
        if format not in self._VALID_FORMATS:
            raise ValueError(f"format must be one of {sorted(self._VALID_FORMATS)}, got {format}")
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
        from .engine import reverse as _reverse
        return _reverse(input_path=video, output_path=output)

    def chroma_key(
        self,
        video: str,
        color: str = "0x00FF00",
        similarity: float = 0.01,
        blend: float = 0.0,
        output: str | None = None,
    ) -> EditResult:
        """Remove a solid color background (green screen / chroma key)."""
        from .engine import chroma_key as _chroma_key
        return _chroma_key(input_path=video, color=color, similarity=similarity, blend=blend, output_path=output)

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
            background_path=background, overlay_path=overlay, position=position,
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
        return _split_screen(left_path=left, right_path=right, layout=layout, output_path=output)

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
        output: str | None = None,
    ) -> SubtitleResult:
        """Generate SRT subtitles from text entries and optionally burn into video."""
        return _generate_subtitles(entries, video, burn=burn, output_path=output)

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
        output_dir: str | None = None,
    ) -> dict:
        """Apply the same operation to multiple video files."""
        from .engine import video_batch
        return video_batch(inputs, operation=operation, params=params, output_dir=output_dir)

    # ------------------------------------------------------------------
    # Image Analysis
    # ------------------------------------------------------------------

    def extract_colors(
        self,
        image_path: str,
        n_colors: int = 5,
    ) -> dict:
        """Extract dominant colors from an image using K-means clustering."""
        from .image_engine import extract_colors
        return extract_colors(image_path, n_colors=n_colors)

    def generate_palette(
        self,
        image_path: str,
        harmony: str = "complementary",
        n_colors: int = 5,
    ) -> dict:
        """Generate a color harmony palette from an image's dominant color."""
        from .image_engine import generate_palette
        return generate_palette(image_path, harmony=harmony, n_colors=n_colors)

    def analyze_product(
        self,
        image_path: str,
        use_ai: bool = False,
        n_colors: int = 5,
    ) -> dict:
        """Analyze a product image — extract colors and optionally generate AI description."""
        from .image_engine import analyze_product
        return analyze_product(image_path, use_ai=use_ai, n_colors=n_colors)

    # ------------------------------------------------------------------
    # Remotion Integration
    # ------------------------------------------------------------------

    def remotion_render(
        self,
        project_path: str,
        composition_id: str,
        output: str | None = None,
        codec: str = "h264",
        crf: int | None = None,
        width: int | None = None,
        height: int | None = None,
        fps: float | None = None,
        concurrency: int | None = None,
        frames: str | None = None,
        props: dict | None = None,
        scale: float | None = None,
    ):
        """Render a Remotion composition to video."""
        from .remotion_engine import render
        return render(project_path, composition_id, output_path=output, codec=codec, crf=crf, width=width, height=height, fps=fps, concurrency=concurrency, frames=frames, props=props, scale=scale)

    def remotion_compositions(self, project_path: str) -> list[dict]:
        """List compositions in a Remotion project."""
        from .remotion_engine import compositions
        return compositions(project_path)

    def remotion_studio(self, project_path: str, port: int = 3000) -> dict:
        """Launch Remotion Studio for live preview."""
        from .remotion_engine import studio
        return studio(project_path, port=port)

    def remotion_still(
        self,
        project_path: str,
        composition_id: str,
        output: str | None = None,
        frame: int = 0,
        image_format: str = "png",
    ) -> dict:
        """Render a single frame as image."""
        from .remotion_engine import still
        return still(project_path, composition_id, output_path=output, frame=frame, image_format=image_format)

    def remotion_create_project(
        self,
        name: str,
        output_dir: str | None = None,
        template: str = "blank",
    ) -> dict:  # already has dict, keeping
        """Scaffold a new Remotion project.

        Args:
            name: Project name
            output_dir: Directory to create project in (default: current dir)
            template: Project template (blank, hello-world)

        Returns:
            dict with key "project_path" (str): absolute path to the new project
        """
        from .remotion_engine import create_project
        return create_project(name, output_dir=output_dir, template=template)

    def remotion_scaffold_template(
        self,
        project_path: str,
        spec: dict,
        slug: str,
    ) -> None:
        """Generate composition from spec."""
        from .remotion_engine import scaffold_template
        return scaffold_template(project_path, spec, slug)

    def remotion_validate(self, project_path: str, composition_id: str | None = None) -> dict:
        """Validate project for rendering readiness.

        Args:
            project_path: Path to the Remotion project directory
            composition_id: Optional specific composition to validate.
                If omitted, validates the overall project structure.

        Returns:
            RemotionValidationResult with pass/fail status and issues list
        """
        from .remotion_engine import validate
        return validate(project_path, composition_id=composition_id)

    def remotion_to_mcpvideo(
        self,
        project_path: str,
        composition_id: str,
        post_process: list[dict],
        output: str | None = None,
    ) -> dict:
        """Render a Remotion composition then post-process with mcp-video tools.

        Args:
            project_path: Path to the Remotion project directory
            composition_id: The composition ID to render
            post_process: List of post-processing operations. Each op has "op" (str) and
                optional "params" (dict). Valid op values: resize, convert, add_audio,
                normalize_audio, add_text, fade, watermark
            output: Output file path (auto-generated if omitted)

        Returns:
            RemotionPipelineResult with output path and applied operations
        """
        from .remotion_engine import render_and_post
        return render_and_post(project_path, composition_id, post_process, output_path=output)

    # ------------------------------------------------------------------
    # Audio Synthesis (P1 Features)
    # ------------------------------------------------------------------

    def audio_synthesize(
        self,
        output: str,
        waveform: Literal["sine", "square", "sawtooth", "triangle", "noise"] = "sine",
        frequency: float = 440.0,
        duration: float = 1.0,
        volume: float = 0.5,
        effects: dict | None = None,
    ) -> str:
        """Generate audio procedurally using synthesis.

        Args:
            output: Output WAV file path
            waveform: Type of waveform (sine, square, sawtooth, triangle, noise)
            frequency: Base frequency in Hz
            duration: Duration in seconds
            volume: Amplitude (0-1)
            effects: Optional effects dict with envelope, fade_in, fade_out, reverb, lowpass

        Returns:
            Path to generated WAV file
        """
        from .audio_engine import audio_synthesize
        return audio_synthesize(
            output=output,
            waveform=waveform,
            frequency=frequency,
            duration=duration,
            volume=volume,
            effects=effects,
        )

    def audio_preset(
        self,
        preset: str,
        output: str,
        pitch: Literal["low", "mid", "high"] = "mid",
        duration: float | None = None,
        intensity: float = 0.5,
    ) -> str:
        """Generate preset sound design elements.

        Presets: ui-blip, ui-click, ui-tap, ui-whoosh-up, ui-whoosh-down,
                 drone-low, drone-mid, drone-tech, drone-ominous,
                 chime-success, chime-error, chime-notification,
                 typing, scan, processing, data-flow,
                 upload, download

        Returns:
            Path to generated WAV file
        """
        from .audio_engine import audio_preset
        return audio_preset(
            preset=preset,
            output=output,
            pitch=pitch,
            duration=duration,
            intensity=intensity,
        )

    def audio_sequence(
        self,
        sequence: list[dict],
        output: str,
    ) -> str:
        """Compose multiple audio events into a timed sequence.

        Args:
            sequence: List of audio events with type, at (time), duration, etc.
            output: Output WAV file path

        Returns:
            Path to generated WAV file
        """
        from .audio_engine import audio_sequence
        return audio_sequence(sequence=sequence, output=output)

    def audio_compose(
        self,
        tracks: list[dict],
        duration: float,
        output: str,
    ) -> str:
        """Layer multiple audio tracks with mixing.

        Args:
            tracks: List of track configs. Each dict has keys:
                - file (str): Absolute path to WAV file (required)
                - volume (float): Volume multiplier 0-1 (default 1.0)
                - start (float): Start time offset in seconds (default 0.0)
                - loop (bool): Whether to loop the track (default False)
            duration: Total duration of output in seconds
            output: Output WAV file path

        CLI equivalent: mcp-video audio-compose --tracks '<json>' ...

        Returns:
            Path to generated WAV file
        """
        from .audio_engine import audio_compose
        return audio_compose(tracks=tracks, duration=duration, output=output)

    def audio_effects(
        self,
        input_path: str,
        output: str,
        effects: list[dict],
    ) -> str:
        """Apply audio effects chain.

        Args:
            input_path: Input WAV file path
            output: Output WAV file path
            effects: List of effect configs with type and parameters

        Returns:
            Path to processed WAV file
        """
        from .audio_engine import audio_effects
        return audio_effects(input_path=input_path, output=output, effects=effects)

    def add_generated_audio(
        self,
        video: str,
        audio_config: dict,
        output: str,
    ) -> str:
        """Add generated audio to a video file.

        Args:
            video: Input video path
            audio_config: Configuration with drone and/or events
            output: Output video path

        Returns:
            Path to output video
        """
        from .audio_engine import add_generated_audio
        return add_generated_audio(input_path=video, audio_config=audio_config, output_path=output)

    # ------------------------------------------------------------------
    # Visual Effects (P1 Features)
    # ------------------------------------------------------------------

    def effect_vignette(
        self,
        video: str,
        output: str,
        intensity: float = 0.5,
        radius: float = 0.8,
        smoothness: float = 0.5,
    ) -> str:
        """Apply vignette effect - darkened edges."""
        from .effects_engine import effect_vignette
        return effect_vignette(input_path=video, output=output, intensity=intensity, radius=radius, smoothness=smoothness)

    def effect_chromatic_aberration(
        self,
        video: str,
        output: str,
        intensity: float = 2.0,
        angle: float = 0,
    ) -> str:
        """Apply RGB channel separation effect."""
        from .effects_engine import effect_chromatic_aberration
        return effect_chromatic_aberration(input_path=video, output=output, intensity=intensity, angle=angle)

    def effect_scanlines(
        self,
        video: str,
        output: str,
        line_height: int = 2,
        opacity: float = 0.3,
        flicker: float = 0.1,
    ) -> str:
        """Apply CRT-style scanline overlay."""
        from .effects_engine import effect_scanlines
        return effect_scanlines(input_path=video, output=output, line_height=line_height, opacity=opacity, flicker=flicker)

    def effect_noise(
        self,
        video: str,
        output: str,
        intensity: float = 0.05,
        mode: str = "film",
        animated: bool = True,
    ) -> str:
        """Apply film grain / digital noise."""
        from .effects_engine import effect_noise
        return effect_noise(input_path=video, output=output, intensity=intensity, mode=mode, animated=animated)

    def effect_glow(
        self,
        video: str,
        output: str,
        intensity: float = 0.5,
        radius: int = 10,
        threshold: float = 0.7,
    ) -> str:
        """Apply bloom/glow effect for highlights."""
        from .effects_engine import effect_glow
        return effect_glow(input_path=video, output=output, intensity=intensity, radius=radius, threshold=threshold)

    # ------------------------------------------------------------------
    # Layout & Composition
    # ------------------------------------------------------------------

    _VALID_LAYOUTS: ClassVar[set[str]] = {"2x2", "3x1", "1x3", "2x3"}
    _VALID_PIP_POSITIONS: ClassVar[set[str]] = {"top-left", "top-right", "bottom-left", "bottom-right"}

    def layout_grid(
        self,
        clips: list[str],
        layout: str,
        output: str,
        gap: int = 10,
        padding: int = 20,
        background: str = "#141414",
    ) -> str:
        """Create grid-based multi-video layout.

        Args:
            clips: List of video file paths
            layout: Grid layout (2x2, 3x1, 1x3, 2x3). CLI: -l/--layout
            output: Output video path
            gap: Pixels between clips
            padding: Padding around grid
            background: Background color hex

        Raises:
            ValueError: If layout is invalid
        """
        if layout not in self._VALID_LAYOUTS:
            raise ValueError(f"layout must be one of {sorted(self._VALID_LAYOUTS)}, got {layout}")
        from .effects_engine import layout_grid
        return layout_grid(clips, layout, output, gap, padding, background)

    def layout_pip(
        self,
        main: str,
        pip: str,
        output: str,
        position: str = "bottom-right",
        size: float = 0.25,
        margin: int = 20,
        rounded_corners: bool = True,
        border: bool = True,
        border_color: str = "#CCFF00",
        border_width: int = 2,
    ) -> str:
        """Picture-in-picture overlay.

        Args:
            main: Main video path
            pip: Picture-in-picture video path
            output: Output video path
            position: Position (top-left, top-right, bottom-left, bottom-right). CLI: -p/--position
            size: PIP size as fraction of main (0-1)
            margin: Margin from edges in pixels
            rounded_corners: Apply rounded corners to PIP
            border: Add border around PIP
            border_color: Border color hex
            border_width: Border width in pixels

        Raises:
            ValueError: If position is invalid
        """
        if position not in self._VALID_PIP_POSITIONS:
            raise ValueError(f"position must be one of {sorted(self._VALID_PIP_POSITIONS)}, got {position}")
        from .effects_engine import layout_pip
        return layout_pip(main, pip, output, position, size, margin, rounded_corners, border, border_color, border_width)

    # ------------------------------------------------------------------
    # Text & Typography
    # ------------------------------------------------------------------

    def text_animated(
        self,
        video: str,
        text: str,
        output: str,
        animation: str = "fade",
        font: str = "Arial",
        size: int = 48,
        color: str = "white",
        position: str = "center",
        start: float = 0,
        duration: float = 3.0,
    ) -> str:
        """Add animated text to video."""
        from .effects_engine import text_animated
        return text_animated(video, text, output, animation, font, size, color, position, start, duration)

    def text_subtitles(
        self,
        video: str,
        subtitles: str,
        output: str,
        style: dict | None = None,
    ) -> str:
        """Burn subtitles from SRT/VTT with styling."""
        from .effects_engine import text_subtitles
        return text_subtitles(video=video, subtitles=subtitles, output=output, style=style)

    # ------------------------------------------------------------------
    # Motion Graphics
    # ------------------------------------------------------------------

    def mograph_count(
        self,
        start: int,
        end: int,
        duration: float,
        output: str,
        style: dict | None = None,
        fps: int = 30,
    ) -> str:
        """Generate animated number counter video.

        Args:
            start: Starting number (CLI: positional arg)
            end: Ending number (CLI: positional arg)
            duration: Animation duration in seconds
            output: Output video path
            style: Style dict with optional keys: font, size, color, glow
            fps: Frame rate

        Note:
            In the CLI (video-mograph-count), start and end are positional arguments.
            In the Python client, they must be passed as named arguments.
        """
        from .effects_engine import mograph_count
        return mograph_count(start, end, duration, output, style, fps)

    def mograph_progress(
        self,
        duration: float,
        output: str,
        style: str = "bar",
        color: str = "#CCFF00",
        track_color: str = "#333333",
        fps: int = 30,
    ) -> str:
        """Generate progress bar / loading animation."""
        from .effects_engine import mograph_progress
        return mograph_progress(duration, output, style, color, track_color, fps)

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def video_info_detailed(self, video: str) -> dict:
        """Get extended video metadata."""
        from .effects_engine import video_info_detailed
        return video_info_detailed(video)

    def auto_chapters(self, video: str, threshold: float = 0.3) -> list[tuple[float, str]]:
        """Auto-detect scene changes and create chapters."""
        from .effects_engine import auto_chapters
        return auto_chapters(video, threshold)

    # ------------------------------------------------------------------
    # Transitions (Wave 2)
    # ------------------------------------------------------------------

    def transition_glitch(self, clip1: str, clip2: str, output: str, duration: float = 0.5, intensity: float = 0.3) -> str:
        """Apply glitch transition between two video clips.

        Args:
            clip1: First video clip path
            clip2: Second video clip path
            output: Output video path
            duration: Transition duration in seconds. CLI: -d/--duration
            intensity: Glitch intensity 0-1. CLI: -i/--intensity
        """
        from .transitions_engine import transition_glitch
        return transition_glitch(clip1, clip2, output, duration, intensity)

    def transition_pixelate(self, clip1: str, clip2: str, output: str, duration: float = 0.4, pixel_size: int = 50) -> str:
        """Apply pixelate transition between two video clips.

        Args:
            clip1: First video clip path
            clip2: Second video clip path
            output: Output video path
            duration: Transition duration in seconds. CLI: -d/--duration
            pixel_size: Maximum pixel size during transition. CLI: -p/--pixel-size
        """
        from .transitions_engine import transition_pixelate
        return transition_pixelate(clip1, clip2, output, duration, pixel_size)

    def transition_morph(self, clip1: str, clip2: str, output: str, duration: float = 0.6, mesh_size: int = 10) -> str:
        """Apply morph transition between two video clips.

        Args:
            clip1: First video clip path
            clip2: Second video clip path
            output: Output video path
            duration: Transition duration in seconds. CLI: -d/--duration
            mesh_size: Grid subdivisions. CLI: -m/--mesh-size
        """
        from .transitions_engine import transition_morph
        return transition_morph(clip1, clip2, output, duration, mesh_size)

    # ------------------------------------------------------------------
    # AI Features (Wave 3)
    # ------------------------------------------------------------------

    def ai_remove_silence(self, video: str, output: str, silence_threshold: float = -50, min_silence_duration: float = 0.5, keep_margin: float = 0.1) -> str:
        """Remove silent sections from video."""
        from .ai_engine import ai_remove_silence
        return ai_remove_silence(video, output, silence_threshold, min_silence_duration, keep_margin)

    def ai_transcribe(self, video: str, output_srt: str | None = None, model: str = "base", language: str | None = None) -> dict:
        """Transcribe speech to text using Whisper.

        Args:
            video: Input video/audio path
            output_srt: If provided, write SRT subtitle file to this path
            model: Whisper model name (base, small, medium, large)
            language: Language code (e.g. "en"), or None for auto-detect

        Returns:
            dict with keys:
                - transcript (str): Full transcript text
                - segments (list[dict]): Timestamped segments
                - language (str): Detected language
        """
        from .ai_engine import ai_transcribe
        return ai_transcribe(video, output_srt, model, language)

    def analyze_video(
        self,
        video: str,
        *,
        whisper_model: str = "base",
        language: str | None = None,
        scene_threshold: float = 0.3,
        include_transcript: bool = True,
        include_scenes: bool = True,
        include_audio: bool = True,
        include_quality: bool = True,
        include_chapters: bool = True,
        include_colors: bool = True,
        output_srt: str | None = None,
        output_txt: str | None = None,
        output_md: str | None = None,
        output_json: str | None = None,
    ) -> dict:
        """Comprehensive video analysis — transcript, metadata, scenes, audio, quality, chapters, colors.

        Points at any existing video file and reverse-engineers everything about it.

        Args:
            video: Path to existing video file.
            whisper_model: Whisper model size (tiny, base, small, medium, large, turbo).
            language: Language code for transcription (auto-detect if None).
            scene_threshold: Scene change sensitivity 0.0–1.0.
            include_transcript: Run speech-to-text via Whisper (requires openai-whisper).
            include_scenes: Detect scene changes and boundaries.
            include_audio: Analyse audio waveform, peaks, and silence regions.
            include_quality: Run visual quality check.
            include_chapters: Auto-generate chapter markers from scene changes.
            include_colors: Extract dominant colors and extended metadata.
            output_srt: Optional path to write SRT subtitle file.
            output_txt: Optional path to write plain-text transcript.
            output_md: Optional path to write Markdown transcript with timestamps.
            output_json: Optional path to write full JSON transcript data.

        Returns:
            dict with keys: success, video, metadata, transcript, scenes, audio,
            chapters, colors, quality, errors.
        """
        from .ai_engine import analyze_video as _analyze_video
        return _analyze_video(
            video,
            whisper_model=whisper_model,
            language=language,
            scene_threshold=scene_threshold,
            include_transcript=include_transcript,
            include_scenes=include_scenes,
            include_audio=include_audio,
            include_quality=include_quality,
            include_chapters=include_chapters,
            include_colors=include_colors,
            output_srt=output_srt,
            output_txt=output_txt,
            output_md=output_md,
            output_json=output_json,
        )

    def ai_scene_detect(self, video: str, threshold: float = 0.3, use_ai: bool = False) -> list[dict]:
        """Detect scene changes in video."""
        from .ai_engine import ai_scene_detect
        return ai_scene_detect(video, threshold, use_ai)

    def ai_stem_separation(self, video: str, output_dir: str, stems: list[str] | None = None, model: str = "htdemucs") -> dict[str, str]:
        """Separate audio into stems using Demucs.

        Args:
            video: Input video/audio path
            output_dir: Directory to write separated stem files
            stems: List of stems to extract (e.g. ["vocals", "drums"]). Default (None)
                extracts all four: vocals, drums, bass, other
            model: Demucs model name (htdemucs, htdemucs_ft, mdx_extra)

        Returns:
            dict mapping stem name to output WAV file path, e.g.
            {"vocals": "/path/to/vocals.wav", "drums": "/path/to/drums.wav", ...}
        """
        from .ai_engine import ai_stem_separation
        return ai_stem_separation(video, output_dir, stems, model)

    def ai_upscale(self, video: str, output: str, scale: int = 2, model: str = "realesrgan") -> str:
        """Upscale video using AI super-resolution.

        Args:
            video: Input video path
            output: Output video path
            scale: Upscale factor (2 or 4). CLI: -s/--scale accepts {2, 4}
            model: Model name (realesrgan, bsrgan, swinir)

        Raises:
            ValueError: If scale is not 2 or 4
        """
        from .ai_engine import ai_upscale
        return ai_upscale(video, output, scale, model)

    def ai_color_grade(self, video: str, output: str, reference: str | None = None, style: str = "auto") -> str:
        """Auto color grade video."""
        from .ai_engine import ai_color_grade
        return ai_color_grade(video, output, reference, style)

    def audio_spatial(self, video: str, output: str, positions: list[dict], method: str = "hrtf") -> str:
        """Apply 3D spatial audio positioning."""
        from .ai_engine import audio_spatial
        return audio_spatial(video, output, positions, method)

    def quality_check(self, video: str, fail_on_warning: bool = False) -> dict:
        """Run visual quality guardrails on a video.

        Args:
            video: Video file path
            fail_on_warning: Treat warnings as failures

        Returns:
            dict with keys:
                - video (str): input path
                - overall_score (float): 0-100 average across all checks
                - all_passed (bool): True if every check passed
                - checks (list[dict]): per-check results with name, passed, score, message, details
                - recommendations (list[str]): improvement suggestions
        """
        from .quality_guardrails import quality_check
        return quality_check(video, fail_on_warning)

    def design_quality_check(
        self,
        video: str,
        auto_fix: bool = False,
        strict: bool = False,
    ) -> Any:  # DesignQualityReport
        """Run comprehensive design quality analysis.

        Checks layout, typography, color, motion, and composition.
        Can automatically fix issues where possible.

        Args:
            video: Video file path
            auto_fix: If True, automatically apply fixes to the video file.
                WARNING: This modifies the input video directly (overwrites in place).
                Use fix_design_issues() with a separate output path for non-destructive fixes.
            strict: If True, treat warnings as errors

        Returns:
            DesignQualityReport with fields:
                - overall_score (float): 0-100
                - technical_score (float): brightness, contrast, audio
                - design_score (float): layout, typography, color, motion
                - hierarchy_score (float): text size ratios
                - motion_score (float): fps, smoothness
                - issues (list[DesignIssue]): categorized issues with severity (error/warning/info)
                - fixes_applied (list[str]): descriptions of auto-applied fixes
                - recommendations (list[str]): improvement suggestions
        """
        from .design_quality import design_quality_check
        return design_quality_check(video, auto_fix=auto_fix, strict=strict)

    def fix_design_issues(
        self,
        video: str,
        output: str | None = None,
    ) -> str:
        """Auto-fix design issues in a video.

        Args:
            video: Input video path
            output: Output path (auto-generated if None)

        Returns:
            Path to fixed video
        """
        from .design_quality import fix_design_issues
        return fix_design_issues(video, output=output)


# Fix the circular import for resize
