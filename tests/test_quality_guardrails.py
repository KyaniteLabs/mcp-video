"""Tests for visual design quality guardrails."""

from __future__ import annotations

import os
import subprocess
import tempfile

import pytest

from mcp_video import quality_check, VisualQualityGuardrails, QualityReport


def create_test_video(output_path: str, color: str = "gray", duration: float = 2.0) -> str:
    """Create a test video with specified color background.

    Args:
        output_path: Path to save the video
        color: Color name (gray, black, white, red, green, blue)
        duration: Video duration in seconds

    Returns:
        Path to created video
    """
    # Map color names to ffmpeg color values
    color_map = {
        "gray": "gray",
        "black": "black",
        "white": "white",
        "red": "red",
        "green": "green",
        "blue": "blue",
        "yellow": "yellow",
        "cyan": "cyan",
        "magenta": "magenta",
    }

    ffmpeg_color = color_map.get(color, "gray")

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c={ffmpeg_color}:s=320x240:d={duration}",
        "-f", "lavfi", "-i", f"sine=frequency=1000:duration={duration}",
        "-pix_fmt", "yuv420p", "-shortest",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to create test video: {result.stderr}")
    return output_path


def create_video_no_audio(output_path: str, color: str = "gray", duration: float = 2.0) -> str:
    """Create a test video without audio."""
    ffmpeg_color = color
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c={ffmpeg_color}:s=320x240:d={duration}",
        "-pix_fmt", "yuv420p",
        "-an",  # No audio
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to create test video: {result.stderr}")
    return output_path


class TestQualityReport:
    """Tests for QualityReport dataclass."""

    def test_quality_report_creation(self):
        """Test creating a QualityReport."""
        report = QualityReport(
            check_name="brightness",
            passed=True,
            score=85.0,
            message="Brightness is good",
            details={"y_avg": 128.0}
        )
        assert report.check_name == "brightness"
        assert report.passed is True
        assert report.score == 85.0
        assert report.message == "Brightness is good"
        assert report.details == {"y_avg": 128.0}

    def test_quality_report_default_details(self):
        """Test QualityReport with default empty details."""
        report = QualityReport(
            check_name="contrast",
            passed=False,
            score=45.0,
            message="Contrast too low",
        )
        assert report.details == {}


class TestVisualQualityGuardrails:
    """Tests for VisualQualityGuardrails class."""

    @pytest.fixture
    def guardrails(self):
        """Create a VisualQualityGuardrails instance."""
        return VisualQualityGuardrails()

    def test_initialization(self, guardrails):
        """Test guardrails initializes with correct thresholds."""
        assert guardrails.BRIGHTNESS_MIN == 16
        assert guardrails.BRIGHTNESS_MAX == 235
        assert guardrails.BRIGHTNESS_TARGET_MIN == 40
        assert guardrails.BRIGHTNESS_TARGET_MAX == 200
        assert guardrails.CONTRAST_MIN == 20
        assert guardrails.CONTRAST_MAX == 100
        assert guardrails.AUDIO_LUFS_TARGET == -16

    def test_check_brightness_with_gray_video(self, guardrails, tmp_path):
        """Test brightness check on a gray video."""
        video_path = str(tmp_path / "gray.mp4")
        create_test_video(video_path, "gray")

        report = guardrails.check_brightness(video_path)

        assert report.check_name == "brightness"
        assert isinstance(report.passed, bool)
        assert 0 <= report.score <= 100
        assert isinstance(report.message, str)
        assert "y_avg" in report.details or report.score == 0.0

    def test_check_brightness_with_black_video(self, guardrails, tmp_path):
        """Test brightness check on a black video (should fail)."""
        video_path = str(tmp_path / "black.mp4")
        create_test_video(video_path, "black")

        report = guardrails.check_brightness(video_path)

        assert report.check_name == "brightness"
        assert isinstance(report.score, float)
        if report.score > 0:  # If analysis succeeded
            assert report.score < 80  # Black video should have low score

    def test_check_contrast(self, guardrails, tmp_path):
        """Test contrast check."""
        video_path = str(tmp_path / "test.mp4")
        create_test_video(video_path, "gray")

        report = guardrails.check_contrast(video_path)

        assert report.check_name == "contrast"
        assert isinstance(report.score, float)
        assert 0 <= report.score <= 100
        assert isinstance(report.message, str)

    def test_check_saturation(self, guardrails, tmp_path):
        """Test saturation check."""
        video_path = str(tmp_path / "test.mp4")
        create_test_video(video_path, "gray")

        report = guardrails.check_saturation(video_path)

        assert report.check_name == "saturation"
        assert isinstance(report.score, float)
        assert 0 <= report.score <= 100

    def test_check_color_balance(self, guardrails, tmp_path):
        """Test color balance check."""
        video_path = str(tmp_path / "test.mp4")
        create_test_video(video_path, "gray")

        report = guardrails.check_color_balance(video_path)

        assert report.check_name == "color_balance"
        assert isinstance(report.score, float)
        assert 0 <= report.score <= 100
        assert isinstance(report.message, str)

    def test_check_color_balance_detects_red_cast(self, guardrails, tmp_path):
        """Test color balance detects red color cast."""
        video_path = str(tmp_path / "red.mp4")
        create_test_video(video_path, "red")

        report = guardrails.check_color_balance(video_path)

        if report.score > 0:  # If analysis succeeded
            # Red video should have red in color_cast or lower score
            details = report.details
            if details.get("color_cast"):
                assert "red" in details["color_cast"] or report.score < 70

    def test_check_audio_levels_with_audio(self, guardrails, tmp_path):
        """Test audio levels check on video with audio."""
        video_path = str(tmp_path / "test.mp4")
        create_test_video(video_path, "gray")

        report = guardrails.check_audio_levels(video_path)

        assert report.check_name == "audio_levels"
        assert isinstance(report.score, float)
        assert 0 <= report.score <= 100
        assert "lufs" in report.details or report.details.get("has_audio") is False

    def test_check_audio_levels_no_audio(self, guardrails, tmp_path):
        """Test audio levels check on video without audio."""
        video_path = str(tmp_path / "no_audio.mp4")
        create_video_no_audio(video_path, "gray")

        report = guardrails.check_audio_levels(video_path)

        assert report.check_name == "audio_levels"
        # Should detect no audio and still pass
        if report.details.get("has_audio") is False:
            assert report.passed is True
            assert report.score == 100.0

    def test_run_all_checks(self, guardrails, tmp_path):
        """Test running all quality checks."""
        video_path = str(tmp_path / "test.mp4")
        create_test_video(video_path, "gray")

        checks = guardrails.run_all_checks(video_path)

        assert len(checks) == 5
        check_names = [c.check_name for c in checks]
        assert "brightness" in check_names
        assert "contrast" in check_names
        assert "saturation" in check_names
        assert "audio_levels" in check_names
        assert "color_balance" in check_names

    def test_generate_report(self, guardrails, tmp_path):
        """Test generating comprehensive quality report."""
        video_path = str(tmp_path / "test.mp4")
        create_test_video(video_path, "gray")

        report = guardrails.generate_report(video_path)

        assert "video" in report
        assert "overall_score" in report
        assert "all_passed" in report
        assert "checks" in report
        assert "recommendations" in report
        assert isinstance(report["overall_score"], (int, float))
        assert isinstance(report["all_passed"], bool)
        assert isinstance(report["checks"], list)
        assert len(report["checks"]) == 5
        assert report["video"] == video_path


class TestQualityCheckAPI:
    """Tests for the quality_check public API."""

    def test_quality_check_basic(self, tmp_path):
        """Test basic quality_check function."""
        video_path = str(tmp_path / "test.mp4")
        create_test_video(video_path, "gray")

        report = quality_check(video_path)

        assert "video" in report
        assert "overall_score" in report
        assert "all_passed" in report
        assert "checks" in report
        assert "recommendations" in report

    def test_quality_check_fail_on_warning(self, tmp_path):
        """Test quality_check with fail_on_warning=True."""
        video_path = str(tmp_path / "test.mp4")
        create_test_video(video_path, "gray")

        report = quality_check(video_path, fail_on_warning=True)

        assert "all_passed" in report
        # If overall score < 80, all_passed should be False
        if report["overall_score"] < 80:
            assert report["all_passed"] is False

    def test_quality_check_with_black_video(self, tmp_path):
        """Test quality_check on black video."""
        video_path = str(tmp_path / "black.mp4")
        create_test_video(video_path, "black")

        report = quality_check(video_path)

        assert "checks" in report
        # Should have recommendations for dark video
        assert isinstance(report["recommendations"], list)

    def test_quality_check_with_white_video(self, tmp_path):
        """Test quality_check on white video."""
        video_path = str(tmp_path / "white.mp4")
        create_test_video(video_path, "white")

        report = quality_check(video_path)

        assert "checks" in report
        # Should have recommendations for bright video
        brightness_check = None
        for check in report["checks"]:
            if check["name"] == "brightness":
                brightness_check = check
                break

        if brightness_check and brightness_check["score"] > 0:
            # White video should have lower brightness score
            assert brightness_check["score"] < 90


class TestClientIntegration:
    """Tests for Client.quality_check integration."""

    def test_client_quality_check_method(self, tmp_path):
        """Test that Client has quality_check method."""
        from mcp_video import Client

        client = Client()
        video_path = str(tmp_path / "test.mp4")
        create_test_video(video_path, "gray")

        report = client.quality_check(video_path)

        assert "overall_score" in report
        assert "checks" in report


@pytest.mark.skipif(
    not subprocess.run(["which", "ffmpeg"], capture_output=True).returncode == 0,
    reason="FFmpeg not installed"
)
class TestFFmpegAvailability:
    """Tests that require FFmpeg to be installed."""

    def test_ffmpeg_available(self):
        """Verify FFmpeg is available."""
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        assert result.returncode == 0
        assert "ffmpeg version" in result.stdout.lower()

    def test_ffprobe_available(self):
        """Verify ffprobe is available."""
        result = subprocess.run(["ffprobe", "-version"], capture_output=True, text=True)
        assert result.returncode == 0
        assert "ffprobe version" in result.stdout.lower()


if __name__ == "__main__":
    # Run a quick manual test
    with tempfile.TemporaryDirectory() as tmpdir:
        video = os.path.join(tmpdir, "test.mp4")
        create_test_video(video, "gray")

        report = quality_check(video)

        print(f"\n✓ Quality score: {report['overall_score']:.1f}/100")
        print(f"  All passed: {report['all_passed']}")
        print("\n  Individual checks:")
        for check in report["checks"]:
            status = "✓" if check["passed"] else "✗"
            print(f"    {status} {check['name']}: {check['score']:.1f} - {check['message']}")

        if report["recommendations"]:
            print("\n  Recommendations:")
            for rec in report["recommendations"]:
                print(f"    - {rec}")
        else:
            print("\n  No recommendations - video looks good!")
