"""Real-media integration tests — validates v0.3.0 features against iPhone footage.

These tests use actual camera files from ~/Downloads/ and are marked @pytest.mark.slow.
They exercise real-world codecs (HEVC/H.264 in MOV containers), variable frame rates,
alpha-blending with PNG screenshots, and composition of multiple features.

Run with: pytest tests/test_real_media.py -v -m slow
"""

from __future__ import annotations

import os
import shutil

import pytest

from mcp_video.engine import (
    apply_filter,
    normalize_audio,
    overlay_video,
    split_screen,
    probe,
)
from mcp_video.server import video_batch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DOWNLOADS = os.path.expanduser("~/Downloads")

_REAL_FILES = {
    "portrait_4k": os.path.join(_DOWNLOADS, "IMG_4949_trimmed.mov"),
    "square_1080": os.path.join(_DOWNLOADS, "IMG_4949_trimmed_1080x1080.mov"),
    "portrait_1080": os.path.join(_DOWNLOADS, "IMG_4949_trimmed_1080x1920.mov"),
    "landscape_1080": os.path.join(_DOWNLOADS, "IMG_4949_trimmed_1920x1080.mov"),
    "crop_640x480": os.path.join(_DOWNLOADS, "IMG_4949_trimmed_crop_640x480.mov"),
    "timeline_mp4": os.path.join(_DOWNLOADS, "IMG_4949_trimmed_timeline.mp4"),
    "audio_mp3": os.path.join(_DOWNLOADS, "IMG_4949_trimmed_audio_audio.mp3"),
    # This file has real AAC audio from iPhone
    "video_with_audio": os.path.join(_DOWNLOADS, "IMG_4949_trimmed_audio.mov"),
}

# Resolve PNG files by scanning directory (handles Unicode narrow no-break spaces)
_PNG_FILES: dict[str, str] = {}
if os.path.isdir(_DOWNLOADS):
    for _f in os.listdir(_DOWNLOADS):
        if _f.endswith(".png") and "Screenshot 2026-02-24" in _f:
            _PNG_FILES["png_screenshot_1"] = os.path.join(_DOWNLOADS, _f)
        elif _f.endswith(".png") and "Screenshot 2026-02-25" in _f:
            _PNG_FILES["png_screenshot_2"] = os.path.join(_DOWNLOADS, _f)


def _require_file(name: str) -> str:
    """Return the real file path or skip the test if not found."""
    path = _REAL_FILES.get(name) or _PNG_FILES.get(name)
    if path is None or not os.path.isfile(path):
        pytest.skip(f"Real media file not found: {name} ({path})")
    return path


def _require_ffmpeg():
    if shutil.which("ffmpeg") is None:
        pytest.skip("FFmpeg not installed")


# ---------------------------------------------------------------------------
# Session-scoped fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def real_landscape():
    return _require_file("landscape_1080")


@pytest.fixture(scope="session")
def real_square():
    return _require_file("square_1080")


@pytest.fixture(scope="session")
def real_portrait():
    return _require_file("portrait_1080")


@pytest.fixture(scope="session")
def real_crop():
    return _require_file("crop_640x480")


@pytest.fixture(scope="session")
def real_mp4():
    return _require_file("timeline_mp4")


@pytest.fixture(scope="session")
def real_png():
    return _require_file("png_screenshot_1")


@pytest.fixture(scope="session")
def real_png_2():
    return _require_file("png_screenshot_2")


@pytest.fixture(scope="session")
def real_audio():
    return _require_file("audio_mp3")


@pytest.fixture(scope="session")
def real_video_with_audio():
    return _require_file("video_with_audio")


# ---------------------------------------------------------------------------
# 1. Filter tests on real media
# ---------------------------------------------------------------------------


@pytest.mark.slow
class TestFilterRealMedia:
    """Validate video filters on real iPhone footage."""

    def test_blur_on_landscape(self, real_landscape, tmp_path):
        _require_ffmpeg()
        out = str(tmp_path / "blur.mov")
        result = apply_filter(real_landscape, "blur", {"radius": 8}, out)
        assert result.success
        assert os.path.isfile(result.output_path)
        info = probe(result.output_path)
        orig = probe(real_landscape)
        assert info.width == orig.width
        assert info.height == orig.height

    @pytest.mark.parametrize("preset", ["warm", "cool", "vintage", "cinematic", "noir"])
    def test_color_preset_preserves_resolution(self, real_landscape, tmp_path, preset):
        _require_ffmpeg()
        out = str(tmp_path / f"preset_{preset}.mov")
        result = apply_filter(real_landscape, "color_preset", {"preset": preset}, out)
        assert result.success
        info = probe(result.output_path)
        orig = probe(real_landscape)
        assert info.width == orig.width
        assert info.height == orig.height

    def test_grayscale_on_real_content(self, real_square, tmp_path):
        _require_ffmpeg()
        out = str(tmp_path / "gray.mov")
        result = apply_filter(real_square, "grayscale", output_path=out)
        assert result.success
        info = probe(result.output_path)
        orig = probe(real_square)
        assert info.width == orig.width
        assert info.height == orig.height

    def test_sharpen_preserves_resolution(self, real_landscape, tmp_path):
        _require_ffmpeg()
        out = str(tmp_path / "sharp.mov")
        result = apply_filter(real_landscape, "sharpen", {"amount": 2.0}, out)
        assert result.success
        info = probe(result.output_path)
        orig = probe(real_landscape)
        assert info.width == orig.width
        assert info.height == orig.height

    def test_sepia_on_portrait(self, real_portrait, tmp_path):
        _require_ffmpeg()
        out = str(tmp_path / "sepia.mov")
        result = apply_filter(real_portrait, "sepia", output_path=out)
        assert result.success
        info = probe(result.output_path)
        orig = probe(real_portrait)
        assert info.width == orig.width
        assert info.height == orig.height

    def test_invert_on_crop(self, real_crop, tmp_path):
        _require_ffmpeg()
        out = str(tmp_path / "invert.mov")
        result = apply_filter(real_crop, "invert", output_path=out)
        assert result.success
        assert os.path.isfile(result.output_path)

    def test_vignette_on_mp4(self, real_mp4, tmp_path):
        _require_ffmpeg()
        out = str(tmp_path / "vignette.mp4")
        result = apply_filter(real_mp4, "vignette", output_path=out)
        assert result.success
        assert os.path.isfile(result.output_path)

    def test_brightness_contrast_saturation_chain(self, real_landscape, tmp_path):
        """Apply brightness then contrast then saturation sequentially."""
        _require_ffmpeg()
        step1 = str(tmp_path / "bright.mov")
        step2 = str(tmp_path / "contrast.mov")
        step3 = str(tmp_path / "saturated.mov")

        r1 = apply_filter(real_landscape, "brightness", {"level": 0.15}, step1)
        assert r1.success
        r2 = apply_filter(r1.output_path, "contrast", {"level": 1.3}, step2)
        assert r2.success
        r3 = apply_filter(r2.output_path, "saturation", {"level": 1.8}, step3)
        assert r3.success

        info = probe(r3.output_path)
        orig = probe(real_landscape)
        assert info.width == orig.width
        assert info.height == orig.height


# ---------------------------------------------------------------------------
# 2. Normalize audio tests on real media
# ---------------------------------------------------------------------------


@pytest.mark.slow
class TestNormalizeAudioRealMedia:
    """Validate audio normalization on real iPhone footage."""

    def test_youtube_lufs(self, real_video_with_audio, tmp_path):
        _require_ffmpeg()
        out = str(tmp_path / "norm_youtube.mov")
        result = normalize_audio(real_video_with_audio, target_lufs=-16.0, output_path=out)
        assert result.success
        assert os.path.isfile(result.output_path)
        info = probe(result.output_path)
        # Audio codec should be AAC after normalization
        assert info.audio_codec in ("aac", "mp4a")

    def test_broadcast_lufs(self, real_video_with_audio, tmp_path):
        _require_ffmpeg()
        out = str(tmp_path / "norm_broadcast.mov")
        result = normalize_audio(real_video_with_audio, target_lufs=-23.0, output_path=out)
        assert result.success
        assert os.path.isfile(result.output_path)

    def test_spotify_lufs(self, real_video_with_audio, tmp_path):
        _require_ffmpeg()
        out = str(tmp_path / "norm_spotify.mov")
        result = normalize_audio(real_video_with_audio, target_lufs=-14.0, output_path=out)
        assert result.success
        assert os.path.isfile(result.output_path)

    def test_normalize_preserves_video_codec(self, real_video_with_audio, tmp_path):
        """Normalize audio and verify video stream is preserved."""
        _require_ffmpeg()
        out = str(tmp_path / "norm_codec.mov")
        result = normalize_audio(real_video_with_audio, target_lufs=-16.0, output_path=out)
        assert result.success
        assert os.path.isfile(result.output_path)
        info = probe(result.output_path)
        # Video codec should be preserved
        assert info.codec in ("h264", "hevc", "libx264")


# ---------------------------------------------------------------------------
# 3. Overlay tests on real media
# ---------------------------------------------------------------------------


@pytest.mark.slow
class TestOverlayRealMedia:
    """Validate picture-in-picture overlay with real files."""

    def test_square_on_landscape_pip(self, real_landscape, real_square, tmp_path):
        _require_ffmpeg()
        out = str(tmp_path / "pip.mov")
        result = overlay_video(
            real_landscape,
            real_square,
            position="bottom-right",
            width=360,
            output_path=out,
        )
        assert result.success
        assert os.path.isfile(result.output_path)
        info = probe(result.output_path)
        # Output dimensions should match background
        orig = probe(real_landscape)
        assert info.width == orig.width
        assert info.height == orig.height

    def test_portrait_on_landscape_with_timing(self, real_landscape, real_portrait, tmp_path):
        _require_ffmpeg()
        out = str(tmp_path / "pip_timed.mov")
        result = overlay_video(
            real_landscape,
            real_portrait,
            position="top-left",
            width=480,
            start_time=0.0,
            duration=1.0,
            output_path=out,
        )
        assert result.success
        assert os.path.isfile(result.output_path)
        info = probe(result.output_path)
        orig = probe(real_landscape)
        assert info.width == orig.width
        assert info.height == orig.height

    def test_png_alpha_overlay(self, real_landscape, real_png, tmp_path):
        _require_ffmpeg()
        out = str(tmp_path / "png_overlay.mov")
        result = overlay_video(
            real_landscape,
            real_png,
            position="center",
            width=400,
            opacity=0.9,
            output_path=out,
        )
        assert result.success
        assert os.path.isfile(result.output_path)
        info = probe(result.output_path)
        orig = probe(real_landscape)
        assert info.width == orig.width
        assert info.height == orig.height

    def test_crop_overlay_on_mp4(self, real_mp4, real_crop, tmp_path):
        _require_ffmpeg()
        out = str(tmp_path / "crop_overlay.mp4")
        result = overlay_video(
            real_mp4,
            real_crop,
            position="top-right",
            width=320,
            height=240,
            output_path=out,
        )
        assert result.success
        assert os.path.isfile(result.output_path)


# ---------------------------------------------------------------------------
# 4. Split-screen tests on real media
# ---------------------------------------------------------------------------


@pytest.mark.slow
class TestSplitScreenRealMedia:
    """Validate split-screen compositing with real files."""

    def test_portrait_square_side_by_side(self, real_portrait, real_square, tmp_path):
        _require_ffmpeg()
        out = str(tmp_path / "sbs.mov")
        result = split_screen(real_portrait, real_square, layout="side-by-side", output_path=out)
        assert result.success
        assert os.path.isfile(result.output_path)
        info = probe(result.output_path)
        portrait_info = probe(real_portrait)
        square_info = probe(real_square)
        # Max-dims: both scaled to max height (1920), so width = portrait_w + scaled_square_w
        target_h = max(portrait_info.height, square_info.height)
        scaled_square_w = int(square_info.width * target_h / square_info.height)
        assert info.height == target_h
        assert info.width == portrait_info.width + scaled_square_w

    def test_landscape_square_top_bottom(self, real_landscape, real_square, tmp_path):
        _require_ffmpeg()
        out = str(tmp_path / "tb.mov")
        result = split_screen(real_landscape, real_square, layout="top-bottom", output_path=out)
        assert result.success
        assert os.path.isfile(result.output_path)
        info = probe(result.output_path)
        landscape_info = probe(real_landscape)
        square_info = probe(real_square)
        # Max-dims: both scaled to max width (1920), so height = landscape_h + scaled_square_h
        target_w = max(landscape_info.width, square_info.width)
        scaled_square_h = int(square_info.height * target_w / square_info.width)
        assert info.width == target_w
        assert info.height == landscape_info.height + scaled_square_h

    def test_same_height_no_resize(self, real_square, tmp_path):
        """Two square videos should not need resize."""
        _require_ffmpeg()
        out = str(tmp_path / "sbs_same.mov")
        result = split_screen(real_square, real_square, layout="side-by-side", output_path=out)
        assert result.success
        info = probe(result.output_path)
        sq = probe(real_square)
        assert info.width == sq.width * 2
        assert info.height == sq.height

    def test_crop_landscape_side_by_side(self, real_crop, real_landscape, tmp_path):
        _require_ffmpeg()
        out = str(tmp_path / "crop_landscape_sbs.mov")
        result = split_screen(real_crop, real_landscape, layout="side-by-side", output_path=out)
        assert result.success
        assert os.path.isfile(result.output_path)
        info = probe(result.output_path)
        assert info.height > 0
        assert info.width > 0


# ---------------------------------------------------------------------------
# 5. Batch processing tests on real media
# ---------------------------------------------------------------------------


@pytest.mark.slow
class TestBatchRealMedia:
    """Validate batch_process with real media files."""

    def test_blur_across_resolutions(self, real_landscape, real_square, real_crop, tmp_path):
        _require_ffmpeg()
        files = [real_landscape, real_square, real_crop]
        result = video_batch(
            inputs=files,
            operation="blur",
            params={"filter_params": {"radius": 8, "strength": 2}},
        )
        assert result["success"]
        results = result["results"]
        assert len(results) == 3
        for r in results:
            assert r["success"], f"Batch blur failed: {r}"
            assert os.path.isfile(r["output_path"])

    def test_color_grade_across_files(self, real_landscape, real_mp4, tmp_path):
        _require_ffmpeg()
        files = [real_landscape, real_mp4]
        result = video_batch(
            inputs=files,
            operation="color_grade",
            params={"preset": "cinematic"},
        )
        assert result["success"]
        results = result["results"]
        assert len(results) == 2
        for r in results:
            assert r["success"], f"Batch color_grade failed: {r}"
            assert os.path.isfile(r["output_path"])

    def test_normalize_audio_across_files(self, real_video_with_audio, tmp_path):
        _require_ffmpeg()
        # Use the same file twice (different operations) — batch with real audio
        files = [real_video_with_audio]
        result = video_batch(
            inputs=files,
            operation="normalize_audio",
            params={"target_lufs": -16.0},
        )
        assert result["success"]
        results = result["results"]
        assert len(results) == 1
        assert results[0]["success"]
        assert os.path.isfile(results[0]["output_path"])

    def test_trim_across_files(self, real_landscape, real_square, tmp_path):
        _require_ffmpeg()
        files = [real_landscape, real_square]
        result = video_batch(
            inputs=files,
            operation="trim",
            params={"start": 0, "duration": 1},
        )
        assert result["success"]
        results = result["results"]
        assert len(results) == 2
        for r in results:
            assert r["success"], f"Batch trim failed: {r}"
            assert os.path.isfile(r["output_path"])


# ---------------------------------------------------------------------------
# 6. Cross-feature composition tests
# ---------------------------------------------------------------------------


@pytest.mark.slow
class TestCrossFeatureRealMedia:
    """Test composition of multiple v0.3.0 features."""

    def test_filter_then_overlay(self, real_landscape, real_square, tmp_path):
        _require_ffmpeg()
        # Step 1: apply filter to background
        filtered = str(tmp_path / "filtered.mov")
        r1 = apply_filter(real_landscape, "color_preset", {"preset": "warm"}, filtered)
        assert r1.success

        # Step 2: overlay square on filtered video
        out = str(tmp_path / "filtered_pip.mov")
        r2 = overlay_video(
            r1.output_path,
            real_square,
            position="bottom-right",
            width=320,
            output_path=out,
        )
        assert r2.success
        assert os.path.isfile(r2.output_path)
        info = probe(r2.output_path)
        assert info.width == probe(real_landscape).width

    def test_split_then_normalize(self, real_landscape, real_square, tmp_path):
        _require_ffmpeg()
        # Step 1: split screen
        split_out = str(tmp_path / "split.mov")
        r1 = split_screen(real_landscape, real_square, layout="side-by-side", output_path=split_out)
        assert r1.success

        # Step 2: normalize audio on the split result
        norm_out = str(tmp_path / "split_normalized.mov")
        r2 = normalize_audio(r1.output_path, target_lufs=-16.0, output_path=norm_out)
        assert r2.success
        assert os.path.isfile(r2.output_path)

    def test_batch_mixed_operations(self, real_landscape, real_square, real_crop, tmp_path):
        """Batch with different operations — tests batch actually processes multiple files."""
        _require_ffmpeg()
        # Blur 3 files in a single batch call
        r1 = video_batch(
            inputs=[real_landscape, real_square, real_crop],
            operation="blur",
            params={"filter_params": {"radius": 3}},
        )
        assert r1["success"]
        assert r1["total"] == 3
        assert r1["succeeded"] == 3
        for r in r1["results"]:
            assert r["success"], f"Batch blur failed: {r}"
            assert os.path.isfile(r["output_path"])

        # Color grade 2 files in a single batch call
        r2 = video_batch(
            inputs=[real_landscape, real_square],
            operation="color_grade",
            params={"preset": "noir"},
        )
        assert r2["success"]
        assert r2["total"] == 2
        assert r2["succeeded"] == 2
        for r in r2["results"]:
            assert r["success"], f"Batch color_grade failed: {r}"
            assert os.path.isfile(r["output_path"])

        # Trim 2 files in a single batch call
        r3 = video_batch(
            inputs=[real_landscape, real_crop],
            operation="trim",
            params={"start": 0, "duration": 1},
        )
        assert r3["success"]
        assert r3["total"] == 2
        assert r3["succeeded"] == 2
        for r in r3["results"]:
            assert r["success"], f"Batch trim failed: {r}"
            assert os.path.isfile(r["output_path"])

    def test_grayscale_then_split(self, real_landscape, real_square, tmp_path):
        _require_ffmpeg()
        # Step 1: grayscale both
        g1 = str(tmp_path / "gray1.mov")
        g2 = str(tmp_path / "gray2.mov")
        r1 = apply_filter(real_landscape, "grayscale", output_path=g1)
        r2 = apply_filter(real_square, "grayscale", output_path=g2)
        assert r1.success and r2.success

        # Step 2: split the grayscale videos
        out = str(tmp_path / "gray_split.mov")
        r3 = split_screen(r1.output_path, r2.output_path, layout="side-by-side", output_path=out)
        assert r3.success
        assert os.path.isfile(r3.output_path)

    def test_filter_chain_then_normalize(self, real_mp4, tmp_path):
        _require_ffmpeg()
        # Step 1: apply multiple filters
        step1 = str(tmp_path / "cinematic.mp4")
        r1 = apply_filter(real_mp4, "color_preset", {"preset": "cinematic"}, step1)
        assert r1.success

        step2 = str(tmp_path / "cinematic_sharp.mp4")
        r2 = apply_filter(r1.output_path, "sharpen", {"amount": 1.5}, step2)
        assert r2.success

        # Step 2: normalize audio on the final result
        out = str(tmp_path / "final.mp4")
        r3 = normalize_audio(r2.output_path, target_lufs=-14.0, output_path=out)
        assert r3.success
        assert os.path.isfile(r3.output_path)
