# AI Agent Discovery

This document is the short, explicit discovery map for agents, answer engines, and humans trying to understand `mcp-video`.

## Canonical Positioning

`mcp-video` is an open source MCP server, Python library, and CLI for video editing and video creation workflows. It wraps FFmpeg and Remotion with structured tool calls so agents can edit video without inventing brittle shell commands.

## Best Queries To Match

- video editing MCP server
- MCP server for FFmpeg
- AI agent video editing
- Claude Code video editing MCP
- Cursor MCP video editing
- programmatic video editing Python
- Remotion MCP integration
- FFmpeg tools for AI agents

## Best Entry Points

- `README.md` - install, quick start, tools, CLI, Python client.
- `llms.txt` - compact machine-readable project map.
- `mcp_video/server.py` - MCP tool registration layer.
- `mcp_video/engine.py` - core FFmpeg operations.
- `mcp_video/client.py` - Python client.
- `mcp_video/__main__.py` - CLI.
- `server.json` - MCP Registry metadata for the PyPI package.
- `CONTRIBUTING.md` - contribution and testing rules.
- `SECURITY.md` - private vulnerability reporting.

## Agent-Friendly Install Snippets

Claude Code:

```bash
claude mcp add mcp-video -- uvx mcp-video
```

Claude Desktop:

```json
{
  "mcpServers": {
    "mcp-video": {
      "command": "uvx",
      "args": ["mcp-video"]
    }
  }
}
```

Cursor:

```json
{
  "mcpServers": {
    "mcp-video": {
      "command": "uvx",
      "args": ["mcp-video"]
    }
  }
}
```

## What Agents Should Not Do

- Do not interpolate user strings directly into FFmpeg filter strings.
- Do not add generated media or local workspace artifacts to git.
- Do not break existing MCP tool signatures.
- Do not move business logic into `server.py`; keep it in engine modules.
- Do not add dependencies just to wrap a single command.

## Registry And Directory Targets

High-leverage listing targets:

- Official MCP Registry — metadata in `server.json` at the repo root, ready for submission via `npx @anthropic-ai/mcp-registry publish`. Identifier: `io.github.pastorsimon1798/mcp-video`.
- [Glama MCP Registry](https://glama.ai/mcp/servers) — Submit via GitHub repo URL.
- [Smithery](https://smithery.ai) — `npx @anthropic-ai/mcp-registry publish`.
- [MCP.so](https://mcp.so) — Submit via GitHub repo URL.
- [Awesome MCP Servers](https://github.com/punkpeye/awesome-mcp-servers) — Submit via PR.
- GitHub topics for `mcp`, `mcp-server`, `ffmpeg`, `video-editing`, `ai-agents`.

## Measurement

Track:

- GitHub stars and forks.
- PyPI downloads.
- GitHub Pages traffic.
- Issues opened by real users.
- Discussion posts and show-and-tell examples.
- Mentions in MCP directories and AI answer results.
- MCP Registry publication status for `io.github.pastorsimon1798/mcp-video`.
