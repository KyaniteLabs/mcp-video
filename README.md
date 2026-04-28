<p align="center">
  <img src="og-social-preview.png" alt="mcp-video" width="100%">
</p>

<!-- mcp-name: io.github.pastorsimon1798/mcp-video -->

<h1 align="center">mcp-video</h1>

<p align="center">
  <strong>Video editing and creation for AI agents.</strong><br>
  Edit existing video with FFmpeg. Create new video from code with Hyperframes.
</p>

<p align="center">
  <a href="https://pypi.org/project/mcp-video/"><img src="https://img.shields.io/pypi/v/mcp-video.svg" alt="PyPI"></a>
  <a href="https://github.com/pastorsimon1798/mcp-video/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/pastorsimon1798/mcp-video/.github/workflows/ci.yml?branch=master&label=CI" alt="CI"></a>
  <img src="https://img.shields.io/badge/tools-85%20MCP%20tools-orange.svg" alt="Tools">
  <img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="License">
  <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python">
</p>

<p align="center">
  <a href="#installation">Install</a> &bull;
  <a href="#quick-start">Quick Start</a> &bull;
  <a href="#tools-overview">Tools</a> &bull;
  <a href="docs/TOOLS.md">Full Reference</a> &bull;
  <a href="docs/AI_AGENT_DISCOVERY.md">Agent Discovery</a> &bull;
  <a href="CONTRIBUTING.md">Contributing</a> &bull;
  <a href="CHANGELOG.md">Changelog</a>
</p>

---

## What is mcp-video?

An open-source video editing server built on the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/). It gives AI agents, developers, and video creators the ability to programmatically edit and create video files.

**Two modes:**
1. **Edit existing video** with FFmpeg — trim, merge, overlay text, add audio, apply filters, stabilize, detect scenes, transcribe, and more.
2. **Create new video from code** with [Hyperframes](https://hyperframes.io/) (HTML-native, Apache 2.0) — scaffold compositions, preview live, render to MP4, then post-process.

**Three interfaces:**

| Interface | Best For | Example |
|-----------|----------|---------|
| **MCP Server** | AI agents (Claude Code, Cursor) | *"Trim this video and add a title"* |
| **Python Client** | Scripts, automation, pipelines | `editor.trim("v.mp4", start="0:30", duration="15")` |
| **CLI** | Shell scripts, quick ops, humans | `mcp-video trim video.mp4 -s 0:30 -d 15` |

---

## Installation

**Prerequisites:** [FFmpeg](https://ffmpeg.org) must be installed. For Hyperframes features, you also need [Node.js](https://nodejs.org/) 22+.

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

**Install:**

```bash
pip install mcp-video
# or run without installing:
uvx mcp-video
```

Verify your setup:

```bash
mcp-video doctor
mcp-video doctor --json
```

---

## Quick Start

### As an MCP Server (for AI agents)

**Claude Code:**
```bash
claude mcp add mcp-video -- uvx mcp-video
```

**Claude Desktop:**
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

**Cursor:**
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

### As a Python Library

```python
from mcp_video import Client

editor = Client()

info = editor.info("interview.mp4")
clip = editor.trim("interview.mp4", start="00:02:15", duration="00:00:30")
video = editor.merge(clips=["intro.mp4", clip.output_path, "outro.mp4"])
video = editor.add_text(video.output_path, text="EPISODE 42", position="top-center", size=48)
result = editor.resize(video.output_path, aspect_ratio="9:16")
```

### Agent-safe Python workflow

For autonomous agents, prefer inspection, pipeline chaining, and a release checkpoint:

```python
from mcp_video import Client

client = Client()
print(client.inspect("create_from_images"))  # Real params, aliases, return type

result = client.pipeline(
    [
        {"op": "create_from_images", "images": frames, "fps": 30},
        {"op": "effect_glow", "intensity": 0.2},  # safe capped default
        {"op": "add_audio", "audio_path": "soundtrack.wav", "mix": True},
        {"op": "export", "quality": "high"},
    ],
    output_path="final.mp4",
)

checkpoint = client.release_checkpoint(result.output_path)
print(checkpoint["thumbnail"], checkpoint["storyboard"])
```

Agent contract:

- Media-producing client calls return `EditResult` with `.output_path`.
- Analysis/discovery calls return typed reports or dictionaries.
- `Client.inspect(name)` exposes parameters, aliases, category, and return type.
- Raw unexpected-keyword errors are converted into actionable `MCPVideoError` guidance.
- Do not publish agent-generated video without `assert_quality()` or `release_checkpoint()` plus human visual/audio inspection.

### As a CLI Tool

```bash
mcp-video info video.mp4
mcp-video trim video.mp4 -s 00:02:15 -d 30
mcp-video convert video.mp4 -f webm -q high
mcp-video template tiktok video.mp4 --caption "Check this out!"
```

---

## MCP Tools

85 unique MCP tools across 10 categories, plus a `search_tools` meta-tool for fast discovery. All return structured JSON. See the [full tool reference](docs/TOOLS.md) for complete details.

| Category | Count | Highlights |
|----------|-------|------------|
| **Core Video** | 29 | trim, merge, text, audio, resize, convert, filters, stabilize, chroma key, subtitles, watermark, batch, export, normalize audio |
| **AI-Powered** | 11 | transcribe (Whisper), scene detect, stem separation (Demucs), upscale, color grade |
| **Hyperframes** | 8 | init, render, still, preview, compositions, validate, add block, pipeline |
| **Audio Synthesis** | 7 | generate waveforms, presets, sequences, effects, spatial audio — pure NumPy |
| **Visual Effects** | 6 | vignette, chromatic aberration, scanlines, noise, glow, mask |
| **Transitions** | 3 | glitch, pixelate, morph |
| **Layout & Motion** | 6 | grid, pip, animated text, counters, progress bars, auto-chapters |
| **Analysis** | 8 | scene detect, thumbnail, preview, storyboard, quality compare, metadata, waveform, release checkpoint |
| **Image Analysis** | 3 | color extraction, palette generation, product analysis |
| **Meta** | 1 | `search_tools` — keyword search across all tools |

**Tool discovery:**
```python
from mcp_video import Client
editor = Client()
results = editor.search_tools("subtitle")  # Find subtitle-related tools
```

---

## Hyperframes Integration

Create videos programmatically with [Hyperframes](https://hyperframes.io/) — an HTML-native framework for video (Apache 2.0).

```
1. Create project     -> hyperframes_init
2. Add blocks         -> hyperframes_add_block
3. Preview live       -> hyperframes_preview
4. Render             -> hyperframes_render
5. Post-process       -> hyperframes_to_mcpvideo
```

See [Hyperframes docs](docs/TOOLS.md#hyperframes--html-native-video-8-tools) and the [Python client reference](docs/PYTHON_CLIENT.md).

## Hyperframes Integration

Create videos programmatically with [Hyperframes](https://hyperframes.io/) — an HTML-native framework for video.

```
1. Init project       -> hyperframes_init
2. Add blocks         -> hyperframes_add_block
3. Preview live       -> hyperframes_preview
4. Render             -> hyperframes_render
5. Post-process       -> hyperframes_to_mcpvideo
```

See [Hyperframes docs](docs/TOOLS.md#hyperframes--html-native-video-8-tools) and the [Python client reference](docs/PYTHON_CLIENT.md).

---

## Python Client

```python
from mcp_video import Client
editor = Client()
```

See the [full Python client reference](docs/PYTHON_CLIENT.md) for all methods and return types.

---

## CLI Reference

```
mcp-video [command] [options]
```

See the [full CLI reference](docs/CLI_REFERENCE.md) for all commands and options.

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
            ],
        },
        {
            "type": "audio",
            "clips": [
                {"source": "music.mp3", "start": 0, "volume": 0.7, "fade_in": 2},
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
from mcp_video.templates import tiktok_template, youtube_shorts_template

timeline = tiktok_template(video_path="clip.mp4", caption="Check this out!", music_path="bgm.mp3")
result = editor.edit(timeline)
```

Supports: TikTok, YouTube Shorts, Instagram Reels/Posts, YouTube Videos.

---

## Error Handling

Structured, actionable errors with auto-fix suggestions:

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

---

## Workflows

ICM-style staged pipelines for common productions — with `CONTEXT.md` stage contracts, `references/` factory config, and runnable `workflow.py` scripts.

```bash
cd workflows/01-social-media-clip
python workflow.py /path/to/video.mp4
```

| Workflow | Stages | Description |
|----------|--------|-------------|
| `01-social-media-clip` | 5 | Landscape → TikTok / Short / Reel |
| `02-podcast-clip` | 6 | Highlight with chapters + burned captions |
| `03-explainer-video` | 7 | Branded explainer from scratch |

See [`workflows/CONTEXT.md`](workflows/CONTEXT.md) for the routing table.

## Architecture

```
mcp_video/
  client/                # Python Client API (mixins per domain)
  client/meta.py         # Client discovery mixin (search_tools)
  server.py              # MCP server (85 tools + 4 resources + search_tools meta-tool)
  server_tools_*.py      # Tool registration by category
  engine.py              # Core FFmpeg engine
  engine_*.py            # Specialized engines (thumbnail, edit, probe, etc.)
  models.py              # Pydantic models
  errors.py              # Error hierarchy + FFmpeg stderr parser
  ffmpeg_helpers.py      # Shared FFmpeg utilities
  audio_engine.py        # Procedural audio synthesis
  effects_engine.py      # Visual effects + motion graphics
  transitions_engine.py  # Clip transitions
  ai_engine.py           # AI features (Whisper, Demucs, Real-ESRGAN)
  hyperframes_engine.py  # Hyperframes CLI wrapper
  hyperframes_engine.py  # Hyperframes CLI wrapper
  image_engine.py        # Image color analysis
  quality_guardrails.py  # Automated quality checks
workflows/               # ICM staged pipelines
  CONTEXT.md             # Layer 1 routing table
  01-social-media-clip/  # Stage contract + runnable script
  02-podcast-clip/       # Stage contract + runnable script
  03-explainer-video/    # Stage contract + runnable script
```

---

## Supported Formats

| Video | Audio (extraction) | Subtitles |
|-------|-------------------|-----------|
| MP4, WebM, MOV, GIF | MP3, AAC, WAV, OGG, FLAC | SRT, WebVTT |

---

## Agent Discovery

- [`llms.txt`](llms.txt) — compact project map for agents
- [`docs/AI_AGENT_DISCOVERY.md`](docs/AI_AGENT_DISCOVERY.md) — richer positioning and integration snippets

---

## Development

```bash
git clone https://github.com/pastorsimon1798/mcp-video.git
cd mcp-video
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

---

## Community & Support

- **Contributing:** [CONTRIBUTING.md](CONTRIBUTING.md)
- **Security:** [SECURITY.md](SECURITY.md) (private reporting path)
- **Help:** [SUPPORT.md](SUPPORT.md) or [GitHub Discussions](https://github.com/pastorsimon1798/mcp-video/discussions)
- **Code of Conduct:** [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- **Changelog:** [CHANGELOG.md](CHANGELOG.md)
- **Roadmap:** [ROADMAP.md](ROADMAP.md)
- **Governance:** [GOVERNANCE.md](GOVERNANCE.md)
- **Maintainers:** [MAINTAINERS.md](MAINTAINERS.md)

## Testing

Tests are excluded from the PyPI package. To run locally:

```bash
pip install -e ".[dev]"
pytest tests/ -v -m "not slow and not hyperframes"
```

See [docs/TESTING.md](docs/TESTING.md) for full test categories and CI details.

## License

Apache 2.0 — see [LICENSE](LICENSE).

Built on [FFmpeg](https://ffmpeg.org/), [Hyperframes](https://hyperframes.io/), and the [Model Context Protocol](https://modelcontextprotocol.io/).

See [docs/LEGAL_REVIEW.md](docs/LEGAL_REVIEW.md) for dependency licensing notes.
