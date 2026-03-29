# MCP-Video Feedback & Improvement Suggestions

**Date:** 2026-03-27  
**Context:** Used for Cerafica product video processing (Instagram + Website pipeline)  
**Version Tested:** 0.5.0

---

## Executive Summary

MCP-Video is excellent for AI agent video editing. These suggestions would make it production-ready for professional workflows like Cerafica's multi-platform content pipeline.

---

## 🔴 HIGH PRIORITY

### 1. Multi-Overlay Composite API

**Problem:** Adding the "Cerafica Exploration Log" UI required 5 separate operations:
1. Add header text
2. Add product name text  
3. Extract frames → create zoom panel image
4. Overlay zoom panels (watermark)
5. Overlay logo (watermark)

Each step re-encodes the video, losing quality and taking time.

**Suggested API:**
```python
client.composite(
    video="input.mp4",
    overlays=[
        {
            "type": "text",
            "text": "Cerafica Exploration Log",
            "position": "top-left",
            "size": 32,
            "color": "cyan",
            "start_time": 0,
            "duration": "full"
        },
        {
            "type": "text", 
            "text": "Product-Name",
            "position": "top-right",
            "size": 28,
            "color": "white"
        },
        {
            "type": "image",
            "image": "zoom-panels.png",
            "position": "top-right",
            "margin": [10, 80, 0, 0]  # x, y from position anchor
        },
        {
            "type": "image",
            "image": "logo.png", 
            "position": "bottom-right",
            "opacity": 0.9
        }
    ],
    output="output.mp4",
    quality="high"  # or bitrate/CRF setting
)
```

**Impact:** Reduces 5 steps → 1 step, single re-encode, faster, higher quality.

---

### 2. Quality Preservation / Lossless Options

**Problem:** Every `convert`, `watermark`, `add_text` operation re-encodes with default settings. Going from Instagram's high-quality source (17MB) to processed resulted in noticeable quality loss.

**Current:**
```python
client.add_text(video="input.mp4", output="output.mp4", ...)  # Re-encodes
client.watermark(video="output.mp4", output="final.mp4", ...)  # Re-encodes again
```

**Suggested:**
```python
# Option 1: Copy codec when possible (for format/container changes only)
client.convert(
    video="input.mp4",
    output="output.mp4", 
    codec="copy"  # No re-encode
)

# Option 2: Quality presets
client.add_text(
    video="input.mp4",
    output="output.mp4",
    quality="lossless"  # or "high", "web", "draft"
)

# Option 3: Explicit bitrate/CRF control
client.add_text(
    video="input.mp4",
    output="output.mp4",
    crf=18,  # x264/x265 CRF (lower = better)
    preset="slow"  # Encoding preset
)
```

---

### 3. Zoom Panel / Image Grid Generation

**Problem:** Creating the 3-panel zoom detail view required manual PIL operations:
- Extract frames at timestamps
- Crop to square
- Resize
- Add borders
- Combine vertically
- Label each panel

**Suggested API:**
```python
client.create_zoom_panels(
    video="input.mp4",
    timestamps=[2.0, 4.0, 6.0],
    panel_size=(200, 200),
    crop_from="center",  # or "auto" to detect subject
    border={
        "width": 2,
        "color": "cyan",
        "margin": 10
    },
    labels=["zoom-1", "zoom-2", "zoom-3"],
    layout="vertical",  # or "horizontal", "grid"
    output="panels.png"
)
```

---

## 🟡 MEDIUM PRIORITY

### 4. Pixel/Percentage-Based Positioning

**Problem:** Position options are limited to `"top-left"`, `"top-right"`, etc. Can't fine-tune placement.

**Current:**
```python
client.watermark(
    video="input.mp4",
    image="logo.png",
    position="bottom-right",  # Fixed position
    margin=20  # Single margin value
)
```

**Suggested:**
```python
client.watermark(
    video="input.mp4",
    image="logo.png",
    position=(100, 50),  # x, y pixels from top-left
    # OR
    position=(0.85, 0.9),  # percentage of video width/height
    anchor="bottom-right",  # anchor point of the overlay itself
)
```

---

### 5. Batch Processing API

**Problem:** Processing multiple videos requires Python loops.

**Suggested:**
```python
client.batch(
    videos=["vid1.mp4", "vid2.mp4", "vid3.mp4"],
    operation="add_text",
    params={
        "text": "Cerafica Exploration Log",
        "position": "top-left",
        "color": "cyan"
    },
    output_pattern="{name}_branded.mp4",
    parallel=True,  # Process in parallel
    max_workers=4
)
```

---

### 6. Preview / Dry-Run Mode

**Problem:** Had to process full 10-second videos to see results. Slow iteration.

**Suggested:**
```python
# Process only first 2 seconds for quick preview
client.add_text(
    video="input.mp4",
    output="preview.mp4",
    text="Test",
    preview=True,  # or preview_duration=2.0
)
```

---

### 7. Parameter Naming Consistency

**Problem:** Inconsistent parameter names across methods:
- `Client.add_text(video=...)` - uses `video`
- `Client.overlay_video(background=..., overlay=...)` - uses `background`/`overlay`
- `Client.thumbnail(timestamp=...)` - uses `timestamp`

**Suggested:** Standardize on:
- `input` or `source` for primary video
- `time` instead of `timestamp` (shorter)

---

## 🟢 LOW PRIORITY

### 8. Return Object Consistency

**Problem:** Different methods return different result types with different attributes.

**Observed:**
- `add_text()` → `EditResult` (has `success`, `output_path`, `duration`)
- `thumbnail()` → `ThumbnailResult` (different attributes)
- `info()` → `VideoInfo` (different structure)

**Suggested:** All results should have:
```python
result.success        # bool
result.output_path    # str or None
result.duration       # float (video duration)
result.resolution     # str (e.g., "1920x1080")
result.size_mb        # float
result.operation      # str (what was done)
result.error_message  # str or None
```

---

### 9. RGBA/PIL Compatibility

**Problem:** PIL RGBA images can't be saved as JPEG directly.

**Current Error:**
```
OSError: cannot write mode RGBA as JPEG
```

**Suggested:** Auto-convert RGBA→RGB when saving to JPEG formats, or provide clear error message.

---

### 10. Extract Frame at Specific Time

**Problem:** `thumbnail()` method name is unclear for extracting frames.

**Suggested:** Add alias:
```python
client.extract_frame(video="input.mp4", time=2.5, output="frame.jpg")
# Alias for: client.thumbnail(video="input.mp4", timestamp=2.5, output="frame.jpg")
```

---

## Real-World Use Case: Cerafica Pipeline

Current workflow with 11 products:

```python
# Without composite API - 55 operations, 55 re-encodes
for product in products:
    add_text(header)      # 1
    add_text(name)        # 2
    create_panels()       # 3-7 (extract, crop, combine)
    watermark(panels)     # 8
    watermark(logo)       # 9

# With composite API - 11 operations, 11 re-encodes
for product in products:
    composite(all_overlays)  # 1
```

**Time saved:** ~80% reduction in processing time  
**Quality:** Higher (single encode vs 5 encodes)  
**Code:** 60% less code

---

## Integration Wishlist

For the Cerafica Instagram + Website pipeline:

1. **Remotion Integration**: Generate videos from React components, then use mcp-video for final output/optimization
2. **Blender MCP**: 3D vessel rotation (photorealistic) instead of filmed footage
3. **Image Analysis MCP**: Auto-extract glaze colors, generate descriptions

---

## Summary Table

| Priority | Feature | Impact | Est. Effort |
|----------|---------|--------|-------------|
| 🔴 | Multi-overlay composite | **Critical** - 80% time savings | Medium |
| 🔴 | Quality preservation | **Critical** - Professional output | Low |
| 🔴 | Zoom panel generation | **High** - Common use case | Medium |
| 🟡 | Better positioning | **Medium** - More flexibility | Low |
| 🟡 | Batch processing | **Medium** - Nice to have | Low |
| 🟡 | Preview mode | **Medium** - Dev experience | Low |
| 🟢 | Param consistency | **Low** - Code cleanup | Low |
| 🟢 | Result consistency | **Low** - API polish | Low |

---

## Overall Assessment

**MCP-Video is excellent for AI agents.** The API is clean, error messages are helpful, and it integrates well with Claude Code. These improvements would make it production-ready for professional video workflows.

**Top 3 to implement:**
1. Multi-overlay composite (biggest impact)
2. Quality/bitrate control (professional requirement)
3. Zoom panel helper (Cerafica-specific but common pattern)
