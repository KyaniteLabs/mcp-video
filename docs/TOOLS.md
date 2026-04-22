# MCP Tools Reference

81 unique MCP tools across 12 categories, plus a `search_tools` meta-tool. All return structured JSON with `success`, `output_path`, and operation metadata. On failure, they return `{"success": false, "error": {...}}` with auto-fix suggestions.

---

## Core Editing (27 tools)

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
| `video_chroma_key` | Remove solid color background (green screen) |
| `video_stabilize` | Stabilize shaky footage (requires FFmpeg with vidstab) |
| `video_subtitles` | Burn SRT/VTT subtitles into video |
| `video_subtitles_styled` | Burn subtitles with custom styling (font, size, color, outline) |
| `video_generate_subtitles` | Create SRT from text entries, optionally burn in |
| `video_watermark` | Add image watermark with opacity and positioning |
| `video_overlay` | Picture-in-picture overlay |
| `video_split_screen` | Side-by-side or top/bottom layout |
| `video_edit` | Full timeline-based edit from JSON DSL |
| `video_create_from_images` | Create video from image sequence |
| `video_export_frames` | Export video as individual image frames |
| `video_extract_audio` | Extract audio as mp3, wav, aac, ogg, or flac |

---

## AI-Powered (10 tools)

| Tool | Description | Dependencies |
|------|-------------|--------------|
| `video_analyze` | Comprehensive video analysis: transcript, metadata, scenes, audio, quality, chapters, and colors | FFmpeg; optional Whisper/image extras |
| `video_ai_remove_silence` | Auto-remove silent sections with configurable threshold | FFmpeg |
| `video_ai_transcribe` | Speech-to-text with timestamp alignment | [openai-whisper](https://pypi.org/project/openai-whisper/) |
| `video_ai_scene_detect` | ML-enhanced scene change detection (perceptual hashing) | [imagehash](https://pypi.org/project/imagehash/), Pillow |
| `video_ai_stem_separation` | Isolate vocals, drums, bass, other instruments | [demucs](https://pypi.org/project/demucs/) |
| `video_ai_upscale` | AI super-resolution upscaling (2x or 4x) | [realesrgan](https://pypi.org/project/realesrgan/) or [opencv-contrib-python](https://pypi.org/project/opencv-contrib-python/) |
| `video_ai_color_grade` | Auto color grading with style presets or reference matching | FFmpeg |
| `video_quality_check` | Check brightness, contrast, saturation, audio levels, color balance |
| `video_design_quality_check` | Full design quality analysis: layout, typography, color, motion, composition |
| `video_fix_design_issues` | Auto-fix brightness, contrast, saturation, and audio level issues |

Install only the AI dependencies you need:

```bash
pip install "mcp-video[transcribe]"  # Whisper transcription
pip install "mcp-video[ai-scene]"    # perceptual scene hashing
pip install "mcp-video[stems]"       # Demucs stem separation
pip install "mcp-video[upscale]"     # Real-ESRGAN/OpenCV upscaling
pip install "mcp-video[ai]"          # all AI extras, kept for compatibility
```

---

## Remotion & Motion Graphics (8 tools)

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
| `remotion_to_mcpvideo` | Pipeline: render with Remotion, then post-process with mcp-video |

---

## Audio Synthesis (6 tools)

Generate audio from code — no external audio files needed. Pure NumPy, no extra dependencies.

| Tool | Description |
|------|-------------|
| `audio_synthesize` | Generate waveforms: sine, square, sawtooth, triangle, noise. With envelopes, reverb, filtering. |
| `audio_preset` | 15 pre-configured sounds: UI blips, ambient drones, notification chimes, data sounds |
| `audio_sequence` | Compose timed audio events into a layered track |
| `audio_compose` | Mix multiple WAV tracks with individual volume control |
| `audio_effects` | Apply effects chain: lowpass, reverb, normalize, fade |
| `video_add_generated_audio` | Generate audio and add it to a video in one call |
| `video_audio_spatial` | 3D spatial audio positioning (azimuth + elevation) |

---

## Visual Effects (5 tools)

| Tool | Description |
|------|-------------|
| `effect_vignette` | Darken edges for cinematic focus |
| `effect_chromatic_aberration` | RGB color separation (glitch aesthetic) |
| `effect_scanlines` | Retro CRT scanline effect with flicker |
| `effect_noise` | Film grain and digital noise |
| `effect_glow` | Bloom/glow for highlights |

---

## Transitions (3 tools)

| Tool | Description |
|------|-------------|
| `transition_glitch` | RGB shift + noise for digital distortion |
| `transition_pixelate` | Block dissolve with configurable pixel size |
| `transition_morph` | Mesh warp transition |

---

## Layout & Motion Graphics (6 tools)

| Tool | Description |
|------|-------------|
| `video_layout_grid` | Grid layout for multiple videos (2x2, 3x1, etc.) |
| `video_layout_pip` | Picture-in-picture with border and positioning |
| `video_text_animated` | Animated text overlays (fade, slide, typewriter) |
| `video_mograph_count` | Animated number counter video |
| `video_mograph_progress` | Progress bar/circle/dots animation |
| `video_auto_chapters` | Auto-detect scenes and create chapter timestamps |

---

## Analysis (8 tools)

| Tool | Description |
|------|-------------|
| `video_detect_scenes` | Auto-detect scene changes with threshold control |
| `video_thumbnail` | Extract a single frame (thumbnail / frame grab) at any timestamp |
| `video_preview` | Generate fast low-res preview |
| `video_storyboard` | Extract key frames as a grid for review |
| `video_compare_quality` | Compare PSNR/SSIM quality metrics between videos |
| `video_read_metadata` | Read video metadata tags |
| `video_write_metadata` | Write video metadata tags |
| `video_audio_waveform` | Extract audio waveform peaks and silence regions |

---

## Image Analysis (3 tools)

| Tool | Description |
|------|-------------|
| `image_extract_colors` | Extract dominant colors from an image or video frame via K-means clustering (1-20 colors) |
| `image_generate_palette` | Generate color harmony palette from an image or video frame |
| `image_analyze_product` | Analyze a product image or video frame — extract colors + optional AI description (Claude Vision) |
