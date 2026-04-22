#!/usr/bin/env python3
"""
Explainer Video Workflow for mcp-video.

Builds a branded explainer video from scratch using synthesized audio, scenes,
effects, and transitions — using only mcp-video client methods.

Usage:
    python workflow.py

The script runs 7 stages and outputs the final video to output/final_video.mp4.
"""

import os

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:
    raise ImportError("Pillow is required for the explainer workflow. Install it with: pip install Pillow") from exc

from mcp_video import Client

client = Client()

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)
TMP_DIR = os.path.join(OUTPUT_DIR, "tmp")
os.makedirs(TMP_DIR, exist_ok=True)

SCENES = [
    {"color": "#1a1a2e", "text": "Meet mcp-video", "duration": 5},
    {"color": "#16213e", "text": "Edit video with AI agents", "duration": 5},
    {"color": "#0f3460", "text": "81 MCP tools at your command", "duration": 5},
    {"color": "#533483", "text": "Built on FFmpeg + Remotion", "duration": 5},
]

FPS = 30
WIDTH, HEIGHT = 1920, 1080


def _load_font(size: int):
    """Try common system fonts across platforms, fallback to default."""
    candidates = [
        "/System/Library/Fonts/Helvetica.ttc",  # macOS
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
        "C:/Windows/Fonts/arial.ttf",  # Windows
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _create_scene_image(color: str, text: str, output: str) -> str:
    """Create a branded scene image using Pillow."""
    img = Image.new("RGB", (WIDTH, HEIGHT), color)
    draw = ImageDraw.Draw(img)
    font = _load_font(64)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (WIDTH - text_w) // 2
    y = (HEIGHT - text_h) // 2
    draw.rectangle(
        [x - 20, y - 10, x + text_w + 20, y + text_h + 10],
        fill="black",
    )
    draw.text((x, y), text, fill="white", font=font)
    img.save(output)
    return output


def _stage_soundtrack() -> str:
    print("\n[1/7] Generating soundtrack...")
    drone = client.audio_preset(
        "drone-tech",
        os.path.join(TMP_DIR, "drone.wav"),
        duration=20,
        intensity=0.4,
    )
    chime = client.audio_preset(
        "chime-success",
        os.path.join(TMP_DIR, "chime.wav"),
        intensity=0.6,
    )
    soundtrack = client.audio_compose(
        tracks=[
            {"file": drone, "volume": 0.3, "start": 0},
            {"file": chime, "volume": 0.8, "start": 0},
            {"file": chime, "volume": 0.8, "start": 5},
            {"file": chime, "volume": 0.8, "start": 10},
            {"file": chime, "volume": 0.8, "start": 15},
        ],
        duration=20,
        output=os.path.join(OUTPUT_DIR, "01_soundtrack.wav"),
    )
    print(f"   -> {soundtrack}")
    return soundtrack


def _stage_scenes() -> list[str]:
    print("\n[2/7] Creating scene videos...")
    scene_clips = []
    for i, scene in enumerate(SCENES):
        img_path = os.path.join(TMP_DIR, f"scene_{i:02d}.png")
        _create_scene_image(scene["color"], scene["text"], img_path)
        frame_count = int(scene["duration"] * FPS)
        images = [img_path] * frame_count
        video_path = os.path.join(TMP_DIR, f"scene_{i:02d}.mp4")
        result = client.create_from_images(images, output=video_path, fps=FPS)
        scene_clips.append(result.output_path)
        print(f"   -> {result.output_path}")
    return scene_clips


def _stage_effects(scene_clips: list[str]) -> list[str]:
    print("\n[3/7] Applying effects...")
    fx_clips = []
    for i, clip in enumerate(scene_clips):
        out = os.path.join(TMP_DIR, f"scene_{i:02d}_fx.mp4")
        if i % 2 == 0:
            client.effect_vignette(clip, out, intensity=0.4)
        else:
            client.effect_glow(clip, out, intensity=0.3)
        fx_clips.append(out)
        print(f"   -> {out}")
    return fx_clips


def _stage_transitions(fx_clips: list[str]) -> list[str]:
    print("\n[4/7] Creating transitions...")
    transition_clips = []
    for i in range(len(fx_clips) - 1):
        out = os.path.join(TMP_DIR, f"transition_{i:02d}.mp4")
        if i % 3 == 0:
            client.transition_glitch(fx_clips[i], fx_clips[i + 1], out, duration=0.5)
        elif i % 3 == 1:
            client.transition_pixelate(fx_clips[i], fx_clips[i + 1], out, duration=0.5)
        else:
            client.transition_morph(fx_clips[i], fx_clips[i + 1], out, duration=0.5)
        transition_clips.append(out)
        print(f"   -> {out}")
    return transition_clips


def _stage_assemble(fx_clips: list[str]) -> str:
    print("\n[5/7] Assembling scenes with transitions...")
    assembled = client.merge(
        clips=fx_clips,
        output=os.path.join(OUTPUT_DIR, "05_assembled.mp4"),
        transitions=["fade", "pixelize", "dissolve"],
        transition_duration=0.5,
    )
    print(f"   -> {assembled.output_path}")
    return assembled.output_path


def _stage_audio_mix(video: str, soundtrack: str) -> str:
    print("\n[6/7] Mixing audio...")
    mixed = client.add_audio(
        video=video,
        audio=soundtrack,
        mix=True,
        volume=0.8,
        output=os.path.join(OUTPUT_DIR, "06_mixed.mp4"),
    )
    print(f"   -> {mixed.output_path}")
    return mixed.output_path


def _stage_export(video: str) -> str:
    print("\n[7/7] Exporting final video...")
    final = client.convert(
        video,
        format="mp4",
        quality="high",
        output=os.path.join(OUTPUT_DIR, "final_video.mp4"),
    )
    print(f"   -> {final.output_path}")
    return final.output_path


def main() -> None:
    print("=" * 60)
    print("03-explainer-video workflow")
    print("=" * 60)

    soundtrack = _stage_soundtrack()
    scene_clips = _stage_scenes()
    fx_clips = _stage_effects(scene_clips)
    _stage_transitions(fx_clips)
    assembled = _stage_assemble(fx_clips)
    mixed = _stage_audio_mix(assembled, soundtrack)
    _stage_export(mixed)

    print("\n" + "=" * 60)
    print("Workflow complete! Review output/final_video.mp4")
    print("=" * 60)


if __name__ == "__main__":
    main()
