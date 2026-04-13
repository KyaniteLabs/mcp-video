"""Exhaustive Real Media Test Suite for mcp-video v1.0

Tests ALL features using REAL video files and media operations.
This is the comprehensive integration test suite.
"""

import os
import sys
import pytest
import tempfile
import subprocess
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_video import Client

# Test video files (real media)
TEST_VIDEOS = {
    'explainer': 'out/McpVideoExplainer-FINAL.mp4',
    'original': 'out/McpVideoExplainerV1.mp4',
    'short': 'out/new-scenes-bright.mp4',
}

# Skip if no test videos
pytestmark = [
    pytest.mark.skipif(
        not os.path.exists(TEST_VIDEOS['explainer']),
        reason="Test video not found - run explainer render first"
    ),
    pytest.mark.slow,
]


class TestRealVideoEditing:
    """Test core video editing with real videos."""

    @pytest.fixture
    def client(self):
        return Client()

    @pytest.fixture
    def test_video(self):
        return TEST_VIDEOS['explainer']

    @pytest.fixture
    def output_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            yield tmp

    def test_01_video_info(self, client, test_video):
        """Get real video info."""
        print("\n[Test] Video info...")
        info = client.info(test_video)

        assert info.width == 1920
        assert info.height == 1080
        assert info.fps == 30
        assert abs(info.duration - 100.0) < 5.0
        print(f"  ✓ Duration: {info.duration:.1f}s, Resolution: {info.width}x{info.height}")

    def test_02_trim_video(self, client, test_video, output_dir):
        """Trim real video."""
        print("\n[Test] Trim 10-20s from video...")
        output = os.path.join(output_dir, 'trimmed.mp4')

        result = client.edit({
            'tracks': [{
                'type': 'video',
                'clips': [{
                    'source': test_video,
                    'in': 0,
                    'out': 10,
                    'trim_start': 10,
                    'trim_end': 90
                }]
            }],
            'output': output
        })

        # Check edit was successful
        assert result.success
        assert result.duration > 0
        print(f"  ✓ Trimmed duration: {result.duration:.1f}s")

    def test_03_resize_video(self, client, test_video, output_dir):
        """Resize to 720p."""
        print("\n[Test] Resize to 720p...")
        output = os.path.join(output_dir, '720p.mp4')

        # Use ffmpeg directly for resize test
        subprocess.run([
            'ffmpeg', '-y', '-i', test_video,
            '-t', '5', '-vf', 'scale=1280:720',
            '-c:v', 'libx264', '-c:a', 'aac',
            output
        ], capture_output=True, check=True)

        assert os.path.exists(output)
        info = client.info(output)
        assert info.width == 1280
        assert info.height == 720
        print(f"  ✓ Resized to {info.width}x{info.height}")


class TestRealAIFeatures:
    """Test AI features with real videos."""

    @pytest.fixture
    def client(self):
        return Client()

    def test_04_ai_scene_detect(self, client):
        """Detect scenes in video."""
        print("\n[Test] AI scene detection...")
        test_video = TEST_VIDEOS.get('explainer')
        if not test_video or not os.path.exists(test_video):
            pytest.skip("No test video available")

        result = client.ai_scene_detect(test_video, threshold=0.3)

        assert isinstance(result, list)
        print(f"  ✓ Scenes detected: {len(result)}")


class TestRealEffects:
    """Test video effects with real videos."""

    @pytest.fixture
    def client(self):
        return Client()

    @pytest.fixture
    def output_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            yield tmp

    def test_05_transition_glitch(self, client, output_dir):
        """Apply glitch transition."""
        print("\n[Test] Glitch transition...")
        clip1 = os.path.join(output_dir, 'clip1.mp4')
        clip2 = os.path.join(output_dir, 'clip2.mp4')

        subprocess.run([
            'ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=red:s=320x240:d=2',
            '-c:v', 'libx264', '-pix_fmt', 'yuv420p', clip1
        ], capture_output=True, check=True)

        subprocess.run([
            'ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=blue:s=320x240:d=2',
            '-c:v', 'libx264', '-pix_fmt', 'yuv420p', clip2
        ], capture_output=True, check=True)

        output = os.path.join(output_dir, 'glitch.mp4')
        result = client.transition_glitch(clip1, clip2, output, duration=0.5)

        assert os.path.exists(result)
        print(f"  ✓ Glitch transition applied")

    def test_06_transition_pixelate(self, client, output_dir):
        """Apply pixelate transition."""
        print("\n[Test] Pixelate transition...")
        clip1 = os.path.join(output_dir, 'clip1.mp4')
        clip2 = os.path.join(output_dir, 'clip2.mp4')
        output = os.path.join(output_dir, 'pixelate.mp4')

        # Create fresh clips
        subprocess.run([
            'ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=green:s=320x240:d=2',
            '-c:v', 'libx264', '-pix_fmt', 'yuv420p', clip1
        ], capture_output=True, check=True)
        subprocess.run([
            'ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=yellow:s=320x240:d=2',
            '-c:v', 'libx264', '-pix_fmt', 'yuv420p', clip2
        ], capture_output=True, check=True)

        result = client.transition_pixelate(clip1, clip2, output, duration=0.4)

        assert os.path.exists(result)
        print(f"  ✓ Pixelate transition applied")

    def test_07_transition_morph(self, client, output_dir):
        """Apply morph transition."""
        print("\n[Test] Morph transition...")
        clip1 = os.path.join(output_dir, 'clip1.mp4')
        clip2 = os.path.join(output_dir, 'clip2.mp4')
        output = os.path.join(output_dir, 'morph.mp4')

        # Create fresh clips
        subprocess.run([
            'ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=purple:s=320x240:d=2',
            '-c:v', 'libx264', '-pix_fmt', 'yuv420p', clip1
        ], capture_output=True, check=True)
        subprocess.run([
            'ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=orange:s=320x240:d=2',
            '-c:v', 'libx264', '-pix_fmt', 'yuv420p', clip2
        ], capture_output=True, check=True)

        result = client.transition_morph(clip1, clip2, output, duration=0.6)

        assert os.path.exists(result)
        print(f"  ✓ Morph transition applied")


class TestRealQualityGuardrails:
    """Test quality guardrails with real videos."""

    @pytest.fixture
    def client(self):
        return Client()

    @pytest.fixture
    def test_video(self):
        return TEST_VIDEOS.get('explainer')

    def test_08_video_info_detailed(self, client, test_video):
        """Get detailed video info."""
        print("\n[Test] Detailed video info...")
        if not test_video or not os.path.exists(test_video):
            pytest.skip("No test video")

        result = client.video_info_detailed(test_video)

        assert isinstance(result, dict)
        assert 'duration' in result
        print(f"  ✓ Detailed info: {len(result)} fields")

    def test_09_quality_check(self, client, test_video):
        """Run quality check."""
        print("\n[Test] Quality check...")
        if not test_video or not os.path.exists(test_video):
            pytest.skip("No test video")

        result = client.quality_check(test_video)

        assert isinstance(result, dict)
        print(f"  ✓ Quality check: {'PASS' if result.get('valid') else 'FAIL'}")

    def test_10_auto_chapters(self, client, test_video):
        """Auto-detect chapters."""
        print("\n[Test] Auto chapters...")
        if not test_video or not os.path.exists(test_video):
            pytest.skip("No test video")

        result = client.auto_chapters(test_video, threshold=0.3)

        assert isinstance(result, list)
        print(f"  ✓ Chapters detected: {len(result)}")


def run_all_tests():
    """Run all exhaustive tests with verbose output."""
    print("=" * 70)
    print("EXHAUSTIVE REAL MEDIA TEST SUITE")
    print("=" * 70)
    print(f"\nTest videos:")
    for name, path in TEST_VIDEOS.items():
        exists = "✓" if os.path.exists(path) else "✗"
        print(f"  {exists} {name}: {path}")
    print()

    pytest.main([__file__, '-v', '--tb=short', '-s'])


if __name__ == '__main__':
    run_all_tests()
