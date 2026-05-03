# Audio Exploration for mcp-video Explainer

> **Historical document.** Remotion was removed in v1.3.0/v1.3.1. This exploration is preserved for reference only.
>
> Status: Research only — no implementation in this phase.

## Current State

The explainer video (`video-social-v2.mp4`) is a silent 70s visual at 30fps. The video audit flagged lack of audio as a P3 concern — not blocking for social media distribution, but important for YouTube and polished presentations.

## Audio Layers to Consider

### 1. Background Music

**Options:**

| Approach | Pros | Cons |
|----------|------|------|
| Remotion `<Audio>` component with local file | Full control, no external deps | Need to source/license music |
| Free music libraries (Pixabay, Free Music Archive) | Free, CC-licensed | Quality varies, search time |
| AI-generated (Suno, Udio, AIVA) | Custom fit, fast | Cost, licensing unclear |
| Commission from freelance musician | Perfect fit | Expensive ($200-500+) |

**Remotion integration:**
```tsx
import { Audio, staticFile } from 'remotion';

<Audio src={staticFile('background.mp3')} volume={0.3} />
```

**Recommended approach:** Use a royalty-free track from Pixabay or similar. Add `<Audio>` to `ExplainerVideo.tsx` with volume ducking during key moments.

### 2. Sound Effects (SFX)

**Scenes that benefit from SFX:**
- S1 Hook: Subtle "whoosh" on logo slam
- S3 Core Editing: UI click/tap sounds on feature transitions
- S5 Image Code: Camera shutter on color extraction
- S6 Remotion: Code typing sounds
- S7 Architecture: Data flow "ping" sounds
- S10 CTA: Terminal typing + success chime on "Copied!"

**Integration pattern:**
```tsx
import { Audio, staticFile, useCurrentFrame, interpolate } from 'remotion';

// In each scene, conditionally play SFX
const sfxVolume = interpolate(frame, [30, 35], [0, 1], {
  extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
});
<Audio src={staticFile('sfx-logo-slam.mp3')} volume={sfxVolume} />
```

**Source:** Freesound.org (CC0), or generate with AI tools.

### 3. Voiceover / Narration

**Options:**

| Approach | Pros | Cons |
|----------|------|------|
| Text-to-speech (ElevenLabs, OpenAI TTS) | Consistent, fast iteration | Can sound robotic |
| Professional VO artist | Best quality | Expensive, slow turnaround |
| AI voice (ElevenLabs Turbo v2) | Good quality, cheap | Needs careful prompt tuning |

**Script outline (matching burned captions):**
1. "What if AI could edit video?" (0-3s)
2. "43 powerful video editing tools" (3-9s)
3. "Trim, merge, color grade — everything you need" (9-16s)
4. "Chroma key, stabilization, subtitles, and more" (16-23s)
5. "Extract colors and automate your workflow" (23-32s)
6. "Seamless Remotion integration" (32-38s)
7. "AI to MCP to FFmpeg to output" (38-45s)
8. "MCP = USB-C for AI tools" (45-50s)
9. "Simple code, powerful results" (50-56s)
10. "pip install mcp-video" (56-67s)

**Recommended:** ElevenLabs Turbo v2 with a professional voice preset. Cost ~$0.30 per generation.

### 4. Music + VO Balance

**Ducking strategy:**
- Music plays throughout at 0.3 volume
- Duck to 0.1 during narration
- Raise to 0.4 during transitions
- Fade out over last 2 seconds with video

## Technical Integration in Remotion

### File structure:
```
explainer-video/public/
  audio/
    background.mp3
    sfx-logo-slam.mp3
    sfx-typing.mp3
    sfx-success.mp3
    narration/
      s1-hook.mp3
      s2-solution.mp3
      ...
```

### Implementation in ExplainerVideo.tsx:
```tsx
import { Audio, staticFile } from 'remotion';

// Background music throughout
<Audio src={staticFile('audio/background.mp3')} volume={0.3} />

// Per-sequence SFX and narration inside each TransitionSeries.Sequence
<TransitionSeries.Sequence durationInFrames={90}>
  <S1Hook />
  <BurnedCaption text="What if AI could edit video?" />
  <Audio src={staticFile('audio/narration/s1-hook.mp3')} volume={0.8} />
</TransitionSeries.Sequence>
```

### Audio rendering notes:
- Remotion renders audio natively — no FFmpeg audio pass needed
- Output codec: AAC (default with H.264)
- Ensure audio files are in `public/` directory for `staticFile()` access
- Use `remotion_to_mcpvideo` post-process for final audio normalization

## Cost Estimate

| Item | Source | Cost |
|------|--------|------|
| Background music | Pixabay (free) | $0 |
| SFX (10 sounds) | Freesound.org (CC0) | $0 |
| Voiceover (10 segments) | ElevenLabs Turbo v2 | ~$3 |
| Music normalization | mcp-video tool | $0 |
| **Total** | | **~$3** |

## Next Steps

1. Select and download background music track
2. Generate voiceover with ElevenLabs
3. Source SFX from Freesound.org
4. Add `<Audio>` components to each scene
5. Test audio balance in Remotion Studio
6. Render final video with audio
7. Normalize loudness to -16 LUFS (YouTube standard) via `video_normalize_audio`
