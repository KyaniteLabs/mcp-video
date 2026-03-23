# mcp-video v0.5.0 Release Notes

## 🎉 What's New

**11 new FFmpeg features** across 5 development waves, plus comprehensive testing and bug fixes.

---

## New MCP Tools (11)

### Wave 1: Enhanced Editing
- **Ken Burns effect** - Smooth pan/zoom animation filter for dynamic video movement
- **Two-pass encoding** - Higher quality at lower bitrates for efficient compression

### Wave 2: Audio Effects
- **Audio reverb** - Add echo/reverb effect to audio tracks
- **Audio compressor** - Dynamic range compression for balanced audio
- **Pitch shift** - Change audio pitch while maintaining duration
- **Noise reduction** - Remove background noise from audio tracks

### Wave 3: Analysis & Export
- **Scene detection** - Automatically identify scene changes in videos
- **Image sequences** - Create videos from image sequences, export frames
- **Quality metrics** - PSNR/SSIM comparison between original and processed videos
- **Metadata editing** - Read and write video metadata tags

### Wave 4: Advanced Processing
- **Video stabilization** - Stabilize shaky footage using motion vectors (requires vidstab)
- **Apply mask** - Image masking with edge feathering for compositing

### Wave 5: Content Generation
- **Generate subtitles** - Create SRT subtitles from text entries, optionally burn into video
- **Audio waveform** - Extract audio waveform data (peaks and silence regions)

---

## API Improvements

### Client Class
- New methods: `detect_scenes()`, `create_from_images()`, `export_frames()`, `generate_subtitles()`, `audio_waveform()`, `compare_quality()`, `read_metadata()`, `write_metadata()`, `stabilize()`, `apply_mask()`, `batch()`
- `convert()` now supports `two_pass` and `target_bitrate` parameters

### CLI Enhancements
- Rich terminal output with tables, spinners, and styled error panels
- `--format json` mode for scripted/pipe-friendly JSON output
- Video templates: TikTok, YouTube Shorts, Instagram Reel, YouTube, Instagram Post
- New commands: `detect-scenes`, `create-from-images`, `export-frames`, `generate-subtitles`, `audio-waveform`, `compare-quality`, `read-metadata`, `write-metadata`, `stabilize`, `apply-mask`, `batch`, `templates`

---

## Bug Fixes

- Fixed FFmpeg return code checking in `detect_scenes()` and `compare_quality()`
- Fixed metadata validation to check both keys and values
- Fixed `audio_waveform()` to check FFmpeg return code before parsing
- Fixed vidstabtransform parameter: `zooming` → `zoom`
- Fixed `create_from_images()` to normalize images before concatenation

---

## Testing

**545 tests passing**, including:
- 38 engine tests
- 119 server tests
- 413 adversarial/red-team tests
- 331 CLI tests
- 18 comprehensive real-video integration tests

---

## Installation

```bash
pip install --upgrade mcp-video
```

Or with UVX:
```bash
uvx mcp_video
```

---

## Documentation

- Updated README with all 29 tools
- Added CLI reference
- Added template documentation
- Roadmap updated with completed features

---

## Breaking Changes

None. Fully backward compatible with v0.4.x.

---

## Requirements

- Python 3.11+
- FFmpeg (for video processing)
- Optional: FFmpeg with vidstab (for stabilization feature)

---

## Full Changelog

### Added
- 11 new MCP tools for advanced video processing
- 5 result types: `SceneDetectionResult`, `ImageSequenceResult`, `SubtitleResult`, `WaveformResult`, `QualityMetricsResult`, `MetadataResult`
- Rich CLI output with formatting options
- Video templates for social media platforms
- Comprehensive real-video testing suite

### Changed
- Client.convert() now supports two_pass and target_bitrate
- Improved error messages with auto-fix suggestions
- Better validation for metadata operations

### Fixed
- FFmpeg return code checking in detect_scenes and compare_quality
- Metadata value validation for special characters
- audio_waveform return code checking
- vidstabtransform parameter name (zooming → zoom)
- create_from_images image normalization

---

## Contributors

- @pastorsimon1798

## Links

- [GitHub](https://github.com/Pastorsimon1798/mcp-video)
- [PyPI](https://pypi.org/project/mcp-video/)
- [Documentation](https://github.com/Pastorsimon1798/mcp-video)
