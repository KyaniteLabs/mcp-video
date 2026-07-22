# Long-form stream-to-shorts acceptance receipt — 2026-07-22

## Status

**PARTIAL.** The real-media workflow produced candidates, human-reviewed edits, four current vertical drafts, editable captions, cache-hit rerender receipts, and four complete packages. Production-readiness remains blocked by the manual audio-listening requirement and by safe padded framing that still needs an operator framing decision.

## Source and provenance

- Recording: *BBS Documentary Interview: John Sheetz*
- Source page: <https://archive.org/details/20030322-bbs-sheetz>
- License: CC BY-SA 2.5
- Path of record: `/tmp/kinocut-acceptance/bbs-sheetz-60min-640x480.mp4`
- Duration: 3598.864 seconds
- Resolution: 640×480
- Audio: AAC present
- Source SHA-256 before and after processing: `dfdff84c7c585c284e828acbd132129397b7a039bf6ca47c3d213c21228939c8`
- Original media was unchanged.

## Transcription and discovery

- Local transcription: OpenAI Whisper `tiny`, English, CPU
- Result: 828 segments in 64.407 seconds
- Transcript JSON: `/tmp/kinocut-acceptance/local-whisper-tiny.json`
- Transcript JSON SHA-256: `e770ee6f7c95fd2a166764396a4d9afd6c77ac10604ae8e2d08327e6097376a0`
- Full editable transcript SRT: `/tmp/kinocut-acceptance/local-whisper-tiny.srt`
- Distinct candidates after temporal duplicate suppression: 8
- Acceptance receipt: `/tmp/kinocut-acceptance/acceptance-receipt.json`
- Canonical CLI was also replayed directly against the real source with the `transcribe` extra and no pre-shaped transcript:
  - command: `uv run --frozen --extra transcribe kino --format json shorts <source> --platform youtube-shorts --platform instagram-reel --min-clip-seconds 15 --max-clip-seconds 45 --captions-editable --output-dir /tmp/kinocut-acceptance/cli-out`
  - result: `shorts_c400a8a5fd60ef6c`, status `review_required`, source checksum verified, both platforms present, editable captions enabled, burned captions disabled, and multiple proposals emitted.
- Post-review fixes now whitelist raw Whisper segment fields, derive transcript confidence, and route recordings over 3600 seconds through `transcribe_longform`; focused seam tests pass.

The tiny local model produced recognizable but imperfect wording. Candidate/caption copy therefore requires human editorial review; Kinocut did not synthesize replacement words.

## Human review actions

- Adjusted candidate: `local_000483-fdca2b`
  - start moved forward 0.75 seconds
  - end moved backward 0.75 seconds
  - title edited to “How Teletype Art Was Refined”
  - hook edited to “Each revision made the picture clearer.”
- Approved candidates:
  - `local_000483-fdca2b`
  - `local_000731-a941e8`
- Rendering remained blocked until explicit approval records existed.

## Rendered drafts

Four 1080×1920 H.264/AAC drafts were rendered:

1. `/tmp/kinocut-acceptance/acceptance-local-out/drafts/local_000483-fdca2b/youtube-shorts/vertical.mp4`
2. `/tmp/kinocut-acceptance/acceptance-local-out/drafts/local_000483-fdca2b/instagram-reel/vertical.mp4`
3. `/tmp/kinocut-acceptance/acceptance-local-out/drafts/local_000731-a941e8/youtube-shorts/vertical.mp4`
4. `/tmp/kinocut-acceptance/acceptance-local-out/drafts/local_000731-a941e8/instagram-reel/vertical.mp4`

Measured A/V duration deltas were 0.083–0.091 seconds. True peaks were −1.0 to −0.9 dBFS. Integrated loudness measured −14.3 LUFS for the first pair and −16.7 LUFS for the second pair. Full measurements: `/tmp/kinocut-acceptance/audio-sync-report.json`.

A repeated unchanged render of the adjusted candidate returned cache hits for both platform drafts, proving rerender from the saved plan without retranscription.

## Visual inspection

Beginning/middle/end contact sheets were directly inspected for every current draft:

- `/tmp/kinocut-acceptance/inspection-local/local_000483-fdca2b-youtube-shorts-sheet.jpg`
- `/tmp/kinocut-acceptance/inspection-local/local_000483-fdca2b-instagram-reel-sheet.jpg`
- `/tmp/kinocut-acceptance/inspection-local/local_000731-a941e8-youtube-shorts-sheet.jpg`
- `/tmp/kinocut-acceptance/inspection-local/local_000731-a941e8-instagram-reel-sheet.jpg`

Observed result: the face and hands remained visible at all sampled points and no primary subject was cropped out. The conservative safe composition introduces large black padding above and below the 4:3 source. This is honest fallback behavior, not a polished subject-aware crop, and must be flagged for manual framing review.

Burned captions were disabled by default. Editable SRT examples:

- `/tmp/kinocut-acceptance/acceptance-local-out/drafts/local_000483-fdca2b/youtube-shorts/captions.srt`
- `/tmp/kinocut-acceptance/acceptance-local-out/drafts/local_000731-a941e8/youtube-shorts/captions.srt`

The SRT files are phrase-grouped, monotonic, and bounded to clip time. Tiny-model recognition errors remain visible for operator correction.

## Export packages

Each approved candidate has YouTube Shorts and Instagram Reels packages under:

- `/tmp/kinocut-acceptance/acceptance-local-out/packages/local_000483-fdca2b/`
- `/tmp/kinocut-acceptance/acceptance-local-out/packages/local_000731-a941e8/`

Every platform directory contains:

- `vertical.mp4`
- `captions.srt`
- `thumbnail.jpg`
- `pkg_*__manifest.json`

The manifest embeds suggested title, short description/hook, source timestamps, candidate rationale/context, transcript/source lineage, and render receipt digest. Metadata is marked as drafting-only and makes no search, engagement, or virality claim.

## Automated verification

- Focused workflow suite: 340 passed.
- Final full repository suite: **4548 passed, 172 skipped** in 432.01 seconds.
- Ruff passed across `kinocut`, `tests`, and `scripts`; `git diff --check` passed.
- Post-review transcription, optional burn-in, and intake corrections: 109 focused tests passed after restoring the base development environment.

## Remaining acceptance blocker

No available tool provides trustworthy human auditory perception. Automated loudness, true-peak, A/V duration, and boundary-fade checks passed, but **every edit boundary has not been human-listened**. This receipt therefore cannot claim DONE or production-ready status.
A human-ready listening pack now isolates the first and last two seconds of every draft:

- directory: `/tmp/kinocut-acceptance/boundary-listening-pack/`
- playlist: `/tmp/kinocut-acceptance/boundary-listening-pack/playlist.m3u`
- checklist/index: `/tmp/kinocut-acceptance/boundary-listening-pack/index.json`
- clips: 8 WAV files covering both boundaries of all four drafts

For each clip, record pass/fail for pops or clicks, clipped syllables, abrupt discontinuities, and unexpected silence.
