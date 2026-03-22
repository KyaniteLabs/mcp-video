<p align="center">
  <img src="https://img.shields.io/badge/version-0.4.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/tests-388%20passed-brightgreen.svg" alt="Tests">
  <a href="https://github.com/pastorsimon1798/mcp-video/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/pastorsimon1798/mcp-video/.github/workflows/ci.yml?branch=master&label=CI" alt="CI"></a>
  <a href="https://glama.ai/mcp/servers/pastorsimon1798/mcp-video"><img src="https://glama.ai/mcp/servers/pastorsimon1798/mcp-video/badges/score.svg" alt="Glama Score"></a>
  <img src="https://img.shields.io/badge/pypi-mcp--video-blue.svg" alt="PyPI">
  <img src="https://img.shields.io/badge/tools-29%20MCP%20tools-orange.svg" alt="Tools">
  <img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="License">
  <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python">
</p>

<h1 align="center">mcp-video</h1>

<p align="center">
  <strong>The video editing MCP server for AI agents and humans.</strong><br>
  26 tools. 3 interfaces. Rich CLI. Purpose-built for AI agents.
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> &bull;
  <a href="#mcp-tools">Tools</a> &bull;
  <a href="#python-client">Python API</a> &bull;
  <a href="#cli">CLI</a> &bull;
  <a href="#timeline-dsl">Timeline DSL</a> &bull;
  <a href="#templates">Templates</a> &bull;
  <a href="ROADMAP.md">Roadmap</a> &bull;
  <a href="CONTRIBUTING.md">Contributing</a>
</p>

---

## What is mcp-video?

mcp-video is an open-source video editing server built on the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/). It gives AI agents, developers, and video creators the ability to programmatically edit video files.

Think of it as **ffmpeg with an API that AI agents can actually use**. Instead of memorizing cryptic command-line flags, an agent calls structured tools with clear parameters and gets structured results back — or a human uses the rich CLI with spinners, tables, and error panels.

### The Problem It Solves

AI agents can write code, analyze documents, and browse the web — but they can't edit video. Existing video editing tools are either:
- **GUI-only** (Premiere, DaVinci, CapCut) — agents can't use them
- **Raw FFmpeg wrappers** — require memorizing hundreds of flags
- **Cloud APIs** (Render, Bannerbear) — expensive, slow, vendor lock-in

mcp-video bridges this gap. It's a local, fast, free video editing layer that any AI agent can use through a standard protocol.

### Three Ways to Use It

| Interface | Best For | Example |
|-----------|----------|---------|
| **MCP Server** | AI agents (Claude Code, Cursor) | *"Trim this video and add a title"* |
| **Python Client** | Scripts, automation, pipelines | `editor.trim("v.mp4", start="0:30", duration="15")` |
| **CLI** | Shell scripts, quick ops, humans | `mcp_video trim video.mp4 -s 0:30 -d 15` |

---

## Install

### Prerequisites

[FFmpeg](https://ffmpeg.org) must be installed on your system:
```bash
# macOS
brew install ffmpeg

# For full text overlay support (drawtext filter):
# brew install freetype harfbuzz
# brew reinstall --build-from-source ffmpeg
# Verify: ffmpeg -filters | grep drawtext

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

### Installation

```bash
pip install mcp-video
```

Or with UVX (no install needed):
```bash
uvx mcp_video
```

---

## Quick Start

### 1. As an MCP Server (for AI agents)

Install [FFmpeg](https://ffmpeg.org) first, then pick your client:

**Claude Code:**
```bash
claude mcp add mcp-video -- pip install mcp-video && mcp-video --mcp
```

**Claude Desktop** — add to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "mcp-video": {
      "command": "uvx",
      "args": ["mcp_video"]
    }
  }
}
```

**Cursor** — add to your `.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "mcp-video": {
      "command": "uvx",
      "args": ["mcp_video"]
    }
  }
}
```

**Any MCP client** — if installed via pip, the command is just `mcp-video`.

Then just ask your agent: *"Trim this video from 0:30 to 1:00, add a title card, and resize for TikTok."*

### 2. As a Python Library

```python
from mcp_video import Client

editor = Client()

# Get video info
info = editor.info("interview.mp4")
print(f"Duration: {info.duration}s, Resolution: {info.resolution}")

# Trim a clip
clip = editor.trim("interview.mp4", start="00:02:15", duration="00:00:30")

# Merge clips with transitions
video = editor.merge(
    clips=["intro.mp4", clip.output_path, "outro.mp4"],
    transitions=["fade", "dissolve", "fade"],
)

# Add text overlay
video = editor.add_text(
    video=video.output_path,
    text="EPISODE 42: The Future of AI",
    position="top-center",
    size=48,
)

# Add background music
video = editor.add_audio(
    video=video.output_path,
    audio="music.mp3",
    volume=0.7,
    fade_in=2.0,
    fade_out=3.0,
)

# Resize for TikTok (9:16)
video = editor.resize(video=video.output_path, aspect_ratio="9:16")

# Export final video
result = editor.export(video.output_path, quality="high")
print(result)
# EditResult(output_path='interview_9:16.mp4', duration=45.0, resolution='1080x1920', ...)
```

### 3. As a CLI Tool

The CLI outputs rich formatted tables, spinners, and styled error panels by default. Add `--format json` for scripted/pipe-friendly JSON output.

```bash
# Show version
mcp_video --version

# Get video metadata (rich table output)
mcp_video info video.mp4

# Same, but as JSON for scripts
mcp_video --format json info video.mp4

# Generate a fast low-res preview
mcp_video preview video.mp4

# Extract storyboard frames for review
mcp_video storyboard video.mp4 -n 12

# Trim a clip
mcp_video trim video.mp4 -s 00:02:15 -d 30 -o trimmed.mp4

# Convert to a different format
mcp_video convert video.mp4 -f webm -q high

# List available templates
mcp_video templates

# Apply a TikTok template with caption
mcp_video template tiktok video.mp4 --caption "Check this out!"
```

---

## MCP Tools

mcp-video exposes 29 tools for AI agents. All tools return structured JSON with `success`, `output_path`, and operation metadata. On failure, they return `{"success": false, "error": {...}}` with auto-fix suggestions.

**New in v0.4.0:** Video reverse playback, green screen / chroma key removal, denoise and deinterlace filters, and smarter GIF output with quality-based scaling.

**New in v0.3.0:** Video filters & effects (blur, sharpen, color grading with presets), audio normalization to LUFS targets, picture-in-picture and split-screen compositing, and batch processing for multi-file workflows.

### Video Operations

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `video_info` | Get video metadata | `input_path` |
| `video_trim` | Trim clip by timestamp | `input_path`, `start`, `duration`/`end` |
| `video_merge` | Concatenate multiple clips | `clips[]`, `transitions[]`, `transition_duration` |
| `video_speed` | Change playback speed | `input_path`, `factor` (0.5=slow, 2.0=fast) |
| `video_reverse` | Reverse video and audio playback | `input_path` |

### Effects & Overlays

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `video_add_text` | Overlay text/title | `input_path`, `text`, `position`, `size`, `color` |
| `video_add_audio` | Add or replace audio | `video_path`, `audio_path`, `volume`, `mix` |
| `video_subtitles` | Burn SRT/VTT subtitles | `input_path`, `subtitle_path` |
| `video_watermark` | Add image watermark | `input_path`, `image_path`, `position`, `opacity` |
| `video_crop` | Crop to rectangular region | `input_path`, `width`, `height`, `x?`, `y?` |
| `video_rotate` | Rotate and/or flip video | `input_path`, `angle`, `flip_horizontal`, `flip_vertical` |
| `video_fade` | Video fade in/out | `input_path`, `fade_in`, `fade_out` |
| `video_chroma_key` | Remove solid color background (green screen) | `input_path`, `color`, `similarity`, `blend` |

### Format & Quality

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `video_resize` | Change resolution/aspect ratio | `input_path`, `width`/`height` or `aspect_ratio` |
| `video_convert` | Convert format | `input_path`, `format` (mp4/webm/gif/mov) |
| `video_export` | Render with quality settings | `input_path`, `quality`, `format` |

### Filters & Effects

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `video_filter` | Apply visual filter (blur, sharpen, grayscale, sepia, invert, vignette, brightness, contrast, saturation, denoise, deinterlace) | `input_path`, `filter_type`, `params` |
| `video_blur` | Blur video | `input_path`, `radius`, `strength` |
| `video_color_grade` | Apply color preset (warm, cool, vintage, cinematic, noir) | `input_path`, `preset` |

### Audio

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `video_normalize_audio` | Normalize loudness to LUFS target | `input_path`, `target_lufs` (-16 YouTube, -23 broadcast, -14 Spotify) |

### Composition

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `video_overlay` | Picture-in-picture overlay | `background_path`, `overlay_path`, `position`, `width`, `opacity` |
| `video_split_screen` | Side-by-side or top/bottom layout | `left_path`, `right_path`, `layout` |

### Batch Processing

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `video_batch` | Apply operation to multiple files | `inputs[]`, `operation`, `params`, `output_dir` |

### Analysis & Extraction

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `video_thumbnail` | Extract a single frame | `input_path`, `timestamp` |
| `video_preview` | Generate fast low-res preview | `input_path`, `scale_factor` |
| `video_storyboard` | Extract key frames as grid | `input_path`, `frame_count` |
| `video_extract_audio` | Extract audio track | `input_path`, `format` (mp3/wav/aac/ogg/flac) |

### Advanced

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `video_edit` | Full timeline-based edit | `timeline` (JSON DSL — see below) |

### MCP Resources

| Resource URI | Description |
|-------------|-------------|
| `mcp-video://video/{path}/info` | Video metadata as JSON |
| `mcp-video://video/{path}/preview` | Key frame timestamps |
| `mcp-video://video/{path}/audio` | Audio track info |
| `mcp-video://templates` | Available templates, presets, and formats |

---

## Python Client API

Full reference for the `Client` class:

```python
from mcp_video import Client
editor = Client()
```

### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `info(path)` | `VideoInfo` | Video metadata (duration, resolution, codec, fps, size) |
| `trim(input, start, duration?, end?, output?)` | `EditResult` | Trim by start time + duration or end time |
| `merge(clips, output?, transitions?, transition_duration?)` | `EditResult` | Concatenate clips with per-pair transitions |
| `add_text(video, text, position?, font?, size?, color?, shadow?, start_time?, duration?, output?)` | `EditResult` | Overlay text on video |
| `add_audio(video, audio, volume?, fade_in?, fade_out?, mix?, start_time?, output?)` | `EditResult` | Add or replace audio track |
| `resize(video, width?, height?, aspect_ratio?, quality?, output?)` | `EditResult` | Resize or change aspect ratio |
| `convert(video, format?, quality?, output?)` | `EditResult` | Convert format (mp4/webm/gif/mov) |
| `speed(video, factor?, output?)` | `EditResult` | Change playback speed |
| `thumbnail(video, timestamp?, output?)` | `ThumbnailResult` | Extract single frame |
| `preview(video, output?, scale_factor?)` | `EditResult` | Fast low-res preview |
| `storyboard(video, output_dir?, frame_count?)` | `StoryboardResult` | Key frames + grid |
| `subtitles(video, subtitle_file, output?)` | `EditResult` | Burn subtitles into video |
| `watermark(video, image, position?, opacity?, margin?, output?)` | `EditResult` | Add image watermark |
| `crop(video, width, height, x?, y?, output?)` | `EditResult` | Crop to rectangular region |
| `rotate(video, angle?, flip_horizontal?, flip_vertical?, output?)` | `EditResult` | Rotate and/or flip video |
| `fade(video, fade_in?, fade_out?, output?)` | `EditResult` | Video fade in/out effect |
| `export(video, output?, quality?, format?)` | `EditResult` | Render with quality settings |
| `edit(timeline, output?)` | `EditResult` | Execute full timeline edit from JSON |
| `extract_audio(video, output?, format?)` | `EditResult` | Extract audio as file path |
| `filter(video, filter_type, params?, output?)` | `EditResult` | Apply visual filter (blur, sharpen, grayscale, etc.) |
| `blur(video, radius?, strength?, output?)` | `EditResult` | Blur video |
| `color_grade(video, preset?, output?)` | `EditResult` | Apply color preset (warm, cool, vintage, etc.) |
| `normalize_audio(video, target_lufs?, output?)` | `EditResult` | Normalize audio to LUFS target |
| `overlay(background, overlay, position?, width?, opacity?, start_time?, duration?, output?)` | `EditResult` | Picture-in-picture overlay |
| `split_screen(left, right, layout?, output?)` | `EditResult` | Side-by-side or top/bottom layout |
| `reverse(video, output?)` | `EditResult` | Reverse video and audio playback |
| `chroma_key(video, color?, similarity?, blend?, output?)` | `EditResult` | Remove solid color background (green screen) |
| `batch(inputs, operation, params?)` | `dict` | Apply operation to multiple files |

### Return Models

```python
VideoInfo(path, duration, width, height, fps, codec, audio_codec, ...)
# .resolution  -> "1920x1080"
# .aspect_ratio -> "16:9"
# .size_mb -> 5.42

EditResult(success=True, output_path, duration, resolution, size_mb, format, operation)

ThumbnailResult(success=True, frame_path, timestamp)

StoryboardResult(success=True, frames=["f1.jpg", ...], grid="grid.jpg", count=8)
```

---

## CLI Reference

```
mcp_video [command] [options]

Commands:
  info           Get video metadata
  trim           Trim a video
  merge          Merge multiple clips
  add-text       Overlay text on a video
  add-audio      Add or replace audio track
  resize         Resize or change aspect ratio
  convert        Convert video format
  speed          Change playback speed
  thumbnail      Extract a single frame
  preview        Generate fast low-res preview
  storyboard     Extract key frames as storyboard
  subtitles      Burn subtitles into video
  watermark      Add image watermark
  crop           Crop to rectangular region
  rotate         Rotate and/or flip video
  fade           Add video fade in/out
  export         Export with quality settings
  extract-audio  Extract audio track
  edit           Execute timeline-based edit from JSON
  filter         Apply visual filter (blur, sharpen, grayscale, etc.)
  blur           Blur video
  color-grade    Apply color preset (warm, cool, vintage, etc.)
  normalize-audio Normalize audio to LUFS target
  overlay-video  Picture-in-picture overlay
  split-screen   Side-by-side or top/bottom layout
  reverse        Reverse video playback
  chroma-key     Remove solid color background (green screen)
  batch          Apply operation to multiple files
  templates      List available video templates
  template       Apply a video template (tiktok, youtube-shorts, etc.)

Global Options:
  --format text|json  Output format (default: text — rich tables & spinners)
  --version           Show version and exit
  --mcp               Run as MCP server (default when no command given)
  -h, --help          Show help
```

### Examples

```bash
# Get metadata (rich table by default)
mcp_video info video.mp4

# Get metadata as JSON (for scripts and piping)
mcp_video --format json info video.mp4

# Preview with custom downscale
mcp_video preview video.mp4 -s 2

# Storyboard with 12 frames
mcp_video storyboard video.mp4 -n 12 -o ./frames

# Trim from 2:15 for 30 seconds
mcp_video trim video.mp4 -s 00:02:15 -d 30 -o clip.mp4

# Convert to GIF at medium quality
mcp_video convert video.mp4 -f gif -q medium

# Apply cinematic color grade
mcp_video color-grade video.mp4 --preset cinematic

# Normalize audio for YouTube (-16 LUFS)
mcp_video normalize-audio video.mp4 --lufs -16

# Picture-in-picture overlay
mcp_video overlay-video background.mp4 overlay.mp4 --position bottom-right --width 360

# Side-by-side split screen
mcp_video split-screen left.mp4 right.mp4 --layout side-by-side

# Batch blur 3 videos at once
mcp_video batch video1.mp4 video2.mp4 video3.mp4 --operation blur

# List available templates
mcp_video templates

# Apply a TikTok template with caption and music
mcp_video template tiktok video.mp4 --caption "Check this out!" --music bgm.mp3

# Apply a YouTube template with title card and outro
mcp_video template youtube video.mp4 --title "My Video" --outro subscribe.mp4

# Default: run MCP server
mcp_video --mcp
```

---

## Timeline DSL

For complex multi-track edits, describe everything in a single JSON object:

```python
editor.edit({
    "width": 1080,
    "height": 1920,
    "tracks": [
        {
            "type": "video",
            "clips": [
                {"source": "intro.mp4", "start": 0, "duration": 5},
                {"source": "main.mp4", "start": 5, "trim_start": 10, "duration": 30},
                {"source": "outro.mp4", "start": 35, "duration": 10},
            ],
            "transitions": [
                {"after_clip": 0, "type": "fade", "duration": 1.0},
                {"after_clip": 1, "type": "dissolve", "duration": 1.0},
            ],
        },
        {
            "type": "audio",
            "clips": [
                {"source": "music.mp3", "start": 0, "volume": 0.7, "fade_in": 2},
            ],
        },
        {
            "type": "text",
            "elements": [
                {"text": "EPISODE 42", "start": 0, "duration": 3, "position": "top-center",
                 "style": {"size": 48, "color": "white", "shadow": True}},
            ],
        },
    ],
    "export": {"format": "mp4", "quality": "high"},
})
```

### Timeline Schema

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `width` | int | 1920 | Output width |
| `height` | int | 1080 | Output height |
| `tracks` | Track[] | [] | Video, audio, and text tracks |
| `export.format` | str | "mp4" | mp4, webm, gif, mov |
| `export.quality` | str | "high" | low, medium, high, ultra |

**Track types:** `video`, `audio`, `text`

**Video clip fields:** `source`, `start`, `duration`, `trim_start`, `trim_end`, `volume`, `fade_in`, `fade_out`

**Transition fields:** `after_clip` (index), `type` (fade/dissolve/wipe-*), `duration`

**Text element fields:** `text`, `start`, `duration`, `position`, `style` (font/size/color/shadow)

**Positions:** top-left, top-center, top-right, center-left, center, center-right, bottom-left, bottom-center, bottom-right

---

## Templates

Pre-built templates for common social media formats:

```python
from mcp_video.templates import tiktok_template, youtube_video_template

# TikTok (9:16, 1080x1920)
timeline = tiktok_template(
    video_path="clip.mp4",
    caption="Check this out!",
    music_path="bgm.mp3",
)

# YouTube Shorts (9:16, title at top)
timeline = youtube_shorts_template("clip.mp4", title="My Short")

# Instagram Reel (9:16)
timeline = instagram_reel_template("clip.mp4", caption="Reel caption")

# YouTube Video (16:9, 1920x1080)
timeline = youtube_video_template(
    video_path="video.mp4",
    title="My Amazing Video",
    outro_path="subscribe.mp4",
    music_path="bgm.mp3",
)

# Instagram Post (1:1, 1080x1080)
timeline = instagram_post_template("clip.mp4", caption="Post caption")

# Execute any template
result = editor.edit(timeline)
```

### Template Registry

```python
from mcp_video.templates import TEMPLATES

print(list(TEMPLATES.keys()))
# ['tiktok', 'youtube-shorts', 'instagram-reel', 'youtube', 'instagram-post']

# Call any template by name
timeline = TEMPLATES["tiktok"](video_path="clip.mp4", caption="Hello!")
```

---

## Quality Presets

| Quality | CRF | Encoder Preset | Max Height | Use Case |
|---------|-----|---------------|------------|----------|
| `low` | 35 | fast | 480p | Drafts, previews |
| `medium` | 28 | medium | 720p | Social media |
| `high` | 23 | slow | 1080p | Production |
| `ultra` | 18 | veryslow | 1080p | Final output |

Lower CRF = better quality, larger file. The `preset` controls encoding speed (slower = better compression).

---

## Aspect Ratios

| Ratio | Resolution | Platforms |
|-------|-----------|-----------|
| `16:9` | 1920x1080 | YouTube |
| `9:16` | 1080x1920 | TikTok, Reels, Shorts |
| `1:1` | 1080x1080 | Instagram Post |
| `4:5` | 1080x1350 | Instagram Feed |
| `4:3` | 1440x1080 | Classic video |
| `21:9` | 2560x1080 | Ultrawide |

```python
editor.resize("video.mp4", aspect_ratio="9:16")  # TikTok
editor.resize("video.mp4", aspect_ratio="16:9")  # YouTube
editor.resize("video.mp4", aspect_ratio="1:1")   # Instagram
```

---

## Error Handling

mcp-video parses FFmpeg errors and returns structured, actionable error responses:

```json
{
  "success": false,
  "error": {
    "type": "encoding_error",
    "code": "unsupported_codec",
    "message": "Codec error: vp9 — Auto-convert input from vp9 to H.264/AAC before editing",
    "suggested_action": {
      "auto_fix": true,
      "description": "Auto-convert input from vp9 to H.264/AAC before editing"
    },
    "documentation_url": "https://github.com/pastorsimon1798/mcp-video#codec-compatibility"
  }
}
```

### Error Types

| Error | Type | Auto-Fix | Description |
|-------|------|----------|-------------|
| `FFmpegNotFoundError` | dependency_error | No | FFmpeg not installed |
| `FFprobeNotFoundError` | dependency_error | No | FFprobe not installed |
| `InputFileError` | input_error | No | File doesn't exist or invalid |
| `CodecError` | encoding_error | Yes | Unsupported codec |
| `ResolutionMismatchError` | encoding_error | Yes | Clips have different resolutions |
| `ProcessingError` | processing_error | No | FFmpeg processing failed |
| `ExportError` | export_error | No | Export/rendering failed |
| `ResourceError` | resource_error | No | Insufficient disk space or memory |

---

## Testing

mcp-video has **388 tests** across the full testing pyramid:

```
tests/
├── conftest.py              # Shared fixtures (sample video, audio, SRT, VTT, watermark PNG, WebM)
├── test_models.py           # 55 tests — Pydantic model validation (no FFmpeg needed)
├── test_errors.py           # 42 tests — Error classes and FFmpeg error parsing (no FFmpeg)
├── test_templates.py        # 21 tests — Template functions and registry (no FFmpeg)
├── test_client.py           # 42 tests — Python Client API wrapper
├── test_server.py           # 55 tests — MCP tool layer
├── test_engine.py           # 33 tests — Core FFmpeg engine operations
├── test_engine_advanced.py  # 78 tests — Edge cases, new operations, filter validation, per-transition merge
├── test_cli.py              # 22 tests — CLI commands via subprocess (text + JSON output)
├── test_e2e.py              # 8 tests  — Full end-to-end workflows
└── test_real_media.py       # 33 tests — Real-media integration tests (marked @slow)
```

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests (excluding slow/real-media tests)
pytest tests/ -v -m "not slow"

# Run all tests including real-media integration tests
pytest tests/ -v

# Run only unit tests (no FFmpeg needed)
pytest tests/test_models.py tests/test_errors.py tests/test_templates.py -v

# Run real-media tests only (requires iPhone footage in ~/Downloads/)
pytest tests/test_real_media.py -v -m slow

# Run with coverage
pytest tests/ -m "not slow" --cov=mcp_video --cov-report=term-missing
```

### Test Pyramid

| Layer | Tests | What It Tests |
|-------|-------|---------------|
| **Unit** | 118 | Models, errors, templates — pure Python, no FFmpeg |
| **Integration** | 229 | Client, server, engine, CLI — real FFmpeg operations |
| **E2E** | 8 | Multi-step workflows (TikTok, YouTube, GIF, speed) |
| **Real Media** | 33 | iPhone footage integration tests (marked @slow) |

---

## Architecture

```
mcp_video/
├── __init__.py       # Exports Client
├── __main__.py       # CLI entry point (argparse)
├── client.py         # Python Client class (wraps engine)
├── engine.py         # FFmpeg engine (all video operations)
├── errors.py         # Error types + FFmpeg stderr parser
├── models.py         # Pydantic models (VideoInfo, EditResult, Timeline DSL)
├── templates.py      # Platform templates (TikTok, YouTube, Instagram)
└── server.py         # MCP server (26 tools + 4 resources)
```

**Dependencies:**
- `mcp>=1.0.0` — Model Context Protocol SDK
- `pydantic>=2.0` — Data validation
- `rich>=13.0` — Rich CLI output (tables, spinners, panels)
- `ffmpeg` — Video processing (external, required)

---

## Supported Formats

### Video
| Format | Container | Video Codec | Audio Codec |
|--------|-----------|-------------|-------------|
| MP4 | mp4 | H.264 (libx264) | AAC |
| WebM | webm | VP9 (libvpx-vp9) | Opus |
| MOV | mov | H.264 (libx264) | PCM |
| GIF | gif | Palette-based | None |

### Audio (extraction)
MP3, AAC, WAV, OGG, FLAC

### Subtitles
SRT, WebVTT (burned into video)

---

## Development

```bash
# Clone
git clone https://github.com/pastorsimon1798/mcp-video.git
cd mcp-video

# Setup
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run a single test file
pytest tests/test_client.py -v

# Run with verbose output
pytest tests/ -v --tb=long
```

---

## Roadmap

- [x] Progress callbacks for long-running operations (v0.2.0)
- [x] Visual verification with thumbnail output (v0.2.0)
- [x] Video filters & effects — blur, sharpen, color grading, presets (v0.3.0)
- [x] Audio normalization to LUFS targets (v0.3.0)
- [x] Picture-in-picture and split-screen compositing (v0.3.0)
- [x] Batch processing for multi-file workflows (v0.3.0)
- [x] Video reverse, green screen/chroma key, denoise & deinterlace filters, smarter GIF output (v0.4.0)
- [x] Rich CLI with human-friendly output, templates, and `--format json` mode (v0.4.0)
- [ ] Streaming upload/download (S3, GCS integration)
- [ ] Web UI for non-agent users
- [ ] FFmpeg filter auto-detection and graceful fallback
- [ ] Thumbnail selection via AI scene detection
- [ ] Plugin system for custom filters

---

## License

Apache 2.0 — see [LICENSE](LICENSE). Use it however you want.

---

## Acknowledgments

Built on [FFmpeg](https://ffmpeg.org/) and the [Model Context Protocol](https://modelcontextprotocol.io/).
