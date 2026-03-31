# Improvement Roadmap

v1.1.3 shipped. 82 MCP tools, 825 tests, security audited. Here's what's next.

---

## ✅ Completed in v1.0.0 (2026-03-29)

### AI-Powered Features
- [x] `video_ai_remove_silence` - Auto-remove silent sections
- [x] `video_ai_transcribe` - Speech-to-text with Whisper
- [x] `video_ai_scene_detect` - ML scene detection
- [x] `video_ai_stem_separation` - Audio stem separation
- [x] `video_ai_upscale` - AI super-resolution
- [x] `video_ai_color_grade` - Auto color grading
- [x] `video_audio_spatial` - 3D spatial audio

### Video Transitions
- [x] `transition_glitch` - Glitch effect transition
- [x] `transition_pixelate` - Pixel dissolve transition
- [x] `transition_morph` - Mesh warp transition

### Audio Synthesis
- [x] `audio_synthesize` - Procedural waveform generation
- [x] `audio_preset` - 18+ pre-configured sounds
- [x] `audio_sequence` - Timed sequence composition
- [x] `audio_compose` - Multi-track mixing
- [x] `audio_effects` - Effects chain processing
- [x] `video_add_generated_audio` - One-shot video+audio

### Visual Effects
- [x] `effect_vignette` - Darkened edges
- [x] `effect_chromatic_aberration` - RGB separation
- [x] `effect_scanlines` - CRT scanlines
- [x] `effect_noise` - Film/digital noise
- [x] `effect_glow` - Bloom/glow effect

---

## High Impact (Directly improves every user session)

- [x] **Progress callbacks** — Long operations (merge, convert, export) give no feedback. A progress percentage in the MCP response would let agents tell users "50% done..." instead of silence. FFmpeg outputs progress to stderr — parse it.
- [ ] **Output file cleanup** — Every operation creates a new file. Multi-step workflows leave 3-4 intermediate files. Add a `cleanup` parameter or a `video_cleanup` tool that removes intermediates, keeping only the final output.
- [ ] **Smarter GIF output** — 3-second GIF at "low" quality = 28MB. The two-pass palette approach is good but `scale=480:-1` is too large for "low". Scale by quality preset: low=320, medium=480, high=640.
- [x] **Visual verification** — After an operation, return a thumbnail of the first frame of the output. *(Shipped in v1.0.0)*

## Medium Impact (Makes the API less frustrating)

- [x] **Video effects/filters** — Blur, sharpen, color grading, color presets (warm/cool/vintage/cinematic/noir), grayscale, sepia, invert, vignette. *(Shipped in v0.3.0 as `video_filter`, `video_blur`, `video_color_grade`)*
- [x] **Audio editing** — Audio normalization to LUFS targets (YouTube -16, broadcast -23, Spotify -14). *(Shipped in v0.3.0 as `video_normalize_audio`)*
- [x] **Reverse playback** — Reverse video and audio so it plays backwards. *(Shipped in v0.4.0)*
- [x] **Green screen / chroma key** — Remove solid color backgrounds using `chromakey` filter. *(Shipped in v0.4.0)*
- [x] **Denoise & deinterlace filters** — New filter types in `video_filter`: `denoise` (hqdn3d) and `deinterlace` (yadif). *(Shipped in v0.4.0)*
- [x] **Smarter GIF output** — Quality-based scaling (low=320, medium=480, high=640, ultra=800) instead of fixed 480px. *(Shipped in v0.4.0)*
- [x] **Rich CLI output** — Human-friendly terminal UI with tables, spinners, styled error panels. `--format json` for scripts. `--version` flag. Video templates (TikTok, YouTube Shorts, Instagram Reel, YouTube, Instagram Post). *(Shipped in v0.4.0)*

- [ ] **Crop by percentage** — Currently requires pixel math (`width=1920, height=1080`). Add `crop_percent: 50` so "center 50%" just works. The engine calculates pixels internally.
- [ ] **Orientation-aware metadata** — `video_info` reports raw stream dimensions (3840x2160) for a portrait phone video that displays as 2160x3840. Read the rotation/side_data metadata from ffprobe and report display orientation.
- [ ] **Merge auto-concat** — When merging clips with different resolutions/codecs, auto-normalize instead of failing. The error message suggests this but doesn't do it.
- [ ] **convert vs export clarity** — Both do similar things. Either merge them or make the distinction obvious in the tool descriptions. Right now users (and agents) have to guess which to use.
- [ ] **Template preview** — Before running a template, return what it *would* do (operations list, estimated output size, duration). Lets agents confirm before committing to a 30-second render.
- [x] **Batch operations** — Accept multiple inputs for a single operation. "Trim these 5 videos to 10 seconds each" in one call instead of 5. *(Shipped in v0.3.0 as `video_batch`)*

## Low Impact (Nice to have)

- [ ] **Custom font upload** — Currently only uses system fonts or a provided path. Allow passing a Google Fonts name and downloading it automatically.
- [ ] **Video concatenation with transitions per-clip** — Already supported in `merge` via `transitions` parameter, but add a `video_edit` shortcut for simple "clip A -> fade -> clip B -> dissolve -> clip C" patterns.
- [ ] **Audio waveform extraction** — Return a text-based waveform representation so agents can "see" the audio without playing it. Useful for finding silence or loud sections.
- [x] **Subtitle generation from text** — Given a list of `[(start, end, text)]` tuples, generate an SRT file and burn it in one step. *(Shipped as `video_generate_subtitles`)*
- [ ] **Frame-accurate seeking** — Use `-ss` before `-i` (input seeking) for speed, but fall back to output seeking for frame accuracy when the user specifies exact timestamps.
- [x] **Output directory option** — Currently outputs go next to the input file. Add a global `output_dir` option so all intermediates go to a temp folder. *(Shipped in v0.3.0 as `video_batch --output-dir` / `output_dir` param)*

## Observability (For you as the maintainer)

- [ ] **Usage analytics** — Optional anonymous ping on startup: version, Python version, OS. Just a single HTTP call, no tracking. Know how many people actually use it.
- [ ] **Structured logging** — Currently silent on success. Add a `--verbose` flag and optional log file. Helps users debug their own issues before filing them.
- [x] **GitHub Actions CI** — Run the full test suite on push. Catch regressions before they ship. Currently manual. *(Shipped in v0.2.x)*

## Not Doing (Intentionally out of scope)

- **Streaming** — RTMP, HLS output. Different domain.
- **GPU acceleration** — Keep it simple. CPU FFmpeg is fast enough for the target use case.

## FFmpeg Coverage Gaps

Features that FFmpeg supports but mcp-video doesn't expose yet. Ordered by impact.

### High Impact
- [x] **Audio effects** — Reverb (`aecho`), equalizer (`equalizer`), compressor (`acompressor`), pitch shift (`asetrate`+`aresample`), noise reduction (`afftdn`)
- [x] **Video stabilization** — Deshake filter (`vidstab`) for shaky handheld footage (requires FFmpeg with vidstab)
- [x] **Scene detection** — Auto-detect scene changes using `select` filter, return timestamps
- [x] **Quality metrics** — PSNR, SSIM, VMAF calculation for comparing video quality

### Medium Impact
- [ ] **HLS/DASH streaming** — Segment video for adaptive bitrate streaming
- [ ] **Advanced codecs** — AV1 (`libaom-av1`), HEVC/H.265 (`libx265`), ProRes (`prores_ks`)
- [x] **Image sequences** — Create video from image sequences (`img2pipe`), export frames
- [x] **Metadata editing** — Read/write video metadata tags, chapter support
- [x] **Audio waveform extraction** — Text-based waveform for silence/loud section detection
- [x] **Subtitle generation** — Generate SRT from `[(start, end, text)]` tuples, burn in one step *(Shipped as `video_generate_subtitles`)*

### Low Impact
- [x] **Ken Burns / zoom pan** — Animated zoom/pan effects via `zoompan` filter
- [ ] **Advanced masking** — Complex mask operations beyond chroma key
- [ ] **Frame-accurate seeking** — Input seeking for speed, output seeking for accuracy
- [x] **Two-pass encoding** — More efficient compression for target file sizes
