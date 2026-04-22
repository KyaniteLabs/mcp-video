# Python Client Reference

```python
from mcp_video import Client

editor = Client()
```

## Methods

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
| `search_tools(query)` | `dict` | Search MCP tools by keyword — returns matching names, descriptions, required params |
| `extract_colors(image_path, n_colors?)` | `ColorExtractionResult` | Extract dominant colors |
| `generate_palette(image_path, harmony?, n_colors?)` | `PaletteResult` | Generate color harmony palette |
| `analyze_product(image_path, use_ai?, n_colors?)` | `ProductAnalysisResult` | Extract colors + optional AI description |

## Return Models

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
