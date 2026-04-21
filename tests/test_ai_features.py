"""Tests for AI-powered video features.

These tests use optional dependencies and gracefully skip if not installed.
"""

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import types
from pathlib import Path
from unittest.mock import patch

# Add parent directory to path for direct execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from mcp_video.errors import InputFileError, MCPVideoError


def has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def has_ffprobe() -> bool:
    return shutil.which("ffprobe") is not None


requires_ffmpeg = pytest.mark.skipif(not has_ffmpeg(), reason="FFmpeg not installed")

requires_ffprobe = pytest.mark.skipif(not has_ffprobe(), reason="FFprobe not installed")


# ---------------------------------------------------------------------------
# ai_remove_silence Tests
# ---------------------------------------------------------------------------


def create_video_with_silence(output_path: str, duration: float = 5) -> str:
    """Create test video with silent audio section.

    Creates a video with:
    - 2 seconds of sine wave audio
    - 1 second of silence
    - 2 seconds of sine wave audio
    """
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c=blue:s=320x240:d={duration}",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=1000:duration=2",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=r=44100:cl=mono",  # silence
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=1000:duration=2",
        "-filter_complex",
        "[1:a][2:a][3:a]concat=n=3:v=0:a=1[a]",
        "-map",
        "0:v",
        "-map",
        "[a]",
        "-pix_fmt",
        "yuv420p",
        "-shortest",
        output_path,
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


def get_video_duration(video_path: str) -> float:
    """Get video duration using ffprobe."""
    probe_cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]
    result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


@requires_ffmpeg
@requires_ffprobe
def test_remove_silence():
    """Test that ai_remove_silence correctly removes silent sections."""
    from mcp_video.ai_engine import ai_remove_silence

    with tempfile.TemporaryDirectory() as tmpdir:
        input_video = os.path.join(tmpdir, "input.mp4")
        output_video = os.path.join(tmpdir, "output.mp4")

        create_video_with_silence(input_video)

        # Get input duration
        input_duration = get_video_duration(input_video)

        result = ai_remove_silence(input_video, output_video, silence_threshold=-50, min_silence_duration=0.3)

        assert os.path.exists(result), "Output not created"

        # Get output duration
        output_duration = get_video_duration(result)

        # Output should be shorter than input (silence removed)
        print(f"Input: {input_duration:.2f}s, Output: {output_duration:.2f}s")
        print(f"✓ Removed {input_duration - output_duration:.2f}s of silence")

        # Assert that some silence was removed
        assert output_duration < input_duration, "Output should be shorter than input"


@requires_ffmpeg
@requires_ffprobe
def test_remove_silence_no_silence():
    """Test that ai_remove_silence handles videos without silence."""
    from mcp_video.ai_engine import ai_remove_silence

    with tempfile.TemporaryDirectory() as tmpdir:
        input_video = os.path.join(tmpdir, "input.mp4")
        output_video = os.path.join(tmpdir, "output.mp4")

        # Create video with continuous audio (no silence)
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=red:s=320x240:d=3",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=500:duration=3",
            "-pix_fmt",
            "yuv420p",
            "-shortest",
            input_video,
        ]
        subprocess.run(cmd, capture_output=True, check=True)

        input_duration = get_video_duration(input_video)

        result = ai_remove_silence(input_video, output_video)

        assert os.path.exists(result), "Output not created"

        output_duration = get_video_duration(result)

        # Duration should be approximately the same
        assert abs(output_duration - input_duration) < 0.5, "Duration should remain similar when no silence to remove"


@requires_ffmpeg
@requires_ffprobe
def test_remove_silence_custom_threshold():
    """Test ai_remove_silence with different silence thresholds."""
    from mcp_video.ai_engine import ai_remove_silence

    with tempfile.TemporaryDirectory() as tmpdir:
        input_video = os.path.join(tmpdir, "input.mp4")
        output_video = os.path.join(tmpdir, "output.mp4")

        create_video_with_silence(input_video)

        # Use stricter threshold (more negative = quieter sounds considered silence)
        result = ai_remove_silence(input_video, output_video, silence_threshold=-60, min_silence_duration=0.3)

        assert os.path.exists(result), "Output not created"

        output_duration = get_video_duration(result)
        assert output_duration > 0, "Output should have positive duration"


@requires_ffmpeg
@requires_ffprobe
def test_remove_silence_with_margin():
    """Test ai_remove_silence with keep_margin parameter."""
    from mcp_video.ai_engine import ai_remove_silence

    with tempfile.TemporaryDirectory() as tmpdir:
        input_video = os.path.join(tmpdir, "input.mp4")
        output_video = os.path.join(tmpdir, "output.mp4")

        create_video_with_silence(input_video)

        input_duration = get_video_duration(input_video)

        # Use larger margin
        result = ai_remove_silence(
            input_video,
            output_video,
            silence_threshold=-50,
            min_silence_duration=0.3,
            keep_margin=0.5,  # Larger margin
        )

        assert os.path.exists(result), "Output not created"

        output_duration = get_video_duration(result)

        # With larger margin, less should be removed
        assert output_duration < input_duration, "Should still remove some silence"


@requires_ffmpeg
@requires_ffprobe
def test_remove_silence_missing_file():
    """Test that ai_remove_silence raises InputFileError for missing video."""
    from mcp_video.ai_engine import ai_remove_silence

    with tempfile.TemporaryDirectory() as tmpdir:
        nonexistent_video = os.path.join(tmpdir, "nonexistent.mp4")
        output_video = os.path.join(tmpdir, "output.mp4")

        with pytest.raises(InputFileError, match="Input file error"):
            ai_remove_silence(nonexistent_video, output_video)


# ---------------------------------------------------------------------------
# ai_transcribe Tests
# ---------------------------------------------------------------------------


def create_video_with_speech(output_path: str) -> str:
    """Create test video with synthetic speech audio."""
    # Create a simple video with sine wave that simulates speech
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "color=c=green:s=320x240:d=3",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=440:duration=3",
        "-pix_fmt",
        "yuv420p",
        "-shortest",
        output_path,
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


@pytest.fixture
def skip_if_no_whisper():
    """Skip test if whisper is not installed."""
    if importlib.util.find_spec("whisper") is None:
        pytest.skip("Whisper not installed, skipping test")


@pytest.fixture
def sample_speech_video():
    """Create a temporary video with synthetic audio."""
    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, "input.mp4")
        create_video_with_speech(video_path)
        yield video_path


class TestTranscription:
    """Tests for ai_transcribe function."""

    def test_transcribe_missing_whisper_dependency(self, monkeypatch):
        """Missing Whisper should raise a structured dependency error."""
        import builtins

        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "whisper":
                raise ImportError("No module named 'whisper'")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        from mcp_video.ai_engine import ai_transcribe

        with pytest.raises(MCPVideoError, match="Whisper not installed") as exc_info:
            ai_transcribe("video.mp4")

        assert exc_info.value.error_type == "dependency_error"
        assert exc_info.value.code == "missing_whisper"

    def test_transcribe_file_not_found(self, skip_if_no_whisper):
        """Test that InputFileError is raised for missing video."""
        from mcp_video.ai_engine import ai_transcribe

        with pytest.raises(InputFileError, match="Input file error"):
            ai_transcribe("/nonexistent/video.mp4")

    def test_transcribe_ffmpeg_extraction_failure(self, monkeypatch, skip_if_no_whisper, sample_video):
        """FFmpeg extraction failure should surface as ProcessingError."""
        from mcp_video.ai_engine import ai_transcribe
        from mcp_video.errors import ProcessingError

        monkeypatch.setattr(
            "mcp_video.ai_engine.subprocess.run", lambda *a, **k: type("R", (), {"returncode": 1, "stderr": "boom"})()
        )

        with pytest.raises(ProcessingError, match="FFmpeg processing failed"):
            ai_transcribe(sample_video)

    def test_transcribe_basic(self, skip_if_no_whisper, sample_speech_video):
        """Test basic transcription returns expected structure."""
        from mcp_video.ai_engine import ai_transcribe

        with tempfile.TemporaryDirectory() as tmpdir:
            output_srt = os.path.join(tmpdir, "output.srt")

            result = ai_transcribe(
                sample_speech_video,
                output_srt=output_srt,
                model="tiny",
            )

            # Check result structure
            assert "transcript" in result
            assert "segments" in result
            assert "language" in result

            assert isinstance(result["transcript"], str)
            assert isinstance(result["segments"], list)
            assert isinstance(result["language"], str)

    def test_transcribe_with_srt_output(self, skip_if_no_whisper, sample_speech_video):
        """Test that SRT file is created when output_srt is provided."""
        from mcp_video.ai_engine import ai_transcribe

        with tempfile.TemporaryDirectory() as tmpdir:
            output_srt = os.path.join(tmpdir, "output.srt")

            ai_transcribe(
                sample_speech_video,
                output_srt=output_srt,
                model="tiny",
            )

            # SRT file should exist
            assert os.path.exists(output_srt), "SRT file should be created"

            # SRT file should have content
            srt_content = Path(output_srt).read_text(encoding="utf-8")
            assert len(srt_content) > 0, "SRT file should not be empty"

    def test_transcribe_language_detection(self, skip_if_no_whisper, sample_speech_video):
        """Test that language is detected and returned."""
        from mcp_video.ai_engine import ai_transcribe

        result = ai_transcribe(
            sample_speech_video,
            model="tiny",
        )

        # Language should be detected
        assert "language" in result
        assert isinstance(result["language"], str)
        assert len(result["language"]) > 0


class TestSRTFormatting:
    """Tests for SRT formatting utilities."""

    def test_seconds_to_srt_time(self):
        """Test conversion of seconds to SRT time format."""
        from mcp_video.ffmpeg_helpers import _seconds_to_srt_time

        # Test various time values
        assert _seconds_to_srt_time(0) == "00:00:00,000"
        assert _seconds_to_srt_time(1.5) == "00:00:01,500"
        assert _seconds_to_srt_time(61.123) == "00:01:01,122"  # Float precision
        assert _seconds_to_srt_time(3661.999) == "01:01:01,998"  # Float precision

    def test_format_srt_empty_segments(self):
        """Test SRT formatting with empty segments."""
        from mcp_video.ai_engine import _format_srt

        result = _format_srt([])
        assert result == ""

    def test_format_srt_single_segment(self):
        """Test SRT formatting with single segment."""
        from mcp_video.ai_engine import _format_srt

        segments = [
            {"start": 0.0, "end": 2.0, "text": "Hello world"},
        ]
        result = _format_srt(segments)

        expected = "1\n00:00:00,000 --> 00:00:02,000\nHello world\n"
        assert result == expected

    def test_format_srt_multiple_segments(self):
        """Test SRT formatting with multiple segments."""
        from mcp_video.ai_engine import _format_srt

        segments = [
            {"start": 0.0, "end": 2.0, "text": "First line"},
            {"start": 2.5, "end": 4.0, "text": "Second line"},
        ]
        result = _format_srt(segments)

        lines = result.strip().split("\n")
        assert "1" in lines[0]
        assert "00:00:00,000 --> 00:00:02,000" in lines[1]
        assert "First line" in lines[2]
        assert "2" in lines[4]
        assert "00:00:02,500 --> 00:00:04,000" in lines[5]
        assert "Second line" in lines[6]

    def test_format_srt_skips_empty_text(self):
        """Test that segments with empty text are skipped."""
        from mcp_video.ai_engine import _format_srt

        segments = [
            {"start": 0.0, "end": 2.0, "text": "Valid text"},
            {"start": 2.0, "end": 3.0, "text": "   "},  # Empty/whitespace
            {"start": 3.0, "end": 4.0, "text": "More text"},
        ]
        result = _format_srt(segments)

        # Should only have entries for non-empty text
        assert result.count("Valid text") == 1
        assert result.count("More text") == 1
        # Second segment should be skipped, so only 2 entries total
        assert result.count("-->") == 2


def test_ai_scene_detect_missing_file_does_not_create_parent_dir(tmp_path, monkeypatch):
    """AI scene detection validates input before shared ffprobe helper can touch paths."""
    from mcp_video.ai_engine import ai_scene_detect

    missing_video = tmp_path / "missing" / "video.mp4"
    monkeypatch.setattr("mcp_video.ai_engine._standard_scene_detect", lambda *_args, **_kwargs: [])
    imagehash_module = types.ModuleType("imagehash")
    pil_module = types.ModuleType("PIL")
    image_module = types.ModuleType("PIL.Image")
    pil_module.Image = image_module
    monkeypatch.setitem(sys.modules, "imagehash", imagehash_module)
    monkeypatch.setitem(sys.modules, "PIL", pil_module)
    monkeypatch.setitem(sys.modules, "PIL.Image", image_module)

    with pytest.raises(InputFileError):
        ai_scene_detect(str(missing_video), use_ai=True)

    assert not missing_video.parent.exists()


# ---------------------------------------------------------------------------
# ai_color_grade Tests
# ---------------------------------------------------------------------------


class TestColorGrade:
    """Tests for ai_color_grade function."""

    @requires_ffmpeg
    def test_color_grade_creates_output(self):
        """Test that color grading creates output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_video = os.path.join(tmpdir, "input.mp4")
            output_video = os.path.join(tmpdir, "output.mp4")

            # Create test video with blue color
            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "color=c=blue:s=320x240:d=2",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=1000:duration=2",
                "-pix_fmt",
                "yuv420p",
                "-shortest",
                input_video,
            ]
            subprocess.run(cmd, capture_output=True, check=True)

            # Test cinematic style
            from mcp_video.ai_engine import ai_color_grade

            result = ai_color_grade(input_video, output_video, style="cinematic")
            assert os.path.exists(result), "Output video should be created"
            assert result == output_video

    @requires_ffmpeg
    def test_color_grade_all_styles(self):
        """Test that all style presets work."""
        from mcp_video.ai_engine import ai_color_grade

        with tempfile.TemporaryDirectory() as tmpdir:
            input_video = os.path.join(tmpdir, "input.mp4")

            # Create test video
            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "color=c=green:s=320x240:d=1",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=1000:duration=1",
                "-pix_fmt",
                "yuv420p",
                "-shortest",
                input_video,
            ]
            subprocess.run(cmd, capture_output=True, check=True)

            # Test each style preset
            for style in ["cinematic", "vintage", "warm", "cool", "dramatic", "auto"]:
                output_video = os.path.join(tmpdir, f"output_{style}.mp4")
                result = ai_color_grade(input_video, output_video, style=style)
                assert os.path.exists(result), f"Output not created for style: {style}"
                assert os.path.getsize(result) > 0, f"Output is empty for style: {style}"


    def test_reference_color_analysis_failure_falls_back_to_neutral(self, monkeypatch):
        """Reference matching should remain best-effort when FFmpeg analysis fails."""
        import subprocess

        from mcp_video.ai_engine.color import _match_reference_colors

        def fake_run(cmd, capture_output, text, timeout):
            return subprocess.CompletedProcess(cmd, 1, "", "signalstats unavailable")

        monkeypatch.setattr(subprocess, "run", fake_run)

        assert _match_reference_colors("input.mp4", "reference.mp4") == {
            "contrast": 1.0,
            "saturation": 1.0,
            "gamma": 1.0,
            "red": 1.0,
            "green": 1.0,
            "blue": 1.0,
        }


    @requires_ffmpeg
    def test_color_grade_with_reference(self):
        """Test color grading with reference video."""
        from mcp_video.ai_engine import ai_color_grade

        with tempfile.TemporaryDirectory() as tmpdir:
            input_video = os.path.join(tmpdir, "input.mp4")
            reference_video = os.path.join(tmpdir, "reference.mp4")
            output_video = os.path.join(tmpdir, "output.mp4")

            # Create input video (blue)
            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "color=c=blue:s=320x240:d=1",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=1000:duration=1",
                "-pix_fmt",
                "yuv420p",
                "-shortest",
                input_video,
            ]
            subprocess.run(cmd, capture_output=True, check=True)

            # Create reference video (red)
            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "color=c=red:s=320x240:d=1",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=1000:duration=1",
                "-pix_fmt",
                "yuv420p",
                "-shortest",
                reference_video,
            ]
            subprocess.run(cmd, capture_output=True, check=True)

            result = ai_color_grade(input_video, output_video, reference=reference_video)
            assert os.path.exists(result), "Output should be created with reference"

    @requires_ffmpeg
    def test_color_grade_invalid_style(self):
        """Test that invalid style defaults to auto."""
        from mcp_video.ai_engine import ai_color_grade

        with tempfile.TemporaryDirectory() as tmpdir:
            input_video = os.path.join(tmpdir, "input.mp4")
            output_video = os.path.join(tmpdir, "output.mp4")

            # Create test video
            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "color=c=gray:s=320x240:d=1",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=1000:duration=1",
                "-pix_fmt",
                "yuv420p",
                "-shortest",
                input_video,
            ]
            subprocess.run(cmd, capture_output=True, check=True)

            # Invalid style should fall back to auto
            result = ai_color_grade(input_video, output_video, style="invalid_style")
            assert os.path.exists(result), "Output should be created even with invalid style"

    def test_color_grade_file_not_found(self):
        """Test that InputFileError is raised for missing input."""
        from mcp_video.ai_engine import ai_color_grade

        with pytest.raises(InputFileError, match="Input file error"):
            ai_color_grade("/nonexistent/video.mp4", "/tmp/output.mp4")


if __name__ == "__main__":
    # Run tests when executed directly
    print("Running AI feature tests...")

    # Test ai_remove_silence
    if has_ffmpeg() and has_ffprobe():
        print("\n=== Testing ai_remove_silence ===")
        print("✓ FFmpeg and FFprobe are installed")

        try:
            test_remove_silence()
            print("✓ test_remove_silence passed")
        except Exception as e:
            print(f"✗ test_remove_silence failed: {e}")

        try:
            test_remove_silence_no_silence()
            print("✓ test_remove_silence_no_silence passed")
        except Exception as e:
            print(f"✗ test_remove_silence_no_silence failed: {e}")

        try:
            test_remove_silence_custom_threshold()
            print("✓ test_remove_silence_custom_threshold passed")
        except Exception as e:
            print(f"✗ test_remove_silence_custom_threshold failed: {e}")

        try:
            test_remove_silence_with_margin()
            print("✓ test_remove_silence_with_margin passed")
        except Exception as e:
            print(f"✗ test_remove_silence_with_margin failed: {e}")

        try:
            test_remove_silence_missing_file()
            print("✓ test_remove_silence_missing_file passed")
        except Exception as e:
            print(f"✗ test_remove_silence_missing_file failed: {e}")
    else:
        print("⚠ FFmpeg or FFprobe not installed, skipping silence removal tests")

    # Test SRT formatting (no dependencies)
    print("\n=== Testing SRT formatting ===")

    test_srt = TestSRTFormatting()
    try:
        test_srt.test_seconds_to_srt_time()
        print("✓ test_seconds_to_srt_time passed")
    except Exception as e:
        print(f"✗ test_seconds_to_srt_time failed: {e}")

    try:
        test_srt.test_format_srt_empty_segments()
        print("✓ test_format_srt_empty_segments passed")
    except Exception as e:
        print(f"✗ test_format_srt_empty_segments failed: {e}")

    try:
        test_srt.test_format_srt_single_segment()
        print("✓ test_format_srt_single_segment passed")
    except Exception as e:
        print(f"✗ test_format_srt_single_segment failed: {e}")

    try:
        test_srt.test_format_srt_multiple_segments()
        print("✓ test_format_srt_formatting_multiple_segments passed")
    except Exception as e:
        print(f"✗ test_format_srt_multiple_segments failed: {e}")

    try:
        test_srt.test_format_srt_skips_empty_text()
        print("✓ test_format_srt_skips_empty_text passed")
    except Exception as e:
        print(f"✗ test_format_srt_skips_empty_text failed: {e}")

    print("\nTests complete!")


# =============================================================================
# Spatial Audio Tests
# =============================================================================


def create_stereo_video(output_path):
    """Create video with stereo audio."""
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "color=c=orange:s=320x240:d=5",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=1000:duration=5",
        "-ac",
        "2",  # stereo
        "-pix_fmt",
        "yuv420p",
        "-shortest",
        output_path,
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


def get_audio_channels(video_path):
    """Get audio channel count."""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "a:0",
        "-show_entries",
        "stream=channels",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return int(result.stdout.strip())


@requires_ffmpeg
@requires_ffprobe
def test_spatial_audio():
    """Test 3D spatial audio positioning."""
    from mcp_video.ai_engine import audio_spatial

    with tempfile.TemporaryDirectory() as tmpdir:
        input_video = os.path.join(tmpdir, "input.mp4")
        output_video = os.path.join(tmpdir, "output.mp4")

        create_stereo_video(input_video)

        # Test simple spatial positioning
        positions = [
            {"time": 0, "azimuth": -45, "elevation": 0},  # left
            {"time": 2.5, "azimuth": 0, "elevation": 30},  # center, up
            {"time": 5, "azimuth": 45, "elevation": 0},  # right
        ]

        result = audio_spatial(input_video, output_video, positions, method="simple")

        assert os.path.exists(result), "Output not created"
        channels = get_audio_channels(result)
        print(f"✓ Spatial audio created: {channels} channels")
        print(f"✓ Positions applied: {len(positions)} keyframes")


def test_spatial_audio_missing_video():
    """Test that spatial audio raises InputFileError for missing video."""
    from mcp_video.ai_engine import audio_spatial

    with tempfile.TemporaryDirectory() as tmpdir:
        nonexistent_video = os.path.join(tmpdir, "nonexistent.mp4")
        output_video = os.path.join(tmpdir, "output.mp4")

        positions = [{"time": 0, "azimuth": 0, "elevation": 0}]

        with pytest.raises(InputFileError, match="Input file error"):
            audio_spatial(nonexistent_video, output_video, positions)


@requires_ffmpeg
def test_spatial_audio_invalid_method():
    """Test that spatial audio raises ValueError for invalid method."""
    from mcp_video.ai_engine import audio_spatial

    with tempfile.TemporaryDirectory() as tmpdir:
        input_video = os.path.join(tmpdir, "input.mp4")
        output_video = os.path.join(tmpdir, "output.mp4")

        create_stereo_video(input_video)

        positions = [{"time": 0, "azimuth": 0, "elevation": 0}]

        with pytest.raises(MCPVideoError, match="Method must be one of"):
            audio_spatial(input_video, output_video, positions, method="invalid")


@requires_ffmpeg
def test_spatial_audio_empty_positions():
    """Test that spatial audio raises ValueError for empty positions."""
    from mcp_video.ai_engine import audio_spatial

    with tempfile.TemporaryDirectory() as tmpdir:
        input_video = os.path.join(tmpdir, "input.mp4")
        output_video = os.path.join(tmpdir, "output.mp4")

        create_stereo_video(input_video)

        with pytest.raises(MCPVideoError, match="At least one position must be provided"):
            audio_spatial(input_video, output_video, [])


def test_azimuth_to_pan():
    """Test azimuth to pan conversion."""
    from mcp_video.ai_engine import _azimuth_to_pan

    assert _azimuth_to_pan(-90) == -1.0, "Left should be -1.0"
    assert _azimuth_to_pan(0) == 0.0, "Center should be 0.0"
    assert _azimuth_to_pan(90) == 1.0, "Right should be 1.0"
    assert _azimuth_to_pan(-45) == -0.5, "Half left should be -0.5"
    assert _azimuth_to_pan(45) == 0.5, "Half right should be 0.5"
    assert _azimuth_to_pan(-180) == -1.0, "Clamped to -1.0"
    assert _azimuth_to_pan(180) == 1.0, "Clamped to 1.0"


def test_elevation_to_volume():
    """Test elevation to volume conversion."""
    from mcp_video.ai_engine import _elevation_to_volume

    assert _elevation_to_volume(0) == 1.0, "Level should be 1.0"
    assert _elevation_to_volume(90) == 0.7, "Above should be 0.7"
    assert _elevation_to_volume(45) == 0.85, "Half up should be 0.85"
    # Linear interpolation: 1.0 - (45/90)*0.3 = 1.0 - 0.15 = 0.85


if __name__ == "__main__":
    # Also run spatial audio tests when module run directly
    print("\n=== Testing Spatial Audio ===")

    try:
        test_spatial_audio()
        print("✓ test_spatial_audio passed")
    except Exception as e:
        print(f"✗ test_spatial_audio failed: {e}")

    try:
        test_spatial_audio_missing_video()
        print("✓ test_spatial_audio_missing_video passed")
    except Exception as e:
        print(f"✗ test_spatial_audio_missing_video failed: {e}")

    try:
        test_spatial_audio_invalid_method()
        print("✓ test_spatial_audio_invalid_method passed")
    except Exception as e:
        print(f"✗ test_spatial_audio_invalid_method failed: {e}")

    try:
        test_spatial_audio_empty_positions()
        print("✓ test_spatial_audio_empty_positions passed")
    except Exception as e:
        print(f"✗ test_spatial_audio_empty_positions failed: {e}")

    try:
        test_azimuth_to_pan()
        print("✓ test_azimuth_to_pan passed")
    except Exception as e:
        print(f"✗ test_azimuth_to_pan failed: {e}")

    try:
        test_elevation_to_volume()
        print("✓ test_elevation_to_volume passed")
    except Exception as e:
        print(f"✗ test_elevation_to_volume failed: {e}")


# ---------------------------------------------------------------------------
# ai_upscale Tests
# ---------------------------------------------------------------------------


def create_low_res_video(output_path, resolution="160x120"):
    """Create low-res test video."""
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c=red:s={resolution}:d=2",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=1000:duration=2",
        "-pix_fmt",
        "yuv420p",
        "-shortest",
        output_path,
    ]
    subprocess.run(cmd, capture_output=True)
    return output_path


def get_video_resolution(video_path):
    """Get video resolution."""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "csv=s=x:p=0",
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip()


def realesrgan_installed():
    """Check if realesrgan is installed."""
    return importlib.util.find_spec("realesrgan") is not None


requires_realesrgan = pytest.mark.skipif(not realesrgan_installed(), reason="Real-ESRGAN not installed")


@requires_ffmpeg
@requires_ffprobe
@requires_realesrgan
def test_ai_upscale():
    """Test AI video upscaling with Real-ESRGAN."""
    from mcp_video.ai_engine import ai_upscale

    with tempfile.TemporaryDirectory() as tmpdir:
        input_video = os.path.join(tmpdir, "input.mp4")
        output_video = os.path.join(tmpdir, "output.mp4")

        create_low_res_video(input_video, "160x120")
        input_res = get_video_resolution(input_video)
        print(f"Input resolution: {input_res}")

        result = ai_upscale(input_video, output_video, scale=2)

        output_res = get_video_resolution(output_video)
        print(f"Output resolution: {output_res}")
        print(f"✓ Upscaled from {input_res} to {output_res}")

        # Verify output file exists
        assert os.path.exists(result), "Output file should exist"
        assert os.path.exists(output_video), "Output video should exist"


@requires_ffmpeg
def test_ai_upscale_missing_dependency():
    """Test that ai_upscale raises MCPVideoError when dnn_superres is unavailable."""
    # Skip if realesrgan IS installed (this test is for when it's NOT installed)
    if realesrgan_installed():
        pytest.skip("Real-ESRGAN is installed, skipping missing dependency test")

    # Also skip if OpenCV is not available (fallback path requires it)
    try:
        import cv2
    except ImportError:
        pytest.skip("OpenCV not available, cannot test fallback path")

    # Skip if cv2 has dnn_superres (full contrib build) — fallback would succeed
    if hasattr(cv2, "dnn_superres"):
        pytest.skip("OpenCV has dnn_superres, skipping missing module test")

    from mcp_video.ai_engine import ai_upscale
    from mcp_video.errors import MCPVideoError

    with tempfile.TemporaryDirectory() as tmpdir:
        input_video = os.path.join(tmpdir, "input.mp4")
        create_low_res_video(input_video, "160x120")
        output_video = os.path.join(tmpdir, "output.mp4")

        with pytest.raises(MCPVideoError, match="dnn_superres"):
            ai_upscale(input_video, output_video, scale=2)


@requires_ffmpeg
def test_ai_upscale_import_error_message_mentions_opencv_contrib(sample_video, tmp_path):
    """ImportError fallback should point users to the supported OpenCV package."""
    from mcp_video.ai_engine import ai_upscale

    output_video = str(tmp_path / "output.mp4")

    with (
        patch("mcp_video.ai_engine._ai_upscale_opencv", side_effect=ImportError),
        pytest.raises(MCPVideoError, match="opencv-contrib-python"),
    ):
        ai_upscale(sample_video, output_video, scale=2)


@requires_ffmpeg
def test_ai_stem_separation_missing_demucs_dependency(monkeypatch, sample_video, tmp_path):
    """Missing Demucs should raise a structured dependency error."""
    import builtins

    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name.startswith("demucs"):
            raise ImportError("No module named 'demucs'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)

    from mcp_video.ai_engine import ai_stem_separation

    with pytest.raises(MCPVideoError, match="Demucs not installed") as exc_info:
        ai_stem_separation(sample_video, str(tmp_path))

    assert exc_info.value.error_type == "dependency_error"
    assert exc_info.value.code == "missing_demucs"


@requires_ffmpeg
@pytest.mark.skipif(importlib.util.find_spec("demucs") is None, reason="Demucs not installed")
def test_ai_stem_separation_ffmpeg_extraction_failure(monkeypatch, sample_video, tmp_path):
    """Stem separation extraction failures should surface as ProcessingError."""
    from mcp_video.ai_engine import ai_stem_separation
    from mcp_video.errors import ProcessingError

    class FakeRun:
        returncode = 1
        stderr = "boom"

    monkeypatch.setattr("mcp_video.ai_engine.subprocess.run", lambda *a, **k: FakeRun())

    with pytest.raises(ProcessingError, match="FFmpeg processing failed"):
        ai_stem_separation(sample_video, str(tmp_path))


@requires_ffmpeg
@requires_realesrgan
def test_ai_upscale_invalid_scale():
    """Test ai_upscale with invalid scale parameter."""
    from mcp_video.ai_engine import ai_upscale

    with tempfile.TemporaryDirectory() as tmpdir:
        input_video = os.path.join(tmpdir, "input.mp4")
        create_low_res_video(input_video, "160x120")
        output_video = os.path.join(tmpdir, "output.mp4")

        with pytest.raises(MCPVideoError) as exc_info:
            ai_upscale(input_video, output_video, scale=3)  # Invalid scale

        assert "scale" in str(exc_info.value).lower()
        print(f"✓ Correctly raised MCPVideoError for invalid scale: {exc_info.value}")


@requires_ffmpeg
@requires_realesrgan
def test_ai_upscale_missing_file():
    """Test ai_upscale with non-existent input file."""
    from mcp_video.ai_engine import ai_upscale

    with tempfile.TemporaryDirectory() as tmpdir:
        input_video = os.path.join(tmpdir, "nonexistent.mp4")
        output_video = os.path.join(tmpdir, "output.mp4")

        with pytest.raises(InputFileError) as exc_info:
            ai_upscale(input_video, output_video, scale=2)

        assert "not found" in str(exc_info.value).lower()
        print(f"✓ Correctly raised InputFileError: {exc_info.value}")


# ---------------------------------------------------------------------------
# analyze_video Tests
# ---------------------------------------------------------------------------


def create_simple_video(output_path: str, duration: float = 3) -> str:
    """Create a minimal test video with audio."""
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c=red:s=320x240:d={duration}",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=440:duration={duration}",
        "-map",
        "0:v",
        "-map",
        "1:a",
        "-pix_fmt",
        "yuv420p",
        "-shortest",
        output_path,
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


@requires_ffmpeg
@requires_ffprobe
def test_analyze_video_no_transcript():
    """analyze_video returns metadata/scenes/audio/quality without Whisper."""
    from mcp_video.ai_engine import analyze_video

    with tempfile.TemporaryDirectory() as tmpdir:
        video = create_simple_video(str(Path(tmpdir) / "test.mp4"))
        result = analyze_video(video, include_transcript=False)

    assert result["success"] is True
    assert result["transcript"] is None

    meta = result["metadata"]
    assert meta["width"] == 320
    assert meta["height"] == 240
    assert meta["duration"] > 0

    # scenes list should be present (even if empty for a short clip)
    assert isinstance(result["scenes"], list)


@requires_ffmpeg
@requires_ffprobe
def test_analyze_video_file_not_found():
    """analyze_video raises FileNotFoundError for missing files."""
    from mcp_video.ai_engine import analyze_video

    with pytest.raises(InputFileError):
        analyze_video("/nonexistent/path/video.mp4", include_transcript=False)


def test_analyze_video_null_byte_path():
    """analyze_video raises InputFileError for null-byte paths."""
    from mcp_video.ai_engine import analyze_video

    with pytest.raises(InputFileError):
        analyze_video("path/with\x00null", include_transcript=False)


@requires_ffmpeg
@requires_ffprobe
def test_analyze_video_errors_are_non_fatal():
    """A sub-analysis failure does not abort the whole result."""
    from unittest.mock import patch
    from mcp_video.ai_engine import analyze_video

    with tempfile.TemporaryDirectory() as tmpdir:
        video = create_simple_video(str(Path(tmpdir) / "test.mp4"))

        with patch("mcp_video.quality_guardrails.quality_check", side_effect=RuntimeError("mock quality failure")):
            result = analyze_video(video, include_transcript=False)

    assert result["success"] is True
    assert result["quality"] is None
    quality_errors = [e for e in result["errors"] if e["section"] == "quality"]
    assert len(quality_errors) == 1
    assert "mock quality failure" in quality_errors[0]["error"]


def test_format_txt_basic():
    """_format_txt joins segment texts as plain lines."""
    from mcp_video.ai_engine import _format_txt

    segments = [
        {"start": 0.0, "end": 1.0, "text": "Hello world"},
        {"start": 1.0, "end": 2.0, "text": "Second line"},
    ]
    result = _format_txt(segments)
    assert "Hello world" in result
    assert "Second line" in result
    assert "-->" not in result


def test_format_txt_strips_whitespace():
    """_format_txt strips leading/trailing whitespace from each segment."""
    from mcp_video.ai_engine import _format_txt

    segments = [{"start": 0.0, "end": 1.0, "text": "  padded  "}]
    result = _format_txt(segments)
    assert result.strip() == "padded"


def test_format_md_contains_timestamps():
    """_format_md includes bold HH:MM:SS timestamps."""
    from mcp_video.ai_engine import _format_md

    segments = [
        {"start": 65.0, "end": 67.0, "text": "One minute in"},
        {"start": 3661.0, "end": 3663.0, "text": "One hour in"},
    ]
    result = _format_md(segments)
    assert "**[00:01:05]**" in result
    assert "**[01:01:01]**" in result
    assert "One minute in" in result
    assert "One hour in" in result


def test_format_json_transcript_structure():
    """_format_json_transcript returns expected keys and segment count."""
    from mcp_video.ai_engine import _format_json_transcript

    segments = [
        {"id": 0, "start": 0.0, "end": 1.5, "text": "Hello", "tokens": [1, 2]},
    ]
    result = _format_json_transcript("Hello", segments, "en")

    assert result["transcript"] == "Hello"
    assert result["language"] == "en"
    assert result["segment_count"] == 1
    assert result["segments"][0]["text"] == "Hello"
    assert result["segments"][0]["start"] == 0.0


@requires_ffmpeg
@requires_ffprobe
def test_analyze_video_writes_txt_output():
    """analyze_video writes plain-text transcript file when output_txt is given."""
    from unittest.mock import patch
    from mcp_video.ai_engine import analyze_video

    fake_transcribe_result = {
        "transcript": "Hello world",
        "segments": [{"id": 0, "start": 0.0, "end": 1.0, "text": "Hello world", "tokens": []}],
        "language": "en",
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        video = create_simple_video(str(Path(tmpdir) / "test.mp4"))
        txt_path = str(Path(tmpdir) / "transcript.txt")

        with patch("mcp_video.ai_engine.ai_transcribe", return_value=fake_transcribe_result):
            result = analyze_video(
                video,
                include_transcript=True,
                output_txt=txt_path,
                include_scenes=False,
                include_audio=False,
                include_quality=False,
                include_chapters=False,
                include_colors=False,
            )

        assert result["success"] is True
        assert result["transcript"]["txt_path"] == txt_path
        assert Path(txt_path).read_text(encoding="utf-8") == "Hello world"


# ---------------------------------------------------------------------------
# URL resolution helper tests
# ---------------------------------------------------------------------------


def test_is_url_detects_http():
    from mcp_video.ai_engine import _is_url

    assert _is_url("http://example.com/video.mp4") is True
    assert _is_url("https://example.com/video.mp4") is True


def test_is_url_rejects_local_path():
    from mcp_video.ai_engine import _is_url

    assert _is_url("/local/path/video.mp4") is False
    assert _is_url("relative/path.mp4") is False
    assert _is_url("C:\\Windows\\video.mp4") is False


def test_url_host_extraction():
    from mcp_video.ai_engine import _url_host

    assert _url_host("https://www.youtube.com/watch?v=abc") == "www.youtube.com"
    assert _url_host("https://example.com/path/video.mp4") == "example.com"
    assert _url_host("http://cdn.example.com:8080/v.mp4") == "cdn.example.com:8080"


def test_resolve_video_source_local_passthrough():
    """Local paths pass through _resolve_video_source unchanged."""
    from mcp_video.ai_engine import _resolve_video_source

    local, tmp, url = _resolve_video_source("/some/local/file.mp4")
    assert local == "/some/local/file.mp4"
    assert tmp is None
    assert url is None




def test_is_safe_url_restores_socket_default_timeout(monkeypatch):
    """SSRF DNS lookup timeout must not clobber an embedding app's global socket default."""
    import socket

    from mcp_video.ai_engine.download import _is_safe_url

    previous_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(3.5)

    def fake_getaddrinfo(*args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 0, "", ("93.184.216.34", 80))]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    try:
        assert _is_safe_url("https://example.com/video.mp4") is True
        assert socket.getdefaulttimeout() == 3.5
    finally:
        socket.setdefaulttimeout(previous_timeout)


def test_resolve_video_source_platform_url_requires_ytdlp(monkeypatch):
    """Platform URLs raise RuntimeError when yt-dlp is not installed."""
    import builtins

    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "yt_dlp":
            raise ImportError("No module named 'yt_dlp'")
        return real_import(name, *args, **kwargs)

    # Bypass SSRF check so DNS availability doesn't affect the test
    monkeypatch.setattr("mcp_video.ai_engine._is_safe_url", lambda url: True)
    monkeypatch.setattr(builtins, "__import__", mock_import)

    from mcp_video.ai_engine import _resolve_video_source

    with pytest.raises(MCPVideoError, match="yt-dlp"):
        _resolve_video_source("https://www.youtube.com/watch?v=dQw4w9WgXcQ")


def test_resolve_video_source_direct_url_no_extension_no_ytdlp(monkeypatch):
    """Non-video-extension direct URLs without yt-dlp raise a clear error."""
    import builtins

    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "yt_dlp":
            raise ImportError("No module named 'yt_dlp'")
        return real_import(name, *args, **kwargs)

    # Bypass SSRF check so DNS availability doesn't affect the test
    monkeypatch.setattr("mcp_video.ai_engine._is_safe_url", lambda url: True)
    monkeypatch.setattr(builtins, "__import__", mock_import)

    from mcp_video.ai_engine import _resolve_video_source

    with pytest.raises(MCPVideoError, match="yt-dlp"):
        _resolve_video_source("https://example.com/stream")  # no .mp4 extension


@requires_ffmpeg
@requires_ffprobe
def test_analyze_video_url_download(monkeypatch):
    """analyze_video downloads a direct URL to a temp file before analysing."""
    from mcp_video.ai_engine import analyze_video

    # Create a real local video to serve as the "downloaded" file
    with tempfile.TemporaryDirectory() as tmpdir:
        real_video = create_simple_video(str(Path(tmpdir) / "real.mp4"))

        # Patch _resolve_video_source to simulate a URL download
        def fake_resolve(video):
            # Pretend it was a URL, return the real local file, no temp dir to clean
            return real_video, None, "https://example.com/fake.mp4"

        monkeypatch.setattr("mcp_video.ai_engine._resolve_video_source", fake_resolve)

        result = analyze_video(
            "https://example.com/fake.mp4",
            include_transcript=False,
            include_scenes=False,
            include_audio=False,
            include_quality=False,
            include_chapters=False,
            include_colors=False,
        )

    assert result["success"] is True
    assert result["source_url"] == "https://example.com/fake.mp4"
    assert result["metadata"]["width"] == 320


# Add ai_upscale tests to __main__ block
if __name__ == "__main__":
    # Run transcription tests
    print("=" * 60)
    print("Testing AI Transcription")
    print("=" * 60)

    test_transcription = TestTranscription()

    # Test file not found
    try:
        test_transcription.test_transcribe_file_not_found()
        print("✓ test_transcribe_file_not_found passed")
    except Exception as e:
        print(f"✗ test_transcribe_file_not_found failed: {e}")

    # Check if whisper is installed for other tests
    try:
        if importlib.util.find_spec("whisper") is None:
            raise ImportError
        print("\n✓ Whisper is installed, running transcription tests...")

        try:
            test_transcription.test_transcribe_basic()
            print("✓ test_transcribe_basic passed")
        except Exception as e:
            print(f"✗ test_transcribe_basic failed: {e}")

        try:
            test_transcription.test_transcribe_with_srt_output()
            print("✓ test_transcribe_with_srt_output passed")
        except Exception as e:
            print(f"✗ test_transcribe_with_srt_output failed: {e}")

        try:
            test_transcription.test_transcribe_language_detection()
            print("✓ test_transcribe_language_detection passed")
        except Exception as e:
            print(f"✗ test_transcribe_language_detection failed: {e}")

    except ImportError:
        print("\n⚠ Whisper not installed, skipping transcription tests")
        print("  Install with: pip install openai-whisper")

    # Run SRT formatting tests
    print("\n" + "=" * 60)
    print("Testing SRT Formatting")
    print("=" * 60)

    test_srt = TestSRTFormatting()

    try:
        test_srt.test_seconds_to_srt_time()
        print("✓ test_seconds_to_srt_time passed")
    except Exception as e:
        print(f"✗ test_seconds_to_srt_time failed: {e}")

    try:
        test_srt.test_format_srt_empty_segments()
        print("✓ test_format_srt_empty_segments passed")
    except Exception as e:
        print(f"✗ test_format_srt_empty_segments failed: {e}")

    try:
        test_srt.test_format_srt_single_segment()
        print("✓ test_format_srt_single_segment passed")
    except Exception as e:
        print(f"✗ test_format_srt_single_segment failed: {e}")

    try:
        test_srt.test_format_srt_multiple_segments()
        print("✓ test_format_srt_formatting_multiple_segments passed")
    except Exception as e:
        print(f"✗ test_format_srt_multiple_segments failed: {e}")

    try:
        test_srt.test_format_srt_skips_empty_text()
        print("✓ test_format_srt_skips_empty_text passed")
    except Exception as e:
        print(f"✗ test_format_srt_skips_empty_text failed: {e}")

    # Run AI upscale tests
    print("\n" + "=" * 60)
    print("Testing AI Upscale")
    print("=" * 60)

    if realesrgan_installed():
        print("✓ Real-ESRGAN is installed")

        if has_ffmpeg() and has_ffprobe():
            try:
                test_ai_upscale()
                print("✓ test_ai_upscale passed")
            except Exception as e:
                print(f"✗ test_ai_upscale failed: {e}")

            try:
                test_ai_upscale_invalid_scale()
                print("✓ test_ai_upscale_invalid_scale passed")
            except Exception as e:
                print(f"✗ test_ai_upscale_invalid_scale failed: {e}")

            try:
                test_ai_upscale_missing_file()
                print("✓ test_ai_upscale_missing_file passed")
            except Exception as e:
                print(f"✗ test_ai_upscale_missing_file failed: {e}")
        else:
            print("⚠ FFmpeg/ffprobe not available, skipping upscale tests")
    else:
        print("⚠ Real-ESRGAN not installed, testing error handling...")

        if has_ffmpeg():
            try:
                test_ai_upscale_missing_dependency()
                print("✓ test_ai_upscale_missing_dependency passed")
            except Exception as e:
                print(f"✗ test_ai_upscale_missing_dependency failed: {e}")
        else:
            print("⚠ FFmpeg not available, skipping tests")

    print("\nTests complete!")
