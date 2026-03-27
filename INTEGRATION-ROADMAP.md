# MCP-Video Integration Roadmap

**Created:** 2026-03-27
**Context:** Integration wishlist from Cerafica feedback — to be addressed after v0.6.0 improvements ship.

---

## 1. Blender MCP Integration — DEFERRED, NOT APPROVED

### Status: Ready to use (existing project)

**Project:** [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp)
- Socket-based bridge: Claude AI <-> Blender
- Supports Blender 3.0+ (including 4.x)
- Create, modify, delete 3D objects via natural language
- Scene creation, lighting, camera control, rendering
- Sketchfab integration for asset import
- Free addon, active development

### Setup Steps
1. Install Blender (latest stable)
2. Install the Blender MCP addon from GitHub releases
3. Configure socket connection in Claude Code MCP settings
4. Test with a simple object creation prompt

### Cerafica Pipeline
```
Blender MCP (3D vessel modeling + rotation animation)
  → Render to MP4 (Blender's render engine)
    → mcp-video (add text overlays, logo, export for Instagram/Web)
```

### Use Cases for Cerafica
- Photorealistic 3D vessel rotation instead of filmed footage
- Consistent lighting and backgrounds across all products
- Batch render 11 products with same camera angle/lighting
- Combine with mcp-video for branded output

### Skills Needed
- Create a Cerafica workflow skill that chains: Blender MCP → mcp-video
- No custom MCP development required

### Effort: 1-2 days (setup + workflow skill)

---

## 2. Image Analysis MCP — COMPLETED

### Status: Shipped in v0.7.0

Three image analysis tools built directly into mcp-video using scikit-learn K-means (already a dependency) and optional Claude Vision API for AI descriptions.

**Tools shipped:**
1. `image_extract_colors(image_path, n_colors=5)` — dominant colors with hex codes + percentages
2. `image_analyze_product(image_path, use_ai=False)` — color extraction + optional AI product description
3. `image_generate_palette(image_path, harmony="complementary")` — color harmony palette generation

**Architecture:**
```
Built into mcp-video server (no separate MCP server needed)
  ├── Color extraction (scikit-learn K-means) — FREE, LOCAL
  └── AI descriptions (Claude Vision API) — OPTIONAL, $0.15/image
```

**Pipeline Integration:**
```
mcp-video (video_export_frames)
  → Image Analysis tools (extract colors, descriptions)
    → mcp-video (use metadata in text overlays)
```

---

## 3. Remotion Integration — MEDIUM PRIORITY — APPROVED

### Status: Third-party template available as reference. Complementary to mcp-video.

### Available Reference Material

A third-party `script-to-animation` template exists at `~/Desktop/Interpreted-Context-Methdology/workspaces/script-to-animation`. It was downloaded (not built by us) and has never been configured or used.

**What it contains:**
- 60+ markdown files defining a 3-stage pipeline: Script → Spec → Build (Remotion components)
- A Remotion best-practices skill (35 rule files covering animations, sequencing, transitions, timing, etc.)
- A design aesthetics skill
- All `{{PLACEHOLDER}}` values are unfilled — brand, voice, audience, colors, fonts
- Targets TikTok/Reels (9:16), YouTube (16:9), YouTube Shorts (9:16)

### Complementary Relationship

**script-to-animation** and **mcp-video** are complementary, not competing:

| | script-to-animation | mcp-video |
|---|---|---|
| **Purpose** | Generate original video from scratch | Manipulate existing video |
| **Engine** | React/Remotion (programmatic animation) | FFmpeg (editing, overlays, export) |
| **Ecosystem** | Node.js/TypeScript | Python |
| **Best for** | Motion graphics, kinetic typography, data-driven templates | Post-processing, overlays, platform export |

**Pipeline:** `script-to-animation (generate) → mcp-video (polish/export)`

### Recommended Approach

1. **Reuse the Remotion skill** — the 35 rule files are high-quality reference material for animations, sequencing, transitions, and timing
2. **Adapt the build conventions** — project structure (composition → beats → constants → assets) is well-designed
3. **Skip the brand questionnaire** — configure for Cerafica or a specific use case when ready
4. **No custom MCP server needed** — Remotion renders via CLI, output feeds directly into mcp-video

### When to Build
- If you need complex motion graphics (animated transitions, kinetic typography)
- If you need to generate 100+ data-driven video variants from templates
- If clients request After Effects-style animations programmatically

### Effort: 5-10 days (Remotion project setup + template design + mcp-video pipeline integration)

---

## Summary

| Integration | Priority | Effort | Status | Approved | ROI |
|-------------|----------|--------|--------|---------|-----|
| Blender MCP | LOW | 1-2 days | Defer | No | Medium |
| Image Analysis | MEDIUM | 2-3 days | **Completed (v0.7.0)** | Yes | Medium |
| Remotion | MEDIUM | 5-10 days | Reference material available | Yes | Medium (later) |
