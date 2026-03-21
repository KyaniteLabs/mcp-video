# AgentCut — Social Media Launch Posts

## Twitter/X Thread

---

**Tweet 1 (hook):**

I just built something that didn't exist: an open-source video editing MCP server for AI agents.

19 tools. 3 interfaces. Purpose-built for AI agents.

Agents can now trim, merge, add text, resize, convert, crop, rotate, fade, and export video — all locally, all free.

Here's what it does:

---

**Tweet 2 (demo):**

"Hey Claude, take this interview clip, trim it to 30 seconds, add a title card, resize for TikTok, and export."

That's it. One prompt. AgentCut handles the rest.

No FFmpeg flags to memorize. No cloud API to pay for. Your video never leaves your machine.

---

**Tweet 3 (tools):**

19 MCP tools:

video_info | video_trim | video_merge | video_add_text
video_add_audio | video_resize | video_convert | video_speed
video_thumbnail | video_preview | video_storyboard | video_subtitles
video_watermark | video_crop | video_rotate | video_fade
video_export | video_edit | video_extract_audio

Plus 5 platform templates: TikTok, YouTube Shorts, Reels, YouTube, Instagram Post.

---

**Tweet 4 (code):**

Python API is clean:

```python
from agentcut import Client

editor = Client()
clip = editor.trim("v.mp4", start="0:30", duration="15")
final = editor.resize(clip.output_path, aspect_ratio="9:16")
result = editor.export(final.output_path, quality="high")
```

Also works as a CLI: `agentcut trim video.mp4 -s 0:30 -d 15`

---

**Tweet 5 (CTA):**

pip install agentcut

GitHub: github.com/pastorsimon1798/agentcut
Apache 2.0. Contributions welcome.

The MCP ecosystem needs more tools like this. Video editing is just the start — image processing, audio mixing, 3D rendering... there's room for so many MCP servers.

If you build with MCP, I'd love to hear what tools you need.

---

## Hacker News Show HN Post

**Title:** Show HN: AgentCut – Video editing MCP server for AI agents (19 tools)

**Body:**

AgentCut is an open-source MCP server that gives AI agents the ability to edit video files. It wraps FFmpeg into 19 structured tools that work with any MCP-compatible client.

The motivation: AI agents can write code, browse the web, create images — but they can't edit video. Existing options are GUI-only (agents can't click), raw FFmpeg (agents can't memorize complex flag combinations), or cloud APIs (expensive, slow, vendor lock-in).

Three interfaces:
- MCP Server: Add to your config, then just tell your agent what to edit
- Python Client: Clean API for automation (`editor.trim("v.mp4", start="0:30", duration="15")`)
- CLI: `agentcut trim video.mp4 -s 0:30 -d 15`

19 tools covering: trim, merge, text overlay, audio sync, resize, crop, rotate, fade, format conversion, speed change, thumbnails, previews, storyboards, subtitles, watermarks, export, full timeline edits, and audio extraction.

Also includes a Timeline DSL for complex multi-track edits (video + audio + text + transitions in one JSON object) and 5 platform templates (TikTok, YouTube Shorts, Instagram Reel, YouTube, Instagram Post).

262 tests across the full testing pyramid. Pure Python, only depends on mcp + pydantic + ffmpeg.

pip install agentcut

GitHub: https://github.com/pastorsimon1798/agentcut

---

## Reddit Posts

### r/MCP (Model Context Protocol)

**Title:** Built a video editing MCP server — 16 tools, 3 interfaces, open source

**Body:**

Hey everyone. I just shipped AgentCut — an MCP server that gives AI agents the ability to edit video files.

It wraps FFmpeg into 19 structured tools. Works with Claude Code, Cursor, or any MCP client.

Quick example — add this to your MCP config:
```json
{
  "mcpServers": {
    "agentcut": {
      "command": "uvx",
      "args": ["agentcut"]
    }
  }
}
```

Then: "Hey Claude, trim this video from 0:30 to 1:00 and add a title card."

19 tools: trim, merge, add_text, add_audio, resize, crop, rotate, fade, convert, speed, thumbnail, preview, storyboard, subtitles, watermark, export, edit_timeline, extract_audio, info.

Also has a Python client and CLI. 262 tests. Apache 2.0.

What tools would you want to see in an MCP server? I'm thinking about building image processing and audio mixing servers next.

GitHub: https://github.com/pastorsimon1798/agentcut

---

### r/ClaudeAI

**Title:** I built a video editing MCP server for Claude Code — here's what it does

**Body:**

If you've ever wanted Claude to edit video for you, this is how.

AgentCut is an MCP server with 19 video editing tools. Add it to your Claude Code MCP settings, and you can just ask Claude to:

- Trim clips by timestamp
- Merge multiple clips with transitions (fade, dissolve)
- Add text overlays, titles, captions
- Sync audio tracks with fade effects
- Resize for any platform (TikTok 9:16, YouTube 16:9, Instagram 1:1)
- Convert between mp4/webm/gif/mov
- Change speed (slow-mo, time-lapse)
- Generate storyboards and thumbnails
- Burn subtitles, add watermarks

Setup is 2 lines in your MCP config:
```json
{
  "mcpServers": {
    "agentcut": { "command": "uvx", "args": ["agentcut"] }
  }
}
```

Then: *"Take this interview clip, trim to 30 seconds, add 'EPISODE 1' as a title, and export for TikTok."*

Everything runs locally. No cloud, no API keys, no per-minute billing. Your video never leaves your machine.

pip install agentcut

https://github.com/pastorsimon1798/agentcut

---

### r/LocalLLaMA

**Title:** AgentCut — open source video editing MCP server (19 tools, works with Claude/Cursor)

**Body:**

Built an MCP server for video editing. 19 tools that wrap FFmpeg into a clean API for AI agents.

Works with Claude Code, Cursor, and any MCP-compatible client. Also has a Python client and CLI.

The key feature is the Timeline DSL — describe a full multi-track edit (video clips + audio + text + transitions) in a single JSON object and execute it in one call.

262 tests. Apache 2.0. pip install agentcut.

https://github.com/pastorsimon1798/agentcut

---

## Beta User Outreach DMs

### DM Template 1 (MCP builders)

Hey [Name], I saw you've been building with MCP and thought you might be interested — I just shipped AgentCut, an open-source video editing MCP server.

19 tools (trim, merge, text, audio, resize, crop, rotate, fade, convert, etc.) that work with Claude Code, Cursor, etc. It's the first MCP server for video editing that I know of in this niche.

Would love your feedback if you get a chance to try it. What video editing capabilities would be most useful in your workflows?

GitHub: https://github.com/pastorsimon1798/agentcut

### DM Template 2 (AI content creators)

Hey [Name], I'm building AgentCut — an open-source tool that lets AI agents edit video. Think "FFmpeg but with an API that Claude can actually use."

The idea is you could tell Claude "take this podcast clip, trim to 60 seconds, add a subscribe CTA, and export for TikTok" and it just works.

Would you be interested in beta testing? Looking for people who edit video regularly and want to see how AI agents can help.

### DM Template 3 (Dev tool builders)

Hey [Name], been following your work on [their project]. I just built AgentCut — an MCP server for video editing.

The architecture is: MCP server wrapping FFmpeg, with a Python client and CLI. 19 tools, 262 tests, Apache 2.0.

Curious if you've thought about adding video capabilities to [their project]? Would be happy to collaborate or share what I've learned about the MCP tool-building patterns.

GitHub: https://github.com/pastorsimon1798/agentcut
