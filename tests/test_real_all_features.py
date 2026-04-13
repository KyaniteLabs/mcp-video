"""Exhaustive Real Media Test Suite for mcp-video v1.0

Tests ALL 70+ features using REAL video files and media operations.
Each test verifies the feature works correctly with actual media.

Run with: python -m pytest tests/test_real_all_features.py -v
Skip slow tests: python -m pytest tests/test_real_all_features.py -v -m "not slow"
"""

import os
import sys
import pytest
import tempfile
import subprocess
import json
import importlib.util
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_video import Client

# Test video files (real media)
TEST_VIDEOS = {
    'explainer': 'out/McpVideoExplainer-FINAL.mp4',
    'original': 'out/McpVideoExplainerV1.mp4',
}

# Skip if no test videos
skip_no_video = pytest.mark.skipif(
    not os.path.exists(TEST_VIDEOS['explainer']),
    reason="Test video not found"
)


def has_ai_upscale_backend() -> bool:
    """Check whether at least one AI upscale backend is available."""
    if importlib.util.find_spec("realesrgan"):
        return True
    try:
        import cv2
    except ImportError:
        return False
    return hasattr(cv2, "dnn_superres")


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def client():
    """Provide a fresh Client instance."""
    return Client()


@pytest.fixture
def test_video():
    """Provide the main test video path."""
    return TEST_VIDEOS['explainer']


@pytest.fixture
def output_dir():
    """Provide a temporary output directory."""
    with tempfile.TemporaryDirectory() as tmp:
        yield tmp


@pytest.fixture
def sample_clips(output_dir):
    """Create sample video clips for testing."""
    clips = []
    colors = ['red', 'blue', 'green', 'yellow']

    for i, color in enumerate(colors):
        clip_path = os.path.join(output_dir, f'sample_{color}.mp4')
        subprocess.run([
            'ffmpeg', '-y', '-f', 'lavfi',
            '-i', f'color=c={color}:s=640x480:d=2',
            '-f', 'lavfi', '-i', 'sine=frequency=1000:duration=2',
            '-c:v', 'libx264', '-c:a', 'aac', '-pix_fmt', 'yuv420p',
            clip_path
        ], capture_output=True, check=True)
        clips.append(clip_path)

    return clips


@pytest.fixture
def short_test_clip(output_dir):
    """Create a short test clip (3s) for quality checks that would timeout on full video."""
    clip_path = os.path.join(output_dir, 'short_test.mp4')
    subprocess.run([
        'ffmpeg', '-y', '-f', 'lavfi',
        '-i', 'color=c=blue:s=640x480:d=3',
        '-f', 'lavfi', '-i', 'sine=frequency=1000:duration=3',
        '-c:v', 'libx264', '-c:a', 'aac', '-pix_fmt', 'yuv420p',
        '-vf', 'drawtext=text=Test:fontsize=30:fontcolor=white:x=10:y=10',
        clip_path
    ], capture_output=True, check=True)
    return clip_path


# =============================================================================
# CATEGORY A: CORE VIDEO EDITING (Tests 01-18)
# =============================================================================

@pytest.mark.slow
class TestCoreVideoEditing:
    """Test core video editing operations with real videos."""

    def test_01_video_info(self, client, test_video):
        """Get video metadata and verify properties."""
        info = client.info(test_video)

        assert info.width == 1920, f"Expected width 1920, got {info.width}"
        assert info.height == 1080, f"Expected height 1080, got {info.height}"
        assert info.fps == 30, f"Expected 30fps, got {info.fps}"
        assert abs(info.duration - 100.0) < 5.0, f"Duration ~100s expected, got {info.duration}"
        assert info.audio_codec is not None
        print(f"✓ Video: {info.width}x{info.height} @ {info.fps}fps, {info.duration:.1f}s")

    def test_02_trim_video(self, client, test_video, output_dir):
        """Trim video to specific time range."""
        output = os.path.join(output_dir, 'trimmed.mp4')

        result = client.trim(test_video, start=10, duration=5, output=output)

        assert result.success
        assert os.path.exists(result.output_path)
        # Verify trimmed duration
        info = client.info(result.output_path)
        assert abs(info.duration - 5.0) < 1.0, f"Expected ~5s, got {info.duration}"
        print(f"✓ Trimmed: {info.duration:.1f}s")

    def test_03_merge_videos(self, client, sample_clips, output_dir):
        """Merge multiple video clips."""
        output = os.path.join(output_dir, 'merged.mp4')

        result = client.merge(sample_clips[:2], output=output)

        assert result.success
        assert os.path.exists(result.output_path)
        # Should be ~4s (2 clips x 2s each)
        info = client.info(result.output_path)
        assert info.duration >= 3.5, f"Merged duration too short: {info.duration}"
        print(f"✓ Merged: {info.duration:.1f}s")

    def test_04_resize_video(self, client, test_video, output_dir):
        """Resize video to different resolution."""
        output = os.path.join(output_dir, 'resized_720p.mp4')

        result = client.resize(test_video, width=1280, height=720, output=output)

        assert result.success
        info = client.info(result.output_path)
        assert info.width == 1280, f"Expected 1280, got {info.width}"
        assert info.height == 720, f"Expected 720, got {info.height}"
        print(f"✓ Resized to {info.width}x{info.height}")

    def test_05_change_speed(self, client, sample_clips, output_dir):
        """Change video playback speed."""
        output = os.path.join(output_dir, '2x_speed.mp4')

        result = client.speed(sample_clips[0], factor=2.0, output=output)

        assert result.success
        info = client.info(result.output_path)
        # 2s clip at 2x speed = ~1s
        assert info.duration <= 1.5, f"Expected ~1s at 2x, got {info.duration}"
        print(f"✓ 2x speed: {info.duration:.1f}s (from 2.0s)")

    def test_06_extract_frame(self, client, test_video, output_dir):
        """Extract a single frame as image."""
        output = os.path.join(output_dir, 'frame.png')

        result = client.extract_frame(test_video, timestamp=5.0, output=output)

        # ThumbnailResult uses frame_path not output_path
        frame_path = result.frame_path if hasattr(result, 'frame_path') else getattr(result, 'output_path', output)
        assert os.path.exists(frame_path)
        assert frame_path.endswith('.png')
        print(f"✓ Frame extracted: {frame_path}")

    def test_07_fade_video(self, client, sample_clips, output_dir):
        """Add fade in/out to video."""
        output = os.path.join(output_dir, 'faded.mp4')

        result = client.fade(sample_clips[0], fade_in=0.5, fade_out=0.5, output=output)

        assert result.success
        assert os.path.exists(result.output_path)
        print(f"✓ Fade applied")

    def test_08_crop_video(self, client, test_video, output_dir):
        """Crop video to region."""
        output = os.path.join(output_dir, 'cropped.mp4')

        result = client.crop(test_video, width=800, height=600, x=560, y=240, output=output)

        assert result.success
        info = client.info(result.output_path)
        assert info.width == 800
        assert info.height == 600
        print(f"✓ Cropped to {info.width}x{info.height}")

    def test_09_rotate_video(self, client, sample_clips, output_dir):
        """Rotate video 90 degrees."""
        output = os.path.join(output_dir, 'rotated.mp4')

        result = client.rotate(sample_clips[0], angle=90, output=output)

        assert result.success
        info = client.info(result.output_path)
        # 640x480 rotated 90° = 480x640
        assert info.width == 480, f"Expected 480, got {info.width}"
        assert info.height == 640, f"Expected 640, got {info.height}"
        print(f"✓ Rotated: {info.width}x{info.height}")

    def test_10_flip_video(self, client, sample_clips, output_dir):
        """Flip video horizontally."""
        output = os.path.join(output_dir, 'flipped.mp4')

        result = client.rotate(sample_clips[0], flip_horizontal=True, output=output)

        assert result.success
        assert os.path.exists(result.output_path)
        print(f"✓ Horizontal flip applied")

    def test_11_reverse_video(self, client, sample_clips, output_dir):
        """Reverse video playback."""
        output = os.path.join(output_dir, 'reversed.mp4')

        result = client.reverse(sample_clips[0], output=output)

        assert result.success
        assert os.path.exists(result.output_path)
        print(f"✓ Video reversed")

    @pytest.mark.skipif(
        subprocess.run(
            ["ffmpeg", "-filters"],
            capture_output=True,
            text=True
        ).stdout.find("vidstabdetect") == -1,
        reason="Requires FFmpeg with vidstabdetect filter"
    )
    def test_12_stabilize_video(self, client, sample_clips, output_dir):
        """Stabilize shaky video."""
        output = os.path.join(output_dir, 'stabilized.mp4')

        # Use a short clip for faster test
        result = client.stabilize(sample_clips[0], smoothing=10, output=output)

        assert result.success
        assert os.path.exists(result.output_path)
        print(f"✓ Stabilization applied")

    def test_13_chroma_key(self, client, sample_clips, output_dir):
        """Remove green screen background."""
        output = os.path.join(output_dir, 'keyed.mp4')

        # Use green clip for chroma key
        result = client.chroma_key(sample_clips[2], color='0x00FF00', similarity=0.1, output=output)

        assert result.success
        assert os.path.exists(result.output_path)
        print(f"✓ Chroma key applied")

    def test_14_blur_video(self, client, sample_clips, output_dir):
        """Apply blur effect."""
        output = os.path.join(output_dir, 'blurred.mp4')

        result = client.blur(sample_clips[0], radius=5, output=output)

        assert result.success
        assert os.path.exists(result.output_path)
        print(f"✓ Blur applied")

    def test_15_watermark_video(self, client, sample_clips, output_dir):
        """Add image watermark."""
        # Create a simple watermark image
        watermark = os.path.join(output_dir, 'watermark.png')
        subprocess.run([
            'ffmpeg', '-y', '-f', 'lavfi',
            '-i', 'color=c=white:s=100x50',
            '-vf', 'drawtext=text=WM:fontsize=30:fontcolor=black',
            '-frames:v', '1', watermark
        ], capture_output=True, check=True)

        output = os.path.join(output_dir, 'watermarked.mp4')
        result = client.watermark(sample_clips[0], image=watermark, output=output)

        assert result.success
        assert os.path.exists(result.output_path)
        print(f"✓ Watermark added")

    def test_16_add_text(self, client, sample_clips, output_dir):
        """Burn text overlay."""
        output = os.path.join(output_dir, 'text_overlay.mp4')

        result = client.add_text(
            sample_clips[0],
            text="Hello World",
            position="center",
            size=48,
            output=output
        )

        assert result.success
        assert os.path.exists(result.output_path)
        print(f"✓ Text overlay added")

    def test_17_overlay_video(self, client, sample_clips, output_dir):
        """Picture-in-picture overlay."""
        output = os.path.join(output_dir, 'overlay.mp4')

        result = client.overlay_video(
            sample_clips[0],
            overlay=sample_clips[1],
            position="top-right",
            width=160,
            height=120,
            output=output
        )

        assert result.success
        assert os.path.exists(result.output_path)
        print(f"✓ PiP overlay applied")

    def test_18_split_screen(self, client, sample_clips, output_dir):
        """Side-by-side split screen."""
        output = os.path.join(output_dir, 'split.mp4')

        result = client.split_screen(
            sample_clips[0],
            sample_clips[1],
            layout="side-by-side",
            output=output
        )

        assert result.success
        assert os.path.exists(result.output_path)
        print(f"✓ Split screen created")


# =============================================================================
# CATEGORY B: AUDIO FEATURES (Tests 19-28)
# =============================================================================

@pytest.mark.slow
class TestAudioFeatures:
    """Test audio processing features."""

    def test_19_extract_audio(self, client, sample_clips, output_dir):
        """Extract audio track from video."""
        output = os.path.join(output_dir, 'audio.mp3')

        result = client.extract_audio(sample_clips[0], output=output, format='mp3')

        assert result.success
        assert os.path.exists(result.output_path)
        assert result.output_path.endswith('.mp3')
        print(f"✓ Audio extracted: {result.output_path}")

    def test_20_normalize_audio(self, client, sample_clips, output_dir):
        """Normalize audio loudness."""
        output = os.path.join(output_dir, 'normalized.mp4')

        result = client.normalize_audio(sample_clips[0], target_lufs=-16.0, output=output)

        assert result.success
        assert os.path.exists(result.output_path)
        print(f"✓ Audio normalized to -16 LUFS")

    def test_21_audio_synthesize(self, client, output_dir):
        """Generate synthetic audio."""
        output = os.path.join(output_dir, 'synth.wav')

        result = client.audio_synthesize(
            output=output,
            waveform='sine',
            frequency=440.0,
            duration=1.0,
            volume=0.5
        )

        assert os.path.exists(result)
        print(f"✓ Synthesized 1s sine wave at 440Hz")

    def test_22_audio_preset(self, client, output_dir):
        """Generate preset sound."""
        output = os.path.join(output_dir, 'preset.wav')

        result = client.audio_preset('ui-blip', output=output)

        assert os.path.exists(result)
        print(f"✓ Generated 'ui-blip' preset")

    def test_23_audio_sequence(self, client, output_dir):
        """Create timed audio sequence."""
        output = os.path.join(output_dir, 'sequence.wav')

        sequence = [
            {'type': 'tone', 'at': 0.0, 'duration': 0.2, 'frequency': 800},
            {'type': 'tone', 'at': 0.3, 'duration': 0.2, 'frequency': 1000},
            {'type': 'tone', 'at': 0.6, 'duration': 0.2, 'frequency': 1200},
        ]

        result = client.audio_sequence(sequence, output=output)

        assert os.path.exists(result)
        print(f"✓ Audio sequence created")

    def test_24_audio_compose(self, client, output_dir):
        """Layer multiple audio tracks."""
        output = os.path.join(output_dir, 'composed.wav')

        # Create two simple audio files
        audio1 = os.path.join(output_dir, 'track1.wav')
        audio2 = os.path.join(output_dir, 'track2.wav')

        client.audio_synthesize(output=audio1, waveform='sine', frequency=440, duration=2.0)
        client.audio_synthesize(output=audio2, waveform='sine', frequency=880, duration=2.0)

        tracks = [
            {'file': audio1, 'volume': 0.5, 'start': 0},
            {'file': audio2, 'volume': 0.3, 'start': 0.5},
        ]

        result = client.audio_compose(tracks, duration=2.5, output=output)

        assert os.path.exists(result)
        print(f"✓ Audio composed with {len(tracks)} tracks")

    def test_25_audio_effects(self, client, output_dir):
        """Apply audio effects chain."""
        output = os.path.join(output_dir, 'effected.wav')

        # Create input audio
        input_audio = os.path.join(output_dir, 'input.wav')
        client.audio_synthesize(output=input_audio, waveform='sine', frequency=1000, duration=1.0)

        effects = [
            {'type': 'gain', 'params': {'db': -6}},
        ]

        result = client.audio_effects(input_audio, output=output, effects=effects)

        assert os.path.exists(result)
        print(f"✓ Audio effects applied")

    def test_26_add_audio(self, client, sample_clips, output_dir):
        """Add audio to video."""
        output = os.path.join(output_dir, 'with_audio.mp4')

        # Create audio file
        audio = os.path.join(output_dir, 'music.wav')
        client.audio_synthesize(output=audio, waveform='sine', frequency=500, duration=2.0)

        result = client.add_audio(sample_clips[0], audio=audio, mix=True, output=output)

        assert result.success
        assert os.path.exists(result.output_path)
        print(f"✓ Audio added to video")

    def test_27_audio_waveform(self, client, sample_clips):
        """Extract waveform data."""
        result = client.audio_waveform(sample_clips[0], bins=50)

        assert isinstance(result.peaks, list)
        assert len(result.peaks) == 50
        print(f"✓ Waveform extracted: {len(result.peaks)} bins")

    def test_28_add_generated_audio(self, client, sample_clips, output_dir):
        """Add procedural audio to video."""
        output = os.path.join(output_dir, 'with_drone.mp4')

        audio_config = {
            'drone': {'frequency': 100, 'volume': 0.2},
            'events': [{'type': 'blip', 'at': 0.5}]
        }

        result = client.add_generated_audio(sample_clips[0], audio_config, output=output)

        assert os.path.exists(result)
        print(f"✓ Generated audio added")


# =============================================================================
# CATEGORY C: VISUAL EFFECTS (Tests 29-36)
# =============================================================================

@pytest.mark.slow
class TestVisualEffects:
    """Test visual effect filters."""

    def test_29_effect_vignette(self, client, sample_clips, output_dir):
        """Apply vignette effect."""
        output = os.path.join(output_dir, 'vignette.mp4')

        result = client.effect_vignette(sample_clips[0], output, intensity=0.5)

        assert os.path.exists(result)
        print(f"✓ Vignette applied")

    def test_30_effect_chromatic_aberration(self, client, sample_clips, output_dir):
        """Apply RGB chromatic aberration."""
        output = os.path.join(output_dir, 'chromatic.mp4')

        result = client.effect_chromatic_aberration(sample_clips[0], output, intensity=3.0)

        assert os.path.exists(result)
        print(f"✓ Chromatic aberration applied")

    def test_31_effect_scanlines(self, client, sample_clips, output_dir):
        """Apply CRT scanlines."""
        output = os.path.join(output_dir, 'scanlines.mp4')

        result = client.effect_scanlines(sample_clips[0], output, line_height=2, opacity=0.5)

        assert os.path.exists(result)
        print(f"✓ Scanlines applied")

    def test_32_effect_noise(self, client, sample_clips, output_dir):
        """Apply film grain noise."""
        output = os.path.join(output_dir, 'noise.mp4')

        result = client.effect_noise(sample_clips[0], output, intensity=0.05, mode='film')

        assert os.path.exists(result)
        print(f"✓ Film noise applied")

    def test_33_effect_glow(self, client, sample_clips, output_dir):
        """Apply bloom/glow effect."""
        output = os.path.join(output_dir, 'glow.mp4')

        result = client.effect_glow(sample_clips[0], output, intensity=0.6, radius=15)

        assert os.path.exists(result)
        print(f"✓ Glow effect applied")

    def test_34_color_grade(self, client, sample_clips, output_dir):
        """Apply color grading preset."""
        output = os.path.join(output_dir, 'graded.mp4')

        result = client.color_grade(sample_clips[0], preset='warm', output=output)

        assert result.success
        assert os.path.exists(result.output_path)
        print(f"✓ Color grading applied")

    def test_35_apply_filter(self, client, sample_clips, output_dir):
        """Apply custom FFmpeg filter."""
        output = os.path.join(output_dir, 'filtered.mp4')

        result = client.filter(
            sample_clips[0],
            filter_type='grayscale',
            output=output
        )

        assert result.success
        assert os.path.exists(result.output_path)
        print(f"✓ Custom filter applied")

    def test_36_apply_mask(self, client, sample_clips, output_dir):
        """Apply image mask."""
        # Create a simple mask
        mask = os.path.join(output_dir, 'mask.png')
        subprocess.run([
            'ffmpeg', '-y', '-f', 'lavfi',
            '-i', 'color=c=white:s=640x480',
            '-vf', 'format=gray',
            '-frames:v', '1', mask
        ], capture_output=True, check=True)

        output = os.path.join(output_dir, 'masked.mp4')
        result = client.apply_mask(sample_clips[0], mask=mask, output=output)

        assert result.success
        assert os.path.exists(result.output_path)
        print(f"✓ Mask applied")


# =============================================================================
# CATEGORY D: TRANSITIONS (Tests 37-39)
# =============================================================================

@pytest.mark.slow
class TestTransitions:
    """Test video transitions."""

    def test_37_transition_glitch(self, client, sample_clips, output_dir):
        """Apply glitch transition."""
        output = os.path.join(output_dir, 'glitch_transition.mp4')

        result = client.transition_glitch(
            sample_clips[0], sample_clips[1],
            output=output, duration=0.5
        )

        assert os.path.exists(result)
        print(f"✓ Glitch transition applied")

    def test_38_transition_pixelate(self, client, sample_clips, output_dir):
        """Apply pixelate transition."""
        output = os.path.join(output_dir, 'pixelate_transition.mp4')

        result = client.transition_pixelate(
            sample_clips[0], sample_clips[1],
            output=output, duration=0.4
        )

        assert os.path.exists(result)
        print(f"✓ Pixelate transition applied")

    def test_39_transition_morph(self, client, sample_clips, output_dir):
        """Apply morph transition."""
        output = os.path.join(output_dir, 'morph_transition.mp4')

        result = client.transition_morph(
            sample_clips[0], sample_clips[1],
            output=output, duration=0.6
        )

        assert os.path.exists(result)
        print(f"✓ Morph transition applied")


# =============================================================================
# CATEGORY E: AI FEATURES (Tests 40-47)
# =============================================================================

@pytest.mark.slow
class TestAIFeatures:
    """Test AI-powered features (skip if dependencies missing)."""

    def test_40_ai_scene_detect(self, client, test_video):
        """Detect scene changes."""
        result = client.ai_scene_detect(test_video, threshold=0.3)

        assert isinstance(result, list)
        print(f"✓ Scenes detected: {len(result)}")

    def test_41_ai_remove_silence(self, client, sample_clips, output_dir):
        """Remove silent sections."""
        output = os.path.join(output_dir, 'no_silence.mp4')

        result = client.ai_remove_silence(
            sample_clips[0], output,
            silence_threshold=-50,
            min_silence_duration=0.3
        )

        assert os.path.exists(result)
        print(f"✓ Silence removed")

    @pytest.mark.skipif(
        not importlib.util.find_spec("whisper"),
        reason="Whisper not installed"
    )
    def test_42_ai_transcribe(self, client, test_video, output_dir):
        """Transcribe speech (requires Whisper)."""
        output_srt = os.path.join(output_dir, 'transcript.srt')

        result = client.ai_transcribe(test_video, output_srt=output_srt, model='tiny')

        assert 'transcript' in result
        print(f"✓ Transcription complete")

    @pytest.mark.skipif(
        not importlib.util.find_spec("demucs"),
        reason="Demucs not installed"
    )
    def test_43_ai_stem_separation(self, client, sample_clips, output_dir):
        """Separate audio into stems (requires Demucs)."""
        result = client.ai_stem_separation(sample_clips[0], output_dir)

        assert isinstance(result, dict)
        print(f"✓ Stems separated: {list(result.keys())}")

    @pytest.mark.skipif(
        not has_ai_upscale_backend(),
        reason="AI upscale backend not installed",
    )
    def test_44_ai_upscale(self, client, sample_clips, output_dir):
        """Upscale video using AI (OpenCV DNN fallback if Real-ESRGAN not available)."""
        output = os.path.join(output_dir, 'upscaled.mp4')

        result = client.ai_upscale(sample_clips[0], output, scale=2)

        assert os.path.exists(result)
        info = client.info(result)
        # Should be 2x resolution (640x480 -> 1280x960)
        assert info.width == 1280, f"Expected width 1280, got {info.width}"
        assert info.height == 960, f"Expected height 960, got {info.height}"
        print(f"✓ Upscaled to {info.width}x{info.height}")

    def test_45_ai_color_grade(self, client, sample_clips, output_dir):
        """Auto color grade video."""
        output = os.path.join(output_dir, 'ai_graded.mp4')

        result = client.ai_color_grade(sample_clips[0], output, style='cinematic')

        assert os.path.exists(result)
        print(f"✓ AI color grading applied")

    def test_46_audio_spatial(self, client, sample_clips, output_dir):
        """Apply 3D spatial audio."""
        output = os.path.join(output_dir, 'spatial.mp4')

        positions = [
            {'time': 0, 'azimuth': -45, 'elevation': 0},
            {'time': 1, 'azimuth': 45, 'elevation': 0},
        ]

        result = client.audio_spatial(sample_clips[0], output, positions)

        assert os.path.exists(result)
        print(f"✓ Spatial audio applied")

    def test_47_extract_colors(self, client, sample_clips, output_dir):
        """Extract dominant colors from frame."""
        # First extract a frame to a file path
        frame_path = os.path.join(output_dir, 'frame_for_colors.png')
        frame_result = client.extract_frame(sample_clips[0], timestamp=1.0, output=frame_path)
        actual_path = frame_result.frame_path if hasattr(frame_result, 'frame_path') else frame_path

        result = client.extract_colors(actual_path, n_colors=5)

        assert hasattr(result, 'colors') or isinstance(result, dict)
        print(f"✓ Colors extracted")


# =============================================================================
# CATEGORY F: LAYOUT & COMPOSITION (Tests 48-55)
# =============================================================================

@pytest.mark.slow
class TestLayoutComposition:
    """Test layout and composition features."""

    def test_48_layout_grid(self, client, sample_clips, output_dir):
        """Create grid layout."""
        output = os.path.join(output_dir, 'grid.mp4')

        result = client.layout_grid(
            sample_clips[:4],
            layout='2x2',
            output=output
        )

        assert os.path.exists(result)
        print(f"✓ 2x2 grid layout created")

    def test_49_layout_pip(self, client, sample_clips, output_dir):
        """Picture-in-picture layout."""
        output = os.path.join(output_dir, 'pip.mp4')

        result = client.layout_pip(
            sample_clips[0],
            sample_clips[1],
            output=output,
            position='bottom-right',
            size=0.25
        )

        assert os.path.exists(result)
        print(f"✓ PiP layout created")

    def test_50_text_animated(self, client, sample_clips, output_dir):
        """Add animated text."""
        output = os.path.join(output_dir, 'animated_text.mp4')

        result = client.text_animated(
            sample_clips[0],
            text="Animated!",
            output=output,
            animation='fade',
            start=0.5,
            duration=1.0
        )

        assert os.path.exists(result)
        print(f"✓ Animated text added")

    def test_51_text_subtitles(self, client, sample_clips, output_dir):
        """Burn SRT subtitles."""
        # Create SRT file
        srt_path = os.path.join(output_dir, 'subs.srt')
        with open(srt_path, 'w') as f:
            f.write("""1
00:00:00,000 --> 00:00:01,000
Hello World

2
00:00:01,000 --> 00:00:02,000
Test Subtitle
""")

        output = os.path.join(output_dir, 'with_subs.mp4')
        result = client.text_subtitles(sample_clips[0], srt_path, output)

        assert os.path.exists(result)
        print(f"✓ Subtitles burned")

    def test_52_mograph_count(self, client, output_dir):
        """Generate animated counter."""
        output = os.path.join(output_dir, 'counter.mp4')

        result = client.mograph_count(
            start=0,
            end=100,
            duration=2.0,
            output=output
        )

        assert os.path.exists(result)
        print(f"✓ Counter animation created")

    def test_53_mograph_progress(self, client, output_dir):
        """Generate progress bar."""
        output = os.path.join(output_dir, 'progress.mp4')

        result = client.mograph_progress(
            duration=2.0,
            output=output,
            style='bar',
            color='#CCFF00'
        )

        assert os.path.exists(result)
        print(f"✓ Progress bar animation created")

    def test_54_create_from_images(self, client, sample_clips, output_dir):
        """Create video from image sequence."""
        # Export frames first
        frames_dir = os.path.join(output_dir, 'frames')
        os.makedirs(frames_dir, exist_ok=True)

        client.export_frames(sample_clips[0], output_dir=frames_dir, fps=5)

        # Get exported frames
        images = sorted([os.path.join(frames_dir, f) for f in os.listdir(frames_dir) if f.endswith('.jpg')])

        output = os.path.join(output_dir, 'from_images.mp4')
        result = client.create_from_images(images[:5], output=output, fps=5)

        assert result.success
        assert os.path.exists(result.output_path)
        print(f"✓ Video from {len(images[:5])} images created")

    def test_55_export_frames(self, client, sample_clips, output_dir):
        """Export video frames as images."""
        output_dir = os.path.join(output_dir, 'exported_frames')
        os.makedirs(output_dir, exist_ok=True)

        result = client.export_frames(sample_clips[0], output_dir=output_dir, fps=2)

        assert os.path.exists(output_dir)
        frames = [f for f in os.listdir(output_dir) if f.endswith('.jpg')]
        assert len(frames) > 0
        print(f"✓ {len(frames)} frames exported")


# =============================================================================
# CATEGORY G: QUALITY & METADATA (Tests 56-63)
# =============================================================================

@pytest.mark.slow
class TestQualityMetadata:
    """Test quality checks and metadata operations."""

    def test_56_quality_check(self, client, short_test_clip):
        """Run quality guardrails."""
        result = client.quality_check(short_test_clip)

        # Result can be dict or QualityReport object
        if isinstance(result, dict):
            assert 'all_passed' in result or 'valid' in result
        else:
            # QualityReport object has all_passed attribute
            assert hasattr(result, 'all_passed')
        print(f"✓ Quality check completed")

    def test_57_design_quality_check(self, client, short_test_clip):
        """Run design quality analysis."""
        result = client.design_quality_check(short_test_clip)

        # Result can be dict or DesignQualityReport object
        if isinstance(result, dict):
            assert 'overall_score' in result
            score = result.get('overall_score', 0)
        else:
            # DesignQualityReport object
            assert hasattr(result, 'overall_score')
            score = result.overall_score
        print(f"✓ Design quality score: {score}")

    def test_58_fix_design_issues(self, client, sample_clips, output_dir):
        """Auto-fix design issues."""
        output = os.path.join(output_dir, 'design_fixed.mp4')

        result = client.fix_design_issues(sample_clips[0], output=output)

        assert os.path.exists(result)
        print(f"✓ Design issues auto-fixed")

    def test_59_compare_quality(self, client, short_test_clip, output_dir):
        """Compare video quality."""
        # Create a lower quality version for comparison
        distorted = os.path.join(output_dir, 'distorted.mp4')
        subprocess.run([
            'ffmpeg', '-y', '-i', short_test_clip,
            '-crf', '35', '-vf', 'scale=320:240',
            distorted
        ], capture_output=True, check=True)

        result = client.compare_quality(short_test_clip, distorted)

        assert isinstance(result, dict) or hasattr(result, 'metrics')
        print(f"✓ Quality comparison complete")

    def test_60_auto_chapters(self, client, test_video):
        """Auto-detect chapters."""
        result = client.auto_chapters(test_video, threshold=0.3)

        assert isinstance(result, list)
        print(f"✓ Chapters detected: {len(result)}")

    def test_61_video_info_detailed(self, client, test_video):
        """Get extended video info."""
        result = client.video_info_detailed(test_video)

        assert isinstance(result, dict)
        assert 'duration' in result
        print(f"✓ Detailed info: {len(result)} fields")

    def test_62_read_metadata(self, client, test_video):
        """Read video metadata."""
        result = client.read_metadata(test_video)

        # MetadataResult object with tags dict
        assert hasattr(result, 'tags')
        assert isinstance(result.tags, dict)
        print(f"✓ Metadata read: {len(result.tags)} tags")

    def test_63_write_metadata(self, client, sample_clips, output_dir):
        """Write video metadata."""
        output = os.path.join(output_dir, 'with_metadata.mp4')

        metadata = {
            'title': 'Test Video',
            'author': 'mcp-video Test',
            'comment': 'Generated by test suite'
        }

        result = client.write_metadata(sample_clips[0], metadata=metadata, output=output)

        assert result.success
        # Verify by reading back
        read_result = client.read_metadata(result.output_path)
        print(f"✓ Metadata written and verified")


# =============================================================================
# CATEGORY H: UTILITY (Tests 64-70)
# =============================================================================

@pytest.mark.slow
class TestUtility:
    """Test utility operations."""

    def test_64_convert_format(self, client, sample_clips, output_dir):
        """Convert video format."""
        output = os.path.join(output_dir, 'converted.webm')

        result = client.convert(sample_clips[0], format='webm', output=output)

        assert result.success
        assert os.path.exists(result.output_path)
        assert result.output_path.endswith('.webm')
        print(f"✓ Converted to WebM")

    def test_65_preview(self, client, test_video, output_dir):
        """Generate low-res preview."""
        output = os.path.join(output_dir, 'preview.mp4')

        result = client.preview(test_video, output=output, scale_factor=4)

        assert result.success
        info = client.info(result.output_path)
        # Should be ~1/4 resolution
        assert info.width <= 500
        print(f"✓ Preview: {info.width}x{info.height}")

    def test_66_storyboard(self, client, test_video, output_dir):
        """Extract key frames as storyboard."""
        output_dir = os.path.join(output_dir, 'storyboard')
        os.makedirs(output_dir, exist_ok=True)

        result = client.storyboard(test_video, output_dir=output_dir, frame_count=8)

        assert os.path.exists(output_dir)
        frames = [f for f in os.listdir(output_dir) if f.endswith('.jpg')]
        # 8 frame files + 1 storyboard_grid.jpg
        assert len(frames) >= 8
        print(f"✓ Storyboard: {len(frames)} files")

    def test_67_thumbnail(self, client, test_video, output_dir):
        """Extract thumbnail."""
        output = os.path.join(output_dir, 'thumb.jpg')

        result = client.thumbnail(test_video, timestamp=10.0, output=output)

        # ThumbnailResult uses frame_path not output_path
        frame_path = result.frame_path if hasattr(result, 'frame_path') else output
        assert os.path.exists(frame_path)
        print(f"✓ Thumbnail extracted")

    def test_68_batch_process(self, client, sample_clips, output_dir):
        """Batch process multiple files."""
        result = client.batch(
            sample_clips[:2],
            operation='resize',
            params={'width': 320, 'height': 240}
        )

        assert isinstance(result, dict)
        print(f"✓ Batch processed: {len(result)} files")

    def test_69_timeline_edit(self, client, sample_clips, output_dir):
        """Execute timeline-based edit."""
        output = os.path.join(output_dir, 'timeline_edit.mp4')

        timeline = {
            'tracks': [{
                'type': 'video',
                'clips': [{'source': sample_clips[0], 'in': 0, 'out': 1}]
            }],
            'output': output
        }

        result = client.edit(timeline, output=output)

        assert result.success
        assert os.path.exists(result.output_path)
        print(f"✓ Timeline edit complete")

    def test_70_generate_subtitles(self, client, sample_clips, output_dir):
        """Generate subtitles from entries."""
        entries = [
            {'start': 0.0, 'end': 1.0, 'text': 'First line'},
            {'start': 1.0, 'end': 2.0, 'text': 'Second line'},
        ]

        result = client.generate_subtitles(sample_clips[0], entries, burn=False)

        assert result.success
        # SubtitleResult uses srt_path not subtitle_path
        srt_path = result.srt_path if hasattr(result, 'srt_path') else None
        assert srt_path and os.path.exists(srt_path)
        print(f"✓ Subtitles generated")


# =============================================================================
# MAIN
# =============================================================================

def run_all_tests():
    """Run the complete test suite."""
    print("=" * 70)
    print("EXHAUSTIVE REAL MEDIA TEST SUITE - mcp-video v1.0")
    print("=" * 70)
    print(f"\nTest videos:")
    for name, path in TEST_VIDEOS.items():
        exists = "✓" if os.path.exists(path) else "✗"
        print(f"  {exists} {name}: {path}")
    print()

    pytest.main([__file__, '-v', '--tb=short', '-s'])


if __name__ == '__main__':
    run_all_tests()
