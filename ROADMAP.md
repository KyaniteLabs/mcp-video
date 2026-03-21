# Improvement Roadmap

Bugs fixed, 0.1.1 shipped. Here's what would make mcp-video genuinely better to use.

---

## High Impact (Directly improves every user session)

- [x] **Progress callbacks** — Long operations (merge, convert, export) give no feedback. A progress percentage in the MCP response would let agents tell users "50% done..." instead of silence. FFmpeg outputs progress to stderr — parse it.
- [ ] **Output file cleanup** — Every operation creates a new file. Multi-step workflows leave 3-4 intermediate files. Add a `cleanup` parameter or a `video_cleanup` tool that removes intermediates, keeping only the final output.
- [ ] **Smarter GIF output** — 3-second GIF at "low" quality = 28MB. The two-pass palette approach is good but `scale=480:-1` is too large for "low". Scale by quality preset: low=320, medium=480, high=640.
- [x] **Visual verification** — After an operation, return a thumbnail of the first frame of the output. Lets agents (and users) confirm the result looks correct without opening the file. Could be base64-encoded or a file path.

## Medium Impact (Makes the API less frustrating)

- [ ] **Crop by percentage** — Currently requires pixel math (`width=1920, height=1080`). Add `crop_percent: 50` so "center 50%" just works. The engine calculates pixels internally.
- [ ] **Orientation-aware metadata** — `video_info` reports raw stream dimensions (3840x2160) for a portrait phone video that displays as 2160x3840. Read the rotation/side_data metadata from ffprobe and report display orientation.
- [ ] **Merge auto-concat** — When merging clips with different resolutions/codecs, auto-normalize instead of failing. The error message suggests this but doesn't do it.
- [ ] **convert vs export clarity** — Both do similar things. Either merge them or make the distinction obvious in the tool descriptions. Right now users (and agents) have to guess which to use.
- [ ] **Template preview** — Before running a template, return what it *would* do (operations list, estimated output size, duration). Lets agents confirm before committing to a 30-second render.
- [ ] **Batch operations** — Accept multiple inputs for a single operation. "Trim these 5 videos to 10 seconds each" in one call instead of 5.

## Low Impact (Nice to have)

- [ ] **Custom font upload** — Currently only uses system fonts or a provided path. Allow passing a Google Fonts name and downloading it automatically.
- [ ] **Video concatenation with transitions per-clip** — Already supported in `merge` via `transitions` parameter, but add a `video_edit` shortcut for simple "clip A -> fade -> clip B -> dissolve -> clip C" patterns.
- [ ] **Audio waveform extraction** — Return a text-based waveform representation so agents can "see" the audio without playing it. Useful for finding silence or loud sections.
- [ ] **Subtitle generation from text** — Given a list of `[(start, end, text)]` tuples, generate an SRT file and burn it in one step. Currently requires creating the SRT manually.
- [ ] **Frame-accurate seeking** — Use `-ss` before `-i` (input seeking) for speed, but fall back to output seeking for frame accuracy when the user specifies exact timestamps.
- [ ] **Output directory option** — Currently outputs go next to the input file. Add a global `output_dir` option so all intermediates go to a temp folder.

## Observability (For you as the maintainer)

- [ ] **Usage analytics** — Optional anonymous ping on startup: version, Python version, OS. Just a single HTTP call, no tracking. Know how many people actually use it.
- [ ] **Structured logging** — Currently silent on success. Add a `--verbose` flag and optional log file. Helps users debug their own issues before filing them.
- [ ] **GitHub Actions CI** — Run the full test suite on push. Catch regressions before they ship. Currently manual.

## Not Doing (Intentionally out of scope)

- **Video effects/filters** — Blur, sharpen, color grading. That's DaVinci Resolve territory.
- **Audio editing** — EQ, compression, noise removal. Use a dedicated audio tool.
- **Streaming** — RTMP, HLS output. Different domain.
- **GPU acceleration** — Keep it simple. CPU FFmpeg is fast enough for the target use case.
