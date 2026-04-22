Just shipped my first project ever — and it's 81 video editing tools for AI agents 🤯

6 weeks ago I didn't know what an MCP server was. Today mcp-video is live on PyPI (v1.2.4) with 279 commits, 858 tests, and every single tool verified working on real MP4s.

Repo: https://github.com/Pastorsimon1798/mcp-video
PyPI: https://pypi.org/project/mcp-video/
Landing page: https://pastorsimon1798.github.io/mcp-video/

---

**How Jake broke my brain (in a good way)**

March 10. YouTube algorithm drops a Jake Van Clief video. I binge 6 videos that day. March 20 I create the repo. That evening I re-watch his folder system video and something clicks — what if Claude Code + Remotion + clean folder architecture had a baby?

I didn't use ICM for the core code architecture (that came later, layered on top). But Jake's 5-layer context system became the mental model for how I document everything — AGENTS.md, .omc/, .omx/, workflows/ — so future me actually knows where stuff lives.

---

**What I built**

81 MCP tools across 9 categories:

• Core editing: trim, merge, crop, rotate, speed, resize, convert, fade
• Filters: blur, grayscale, sepia, brightness, contrast, saturation, sharpen, denoise
• Effects: vignette, chromatic aberration, scanlines, noise, glow
• Transitions: glitch, pixelate, morph
• Layout: grid, PIP, split-screen, animated text
• MoGraph: count animations, progress bars
• Audio: presets, sequences, mixing, effects, waveform viz
• Image analysis: color extraction, palette generation, product analysis
• AI: transcription, scene detection, color grading, silence removal
• Remotion: validate, render, stills, studio, scaffold templates

**Every tool was tested end-to-end on real videos today.** Found and fixed 7 real bugs in the process — from ffprobe parsing crashes to Remotion template syntax errors to stale API methods. The AI tools need optional deps (whisper, demucs, opencv-contrib) and Remotion needs Node.js, but they're documented and work once installed.

---

**The numbers**

279 commits in 34 days
858 tests (817 passing)
3 PRs merged today (v1.2.3 → v1.2.4)
81 tools registered
1 person who had never shipped anything before

---

**Proof it works**

Generated actual clips using the tools themselves — no manual FFmpeg:

[Side-by-side: original vs grayscale filter]
[Montage: sepia → vignette → scanlines → glitch transition]
[Thumbnail extraction at timestamp]

Python client makes it dead simple:

```python
from mcp_video import Client

client = Client()
client.trim("input.mp4", start=5, duration=10, output="trimmed.mp4")
client.filter("trimmed.mp4", filter_type="vignette", output="styled.mp4")
client.add_text("styled.mp4", text="mcp-video", position="center", output="final.mp4")
```

---

**What I learned**

1. Shipping is a skill I never practiced. Analysis paralysis killed every idea I had for years. Jake's context layer framework is what let me ship without waiting for perfection.

2. Tests started at zero. Now 858 of them catch my dumb mistakes before they hit main. Non-negotiable.

3. Wrapping 81 FFmpeg operations into clean Python APIs with proper error handling, timeouts, and input validation took 3x longer than the "fun" parts. But that's the actual value.

4. AI agents need deterministic tools — every tool has a schema, validation, typed returns. No guesswork.

---

**The honest truth**

Former data analyst. On medical leave. No Notion dashboard. No morning routine. I have a toddler, a wife, and a laptop.

What I do have: Jake's framework for thinking about context, Claude Code for execution, and a stubborn refusal to let another idea die in a notebook.

This project isn't perfect. Some error messages suck. Some docs are thin. But it's shipped, tested, and real.

If you're on the fence about building something — this is your sign. I had zero business building a video editing server.

---

@Jake Van Clief — your folder system video lives rent-free in my head. The kick in the ass I didn't know I needed 🙏

Shoutout to Claude Code too — 90% of those 279 commits were pair-programmed. The future is weird.

---

**What's next:** better Remotion integration, more AI features, actual video tutorials, and (hopefully) a first community contribution.

If you want to try it: `pip install mcp-video`

Questions / feedback / roasting welcome 👇
