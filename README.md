<p align="center">
  <img src="https://img.shields.io/badge/version-0.1.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/tests-262%20passed-green.svg" alt="Tests">
  <img src="https://img.shields.io/badge/tools-19%20MCP%20tools-orange.svg" alt="Tools">
  <img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="License">
  <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python">
</p>

<h1 align="center">AgentCut</h1>

<p align="center">
  <strong>The video editing MCP server for AI agents.</strong><br>
  19 tools. 3 interfaces. Purpose-built for AI agents.
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> &bull;
  <a href="#mcp-tools">Tools</a> &bull;
  <a href="#python-client">Python API</a> &bull;
  <a href="#cli">CLI</a> &bull;
  <a href="#timeline-dsl">Timeline DSL</a> &bull;
  <a href="#templates">Templates</a>
</p>

---

## What is AgentCut?

AgentCut is an open-source video editing server built on the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/). It gives AI agents and any MCP-compatible client the ability to programmatically edit video files.

Think of it as **ffmpeg with an API that AI agents can actually use**. Instead of memorizing cryptic command-line flags, an agent calls structured tools with clear parameters and gets structured results back.

### The Problem It Solves

AI agents can write code, analyze documents, and browse the web — but they can't edit video. Existing video editing tools are either:
- **GUI-only** (Premiere, DaVinci, CapCut) — agents can't use them
- **Raw FFmpeg wrappers** — require memorizing hundreds of flags
- **Cloud APIs** (Render, Bannerbear) — expensive, slow, vendor lock-in

AgentCut bridges this gap. It's a local, fast, free video editing layer that any AI agent can use through a standard protocol.

### Three Ways to Use It

| Interface | Best For | Example |
|-----------|----------|---------|
| **MCP Server** | AI agents (Claude Code, Cursor) | *"Trim this video and add a title"* |
| **Python Client** | Scripts, automation, pipelines | `editor.trim("v.mp4", start="0:30", duration="15")` |
| **CLI** | Shell scripts, quick ops | `agentcut trim video.mp4 -s 0:30 -d 15` |

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
pip install agentcut
```

Or with UVX (no install needed):
```bash
uvx agentcut
```

---

## Quick Start

### 1. As an MCP Server (for AI agents)

Add to your Claude Code or Claude Desktop MCP settings:

```json
{
  "mcpServers": {
    "agentcut": {
      "command": "uvx",
      "args": ["agentcut"]
    }
  }
}
```

Or if installed via pip:
```json
{
  "mcpServers": {
    "agentcut": {
      "command": "agentcut"
    }
  }
}
```

Then just ask your agent: *"Trim this video from 0:30 to 1:00, add a title card, and resize for TikTok."*

### 2. As a Python Library

```python
from agentcut import Client

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

```bash
# Get video metadata
agentcut info video.mp4

# Generate a fast low-res preview
agentcut preview video.mp4

# Extract storyboard frames for review
agentcut storyboard video.mp4 -n 12

# Trim a clip
agentcut trim video.mp4 -s 00:02:15 -d 30 -o trimmed.mp4

# Convert to a different format
agentcut convert video.mp4 -f webm -q high
```

---

## MCP Tools

AgentCut exposes 19 tools for AI agents. All tools return structured JSON with `success`, `output_path`, and operation metadata. On failure, they return `{"success": false, "error": {...}}` with auto-fix suggestions.

### Video Operations

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `video_info` | Get video metadata | `input_path` |
| `video_trim` | Trim clip by timestamp | `input_path`, `start`, `duration`/`end` |
| `video_merge` | Concatenate multiple clips | `clips[]`, `transitions[]`, `transition_duration` |
| `video_speed` | Change playback speed | `input_path`, `factor` (0.5=slow, 2.0=fast) |

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

### Format & Quality

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `video_resize` | Change resolution/aspect ratio | `input_path`, `width`/`height` or `aspect_ratio` |
| `video_convert` | Convert format | `input_path`, `format` (mp4/webm/gif/mov) |
| `video_export` | Render with quality settings | `input_path`, `quality`, `format` |

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
| `agentcut://video/{path}/info` | Video metadata as JSON |
| `agentcut://video/{path}/preview` | Key frame timestamps |
| `agentcut://video/{path}/audio` | Audio track info |
| `agentcut://templates` | Available templates, presets, and formats |

---

## Python Client API

Full reference for the `Client` class:

```python
from agentcut import Client
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
agentcut [command] [options]

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

Options:
  --mcp      Run as MCP server (default when no command given)
  -h, --help Show help
```

### Examples

```bash
# Get metadata as JSON
agentcut info video.mp4

# Preview with custom downscale
agentcut preview video.mp4 -s 2

# Storyboard with 12 frames
agentcut storyboard video.mp4 -n 12 -o ./frames

# Trim from 2:15 for 30 seconds
agentcut trim video.mp4 -s 00:02:15 -d 30 -o clip.mp4

# Convert to GIF at medium quality
agentcut convert video.mp4 -f gif -q medium

# Default: run MCP server
agentcut --mcp
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
from agentcut.templates import tiktok_template, youtube_video_template

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
from agentcut.templates import TEMPLATES

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

AgentCut parses FFmpeg errors and returns structured, actionable error responses:

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
    "documentation_url": "https://github.com/pastorsimon1798/agentcut#codec-compatibility"
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

AgentCut has **262 tests** across the full testing pyramid:

```
tests/
├── conftest.py              # Shared fixtures (sample video, audio, SRT, VTT, watermark PNG, WebM)
├── test_models.py           # 48 tests — Pydantic model validation (no FFmpeg needed)
├── test_errors.py           # 35 tests — Error classes and FFmpeg error parsing (no FFmpeg)
├── test_templates.py        # 21 tests — Template functions and registry (no FFmpeg)
├── test_client.py           # 35 tests — Python Client API wrapper
├── test_server.py           # 33 tests — MCP tool layer
├── test_engine.py           # 27 tests — Core FFmpeg engine operations
├── test_engine_advanced.py  # 37 tests — Edge cases, new operations, per-transition merge
├── test_cli.py              # 6 tests  — CLI commands via subprocess
└── test_e2e.py              # 8 tests  — Full end-to-end workflows
```

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest tests/ -v

# Run only unit tests (no FFmpeg needed)
pytest tests/test_models.py tests/test_errors.py tests/test_templates.py -v

# Run with coverage
pytest tests/ --cov=agentcut --cov-report=term-missing
```

### Test Pyramid

| Layer | Tests | What It Tests |
|-------|-------|---------------|
| **Unit** | 104 | Models, errors, templates — pure Python, no FFmpeg |
| **Integration** | 150 | Client, server, engine, CLI — real FFmpeg operations |
| **E2E** | 8 | Multi-step workflows (TikTok, YouTube, GIF, speed) |

---

## Architecture

```
agentcut/
├── __init__.py       # Exports Client
├── __main__.py       # CLI entry point (argparse)
├── client.py         # Python Client class (wraps engine)
├── engine.py         # FFmpeg engine (all video operations)
├── errors.py         # Error types + FFmpeg stderr parser
├── models.py         # Pydantic models (VideoInfo, EditResult, Timeline DSL)
├── templates.py      # Platform templates (TikTok, YouTube, Instagram)
└── server.py         # MCP server (19 tools + 4 resources)
```

**Dependencies:**
- `mcp>=1.0.0` — Model Context Protocol SDK
- `pydantic>=2.0` — Data validation
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
git clone https://github.com/pastorsimon1798/agentcut.git
cd agentcut

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

- [ ] Batch processing mode (edit 100 videos at once)
- [ ] Streaming upload/download (S3, GCS integration)
- [ ] Web UI for non-agent users
- [ ] FFmpeg filter auto-detection and graceful fallback
- [ ] Video effects (blur, color grading)
- [ ] Audio normalization and noise reduction
- [ ] Thumbnail selection via AI scene detection
- [ ] Plugin system for custom filters

---

## License

Apache 2.0 — see [LICENSE](LICENSE). Use it however you want.

---

## Acknowledgments

Built on [FFmpeg](https://ffmpeg.org/) and the [Model Context Protocol](https://modelcontextprotocol.io/).
