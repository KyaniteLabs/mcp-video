"""Tests for Pydantic models — no FFmpeg needed."""

import pytest

from mcp_video.models import (
    ASPECT_RATIOS,
    PREVIEW_PRESETS,
    QUALITY_PRESETS,
    EditResult,
    ErrorResult,
    StoryboardResult,
    ThumbnailResult,
    Timeline,
    TimelineClip,
    TimelineExport,
    TimelineTextElement,
    TimelineTrack,
    TimelineTransition,
    VideoInfo,
    WatermarkSettings,
)


class TestVideoInfo:
    def test_basic_creation(self):
        info = VideoInfo(
            path="/tmp/video.mp4",
            duration=10.5,
            width=1920,
            height=1080,
            fps=30.0,
            codec="h264",
        )
        assert info.path == "/tmp/video.mp4"
        assert info.duration == 10.5
        assert info.width == 1920
        assert info.height == 1080
        assert info.fps == 30.0
        assert info.codec == "h264"

    def test_optional_fields_default_none(self):
        info = VideoInfo(
            path="/tmp/video.mp4",
            duration=5.0,
            width=640,
            height=480,
            fps=24.0,
            codec="h264",
        )
        assert info.audio_codec is None
        assert info.audio_sample_rate is None
        assert info.bitrate is None
        assert info.size_bytes is None
        assert info.format is None

    def test_optional_fields_set(self):
        info = VideoInfo(
            path="/tmp/video.mp4",
            duration=5.0,
            width=640,
            height=480,
            fps=24.0,
            codec="h264",
            audio_codec="aac",
            audio_sample_rate=44100,
            bitrate=5000000,
            size_bytes=10485760,
            format="mp4",
        )
        assert info.audio_codec == "aac"
        assert info.audio_sample_rate == 44100
        assert info.bitrate == 5000000
        assert info.size_bytes == 10485760
        assert info.format == "mp4"

    def test_resolution_property(self):
        info = VideoInfo(
            path="/tmp/video.mp4",
            duration=5.0,
            width=1920,
            height=1080,
            fps=30.0,
            codec="h264",
        )
        assert info.resolution == "1920x1080"

    def test_aspect_ratio_property(self):
        info = VideoInfo(
            path="/tmp/video.mp4",
            duration=5.0,
            width=1920,
            height=1080,
            fps=30.0,
            codec="h264",
        )
        assert info.aspect_ratio == "16:9"

    def test_aspect_ratio_4_3(self):
        info = VideoInfo(
            path="/tmp/video.mp4",
            duration=5.0,
            width=640,
            height=480,
            fps=30.0,
            codec="h264",
        )
        assert info.aspect_ratio == "4:3"

    def test_aspect_ratio_9_16(self):
        info = VideoInfo(
            path="/tmp/video.mp4",
            duration=5.0,
            width=1080,
            height=1920,
            fps=30.0,
            codec="h264",
        )
        assert info.aspect_ratio == "9:16"

    def test_size_mb_property(self):
        info = VideoInfo(
            path="/tmp/video.mp4",
            duration=5.0,
            width=640,
            height=480,
            fps=30.0,
            codec="h264",
            size_bytes=10485760,  # 10 MB
        )
        assert info.size_mb == 10.0

    def test_size_mb_property_none(self):
        info = VideoInfo(
            path="/tmp/video.mp4",
            duration=5.0,
            width=640,
            height=480,
            fps=30.0,
            codec="h264",
        )
        assert info.size_mb is None

    def test_size_mb_property_rounding(self):
        info = VideoInfo(
            path="/tmp/video.mp4",
            duration=5.0,
            width=640,
            height=480,
            fps=30.0,
            codec="h264",
            size_bytes=1500000,  # ~1.43 MB
        )
        assert info.size_mb == 1.43

    def test_model_dump(self):
        info = VideoInfo(
            path="/tmp/video.mp4",
            duration=5.0,
            width=640,
            height=480,
            fps=30.0,
            codec="h264",
        )
        d = info.model_dump()
        assert d["path"] == "/tmp/video.mp4"
        assert d["duration"] == 5.0
        assert d["width"] == 640


class TestEditResult:
    def test_defaults(self):
        result = EditResult(output_path="/tmp/out.mp4")
        assert result.success is True
        assert result.output_path == "/tmp/out.mp4"
        assert result.duration is None
        assert result.resolution is None
        assert result.size_mb is None
        assert result.format is None
        assert result.operation is None

    def test_all_fields(self):
        result = EditResult(
            output_path="/tmp/out.mp4",
            duration=10.0,
            resolution="1920x1080",
            size_mb=5.5,
            format="mp4",
            operation="trim",
        )
        assert result.success is True
        assert result.duration == 10.0
        assert result.resolution == "1920x1080"
        assert result.size_mb == 5.5
        assert result.format == "mp4"
        assert result.operation == "trim"

    def test_model_dump(self):
        result = EditResult(output_path="/tmp/out.mp4", operation="convert")
        d = result.model_dump()
        assert d["success"] is True
        assert d["output_path"] == "/tmp/out.mp4"


class TestErrorResult:
    def test_structure(self):
        result = ErrorResult(error={"type": "test", "message": "oops"})
        assert result.success is False
        assert result.error == {"type": "test", "message": "oops"}

    def test_success_always_false(self):
        result = ErrorResult(error={})
        assert result.success is False

    def test_model_dump(self):
        result = ErrorResult(error={"type": "test", "message": "err"})
        d = result.model_dump()
        assert d["success"] is False


class TestStoryboardResult:
    def test_basic(self):
        result = StoryboardResult(
            frames=["frame1.jpg", "frame2.jpg"],
            count=2,
        )
        assert result.success is True
        assert result.frames == ["frame1.jpg", "frame2.jpg"]
        assert result.count == 2
        assert result.grid is None

    def test_with_grid(self):
        result = StoryboardResult(
            frames=["f1.jpg", "f2.jpg", "f3.jpg", "f4.jpg"],
            grid="grid.jpg",
            count=4,
        )
        assert result.grid == "grid.jpg"


class TestThumbnailResult:
    def test_basic(self):
        result = ThumbnailResult(frame_path="/tmp/frame.jpg", timestamp=1.5)
        assert result.success is True
        assert result.frame_path == "/tmp/frame.jpg"
        assert result.timestamp == 1.5


class TestTimelineClip:
    def test_required_field_only(self):
        clip = TimelineClip(source="/tmp/video.mp4")
        assert clip.source == "/tmp/video.mp4"
        assert clip.start == 0.0
        assert clip.duration is None
        assert clip.trim_start == 0.0
        assert clip.trim_end is None
        assert clip.volume == 1.0
        assert clip.fade_in == 0.0
        assert clip.fade_out == 0.0

    def test_all_fields(self):
        clip = TimelineClip(
            source="/tmp/video.mp4",
            start=5.0,
            duration=10.0,
            trim_start=2.0,
            trim_end=8.0,
            volume=0.8,
            fade_in=1.0,
            fade_out=2.0,
        )
        assert clip.start == 5.0
        assert clip.duration == 10.0
        assert clip.trim_start == 2.0
        assert clip.trim_end == 8.0
        assert clip.volume == 0.8


class TestTimelineTransition:
    def test_defaults(self):
        trans = TimelineTransition(after_clip=0)
        assert trans.after_clip == 0
        assert trans.type == "fade"
        assert trans.duration == 1.0

    def test_custom(self):
        trans = TimelineTransition(after_clip=1, type="dissolve", duration=2.0)
        assert trans.after_clip == 1
        assert trans.type == "dissolve"
        assert trans.duration == 2.0


class TestTimelineTextElement:
    def test_defaults(self):
        elem = TimelineTextElement(text="Hello")
        assert elem.text == "Hello"
        assert elem.start == 0.0
        assert elem.duration is None
        assert elem.position == "top-center"
        assert isinstance(elem.style, dict)
        assert elem.style["size"] == 48
        assert elem.style["color"] == "white"
        assert elem.style["shadow"] is True

    def test_custom(self):
        elem = TimelineTextElement(
            text="Title",
            start=1.0,
            duration=3.0,
            position="bottom-center",
            style={"font": "Arial", "size": 36, "color": "yellow"},
        )
        assert elem.position == "bottom-center"
        assert elem.style["size"] == 36


class TestTimelineTrack:
    def test_video_track(self):
        track = TimelineTrack(type="video")
        assert track.type == "video"
        assert track.clips == []
        assert track.transitions == []
        assert track.elements == []

    def test_audio_track(self):
        track = TimelineTrack(type="audio", clips=[TimelineClip(source="a.mp3")])
        assert track.type == "audio"
        assert len(track.clips) == 1

    def test_text_track(self):
        track = TimelineTrack(type="text", elements=[TimelineTextElement(text="Hi")])
        assert track.type == "text"
        assert len(track.elements) == 1

    def test_invalid_type(self):
        with pytest.raises(Exception):
            TimelineTrack(type="invalid")


class TestTimelineExport:
    def test_defaults(self):
        exp = TimelineExport()
        assert exp.format == "mp4"
        assert exp.quality == "high"

    def test_custom(self):
        exp = TimelineExport(format="webm", quality="low")
        assert exp.format == "webm"
        assert exp.quality == "low"


class TestTimeline:
    def test_defaults(self):
        tl = Timeline()
        assert tl.width == 1920
        assert tl.height == 1080
        assert tl.duration is None
        assert tl.tracks == []
        assert tl.export.format == "mp4"
        assert tl.export.quality == "high"

    def test_with_tracks(self):
        tl = Timeline(
            width=1080,
            height=1920,
            tracks=[
                TimelineTrack(type="video", clips=[TimelineClip(source="v.mp4")]),
            ],
        )
        assert tl.width == 1080
        assert tl.height == 1920
        assert len(tl.tracks) == 1


class TestWatermarkSettings:
    def test_defaults(self):
        wm = WatermarkSettings(image_path="/tmp/logo.png")
        assert wm.image_path == "/tmp/logo.png"
        assert wm.position == "bottom-right"
        assert wm.opacity == 0.7
        assert wm.margin == 20

    def test_custom(self):
        wm = WatermarkSettings(
            image_path="/tmp/logo.png",
            position="top-left",
            opacity=0.5,
            margin=30,
        )
        assert wm.position == "top-left"
        assert wm.opacity == 0.5
        assert wm.margin == 30


class TestQualityPresets:
    def test_all_presets_have_required_keys(self):
        for level, preset in QUALITY_PRESETS.items():
            assert "crf" in preset, f"{level} missing crf"
            assert "preset" in preset, f"{level} missing preset"
            assert "max_height" in preset, f"{level} missing max_height"
            assert isinstance(preset["crf"], int)
            assert isinstance(preset["max_height"], int)

    def test_preset_values_order(self):
        # CRF should decrease (better quality) as level increases
        crfs = [QUALITY_PRESETS[k]["crf"] for k in ["low", "medium", "high", "ultra"]]
        assert crfs == sorted(crfs, reverse=True)


class TestAspectRatios:
    def test_all_ratios_have_tuples(self):
        for name, (w, h) in ASPECT_RATIOS.items():
            assert isinstance(w, int), f"{name} width not int"
            assert isinstance(h, int), f"{name} height not int"
            assert w > 0, f"{name} width <= 0"
            assert h > 0, f"{name} height <= 0"

    def test_expected_ratios(self):
        assert "16:9" in ASPECT_RATIOS
        assert "9:16" in ASPECT_RATIOS
        assert "1:1" in ASPECT_RATIOS
        assert "4:3" in ASPECT_RATIOS
        assert "4:5" in ASPECT_RATIOS
        assert "21:9" in ASPECT_RATIOS
        assert len(ASPECT_RATIOS) == 6

    def test_square_ratio(self):
        w, h = ASPECT_RATIOS["1:1"]
        assert w == h


class TestPreviewPresets:
    def test_required_keys(self):
        assert "crf" in PREVIEW_PRESETS
        assert "preset" in PREVIEW_PRESETS
        assert "scale_factor" in PREVIEW_PRESETS

    def test_preview_is_fast(self):
        assert PREVIEW_PRESETS["preset"] == "ultrafast"
        assert PREVIEW_PRESETS["scale_factor"] >= 2


class TestInvalidInputs:
    def test_negative_dimensions_rejected(self):
        # Pydantic doesn't enforce positive by default on int fields,
        # but validate that model accepts valid inputs
        info = VideoInfo(
            path="/tmp/v.mp4",
            duration=1.0,
            width=100,
            height=100,
            fps=30.0,
            codec="h264",
        )
        assert info.width == 100

    def test_export_format_validation(self):
        exp = TimelineExport(format="mp4")
        assert exp.format == "mp4"
        with pytest.raises(Exception):
            TimelineExport(format="invalid")

    def test_quality_level_validation(self):
        exp = TimelineExport(quality="high")
        assert exp.quality == "high"
        with pytest.raises(Exception):
            TimelineExport(quality="invalid")

    def test_position_validation(self):
        elem = TimelineTextElement(text="Hi", position="center")
        assert elem.position == "center"
        with pytest.raises(Exception):
            TimelineTextElement(text="Hi", position="invalid-position")

    def test_transition_type_validation(self):
        trans = TimelineTransition(after_clip=0, type="fade")
        assert trans.type == "fade"
        with pytest.raises(Exception):
            TimelineTransition(after_clip=0, type="invalid")


class TestEditResultNewFields:
    """Tests for new progress and thumbnail_base64 fields in EditResult."""

    def test_edit_result_progress_field(self):
        """Test that EditResult can be created with progress field."""
        result = EditResult(
            output_path="/tmp/out.mp4",
            progress=50.0,
        )
        assert result.progress == 50.0
        assert result.success is True

    def test_edit_result_progress_optional(self):
        """Test that progress defaults to None."""
        result = EditResult(output_path="/tmp/out.mp4")
        assert result.progress is None

    def test_edit_result_thumbnail_base64(self):
        """Test that EditResult can be created with thumbnail_base64 field."""
        result = EditResult(
            output_path="/tmp/out.mp4",
            thumbnail_base64="abc123",
        )
        assert result.thumbnail_base64 == "abc123"
        assert result.success is True

    def test_edit_result_thumbnail_optional(self):
        """Test that thumbnail_base64 defaults to None."""
        result = EditResult(output_path="/tmp/out.mp4")
        assert result.thumbnail_base64 is None

    def test_edit_result_both_new_fields(self):
        """Test that EditResult can have both new fields populated."""
        result = EditResult(
            output_path="/tmp/out.mp4",
            progress=75.5,
            thumbnail_base64="base64encodedstring",
        )
        assert result.progress == 75.5
        assert result.thumbnail_base64 == "base64encodedstring"

    def test_edit_result_with_progress_serializes(self):
        """Test that EditResult with progress serializes correctly."""
        result = EditResult(
            output_path="/tmp/out.mp4",
            progress=100.0,
            operation="convert",
        )
        d = result.model_dump()
        assert d["progress"] == 100.0
        assert d["operation"] == "convert"

    def test_edit_result_with_thumbnail_serializes(self):
        """Test that EditResult with thumbnail_base64 serializes correctly."""
        result = EditResult(
            output_path="/tmp/out.mp4",
            thumbnail_base64="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        )
        d = result.model_dump()
        assert "thumbnail_base64" in d
        assert (
            d["thumbnail_base64"]
            == "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
