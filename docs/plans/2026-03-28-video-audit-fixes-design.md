# Explainer Video Audit Fixes — Design Document

> **Historical document.** Remotion was removed in v1.3.0/v1.3.1. This design is preserved for reference only.

**Date:** 2026-03-28
**Scope:** Address all P0, P1, P2 priorities from VIDEO_AUDIT_RECOMMENDATIONS.md
**Constraint:** No audio implementation. Code-only + mcp-video synthetic clips. Phase 3 explores audio options.

---

## Phase 1: Scene Enhancements (P0 + P1)

### 1.1 S1 Hook — Positive Reframe (P0 #1)

**Current:** "CLI video editing is broken" (negative, alienates CLI users)
**Change to:** "What if AI could edit video?" (positive question hook)

- Keep glitch transition, cursor blink, bracket animation, underline sweep
- Keep orange (#FF6B35) text color for the hook line
- Logo slam timing unchanged (frame 30+)
- Tagline unchanged: "The video editing MCP server for AI agents"

### 1.2 S2 Solution — Slow Orbit + Context (P1 #6)

**Current:** Orbit labels at 1.5°/frame, too fast to read
**Changes:**
- Reduce orbit speed to 0.75°/frame (50% slower)
- Change subtitle from "MCP Tools for AI Agents" to "43 video editing tools"
- Add glow trails to orbit labels (subtle cyan shadow on trailing edge)
- Counter animation unchanged (0 → 43 over 120 frames)

### 1.3 S3 Core Editing — Real Before/After Demos (P0 #3)

**Current:** Static gradient bar with BEFORE/AFTER labels, decorative
**Changes:**
- Replace gradient bar with a cycling demo panel (3 features, ~2.3s each)
- Feature 1 (Trim): Show timeline bar with segment highlighted, scissors icon
- Feature 2 (Color Grade): Animated gradient transition (flat → cinematic)
- Feature 3 (Merge): Two clips sliding together into one
- Keep 3×2 card grid on left side
- Active feature card gets highlight border + scale

### 1.4 S4 Pro Features — Micro-Demos (P1 #7)

**Current:** Static radial graph + Ken Burns placeholder + waveform decoration
**Changes:**
- Keep radial graph layout but add highlight cycling (each node pulses in sequence)
- Replace Ken Burns box with a "Stabilize" micro-demo: shaky rectangle → smooth rectangle
- Replace waveform bars with a "Chroma Key" micro-demo: green rectangle → transparent with background
- Add brief text label under each active demo

### 1.5 S5 Image Code — Context Header (P1 #8)

**Current:** Product image placeholder + code terminal, no explanation
**Changes:**
- Add scene title at top: "AI-Powered Color Analysis" (FONT_SIZE.SUBTITLE, NEON_MAGENTA)
- Add subtitle: "Extract brand colors from any image"
- Improve scan line animation (already exists) — make it more prominent
- Show hex codes floating out from extracted color swatches
- Code terminal: add comment line "# Match your video grade to your brand"

### 1.6 S10 CTA — Improved Ending (P1 #9)

**Current:** Static pip install + stat cards + GitHub URL
**Changes:**
- Keep "mcp-video" logo with bounce entrance
- Typewriter animation for "$ pip install mcp-video" (letter-by-letter reveal)
- After typing completes: "Copied!" confirmation with checkmark
- Stat cards: animate numbers counting up (43, 545, Apache 2.0)
- GitHub URL: underline sweep animation
- Keep fade-to-black at end

### 1.7 Burned-In Captions (P0 #4)

Every scene gets a subtitle bar at the bottom:
```
S1: "What if AI could edit video?"
S2: "43 powerful video editing tools"
S3: "Trim, merge, color grade — everything you need"
S4: "Chroma key, stabilization, subtitles, and more"
S5: "Extract colors and automate your workflow"
S6: "Seamless Remotion integration"
S7: "AI → MCP → FFmpeg → Output"
S8: "MCP = USB-C for AI tools"
S9: "Simple code, powerful results"
S10: "pip install mcp-video"
```

Caption style:
- Position: bottom 80px, centered
- Font: 36px, bold, white
- Background: rgba(0,0,0,0.6) pill with 12px border-radius
- Entrance: fade in with each scene, synced to scene start
- No exit animation (just disappears with scene transition)

---

## Phase 2: New Scenes + Architecture (P2)

### 2.1 S8 NEW — MCP Primer (P2 #12)

**Duration:** 3s (90 frames)
**Purpose:** 1-second primer for viewers who don't know MCP

Layout:
- Left side: "MCP" text in large gradient letters
- Right side: "=" then visual analogy
- Animated sequence:
  - Frame 0-15: "MCP" fades in
  - Frame 15-45: Arrow → "USB-C for AI tools" types in
  - Frame 45-70: Visual: phone icon → USB-C cable → laptop icon
  - Frame 70-90: Subtle glow pulse

### 2.2 S9 NEW — Competitive Comparison (P2 #13)

**Duration:** 4s (120 frames)
**Purpose:** Show mcp-video's simplicity vs alternatives

Layout:
- Split screen: left (red-tinted) vs right (green-tinted)
- Left header: "MoviePy" with red accent
- Right header: "mcp-video" with green accent
- Left code: 10 lines of Python (faded/dimmed)
- Right code: 1 line of Python (highlighted)
- Animated reveal: left fades in first, then right swoops in with emphasis
- Bottom text: "10 lines → 1 tool call"

### 2.3 S7 Architecture — Animated Data Flow (P2 #10)

**Current:** 5 static vertical boxes with code snippets
**Changes:**
- Switch to horizontal flow: [AI Agent] → [MCP] → [mcp-video] → [FFmpeg] → [Output]
- Animated cyan packet (glowing dot) travels left to right
- Each box lights up as packet passes through (border color change, subtle scale)
- Simplified labels (remove "JSON-RPC over stdio")
- Each segment ~1.2s, total ~6s for the flow animation
- Keep the bottom data flow pipeline bar

### 2.4 S6 Remotion — Context (P2 #11)

**Current:** File tree + browser mockup, assumes viewer knows Remotion
**Changes:**
- Add subtitle under title: "The React framework for programmatic video"
- Improve video preview panel (already has play button + progress bar)
- Add pipeline stage descriptions on hover/highlight

---

## Phase 3: Audio & Sound Design Exploration (Research Only)

Research what's possible for future audio integration:

### 3.1 Background Music Options
- Investigate royalty-free electronic/tech music sources
- Identify mcp-video's `video_add_audio` tool capabilities
- Determine if we can use public domain CC0 music

### 3.2 Sound Effects
- Typewriter click for hook text
- Glitch/transition sound for logo slam
- Success ding for CTA "Copied!" confirmation
- UI click sounds for interactive elements

### 3.3 Voiceover Feasibility
- Research TTS options (OpenAI TTS, ElevenLabs, etc.)
- Estimate cost and quality trade-offs
- Draft voiceover script synced to 70s timeline

### 3.4 Technical Integration
- How to add audio via mcp-video: `video_add_audio` tool
- Audio normalization via `video_normalize_audio`
- Mixing multiple audio tracks

**No code changes in this phase** — documentation only.

---

## Updated Scene Timing (2100 frames / 70s)

| # | Scene | Duration | Frames | Transition |
|---|-------|----------|--------|------------|
| 1 | S1 Hook | 3s | 90 | — |
| 2 | S2 Solution | 5s | 150 | slide from-bottom (12) |
| 3 | S3 Core Editing | 7s | 210 | wipe from-left (12) |
| 4 | S4 Pro Features | 7s | 210 | fade (10) |
| 5 | S5 Image Code | 8s | 240 | slide from-right (12) |
| 6 | S6 Remotion | 6s | 180 | wipe from-top (12) |
| 7 | S7 Architecture | 7s | 210 | fade (10) |
| 8 | **S8 MCP Primer** | **3s** | **90** | slide from-right (12) |
| 9 | **S9 Code Comparison** | **4s** | **120** | wipe from-left (12) |
| 10 | S10 CTA | 7s | 210 | — |
| | Transitions | | ~90 | 7 × ~12 |
| | **TOTAL** | **~70s** | **~2100** | |

## Synthetic Video Clips (Generated via mcp-video)

Before implementing scenes, generate these clips:

1. **Color grade before/after**: Create gradient video → apply "cinematic" preset
2. **Stabilize demo**: Create a video with simulated shake → stabilize
3. **Chroma key demo**: Create green rectangle → chroma key → replace background
4. **Trim demo**: Create 5s clip → trim to 2s
5. **Merge demo**: Create two short clips → merge

These will be placed in `explainer-video/assets/` and referenced in scenes.

## Files Changed

- `src/ExplainerVideo.tsx` — Add S8 MCP Primer, S9 Code Comparison, update timing
- `src/scenes/S1Hook.tsx` — Positive hook text
- `src/scenes/S2Solution.tsx` — Slower orbit, new subtitle
- `src/scenes/S3CoreEditing.tsx` — Cycling demo panel
- `src/scenes/S4ProFeatures.tsx` — Micro-demos, remove Ken Burns
- `src/scenes/S5ImageCode.tsx` — Context header, hex codes
- `src/scenes/S6Remotion.tsx` — Context subtitle
- `src/scenes/S7Architecture.tsx` — Horizontal data flow
- `src/scenes/S8CTA.tsx` → rename to `src/scenes/S10CTA.tsx` — Improved CTA
- `src/scenes/S8MCPPrimer.tsx` — NEW
- `src/scenes/S9CodeComparison.tsx` — NEW
- `src/components/BurnedCaption.tsx` — NEW caption component
- `src/Root.tsx` — Update durationInFrames to 2100
