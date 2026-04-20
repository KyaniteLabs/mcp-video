#!/usr/bin/env python3
"""
YouTube Shorts Workflow Example for mcp-video.

Demonstrates how to use the mcp-video Python client to create a YouTube Short
from a longer video. The workflow:
  1. Trim a highlight clip
  2. Resize to 9:16 vertical format
  3. Add animated captions
  4. Normalize audio for social media
  5. Export the final short

Requirements:
  - mcp-video server running and accessible
  - mcp_video Python client installed

Usage:
  python3 shorts_workflow.py

Replace placeholder paths with your actual file paths before running.
"""

import asyncio
import os

from mcp_video.client import MCPVideoClient  # hypothetical client; adapt to actual SDK

# ---------------------------------------------------------------------------
# Configuration -- replace these with your actual paths and preferences
# ---------------------------------------------------------------------------
INPUT_VIDEO = "/videos/my_long_video.mp4"
OUTPUT_DIR = "/output"
CLIP_START = "2:15"       # Timestamp where the highlight begins
CLIP_DURATION = "45"      # Duration in seconds (YouTube Shorts max: 60s)
CAPTION_TEXT = "This changes everything."
CAPTION_START = 2.0       # Seconds into the clip to show caption
CAPTION_DURATION = 5.0    # How long the caption stays on screen
LOGO_PATH = "/assets/logo.png"
TARGET_LUFS = -14         # Target loudness for TikTok/Shorts (-14 LUFS)


async def main() -> None:
    client = MCPVideoClient()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ------------------------------------------------------------------
    # Step 1: Trim the highlight segment from the longer video.
    # We extract a 45-second clip starting at the 2:15 mark.
    # Keeping Shorts under 60 seconds maximizes completion rate.
    # ------------------------------------------------------------------
    print("[1/5] Trimming highlight segment...")
    trimmed = await client.video_trim(
        input_path=INPUT_VIDEO,
        start=CLIP_START,
        duration=CLIP_DURATION,
        output_path=os.path.join(OUTPUT_DIR, "short_trimmed.mp4"),
    )
    print(f"   -> {trimmed.get('output_path')}")

    # ------------------------------------------------------------------
    # Step 2: Resize to 9:16 vertical format for Shorts.
    # YouTube Shorts require a vertical aspect ratio. The tool handles
    # center-cropping to keep the subject in frame.
    # ------------------------------------------------------------------
    print("[2/5] Resizing to 9:16 vertical format...")
    resized = await client.video_resize(
        input_path=trimmed["output_path"],
        aspect_ratio="9:16",
        quality="high",
        output_path=os.path.join(OUTPUT_DIR, "short_vertical.mp4"),
    )
    print(f"   -> {resized.get('output_path')}")

    # ------------------------------------------------------------------
    # Step 3: Add animated caption overlay.
    # Bold animated text in the center of the screen is the standard
    # Shorts pattern. The typewriter animation draws the eye.
    # ------------------------------------------------------------------
    print("[3/5] Adding animated caption...")
    captioned = await client.video_text_animated(
        input_path=resized["output_path"],
        text=CAPTION_TEXT,
        animation="typewriter",
        font="Arial Black",
        size=42,
        color="#FFFFFF",
        position="center",
        start=CAPTION_START,
        duration=CAPTION_DURATION,
        output_path=os.path.join(OUTPUT_DIR, "short_captioned.mp4"),
    )
    print(f"   -> {captioned.get('output_path')}")

    # ------------------------------------------------------------------
    # Step 4: Normalize audio levels.
    # Social platforms apply their own loudness normalization. Setting
    # to -14 LUFS ensures your audio does not get crushed or seem too
    # quiet after platform processing.
    # ------------------------------------------------------------------
    print("[4/5] Normalizing audio to -14 LUFS...")
    normalized = await client.video_normalize_audio(
        input_path=captioned["output_path"],
        target_lufs=TARGET_LUFS,
        output_path=os.path.join(OUTPUT_DIR, "short_normalized.mp4"),
    )
    print(f"   -> {normalized.get('output_path')}")

    # ------------------------------------------------------------------
    # Step 5: Export the final video.
    # High quality MP4 is the safest format for upload to YouTube,
    # TikTok, and Instagram Reels.
    # ------------------------------------------------------------------
    print("[5/5] Exporting final Short...")
    final = await client.video_export(
        input_path=normalized["output_path"],
        format="mp4",
        quality="high",
        output_path=os.path.join(OUTPUT_DIR, "youtube_short_final.mp4"),
    )
    print(f"   -> {final.get('output_path')}")

    # ------------------------------------------------------------------
    # Bonus: Run a quality check on the final output.
    # Catches issues like audio clipping, low contrast, or dim brightness
    # before you upload. Fix with video_fix_design_issues if needed.
    # ------------------------------------------------------------------
    print("[bonus] Running quality check...")
    qc = await client.video_quality_check(
        input_path=final["output_path"],
    )
    if qc.get("passed"):
        print("   -> Quality check PASSED. Ready to upload!")
    else:
        print(f"   -> Quality issues found: {qc.get('issues')}")
        print("   -> Consider running video_fix_design_issues to auto-correct.")

    print("\nDone! Upload youtube_short_final.mp4 to YouTube Shorts.")


if __name__ == "__main__":
    asyncio.run(main())
