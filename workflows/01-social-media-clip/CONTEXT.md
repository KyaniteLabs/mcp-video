# 01-social-media-clip

Turn landscape video into a vertical social media clip (TikTok, YouTube Shorts, Instagram Reels).

## Inputs

| Source | File/Location | Description |
|---|---|---|
| Raw video | User provided | Landscape interview, demo, or raw footage |
| Platform specs | references/platform_specs.md | Target platform requirements (9:16, duration limits, audio specs) |
| Caption style | references/caption_styles.md | Font, color, position conventions per platform |

## Process

1. **01-trim**: Use `video_trim` to extract the viral moment (under 60s)
2. **02-resize**: Use `video_resize` with `aspect_ratio="9:16"` for vertical format
3. **03-caption**: Use `video_add_text` for hook text in the first 3 seconds
4. **04-normalize**: Use `video_normalize_audio` at -14 LUFS for social platforms
5. **05-export**: Use `video_convert` for final MP4 format

## Outputs

| Artifact | Location | Format |
|---|---|---|
| Trimmed clip | output/01_trimmed.mp4 | Source format |
| Vertical clip | output/02_vertical.mp4 | 9:16 aspect ratio |
| Captioned clip | output/03_captioned.mp4 | With hook text overlay |
| Normalized clip | output/04_normalized.mp4 | -14 LUFS audio |
| Final clip | output/final_clip.mp4 | MP4, 9:16, platform-ready |

## Quality gates

- [ ] Duration under platform limit (TikTok: 10m, Shorts: 60s, Reels: 90s)
- [ ] Aspect ratio is exactly 9:16
- [ ] Audio loudness is -14 LUFS
- [ ] Text is readable on a phone screen
