"""Real-media integration tests — validates features against iPhone footage.

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


_DOWNLOADS = os.path.expanduser("~/Downloads")

_REAL_FILES = {
    "landscape_1080": os.path.join(_DOWNLOADS, "IMG_4949_trimmed_1920x1080.mov"),
    "square_1080": os.path.join(_DOWNLOADS, "IMG_4949_trimmed_1080x1080.mov"),
    "portrait_1080": os.path.join(_DOWNLOADS, "IMG_4949_trimmed_1080x1920.mov"),
    "crop_640x480": os.path.join(_DOWNLOADS, "IMG_4949_trimmed_crop_640x480.mov"),
    "timeline_mp4": os.path.join(_DOWNLOADS, "IMG_4949_trimmed_timeline.mp4"),
    "video_with_audio": os.path.join(_DOWNLOADS, "IMG_4949_trimmed_audio.mov"),
}

_PNG_FILES: dict[str, str] = {}
if os.path.isdir(_DOWNLOADS):
    for _f in os.listdir(_DOWNLOADS):
        if _f.endswith(".png") and "Screenshot 2026-02-24" in _f:
            _PNG_FILES["png_screenshot_1"] = os.path.join(_DOWNLOADS, _f)
        elif _f.endswith(".png") and "Screenshot 2026-02-25" in _f:
            _PNG_FILES["png_screenshot_2"] = os.path.join(_DOWNLOADS, _f)


def _require_file(name: str) -> str:
    path = _REAL_FILES.get(name) or _PNG_FILES.get(name)
    if path is None or not os.path.isfile(path):
        pytest.skip(f"Real media file not found: {name} ({path})")
    return path


def _require_ffmpeg():
    if shutil.which("ffmpeg") is None:
        pytest.skip("FFmpeg not installed")


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
def real_video_with_audio():
    return _require_file("video_with_audio")


@pytest.mark.slow
class TestFilterRealMedia:
    """Validate video filters on real iPhone footage."""

    @pytest.mark.parametrize(
        "filter_name,params",
        [
            ("blur", {"radius": 8}),
            ("grayscale", {}),
            ("sharpen", {"amount": 2.0}),
            ("sepia", {}),
            ("invert", {}),
            ("vignette", {}),
        ],
    )
    def test_filter_preserves_resolution(self, real_landscape, tmp_path, filter_name, params):
        _require_ffmpeg()
        out = str(tmp_path / f"{filter_name}.mov")
        result = apply_filter(real_landscape, filter_name, params or None, out)
        assert result.success
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


@pytest.mark.slow
class TestNormalizeAudioRealMedia:
    """Validate audio normalization on real iPhone footage."""

    def test_normalize_audio_preserves_codec(self, real_video_with_audio, tmp_path):
        _require_ffmpeg()
        out = str(tmp_path / "norm_youtube.mov")
        result = normalize_audio(real_video_with_audio, target_lufs=-16.0, output_path=out)
        assert result.success
        info = probe(result.output_path)
        assert info.audio_codec in ("aac", "mp4a")
        assert info.codec in ("h264", "hevc", "libx264")


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
        info = probe(result.output_path)
        orig = probe(real_landscape)
        assert info.width == orig.width
        assert info.height == orig.height


@pytest.mark.slow
class TestSplitScreenRealMedia:
    """Validate split-screen compositing with real files."""

    def test_portrait_square_side_by_side(self, real_portrait, real_square, tmp_path):
        _require_ffmpeg()
        out = str(tmp_path / "sbs.mov")
        result = split_screen(real_portrait, real_square, layout="side-by-side", output_path=out)
        assert result.success
        info = probe(result.output_path)
        assert info.height > 0
        assert info.width > 0


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
        assert result["succeeded"] == 3
        for r in result["results"]:
            assert r["success"]
            assert os.path.isfile(r["output_path"])


@pytest.mark.slow
class TestCrossFeatureRealMedia:
    """Test composition of multiple features."""

    def test_filter_then_overlay(self, real_landscape, real_square, tmp_path):
        _require_ffmpeg()
        filtered = str(tmp_path / "filtered.mov")
        r1 = apply_filter(real_landscape, "color_preset", {"preset": "warm"}, filtered)
        assert r1.success

        out = str(tmp_path / "filtered_pip.mov")
        r2 = overlay_video(
            r1.output_path,
            real_square,
            position="bottom-right",
            width=320,
            output_path=out,
        )
        assert r2.success
        info = probe(r2.output_path)
        assert info.width == probe(real_landscape).width

    def test_filter_chain_then_normalize(self, real_mp4, tmp_path):
        _require_ffmpeg()
        step1 = str(tmp_path / "cinematic.mp4")
        r1 = apply_filter(real_mp4, "color_preset", {"preset": "cinematic"}, step1)
        assert r1.success

        step2 = str(tmp_path / "cinematic_sharp.mp4")
        r2 = apply_filter(r1.output_path, "sharpen", {"amount": 1.5}, step2)
        assert r2.success

        out = str(tmp_path / "final.mp4")
        r3 = normalize_audio(r2.output_path, target_lufs=-14.0, output_path=out)
        assert r3.success
        assert os.path.isfile(r3.output_path)
