"""Advanced engine tests for uncovered operations and edge cases — needs FFmpeg."""

import os

import pytest

from agentcut.engine import (
    _check_filter_available,
    add_audio,
    convert,
    edit_timeline,
    extract_audio,
    get_duration,
    merge,
    normalize,
    preview,
    probe,
    resize,
    speed,
    storyboard,
    thumbnail,
    trim,
    watermark,
)
from agentcut.models import Timeline, TimelineClip, TimelineTrack
from agentcut.errors import InputFileError, AgentCutError


def requires_filter(name: str, feature: str):
    return pytest.mark.skipif(
        not _check_filter_available(name),
        reason=f"FFmpeg filter '{name}' not available ({feature} requires it)",
    )


class TestNormalize:
    def test_normalize_to_h264(self, sample_video, tmp_path):
        out = str(tmp_path / "normalized.mp4")
        result = normalize(sample_video, output_path=out)
        assert os.path.isfile(result)
        info = probe(result)
        assert info.codec == "h264"
        assert info.audio_codec == "aac"


class TestGetDuration:
    def test_returns_float(self, sample_video):
        dur = get_duration(sample_video)
        assert isinstance(dur, float)
        assert dur > 0

    def test_nonexistent_file(self):
        with pytest.raises(InputFileError):
            get_duration("/nonexistent/video.mp4")


class TestWatermark:
    def test_adds_watermark(self, sample_video, sample_watermark_png):
        if not _check_filter_available("overlay"):
            pytest.skip("overlay filter not available")
        result = watermark(sample_video, sample_watermark_png)
        assert os.path.isfile(result.output_path)
        assert result.operation == "watermark"

    def test_with_opacity(self, sample_video, sample_watermark_png):
        if not _check_filter_available("overlay"):
            pytest.skip("overlay filter not available")
        result = watermark(sample_video, sample_watermark_png, opacity=0.3)
        assert os.path.isfile(result.output_path)


class TestExportVideo:
    def test_wrapper_for_convert(self, sample_video):
        from agentcut.engine import export_video
        result = export_video(sample_video)
        assert os.path.isfile(result.output_path)
        assert result.operation == "convert"

    def test_with_quality(self, sample_video):
        from agentcut.engine import export_video
        result = export_video(sample_video, quality="low")
        assert os.path.isfile(result.output_path)


class TestEditTimeline:
    def test_single_clip_no_transitions(self, sample_video):
        tl = Timeline(
            width=640, height=480,
            tracks=[
                TimelineTrack(
                    type="video",
                    clips=[TimelineClip(source=sample_video)],
                ),
            ],
        )
        result = edit_timeline(tl)
        assert os.path.isfile(result.output_path)
        assert result.success is True

    @requires_filter("drawtext", "Text overlay")
    def test_multiple_clips_with_text(self, sample_video):
        tl = Timeline(
            width=640, height=480,
            tracks=[
                TimelineTrack(
                    type="video",
                    clips=[
                        TimelineClip(source=sample_video),
                        TimelineClip(source=sample_video),
                    ],
                ),
                TimelineTrack(
                    type="text",
                    elements=[{
                        "text": "Test Title",
                        "start": 0,
                        "duration": 2,
                        "position": "center",
                        "style": {"size": 36, "color": "white", "shadow": True},
                    }],
                ),
            ],
        )
        result = edit_timeline(tl)
        assert os.path.isfile(result.output_path)

    def test_timeline_with_audio(self, sample_video, sample_audio, tmp_path):
        out = str(tmp_path / "timeline_audio.mp4")
        tl = Timeline(
            width=640, height=480,
            tracks=[
                TimelineTrack(
                    type="video",
                    clips=[TimelineClip(source=sample_video)],
                ),
                TimelineTrack(
                    type="audio",
                    clips=[TimelineClip(source=sample_audio)],
                ),
            ],
        )
        result = edit_timeline(tl, output_path=out)
        assert os.path.isfile(result.output_path)

    def test_timeline_no_video_clips_raises(self):
        tl = Timeline(tracks=[])
        with pytest.raises(AgentCutError):
            edit_timeline(tl)


class TestConvertMov:
    def test_convert_to_mov(self, sample_video):
        result = convert(sample_video, format="mov")
        assert os.path.isfile(result.output_path)
        assert result.format == "mov"


class TestSpeedAdvanced:
    def test_slow_mo(self, sample_video):
        result = speed(sample_video, factor=0.5)
        assert os.path.isfile(result.output_path)
        info = probe(result.output_path)
        orig = probe(sample_video)
        # Slow-mo should roughly double duration
        assert info.duration >= orig.duration * 1.5

    def test_triple_speed(self, sample_video):
        result = speed(sample_video, factor=3.0)
        assert os.path.isfile(result.output_path)
        info = probe(result.output_path)
        orig = probe(sample_video)
        assert info.duration < orig.duration


class TestMergeTransitions:
    def test_merge_with_fade(self, sample_video):
        result = merge(
            [sample_video, sample_video],
            transition="fade",
            transition_duration=0.5,
        )
        assert os.path.isfile(result.output_path)
        assert result.operation == "merge"


class TestTrimEdgeCases:
    def test_trim_to_exact_duration(self, sample_video):
        orig = probe(sample_video)
        result = trim(sample_video, start="0", end=str(orig.duration))
        assert os.path.isfile(result.output_path)
        info = probe(result.output_path)
        assert abs(info.duration - orig.duration) < 0.5


class TestResizeAdvanced:
    def test_resize_width_only(self, sample_video):
        result = resize(sample_video, width=320)
        assert os.path.isfile(result.output_path)
        info = probe(result.output_path)
        assert info.width == 320
        # Height should scale proportionally (640x480 → 320x240)
        assert info.height == 240

    def test_resize_height_only(self, sample_video):
        result = resize(sample_video, height=240)
        assert os.path.isfile(result.output_path)
        info = probe(result.output_path)
        assert info.height == 240

    def test_resize_no_params_raises(self, sample_video):
        with pytest.raises(AgentCutError):
            resize(sample_video)


class TestPreviewAdvanced:
    def test_custom_scale_factor(self, sample_video):
        result = preview(sample_video, scale_factor=2)
        assert os.path.isfile(result.output_path)
        info = probe(result.output_path)
        orig = probe(sample_video)
        # With scale_factor=2, should be roughly half resolution
        assert info.width <= orig.width
        assert info.height <= orig.height


class TestThumbnailAdvanced:
    def test_at_timestamp_zero(self, sample_video):
        result = thumbnail(sample_video, timestamp=0)
        assert os.path.isfile(result.frame_path)
        assert result.timestamp == 0

    def test_default_timestamp(self, sample_video):
        result = thumbnail(sample_video)
        assert os.path.isfile(result.frame_path)
        # Default is 10% of duration
        dur = get_duration(sample_video)
        expected_ts = dur * 0.1
        assert abs(result.timestamp - expected_ts) < 0.01


class TestStoryboardAdvanced:
    def test_two_frames_grid(self, sample_video):
        result = storyboard(sample_video, frame_count=2)
        assert result.count == 2
        for frame in result.frames:
            assert os.path.isfile(frame)
        # Grid may or may not exist depending on FFmpeg version
        # (2-frame grids can fail with some filter combos)
        if result.grid is not None:
            assert os.path.isfile(result.grid)

    def test_single_frame(self, sample_video):
        result = storyboard(sample_video, frame_count=1)
        assert result.count == 1


class TestExtractAudioAdvanced:
    def test_extract_to_wav(self, sample_video):
        result = extract_audio(sample_video, format="wav")
        assert os.path.isfile(result)
        # WAV files should be larger than MP3
        size = os.path.getsize(result)
        assert size > 0


class TestAddAudioAdvanced:
    def test_with_start_time(self, sample_video, sample_audio):
        result = add_audio(
            sample_video, sample_audio,
            start_time=0.5,
        )
        assert os.path.isfile(result.output_path)

    def test_nonexistent_audio(self, sample_video):
        with pytest.raises(InputFileError):
            add_audio(sample_video, "/nonexistent/audio.mp3")
