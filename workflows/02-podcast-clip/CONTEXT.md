# 02-podcast-clip

Extract a podcast highlight with auto-chapters, captions, and platform-ready export.

## Inputs

| Source | File/Location | Description |
|---|---|---|
| Raw episode | User provided | Full podcast episode or interview |
| Transcription | Optional | Existing transcript file (SRT/VTT) |

## Process

1. **01-detect-scenes**: Use `video_detect_scenes` to find natural break points
2. **02-auto-chapters**: Use `video_auto_chapters` to generate chapter markers
3. **03-trim**: Use `video_trim` to extract the highlight segment
4. **04-transcribe**: Use `video_ai_transcribe` to generate timed captions
5. **05-burn-captions**: Use `video_subtitles_styled` to burn captions into the video
6. **06-export**: Use `video_convert` for final format

## Outputs

| Artifact | Location | Format |
|---|---|---|
| Scene detection | output/01_scenes.json | Scene timestamps |
| Chapters | output/02_chapters.json | Chapter markers |
| Trimmed clip | output/03_highlight.mp4 | Highlight segment |
| Transcript | output/04_transcript.srt | SRT subtitles |
| Captioned clip | output/05_captioned.mp4 | With burned captions |
| Final clip | output/final_clip.mp4 | MP4, platform-ready |

## Quality gates

- [ ] Highlight segment is 30-120 seconds
- [ ] Captions are synced to audio
- [ ] Text is readable on mobile
- [ ] Speaker names included if multi-speaker
