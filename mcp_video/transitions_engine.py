"""Video transition effects using FFmpeg."""

import os
import subprocess

from .errors import ProcessingError


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _run_ffmpeg(cmd: list[str], timeout: int = 600) -> subprocess.CompletedProcess[str]:
    """Run an FFmpeg/FFprobe command with timeout and error handling."""
    # Ensure output directory exists
    for arg in reversed(cmd):
        if not arg.startswith("-") and not arg.startswith("ffmpeg") and not arg.startswith("ffprobe"):
            out_dir = os.path.dirname(arg)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            break
    cmd_str = " ".join(cmd)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise ProcessingError(cmd_str, -1, f"FFmpeg command timed out after {timeout}s") from None
    if result.returncode != 0:
        raise ProcessingError(cmd_str, result.returncode, result.stderr)
    return result


def _get_video_duration(video_path: str) -> float:
    """Get video duration using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    result = _run_ffmpeg(cmd)
    return float(result.stdout.strip())


def transition_glitch(
    clip1: str,
    clip2: str,
    output: str,
    duration: float = 0.5,
    intensity: float = 0.3,
) -> str:
    """Glitch transition using RGB shift and noise.

    Args:
        clip1: First video clip path
        clip2: Second video clip path
        output: Output video path
        duration: Transition duration in seconds
        intensity: Glitch intensity 0-1

    Returns:
        Path to output video
    """
    # Get duration of first clip to calculate offset
    clip1_duration = _get_video_duration(clip1)
    offset = clip1_duration - duration

    # Ensure offset is not negative
    if offset < 0:
        offset = 0

    # Calculate intensity-based parameters
    # Intensity 0-1 maps to RGB shift of 0-20 pixels
    rgb_shift = int(intensity * 20)
    noise_amount = intensity * 0.1

    # Use rgbashift filter for RGB channel shifting
    # More reliable than geq which has complex escaping requirements
    filter_complex = (
        f"[0:v][1:v]xfade=transition=fade:duration={duration}:offset={offset}[faded];"
        f"[faded]rgbashift=rh={rgb_shift}:gh=0:bh=-{rgb_shift}:ah=0[rgbshift];"
        f"[rgbshift]noise=alls={noise_amount}:allf=t+u[glitched]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", clip1,
        "-i", clip2,
        "-filter_complex", filter_complex,
        "-map", "[glitched]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output
    ]

    _run_ffmpeg(cmd)

    return output


def transition_pixelate(
    clip1: str,
    clip2: str,
    output: str,
    duration: float = 0.4,
    pixel_size: int = 50,
) -> str:
    """Pixel dissolve transition using scale filter.

    Creates a transition where the video pixelates during the crossfade,
    with the pixelation peaking at the middle of the transition.

    Args:
        clip1: First video clip path
        clip2: Second video clip path
        output: Output video path
        duration: Transition duration in seconds
        pixel_size: Maximum pixel size during transition

    Returns:
        Path to output video
    """
    # Get duration of first clip to calculate offset
    clip1_duration = _get_video_duration(clip1)
    offset = clip1_duration - duration

    # Ensure offset is not negative
    if offset < 0:
        offset = 0

    # Calculate transition midpoint
    mid = offset + duration / 2

    # Build filter_complex using scale with eval=frame
    #
    # The pixelation effect:
    # 1. First scale down by factor N (creating pixelation)
    # 2. Then scale back up with neighbor flag (preserving blocky look)
    #
    # Scale factor N varies from 1 (no pixelation) to pixel_size (max pixelation)
    # Using cos curve centered on transition midpoint for smooth animation
    #
    # eval=frame is required to evaluate expressions per-frame using 't' variable

    # Build scale expressions that ensure dimensions stay even
    # Use trunc to round down to integer, then ensure it's at least 2 and even
    scale_w_expr = f"trunc(iw/max(1,min({pixel_size},1+({pixel_size}-1)*((1+cos((t-{mid})*PI/{duration}))/2)))/2)*2"
    scale_h_expr = f"trunc(ih/max(1,min({pixel_size},1+({pixel_size}-1)*((1+cos((t-{mid})*PI/{duration}))/2)))/2)*2"

    filter_complex = (
        f"[0:v][1:v]xfade=transition=fade:duration={duration}:offset={offset}[faded];"
        f"[faded]scale='{scale_w_expr}':'{scale_h_expr}':flags=neighbor:eval=frame,"
        f"scale=iw:ih:flags=neighbor[output]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", clip1,
        "-i", clip2,
        "-filter_complex", filter_complex,
        "-map", "[output]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output
    ]

    _run_ffmpeg(cmd)

    return output


def transition_morph(
    clip1: str,
    clip2: str,
    output: str,
    duration: float = 0.6,
    mesh_size: int = 10,
) -> str:
    """Mesh warp morph transition using pixelization effect.

    Creates a morph-like transition using FFmpeg's pixelize transition.
    The mesh_size parameter controls the intensity of the warp effect.

    Args:
        clip1: First video clip path
        clip2: Second video clip path
        output: Output video path
        duration: Transition duration in seconds
        mesh_size: Grid subdivisions (reserved for future warp intensity control)

    Returns:
        Path to output video
    """
    # Get duration of first clip to calculate offset
    clip1_duration = _get_video_duration(clip1)
    offset = clip1_duration - duration

    # Ensure offset is not negative
    if offset < 0:
        offset = 0

    # Use xfade with pixelize transition for morph-like effect
    # pixelize creates a blocky dissolve that simulates mesh morphing
    filter_complex = (
        f"[0:v][1:v]xfade=transition=pixelize:duration={duration}:offset={offset}[output]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", clip1,
        "-i", clip2,
        "-filter_complex", filter_complex,
        "-map", "[output]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output
    ]

    _run_ffmpeg(cmd)

    return output
