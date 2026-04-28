"""Shared test fixtures for mcp-video tests."""

import os
import shutil
import subprocess

import pytest


def has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def has_ffprobe() -> bool:
    return shutil.which("ffprobe") is not None


def has_node() -> bool:
    """Check if Node.js is available on PATH."""
    return shutil.which("node") is not None


def has_npx() -> bool:
    """Check if npx is available on PATH."""
    return shutil.which("npx") is not None


@pytest.fixture(scope="session")
def sample_video(tmp_path_factory) -> str:
    """Create a 3-second test video with a color bar pattern."""
    if not has_ffmpeg():
        pytest.skip("FFmpeg not installed")

    video_path = str(tmp_path_factory.mktemp("videos") / "test_video.mp4")

    # Generate a test video: 3 seconds, 640x480, color bars + sine audio
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "smptehdbars=size=640x480:duration=3:rate=30",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=3",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-shortest",
            video_path,
        ],
        capture_output=True,
        timeout=30,
    )

    if not os.path.isfile(video_path):
        pytest.skip("Could not generate test video")

    return video_path


@pytest.fixture(scope="session")
def sample_audio(tmp_path_factory) -> str:
    """Create a 5-second test audio file."""
    if not has_ffmpeg():
        pytest.skip("FFmpeg not installed")

    audio_path = str(tmp_path_factory.mktemp("audio") / "test_audio.mp3")

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=880:duration=5",
            "-c:a",
            "libmp3lame",
            "-b:a",
            "192k",
            audio_path,
        ],
        capture_output=True,
        timeout=30,
    )

    if not os.path.isfile(audio_path):
        pytest.skip("Could not generate test audio")

    return audio_path


@pytest.fixture(scope="session")
def sample_srt(tmp_path_factory) -> str:
    """Create a sample SRT subtitle file."""
    srt_dir = tmp_path_factory.mktemp("subs")
    srt_path = srt_dir / "test.srt"
    srt_path.write_text(
        "1\n00:00:00,000 --> 00:00:02,000\nHello World\n\n2\n00:00:02,000 --> 00:00:04,000\nThis is a test\n"
    )
    return str(srt_path)


@pytest.fixture(scope="session")
def sample_vtt(tmp_path_factory) -> str:
    """Create a sample WebVTT subtitle file."""
    vtt_dir = tmp_path_factory.mktemp("subs")
    vtt_path = vtt_dir / "test.vtt"
    vtt_path.write_text(
        "WEBVTT\n\n00:00:00.000 --> 00:00:02.000\nHello World\n\n00:00:02.000 --> 00:00:04.000\nThis is a test\n"
    )
    return str(vtt_path)


@pytest.fixture(scope="session")
def sample_watermark_png(tmp_path_factory) -> str:
    """Create a PNG image with transparency for watermark tests."""
    if not has_ffmpeg():
        pytest.skip("FFmpeg not installed")

    img_dir = tmp_path_factory.mktemp("images")
    img_path = str(img_dir / "watermark.png")

    # Generate a 100x100 semi-transparent red square
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=red@0.5:s=100x100:d=0.1",
            "-frames:v",
            "1",
            img_path,
        ],
        capture_output=True,
        timeout=15,
    )

    if not os.path.isfile(img_path):
        pytest.skip("Could not generate watermark image")

    return img_path


@pytest.fixture(scope="session")
def sample_video_webm(tmp_path_factory) -> str:
    """Create a 2-second test video in WebM format."""
    if not has_ffmpeg():
        pytest.skip("FFmpeg not installed")

    video_path = str(tmp_path_factory.mktemp("videos") / "test_video.webm")

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "smptehdbars=size=640x480:duration=2:rate=30",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=2",
            "-c:v",
            "libvpx-vp9",
            "-crf",
            "35",
            "-c:a",
            "libopus",
            "-shortest",
            video_path,
        ],
        capture_output=True,
        timeout=30,
    )

    if not os.path.isfile(video_path):
        pytest.skip("Could not generate WebM test video")

    return video_path


@pytest.fixture(scope="session")
def sample_video_no_audio(tmp_path_factory) -> str:
    """Create a 2-second test video without audio track."""
    if not has_ffmpeg():
        pytest.skip("FFmpeg not installed")

    video_path = str(tmp_path_factory.mktemp("videos") / "test_video_no_audio.mp4")

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "smptehdbars=size=640x480:duration=2:rate=30",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-crf",
            "23",
            "-an",
            video_path,
        ],
        capture_output=True,
        timeout=30,
    )

    if not os.path.isfile(video_path):
        pytest.skip("Could not generate video without audio")

    return video_path


@pytest.fixture(scope="session")
def sample_video_2(tmp_path_factory) -> str:
    """Create a 3-second test video with different resolution for compositing tests."""
    if not has_ffmpeg():
        pytest.skip("FFmpeg not installed")

    video_path = str(tmp_path_factory.mktemp("videos") / "test_video_2.mp4")

    # Generate a test video: 3 seconds, 320x240, solid blue + sine audio
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:size=320x240:duration=3:rate=30",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=880:duration=3",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-shortest",
            video_path,
        ],
        capture_output=True,
        timeout=30,
    )

    if not os.path.isfile(video_path):
        pytest.skip("Could not generate second test video")

    return video_path


@pytest.fixture
def sample_remotion_project(tmp_path):
    """Create a minimal Remotion project directory with required files.

    This creates a temp directory containing:
      - package.json
      - src/Root.tsx
      - src/index.ts

    Returns the project directory as a string.
    """
    project_dir = tmp_path / "remotion-project"
    project_dir.mkdir()

    # package.json
    (project_dir / "package.json").write_text(
        '{"name": "test-project", "version": "1.0.0", "dependencies": {"remotion": "^4.0.0"}}'
    )

    # src/ directory
    src_dir = project_dir / "src"
    src_dir.mkdir()

    # src/Root.tsx
    (src_dir / "Root.tsx").write_text(
        'import { Composition } from "remotion";\n'
        'import React from "react";\n'
        "\n"
        "export const RemotionRoot: React.FC = () => {\n"
        "  return (\n"
        "    <>\n"
        '      <Composition id="Test" component={() => null} '
        "durationInFrames={90} fps={30} compositionWidth={1920} "
        "compositionHeight={1080} />\n"
        "    </>\n"
        "  );\n"
        "};\n"
    )

    # src/index.ts
    (src_dir / "index.ts").write_text(
        'import { registerRoot } from "remotion";\n'
        'import { RemotionRoot } from "./Root";\n'
        "registerRoot(RemotionRoot);\n"
    )

    return str(project_dir)


@pytest.fixture
def sample_hyperframes_project(tmp_path):
    """Create a minimal Hyperframes project directory with required files.

    This creates a temp directory containing:
      - index.html (entry point with data-composition-id)
      - package.json (optional, for validation)

    Returns the project directory as a string.
    """
    project_dir = tmp_path / "hyperframes-project"
    project_dir.mkdir()

    # index.html — Hyperframes entry point
    (project_dir / "index.html").write_text(
        '<!DOCTYPE html>\n'
        '<html>\n'
        '  <head><title>Test</title></head>\n'
        '  <body>\n'
        '    <div data-composition-id="test-comp"></div>\n'
        '  </body>\n'
        '</html>\n'
    )

    # package.json (optional but useful for validation)
    (project_dir / "package.json").write_text(
        '{"name": "test-hyperframes-project", "version": "1.0.0"}'
    )

    return str(project_dir)
