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

## 2. Image Analysis MCP — HIGH PRIORITY - APPROVED

### Status: Build thin wrapper (recommended approach)

### Option A: Build Custom (Recommended)
**Why:** scikit-image already installed in mcp-video deps, zero additional cost for color extraction.

**Architecture:**
```
Thin MCP server (Python)
  ├── Color extraction (scikit-image K-means) — FREE, LOCAL
  └── AI descriptions (Claude Vision API) — OPTIONAL, $0.15/image
```

**Tools to build:**
1. `extract_colors(image_path, n_colors=5)` — dominant colors with hex codes + percentages
2. `analyze_product(image_path, use_ai=False)` — color + optional AI description
3. `generate_palette(image_path, harmony="complementary")` — color scheme suggestions

**Dependencies:** scikit-image (already installed), webcolors (already installed), optional anthropic SDK

**Pipeline Integration:**
```
mcp-video (video_export_frames)
  → Image Analysis MCP (extract colors, descriptions)
    → mcp-video (use metadata in text overlays)
```

### Option B: Use Existing Servers
- `2squirrelsai/local-mcp-image-analysis-server` — local color analysis, no AI
- `mario-andreschak/mcp-image-recognition` — Claude/GPT-4 Vision wrapper

### Cerafica Use Cases
- Auto-extract glaze colors from product videos
- Generate product descriptions for e-commerce
- Color-match UI overlays to product colors

### Effort: 2-3 days (thin wrapper + optional AI layer)

---

## 3. Remotion Integration — High Priority - Approved - also investigate a workspace inside ICM called [text](../../Desktop/Interpreted-Context-Methdology/workspaces/script-to-animation)
  
### Status: No existing MCP server. Evaluate after v0.6.0 ships.

### What Remotion Does
- React-based programmatic video creation
- Render React components to MP4/WebM
- Server-side rendering via CLI or Lambda
- Strong for: templated videos, data-driven content, motion graphics

### Why Defer
1. The `video_edit` timeline improvements (v0.6.0) may cover most overlay/compositing needs
2. Remotion requires Node.js/TypeScript — separate ecosystem from mcp-video (Python)
3. Building a `remotion-mcp` server is a significant new project
4. For Cerafica's current needs (text + image overlays on product videos), mcp-video is sufficient

### When to Reconsider
- If you need complex motion graphics (animated transitions, kinetic typography)
- If you need to generate 100+ data-driven video variants from templates
- If clients request After Effects-style animations programmatically

### If Built Later
1. Create `remotion-mcp` as separate TypeScript MCP server
2. Define React video templates (Cerafica brand, product cards, etc.)
3. Pipeline: Data → Remotion MCP (render) → mcp-video (final export)

### Effort: 5-10 days (new project + template design + testing)

---

## Summary

| Integration | Priority | Effort | Status | Approved | ROI |
|-------------|----------|--------|--------|---------|-----|
| Blender MCP | LOW | 1-2 days | Defer | No | Medium |
| Image Analysis | MEDIUM | 2-3 days | Build wrapper | Yes | Medium |
| Remotion | LOW | 5-10 days | Defer | Yes | Medium (later) |
