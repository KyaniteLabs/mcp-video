#!/usr/bin/env python3
"""Generate demo videos for explainer video scenes.

This script creates real feature demonstrations to replace the simulated/CSS
animations in the explainer video with actual video processing outputs.
"""

import os
import sys
import json
import tempfile
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mcp_video import Client

client = Client()
DEMO_DIR = Path("explainer-video/public/demos")
DEMO_DIR.mkdir(parents=True, exist_ok=True)


def create_sample_video(output_path: str, duration: float = 3.0, color: str = "red") -> str:
    """Create a simple colored test video."""
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"color=c={color}:s=640x480:d={duration}",
        "-f", "lavfi", "-i", f"sine=frequency=500:duration={duration}",
        "-c:v", "libx264", "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        output_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


def generate_stabilization_demo():
    """Generate shaky → stabilized demo.
    
    Note: Stabilization requires vidstab FFmpeg filter which may not be available.
    If unavailable, we'll create a simulated version with text overlay.
    """
    print("\n[Demo] Stabilization...")
    
    # Create a "shaky" video (simulated with moving text)
    shaky = DEMO_DIR / "stabilize_before.mp4"
    stable = DEMO_DIR / "stabilize_after.mp4"
    
    # Generate shaky video with jitter simulation
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", "color=c=0x1a1a2e:s=640x480:d=3",
        "-vf", "drawtext=text='BEFORE':fontsize=60:fontcolor=white:x='50+sin(t*10)*30':y='240+cos(t*8)*20'",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(shaky)
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    
    # Try to apply stabilization, fallback to stable version
    try:
        result = client.stabilize(str(shaky), output=str(stable))
        if os.path.exists(result.output_path):
            print(f"  ✓ Stabilization applied: {stable}")
            return
    except Exception as e:
        print(f"  ⚠ Stabilization unavailable: {e}")
    
    # Fallback: create stable version without jitter
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", "color=c=0x1a1a2e:s=640x480:d=3",
        "-vf", "drawtext=text='AFTER':fontsize=60:fontcolor=white:x=50:y=240",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(stable)
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    print(f"  ✓ Created stable demo: {stable}")


def generate_chroma_key_demo():
    """Generate green screen → keyed demo."""
    print("\n[Demo] Chroma Key...")
    
    green = DEMO_DIR / "chroma_before.mp4"
    keyed = DEMO_DIR / "chroma_after.mp4"
    
    # Create green screen video with subject
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", "color=c=00FF00:s=640x480:d=3",  # Green background
        "-vf", "drawtext=text='SUBJECT':fontsize=80:fontcolor=white:x=160:y=200:box=1:boxcolor=black@0.5",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(green)
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    
    # Apply chroma key - use engine directly since client method has issue
    try:
        from mcp_video.engine import chroma_key as _chroma_key
        result = _chroma_key(str(green), output_path=str(keyed), color="0x00FF00", similarity=0.2)
        if os.path.exists(result.output_path):
            print(f"  ✓ Chroma key applied: {keyed}")
    except Exception as e:
        print(f"  ⚠ Chroma key failed: {e}")
        # Fallback: create keyed version manually
        cmd = [
            "ffmpeg", "-y", "-i", str(green),
            "-vf", "chromakey=0x00FF00:0.2:0.1,color=c=black:s=640x480[d];[d]drawtext=text='KEYED':fontsize=80:fontcolor=white:x=160:y=200",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            str(keyed)
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        print(f"  ✓ Created keyed demo: {keyed}")


def generate_effect_demos():
    """Generate effect preview videos."""
    print("\n[Demo] Visual Effects...")
    
    # Create source video
    source = DEMO_DIR / "effect_source.mp4"
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", "color=c=0x533483:s=640x480:d=2",
        "-vf", "drawtext=text='EFFECTS':fontsize=80:fontcolor=white:x=160:y=200",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(source)
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    
    effects = [
        ("vignette", lambda s, o: client.effect_vignette(s, o, intensity=0.7)),
        ("chromatic", lambda s, o: client.effect_chromatic_aberration(s, o, intensity=4.0)),
        ("noise", lambda s, o: client.effect_noise(s, o, intensity=0.08)),
        ("glow", lambda s, o: client.effect_glow(s, o, intensity=0.6)),
    ]
    
    for name, effect_fn in effects:
        output = DEMO_DIR / f"effect_{name}.mp4"
        try:
            result = effect_fn(str(source), str(output))
            if os.path.exists(result):
                print(f"  ✓ {name}: {output.name}")
            else:
                print(f"  ⚠ {name}: output not created")
        except Exception as e:
            print(f"  ⚠ {name}: {e}")


def generate_transition_demos():
    """Generate transition preview videos."""
    print("\n[Demo] Transitions...")
    
    # Create two clips
    clip1 = DEMO_DIR / "trans_clip1.mp4"
    clip2 = DEMO_DIR / "trans_clip2.mp4"
    
    for clip, color, text in [(clip1, "red", "CLIP 1"), (clip2, "blue", "CLIP 2")]:
        cmd = [
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"color=c={color}:s=640x480:d=1.5",
            "-vf", f"drawtext=text='{text}':fontsize=80:fontcolor=white:x=160:y=200",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            str(clip)
        ]
        subprocess.run(cmd, capture_output=True, check=True)
    
    transitions = [
        ("glitch", lambda c1, c2, o: client.transition_glitch(c1, c2, o, duration=0.5)),
        ("pixelate", lambda c1, c2, o: client.transition_pixelate(c1, c2, o, duration=0.4)),
        ("morph", lambda c1, c2, o: client.transition_morph(c1, c2, o, duration=0.6)),
    ]
    
    for name, trans_fn in transitions:
        output = DEMO_DIR / f"trans_{name}.mp4"
        try:
            result = trans_fn(str(clip1), str(clip2), str(output))
            if os.path.exists(result):
                print(f"  ✓ {name}: {output.name}")
        except Exception as e:
            print(f"  ⚠ {name}: {e}")


def generate_ai_demo_data():
    """Generate AI feature demo data/images."""
    print("\n[Demo] AI Features...")
    
    # Use the existing explainer video for AI demos
    test_video = TEST_VIDEOS.get('explainer')
    if not test_video or not os.path.exists(test_video):
        print("  ⚠ No test video available")
        return
    
    # Scene detection
    try:
        scenes = client.ai_scene_detect(test_video, threshold=0.3)
        # Save scene data as JSON
        scene_data = [{"time": s.get('time', 0), "confidence": s.get('confidence', 0)} for s in scenes[:10]]
        with open(DEMO_DIR / "ai_scenes.json", "w") as f:
            json.dump(scene_data, f)
        print(f"  ✓ Scene detection: {len(scenes)} scenes")
    except Exception as e:
        print(f"  ⚠ Scene detection: {e}")
    
    # Color extraction from frame
    try:
        frame_path = DEMO_DIR / "ai_frame.png"
        client.extract_frame(test_video, timestamp=10.0, output=str(frame_path))
        colors = client.extract_colors(str(frame_path), n_colors=5)
        print(f"  ✓ Color extraction: {len(colors.colors)} colors")
    except Exception as e:
        print(f"  ⚠ Color extraction: {e}")


def generate_quality_demo():
    """Generate quality check demo data."""
    print("\n[Demo] Quality Check...")
    
    test_video = TEST_VIDEOS.get('explainer')
    if not test_video or not os.path.exists(test_video):
        print("  ⚠ No test video available")
        return
    
    try:
        # Run design quality check
        result = client.design_quality_check(test_video)
        
        # Save quality data
        quality_data = {
            "overall_score": getattr(result, 'overall_score', 0),
            "technical_score": getattr(result, 'technical_score', 0),
            "design_score": getattr(result, 'design_score', 0),
            "issues_count": len(getattr(result, 'issues', [])),
        }
        with open(DEMO_DIR / "quality_data.json", "w") as f:
            json.dump(quality_data, f)
        print(f"  ✓ Quality check: {quality_data['overall_score']:.1f}/100")
    except Exception as e:
        print(f"  ⚠ Quality check: {e}")


TEST_VIDEOS = {
    'explainer': 'out/McpVideoExplainer-FINAL.mp4',
}


def main():
    """Generate all demo videos and data."""
    
    print("=" * 60)
    print("GENERATING EXPLAINER VIDEO DEMOS")
    print("=" * 60)
    print(f"Output directory: {DEMO_DIR}")
    
    generate_stabilization_demo()
    generate_chroma_key_demo()
    generate_effect_demos()
    generate_transition_demos()
    generate_ai_demo_data()
    generate_quality_demo()
    
    print("\n" + "=" * 60)
    print("DEMO GENERATION COMPLETE")
    print("=" * 60)
    
    # List generated files
    files = sorted(DEMO_DIR.glob("*"))
    print(f"\nGenerated {len(files)} demo files:")
    for f in files:
        size = f.stat().st_size / 1024
        unit = "KB" if size < 1024 else "MB"
        size = size if size < 1024 else size / 1024
        print(f"  {f.name:30} {size:6.1f} {unit}")


if __name__ == "__main__":
    main()
