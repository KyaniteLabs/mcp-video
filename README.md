<p align="center">
  <img src="https://img.shields.io/badge/version-1.2.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/tests-extensive-brightgreen.svg" alt="Tests">
  <a href="https://github.com/pastorsimon1798/mcp-video/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/pastorsimon1798/mcp-video/.github/workflows/ci.yml?branch=master&label=CI" alt="CI"></a>
  <img src="https://img.shields.io/badge/tools-82%20MCP%20tools-orange.svg" alt="Tools">
  <img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="License">
  <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python">
</p>

<h1 align="center">mcp-video</h1>

<p align="center">
  <strong>Video editing and creation for AI agents.</strong><br>
  Edit existing video with FFmpeg. Create new video from code with Remotion.<br>
  82 tools. 3 interfaces. Extensive automated and real-media test coverage.
</p>

<p align="center">
  <a href="#installation">Install</a> &bull;
  <a href="#quick-start">Quick Start</a> &bull;
  <a href="#mcp-tools">Tools</a> &bull;
  <a href="#remotion-integration">Remotion</a> &bull;
  <a href="#python-client">Python</a> &bull;
  <a href="#cli-reference">CLI</a> &bull;
  <a href="#templates">Templates</a> &bull;
  <a href="CONTRIBUTING.md">Contributing</a> &bull;
  <a href="ROADMAP.md">Roadmap</a>
</p>

---

## What is mcp-video?

mcp-video is an open-source video editing server built on the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/). It gives AI agents, developers, and video creators the ability to programmatically edit and create video files.

**Two modes of operation:**

1. **Edit existing video** with FFmpeg — trim, merge, overlay text, add audio, apply filters, stabilize, detect scenes, transcribe, and more. 82 tools covering the full editing pipeline.

2. **Create new video from code** with [Remotion](https://www.remotion.dev/) — scaffold React-based video compositions, preview them live, render to MP4, then post-process with mcp-video. 8 dedicated tools for programmatic video generation.

Think of it as **FFmpeg + Remotion with an API that AI agents can actually use**. Instead of memorizing cryptic flags, an agent calls structured tools with clear parameters and gets structured results back.

### Three Ways to Use It

| Interface | Best For | Example |
|-----------|----------|---------|
| **MCP Server** | AI agents (Claude Code, Cursor) | *"Trim this video and add a title"* |
| **Python Client** | Scripts, automation, pipelines | `editor.trim("v.mp4", start="0:30", duration="15")` |
| **CLI** | Shell scripts, quick ops, humans | `mcp-video trim video.mp4 -s 0:30 -d 15` |

---

## Table of Contents

- [What is mcp-video?](#what-is-mcp-video)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [MCP Tools](#mcp-tools)
  - [Core Video](#core-video-40-tools)
  - [AI-Powered](#ai-powered-7-tools)
  - [Remotion & Motion Graphics](#remotion--motion-graphics-8-tools)
  - [Audio Synthesis](#audio-synthesis-6-tools)
  - [Visual Effects](#visual-effects-5-tools)
  - [Transitions](#transitions-3-tools)
  - [Layout & Motion Graphics](#layout--motion-graphics-7-tools)
  - [Quality & Guardrails](#quality--guardrails-3-tools)
  - [Image Analysis](#image-analysis-3-tools)
- [Remotion Integration](#remotion-integration)
- [Python Client](#python-client)
- [CLI Reference](#cli-reference)
- [Timeline DSL](#timeline-dsl)
- [Templates](#templates)
- [Error Handling](#error-handling)
- [Architecture](#architecture)
- [Testing](#testing)
- [License](#license)

---

## Installation

### Prerequisites

[FFmpeg](https://ffmpeg.org) must be installed:

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

For Remotion features, you also need [Node.js](https://nodejs.org/) (18+) and [npm](https://www.npmjs.com/).

### Install

```bash
pip install mcp-video
```

Or run without installing:

```bash
uvx mcp-video
```

---

## Quick Start

### 1. As an MCP Server (for AI agents)

**Claude Code:**
```bash
claude mcp add mcp-video -- uvx mcp-video
```

**Claude Desktop** — add to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "mcp-video": {
      "command": "uvx",
      "args": ["mcp-video"]
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
      "args": ["mcp-video"]
    }
  }
}
```

Then just ask your agent: *"Trim this video from 0:30 to 1:00, add a title card, and resize for TikTok."*

### 2. As a Python Library

```python
from mcp_video import Client

editor = Client()

# Get video info
info = editor.info("interview.mp4")
print(f"Duration: {info.duration}s, Resolution: {info.resolution}")

# Trim, merge, add text, resize for TikTok
clip = editor.trim("interview.mp4", start="00:02:15", duration="00:00:30")
video = editor.merge(clips=["intro.mp4", clip.output_path, "outro.mp4"])
video = editor.add_text(video.output_path, text="EPISODE 42", position="top-center", size=48)
video = editor.add_audio(video.output_path, audio="music.mp3", volume=0.7, fade_in=2.0, fade_out=3.0)
result = editor.resize(video.output_path, aspect_ratio="9:16")
```

### 3. As a CLI Tool

```bash
mcp-video info video.mp4
mcp-video trim video.mp4 -s 00:02:15 -d 30
mcp-video convert video.mp4 -f webm -q high
mcp-video template tiktok video.mp4 --caption "Check this out!"
```

---

## MCP Tools

82 tools across 9 categories. All return structured JSON with `success`, `output_path`, and operation metadata. On failure, they return `{"success": false, "error": {...}}` with auto-fix suggestions.

### Core Video (40 tools)

| Tool | Description |
|------|-------------|
| `video_info` | Get metadata: duration, resolution, codec, fps, file size |
| `video_info_detailed` | Extended metadata with scene detection and dominant colors |
| `video_trim` | Trim by start time + duration or end time |
| `video_merge` | Concatenate clips with optional per-pair transitions |
| `video_add_text` | Overlay text with positioning, font, color, shadow |
| `video_add_audio` | Add, replace, or mix audio tracks with fade effects |
| `video_resize` | Change resolution or apply preset aspect ratios (16:9, 9:16, 1:1, etc.) |
| `video_convert` | Convert between mp4, webm, gif, mov (two-pass encoding) |
| `video_speed` | Speed up or slow down (0.5x = slow-mo, 2x = time-lapse) |
| `video_reverse` | Reverse video and audio playback |
| `video_fade` | Fade in/out effects |
| `video_crop` | Crop to rectangular region with offset |
| `video_rotate` | Rotate 90/180/270 and flip horizontal/vertical |
| `video_filter` | Apply filters: blur, sharpen, grayscale, sepia, invert, brightness, contrast, saturation, denoise, deinterlace, ken_burns |
| `video_blur` | Blur with custom radius and strength |
| `video_color_grade` | Color presets: warm, cool, vintage, cinematic, noir |
| `video_chroma_key` | Remove solid color background (green screen) |
| `video_stabilize` | Stabilize shaky footage (requires FFmpeg with vidstab) |
| `video_subtitles` | Burn SRT/VTT subtitles into video |
| `video_generate_subtitles` | Create SRT from text entries, optionally burn in |
| `video_watermark` | Add image watermark with opacity and positioning |
| `video_overlay` | Picture-in-picture overlay |
| `video_split_screen` | Side-by-side or top/bottom layout |
| `video_edit` | Full timeline-based edit from JSON DSL |
| `video_detect_scenes` | Auto-detect scene changes with threshold control |
| `video_create_from_images` | Create video from image sequence |
| `video_export_frames` | Export video as individual image frames |
| `video_extract_audio` | Extract audio as mp3, wav, aac, ogg, or flac |
| `video_extract_frame` | Extract a single frame at any timestamp |
| `video_thumbnail` | Extract a frame (auto-selects 10% into video) |
| `video_preview` | Generate fast low-res preview |
| `video_storyboard` | Extract key frames as a grid for review |
| `video_compare_quality` | Compare PSNR/SSIM quality metrics between videos |
| `video_read_metadata` | Read video metadata tags |
| `video_write_metadata` | Write video metadata tags |
| `video_apply_mask` | Apply image mask with edge feathering |
| `video_normalize_audio` | Normalize loudness to LUFS target (-16 YouTube, -23 broadcast, -14 Spotify) |
| `video_audio_waveform` | Extract audio waveform peaks and silence regions |
| `video_batch` | Apply same operation to multiple files |
| `video_export` | Render final video with quality presets |

### AI-Powered (7 tools)

| Tool | Description | Dependencies |
|------|-------------|--------------|
| `video_ai_remove_silence` | Auto-remove silent sections with configurable threshold | FFmpeg |
| `video_ai_transcribe` | Speech-to-text with timestamp alignment | [openai-whisper](https://pypi.org/project/openai-whisper/) |
| `video_ai_scene_detect` | ML-enhanced scene change detection (perceptual hashing) | [imagehash](https://pypi.org/project/imagehash/), Pillow |
| `video_ai_stem_separation` | Isolate vocals, drums, bass, other instruments | [demucs](https://pypi.org/project/demucs/) |
| `video_ai_upscale` | AI super-resolution upscaling (2x or 4x) | [realesrgan](https://pypi.org/project/realesrgan/) or [opencv-contrib-python](https://pypi.org/project/opencv-contrib-python/) |
| `video_ai_color_grade` | Auto color grading with style presets or reference matching | FFmpeg |
| `video_audio_spatial` | 3D spatial audio positioning (azimuth + elevation) | FFmpeg |

### Remotion & Motion Graphics (8 tools)

Create videos programmatically using [Remotion](https://www.remotion.dev/) — a React framework for video. Scaffold projects, render compositions, then post-process with mcp-video.

| Tool | Description |
|------|-------------|
| `remotion_create_project` | Scaffold a new Remotion project (blank or hello-world template) |
| `remotion_scaffold_template` | Generate a composition from a design spec (colors, fonts, FPS, duration) |
| `remotion_render` | Render a Remotion composition to video (MP4) |
| `remotion_still` | Render a single frame as an image (PNG/JPEG/WebP) |
| `remotion_compositions` | List all compositions in a project |
| `remotion_studio` | Launch Remotion Studio for live preview |
| `remotion_validate` | Check project structure and dependencies |
| `remotion_to_mcpvideo` | Pipeline: render with Remotion, then post-process with mcp-video (resize, convert, add audio, normalize, add text, fade, watermark) |

### Audio Synthesis (6 tools)

Generate audio from code — no external audio files needed. Pure NumPy, no extra dependencies.

| Tool | Description |
|------|-------------|
| `audio_synthesize` | Generate waveforms: sine, square, sawtooth, triangle, noise. With envelopes, reverb, filtering. |
| `audio_preset` | 15 pre-configured sounds: UI blips, ambient drones, notification chimes, data sounds |
| `audio_sequence` | Compose timed audio events into a layered track |
| `audio_compose` | Mix multiple WAV tracks with individual volume control |
| `audio_effects` | Apply effects chain: lowpass, reverb, normalize, fade |
| `video_add_generated_audio` | Generate audio and add it to a video in one call |

### Visual Effects (5 tools)

| Tool | Description |
|------|-------------|
| `effect_vignette` | Darken edges for cinematic focus |
| `effect_chromatic_aberration` | RGB color separation (glitch aesthetic) |
| `effect_scanlines` | Retro CRT scanline effect with flicker |
| `effect_noise` | Film grain and digital noise |
| `effect_glow` | Bloom/glow for highlights |

### Transitions (3 tools)

| Tool | Description |
|------|-------------|
| `transition_glitch` | RGB shift + noise for digital distortion |
| `transition_pixelate` | Block dissolve with configurable pixel size |
| `transition_morph` | Mesh warp transition |

### Layout & Motion Graphics (7 tools)

| Tool | Description |
|------|-------------|
| `video_layout_grid` | Grid layout for multiple videos (2x2, 3x1, etc.) |
| `video_layout_pip` | Picture-in-picture with border and positioning |
| `video_text_animated` | Animated text overlays (fade, slide, typewriter) |
| `video_text_subtitles` | Burn subtitles with custom styling |
| `video_mograph_count` | Animated number counter video |
| `video_mograph_progress` | Progress bar/circle/dots animation |
| `video_auto_chapters` | Auto-detect scenes and create chapter timestamps |

### Quality & Guardrails (3 tools)

| Tool | Description |
|------|-------------|
| `video_quality_check` | Check brightness, contrast, saturation, audio levels, color balance. Returns scores. |
| `video_design_quality_check` | Full design quality analysis: layout, typography, color, motion, composition |
| `video_fix_design_issues` | Auto-fix brightness, contrast, saturation, and audio level issues |

### Image Analysis (3 tools)

| Tool | Description |
|------|-------------|
| `image_extract_colors` | Extract dominant colors via K-means clustering (1-20 colors) |
| `image_generate_palette` | Generate color harmony palette (complementary, analogous, triadic, split-complementary) |
| `image_analyze_product` | Extract colors + optional AI product description (Claude Vision) |

---

## Remotion Integration

mcp-video includes 8 dedicated tools for [Remotion](https://www.remotion.dev/) — a React framework for creating videos programmatically. This lets AI agents create videos from scratch using React components, not just edit existing ones.

### Typical Workflow

```
1. Create project    -> remotion_create_project
2. Scaffold composition -> remotion_scaffold_template (from a design spec)
3. Preview live       -> remotion_studio
4. Render             -> remotion_render
5. Post-process       -> remotion_to_mcpvideo (resize, add audio, normalize, etc.)
```

### Example: Create a promotional video from code

```python
from mcp_video import Client

editor = Client()

# 1. Scaffold a new Remotion project
project = editor.remotion_create_project("promo-video", template="hello-world")

# 2. Generate a composition from a design spec
spec = editor.remotion_scaffold_template(
    project_path=project.project_path,
    spec={
        "primary_color": "#CCFF00",
        "heading_font": "Inter",
        "target_fps": 30,
        "target_duration": 15,
    },
    slug="promo",
)

# 3. Render to video
render = editor.remotion_render(
    project_path=project.project_path,
    composition_id="promoComposition",
    codec="h264",
)

# 4. Or use the pipeline: render + post-process in one call
result = editor.remotion_to_mcpvideo(
    project_path=project.project_path,
    composition_id="promoComposition",
    post_process=[
        {"op": "resize", "params": {"aspect_ratio": "9:16"}},
        {"op": "normalize_audio", "params": {"target_lufs": -14}},
    ],
)
```

### Requirements

- [Node.js](https://nodejs.org/) 18+ and npm
- No Python dependencies — Remotion runs via `npx remotion` as a subprocess
- Optional: install Remotion globally with `npm i -g remotion` for faster startup

---

## Python Client

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
| `filter(video, filter_type, params?, output?)` | `EditResult` | Apply visual filter |
| `blur(video, radius?, strength?, output?)` | `EditResult` | Blur video |
| `color_grade(video, preset?, output?)` | `EditResult` | Apply color preset |
| `normalize_audio(video, target_lufs?, output?)` | `EditResult` | Normalize audio to LUFS target |
| `overlay_video(background, overlay, position?, width?, opacity?, start_time?, duration?, output?)` | `EditResult` | Picture-in-picture overlay |
| `split_screen(left, right, layout?, output?)` | `EditResult` | Side-by-side or top/bottom layout |
| `reverse(video, output?)` | `EditResult` | Reverse video and audio playback |
| `chroma_key(video, color?, similarity?, blend?, output?)` | `EditResult` | Remove solid color background |
| `stabilize(video, smoothing?, zoom?, output?)` | `EditResult` | Stabilize shaky footage |
| `apply_mask(video, mask, feather?, output?)` | `EditResult` | Apply image mask with feathering |
| `detect_scenes(video, threshold?, output?)` | `SceneDetectionResult` | Auto-detect scene changes |
| `create_from_images(images, fps?, output?)` | `ImageSequenceResult` | Create video from images |
| `export_frames(video, fps?, output_dir?)` | `ImageSequenceResult` | Export video as frames |
| `compare_quality(video, reference, output?)` | `QualityMetricsResult` | Compare PSNR/SSIM metrics |
| `read_metadata(video)` | `MetadataResult` | Read video metadata tags |
| `write_metadata(video, metadata, output?)` | `EditResult` | Write video metadata tags |
| `generate_subtitles(entries, output?, burn?)` | `SubtitleResult` | Create SRT subtitles |
| `audio_waveform(video, bins?)` | `WaveformResult` | Extract audio waveform |
| `batch(inputs, operation, params?)` | `dict` | Apply operation to multiple files |
| `extract_colors(image_path, n_colors?)` | `ColorExtractionResult` | Extract dominant colors |
| `generate_palette(image_path, harmony?, n_colors?)` | `PaletteResult` | Generate color harmony palette |
| `analyze_product(image_path, use_ai?, n_colors?)` | `ProductAnalysisResult` | Extract colors + optional AI description |

### Return Models

```python
VideoInfo(path, duration, width, height, fps, codec, audio_codec, ...)
# .resolution  -> "1920x1080"
# .aspect_ratio -> "16:9"
# .size_mb -> 5.42

EditResult(success=True, output_path, duration, resolution, size_mb, format, operation)

ThumbnailResult(success=True, frame_path, timestamp)

StoryboardResult(success=True, frames=["f1.jpg", ...], grid="grid.jpg", count=8)

SceneDetectionResult(success=True, scenes=[(start, end), ...], scene_count=5)

ImageSequenceResult(success=True, frame_count=120, fps=30, duration=4.0, output_path)

SubtitleResult(success=True, subtitle_path, entries_count=15)

WaveformResult(success=True, peaks=[...], silence_regions=[...], bin_count=50)

QualityMetricsResult(success=True, psnr=45.2, ssim=0.98)

MetadataResult(success=True, metadata={...})

ColorExtractionResult(success=True, colors=[...], n_colors=5)

PaletteResult(success=True, harmony="complementary", colors=[...])

ProductAnalysisResult(success=True, colors=[...], description="...")
```

---

## CLI Reference

```
mcp-video [command] [options]

Core Editing:
  info                 Get video metadata
  trim                 Trim a video
  merge                Merge multiple clips
  add-text             Overlay text on a video
  add-audio            Add or replace audio track
  resize               Resize or change aspect ratio
  convert              Convert video format (with two-pass encoding)
  speed                Change playback speed
  thumbnail            Extract a single frame
  extract-frame        Extract a single frame (with --time flag)
  preview              Generate fast low-res preview
  storyboard           Extract key frames as storyboard
  subtitles            Burn subtitles into video
  generate-subtitles   Create SRT subtitles from text
  watermark            Add image watermark
  crop                 Crop to rectangular region
  rotate               Rotate and/or flip video
  fade                 Add video fade in/out
  export               Export with quality settings
  extract-audio        Extract audio track
  edit                 Execute timeline-based edit from JSON (file path or inline)
  filter               Apply visual filter (blur, sharpen, grayscale, ken_burns, etc.)
  blur                 Blur video
  color-grade          Apply color preset (warm, cool, vintage, etc.)
  normalize-audio      Normalize audio to LUFS target
  audio-waveform       Extract audio waveform data
  reverse              Reverse video playback
  chroma-key           Remove solid color background (green screen)
  stabilize            Stabilize shaky footage
  apply-mask           Apply image mask with feathering
  detect-scenes        Detect scene changes
  create-from-images   Create video from image sequence
  export-frames        Export video as image frames (--image-format for format)
  compare-quality      Compare PSNR/SSIM quality metrics
  read-metadata        Read video metadata tags
  write-metadata       Write video metadata tags
  batch                Apply operation to multiple files
  overlay-video        Picture-in-picture overlay
  split-screen         Place two videos side by side or top/bottom
  templates            List available video templates
  template             Apply a video template (tiktok, youtube-shorts, etc.)

Visual Effects:
  effect-vignette             Apply vignette (darkened edges)
  effect-glow                 Apply bloom/glow to highlights
  effect-noise                Apply film grain or digital noise
  effect-scanlines            Apply CRT-style scanlines overlay
  effect-chromatic-aberration Apply RGB channel separation

Transitions:
  transition-glitch     Glitch transition between two clips
  transition-morph      Mesh warp morph transition
  transition-pixelate   Pixel dissolve transition

AI Tools:
  video-ai-transcribe    Speech-to-text with Whisper
  video-ai-upscale      AI super-resolution upscaling
  video-ai-stem-separation  Separate audio stems with Demucs
  video-ai-scene-detect  Scene detection with perceptual hashing
  video-ai-color-grade   Auto color grading
  video-ai-remove-silence  Remove silent sections

Audio Synthesis:
  audio-synthesize      Generate audio from waveform synthesis
  audio-compose         Layer multiple audio tracks with mixing
  audio-preset          Generate preset sound effects
  audio-sequence        Compose timed audio event sequence
  audio-effects         Apply audio effects chain (reverb, lowpass, etc.)

Motion Graphics:
  video-text-animated   Add animated text (fade, slide-up, typewriter)
  video-mograph-count   Generate animated number counter
  video-mograph-progress  Generate progress bar / loading animation

Layout:
  video-layout-grid     Arrange multiple videos in a grid
  video-layout-pip      Picture-in-picture with border

Audio-Video:
  video-add-generated-audio  Add procedurally generated audio
  video-audio-spatial   3D spatial audio positioning

Quality & Analysis:
  video-auto-chapters    Auto-detect scene changes as chapters
  video-info-detailed    Extended metadata with scene detection
  video-quality-check    Visual quality checks (brightness, contrast, audio)
  video-design-quality-check  Design quality analysis
  video-fix-design-issues  Auto-fix design issues

Image Analysis:
  image-extract-colors  Extract dominant colors from an image
  image-generate-palette  Generate color harmony palette
  image-analyze-product  Analyze product image (colors + AI description)

Remotion Commands:
  remotion-render       Render a Remotion composition to video
  remotion-compositions List compositions in a Remotion project
  remotion-studio       Launch Remotion Studio for live preview
  remotion-still        Render a single frame as an image
  remotion-create       Scaffold a new Remotion project
  remotion-scaffold     Generate a composition from a design spec
  remotion-validate     Validate a Remotion project structure
  remotion-pipeline     Render + post-process in one step

Global Options:
  --format text|json   Output format (default: text — rich tables & spinners)
  --version            Show version and exit
  --mcp                Run as MCP server (default when no command given)
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
        {
            "type": "image",
            "images": [
                {"source": "logo.png", "position": "top-right", "width": 200, "opacity": 0.8},
            ],
        },
    ],
    "export": {"format": "mp4", "quality": "high"},
})
```

---

## Templates

Pre-built templates for common social media formats:

```python
from mcp_video.templates import tiktok_template, youtube_video_template

# TikTok (9:16, 1080x1920)
timeline = tiktok_template(video_path="clip.mp4", caption="Check this out!", music_path="bgm.mp3")

# YouTube Shorts (9:16, title at top)
timeline = youtube_shorts_template("clip.mp4", title="My Short")

# Instagram Reel (9:16)
timeline = instagram_reel_template("clip.mp4", caption="Reel caption")

# YouTube Video (16:9, 1920x1080)
timeline = youtube_video_template(video_path="video.mp4", title="My Amazing Video",
                                   outro_path="subscribe.mp4", music_path="bgm.mp3")

# Instagram Post (1:1, 1080x1080)
timeline = instagram_post_template("clip.mp4", caption="Post caption")

# Execute any template
result = editor.edit(timeline)
```

---

## Error Handling

mcp-video parses FFmpeg errors and returns structured, actionable responses:

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
    }
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
| `MCPVideoError` | validation_error | No | Invalid parameter (v1.2.0+) |

---

## Architecture

```
mcp_video/
  __init__.py            # Exports Client
  __main__.py            # CLI entry point (argparse + Rich)
  client.py              # Python Client API (wraps all engines)
  server.py              # MCP server (82 tools + 4 resources)
  engine.py              # Core FFmpeg engine (40 video operations)
  models.py              # Pydantic models (VideoInfo, EditResult, Timeline DSL)
  errors.py              # Error hierarchy + FFmpeg stderr parser
  validation.py          # Centralized validation constants & helpers (v1.2.0)
  templates.py           # Social media templates (TikTok, YouTube, Instagram)
  audio_engine.py        # Procedural audio synthesis (pure NumPy)
  effects_engine.py      # Visual effects + motion graphics (FFmpeg filters)
  ffmpeg_helpers.py      # Shared FFmpeg utilities (v1.2.0)
  transitions_engine.py  # Clip transitions (glitch, pixelate, morph)
  ai_engine.py           # AI features (Whisper, Demucs, Real-ESRGAN, spatial audio)
  remotion_engine.py     # Remotion CLI wrapper (render, studio, scaffold, validate)
  remotion_models.py     # Remotion data models
  image_engine.py        # Image color analysis (K-means, palette generation)
  image_models.py        # Image data models
  quality_guardrails.py  # Automated quality checks (brightness, contrast, audio)
  design_quality.py      # Design quality + auto-fix (layout, typography, motion)
  limits.py              # Resource validation constants (max 4h, 8K, 4GB)
```

**Dependencies:**
- `mcp>=1.0.0` — Model Context Protocol SDK
- `pydantic>=2.0` — Data validation
- `rich>=13.0` — Rich CLI output (tables, spinners, panels)
- `ffmpeg` — Video processing (external, required)
- `node`/`npx` — Remotion (external, optional)

---

## Testing

mcp-video includes a broad automated test suite covering unit, integration, CLI, MCP server, security, and real-media workflows. The default CI path focuses on the non-slow Python test surface, while additional real-media and environment-sensitive tests can be run locally when the required tooling is available.

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests (excluding slow/remotion)
pytest tests/ -v -m "not slow and not remotion"

# Run everything
pytest tests/ -v

# Run only unit tests (no FFmpeg needed)
pytest tests/test_models.py tests/test_errors.py tests/test_templates.py -v
```

### Test Categories

| Category | Files | What It Tests |
|----------|-------|---------------|
| **Unit** | test_models, test_errors, test_templates | Pure Python, no FFmpeg |
| **Core Engine** | test_engine, test_engine_advanced, test_client, test_server | FFmpeg operations, API wrapper |
| **CLI** | test_cli | All CLI commands via subprocess |
| **Remotion** | test_remotion_engine | Remotion CLI wrapper (mocked) |
| **AI Features** | test_ai_features | AI tools (mocked where needed) |
| **Effects** | test_transitions, test_audio_presets | Transitions and audio presets |
| **Quality** | test_quality_guardrails | Quality scoring |
| **Image** | test_image_engine | Color extraction, palettes |
| **Security** | test_adversarial_audit, test_red_team | FFmpeg injection, path validation, parameter bounds |
| **Real Media** | test_real_media, test_real_all_features, test_real_exhaustive | Real FFmpeg operations (marked @slow) |
| **E2E** | test_e2e | Multi-step workflows |

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
git clone https://github.com/pastorsimon1798/mcp-video.git
cd mcp-video

python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

pytest tests/ -v -m "not slow and not remotion"
```

---

## License

Apache 2.0 — see [LICENSE](LICENSE).

Built on [FFmpeg](https://ffmpeg.org/), [Remotion](https://www.remotion.dev/), and the [Model Context Protocol](https://modelcontextprotocol.io/).

### Important dependency licensing note

The Python package itself is released under Apache 2.0, but some optional tooling has its own terms:

- **FFmpeg** licensing depends on how FFmpeg is built and distributed.
- **Remotion** uses its own commercial/free license model and may require a paid company license depending on your organization and usage.

See [LEGAL_REVIEW.md](LEGAL_REVIEW.md) for a practical project-specific licensing and commercial-use summary.
