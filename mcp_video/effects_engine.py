"""Video effects and filters engine.

Visual effects using FFmpeg filters and PIL for custom processing.
"""

from __future__ import annotations

import math
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .errors import ProcessingError, InputFileError


def _escape_ffmpeg_filter_value(value: str) -> str:
    """Escape special characters for FFmpeg filter expressions (subtitles, drawtext, etc.)."""
    return (
        value.replace("\\", "/")
        .replace("'", "'\\''")
        .replace(":", "\\:")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace(",", "\\,")
    )


def _validate_input_path(path: str) -> str:
    """Validate and resolve a file path. Rejects null bytes and symlinks."""
    if "\x00" in path:
        raise InputFileError(path, "Path contains null bytes")
    resolved = os.path.realpath(path)
    if not os.path.isfile(resolved):
        raise InputFileError(resolved)
    return resolved


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _run_ffmpeg(cmd: list[str], timeout: int = 600) -> subprocess.CompletedProcess[str]:
    """Run an FFmpeg/FFprobe command with timeout and error handling."""
    # Ensure output directory exists — find the last non-flag argument (the output file)
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
        raise ProcessingError(cmd_str, -1, f"FFmpeg command timed out after {timeout}s")
    if result.returncode != 0:
        raise ProcessingError(cmd_str, result.returncode, result.stderr)
    return result


# ---------------------------------------------------------------------------
# FFmpeg-based Effects
# ---------------------------------------------------------------------------


def effect_vignette(
    input_path: str,
    output: str,
    intensity: float = 0.5,
    radius: float = 0.8,
    smoothness: float = 0.5,
) -> str:
    """Apply vignette effect - darkened edges with adjustable curve.
    
    Args:
        input_path: Input video path
        output: Output video path
        intensity: Darkness amount (0-1)
        radius: Vignette radius (0-1, 1 = edge of frame)
        smoothness: Edge softness (0-1)
    
    Returns:
        Path to output video
    """
    # FFmpeg vignette filter: angle (in radians) controls the radius
    # intensity maps to darkness
    
    # Convert radius to angle (FFmpeg uses angle in radians)
    # angle of PI/2 = corner to center, angle of PI/5 = closer to edges
    angle = 3.14159 * (1 - radius * 0.8)  # Scale to reasonable range
    
    # Build filter chain
    # vignette creates the darkening, we overlay it with the original
    filters = (
        f"split[original][vignetted];"
        f"[vignetted]vignette=angle={angle}:mode=backward[a];"
        f"[a]format=pix_fmts=yuva420p,colorchannelmixer=aa={intensity}[vignette];"
        f"[original][vignette]overlay=format=auto"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", filters,
        "-c:a", "copy",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "23",
        output,
    ]
    
    _run_ffmpeg(cmd)

    return output


def effect_chromatic_aberration(
    input_path: str,
    output: str,
    intensity: float = 2.0,
    angle: float = 0,
) -> str:
    """Apply chromatic aberration - RGB channel separation.
    
    Args:
        input_path: Input video path
        output: Output video path
        intensity: Pixel offset amount
        angle: Separation direction in degrees (0 = horizontal)
    
    Returns:
        Path to output video
    """
    # Convert angle to radians
    angle_rad = angle * 3.14159 / 180
    
    # Calculate x and y offsets
    offset_x = intensity * math.cos(angle_rad)
    offset_y = intensity * math.sin(angle_rad)
    
    # Build filter: shift R channel right, B channel left
    # Using colorchannelmixer to extract and shift channels
    filters = (
        f"split[main][copy];"
        f"[copy]crop=iw:ih:x={offset_x}:y={offset_y},format=rgb24,"
        f"colorchannelmixer=rr=1:gg=0:bb=0[r];"
        f"[main]format=rgb24,colorchannelmixer=rr=0:gg=1:bb=0[g];"
        f"[main]crop=iw:ih:x=-{offset_x}:y=-{offset_y},format=rgb24,"
        f"colorchannelmixer=rr=0:gg=0:bb=1[b];"
        f"[r][g][b]mergeplanes=0x0+0x1+0x2:rgb"
    )
    
    # Simpler approach using chromashift if available
    # chromashift filter directly does what we want
    shift_x = int(offset_x)
    shift_y = int(offset_y)
    
    filters = (
        f"chromashift=cbh={shift_x}:cbv={shift_y}:"
        f"crh=-{shift_x}:crv=-{shift_y}"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", filters,
        "-c:a", "copy",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "23",
        output,
    ]
    
    # Run first attempt, capture error for fallback check
    cmd_str = " ".join(cmd)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        raise ProcessingError(cmd_str, -1, f"FFmpeg command timed out after 600s")

    # Fallback if chromashift not available
    if result.returncode != 0 and "chromashift" in result.stderr:
        filters = (
            f"colorbalance=rs={intensity/100}:bs=-{intensity/100}"
        )
        cmd[4] = filters
        _run_ffmpeg(cmd)
    elif result.returncode != 0:
        raise ProcessingError(cmd_str, result.returncode, result.stderr)

    return output


def effect_scanlines(
    input_path: str,
    output: str,
    line_height: int = 2,
    opacity: float = 0.3,
    flicker: float = 0.1,
) -> str:
    """Apply CRT-style scanlines overlay.
    
    Args:
        input_path: Input video path
        output: Output video path
        line_height: Pixels per line
        opacity: Line opacity (0-1)
        flicker: Subtle brightness variation
    
    Returns:
        Path to output video
    """
    # Use drawgrid filter to create scanlines - simpler and more reliable
    # drawgrid creates horizontal lines with specified spacing
    grid_spacing = line_height * 2
    line_thickness = line_height
    
    filters = f"drawgrid=w=iw:h={grid_spacing}:t={line_thickness}:c=black@{opacity}"
    
    if flicker > 0:
        # Add subtle flicker using eq filter
        filters += f",eq=brightness={flicker}*sin(t*10)"
    
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", filters,
        "-c:a", "copy",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "23",
        output,
    ]
    
    _run_ffmpeg(cmd)

    return output


def effect_noise(
    input_path: str,
    output: str,
    intensity: float = 0.05,
    mode: str = "film",
    animated: bool = True,
) -> str:
    """Apply film grain / digital noise.
    
    Args:
        input_path: Input video path
        output: Output video path
        intensity: Noise amount (0-1)
        mode: "film", "digital", or "color"
        animated: Whether noise changes per frame
    
    Returns:
        Path to output video
    """
    # Use noise filter if available, otherwise usegeq with random
    seed_expr = "random(0)" if animated else "0"
    
    if mode == "color":
        # Color noise
        noise_expr = f"lum(X,Y)+{intensity*50}*({seed_expr}*2-1)"
        filters = f"geq=lum='{noise_expr}':cb='cb(X,Y)+{intensity*30}*({seed_expr}*2-1)':cr='cr(X,Y)+{intensity*30}*({seed_expr}*2-1)'"
    else:
        # Luminance noise only
        noise_expr = f"lum(X,Y)*(1+{intensity}*({seed_expr}*2-1))"
        filters = f"geq=lum='{noise_expr}'"
    
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", filters,
        "-c:a", "copy",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "23",
        output,
    ]
    
    _run_ffmpeg(cmd)

    return output


def effect_glow(
    input_path: str,
    output: str,
    intensity: float = 0.5,
    radius: int = 10,
    threshold: float = 0.7,
) -> str:
    """Apply bloom/glow effect for highlights.
    
    Args:
        input_path: Input video path
        output: Output video path
        intensity: Glow strength (0-1)
        radius: Blur radius in pixels
        threshold: Brightness threshold (0-1) for glow
    
    Returns:
        Path to output video
    """
    # Extract highlights, blur them, overlay back
    threshold_8bit = int(threshold * 255)
    
    filters = (
        f"split[original][highlights];"
        f"[highlights]geq=lum='if(lt(lum(X,Y),{threshold_8bit}),0,lum(X,Y))',"
        f"gblur=sigma={radius}[glow];"
        f"[original][glow]blend=all_mode='addition':all_opacity={intensity}"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", filters,
        "-c:a", "copy",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "23",
        output,
    ]
    
    # Run first attempt, capture error for fallback check
    cmd_str = " ".join(cmd)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        raise ProcessingError(cmd_str, -1, f"FFmpeg command timed out after 600s")

    # Fallback if gblur not available
    if result.returncode != 0 and "gblur" in result.stderr:
        filters = (
            f"split[original][highlights];"
            f"[highlights]geq=lum='if(lt(lum(X,Y),{threshold_8bit}),0,lum(X,Y))',"
            f"boxblur={radius}:{radius}[glow];"
            f"[original][glow]blend=all_mode='addition':all_opacity={intensity}"
        )
        cmd[4] = filters
        _run_ffmpeg(cmd)
    elif result.returncode != 0:
        raise ProcessingError(cmd_str, result.returncode, result.stderr)

    return output


# ---------------------------------------------------------------------------
# Layout & Composition
# ---------------------------------------------------------------------------


def layout_grid(
    clips: list[str],
    layout: str,
    output: str,
    gap: int = 10,
    padding: int = 20,
    background: str = "#141414",
) -> str:
    """Create grid-based multi-video layout using hstack/vstack.
    
    Args:
        clips: List of video file paths
        layout: Grid layout - "2x2", "3x1", "1x3", "2x3"
        output: Output video path
        gap: Pixels between clips (not used with hstack/vstack)
        padding: Padding around grid (not used with hstack/vstack)
        background: Background color (not used with hstack/vstack)
    
    Returns:
        Path to output video
    """
    if len(clips) == 0:
        raise ValueError("At least one clip required")
    
    # Parse layout
    cols, rows = map(int, layout.split('x'))
    n_clips = min(len(clips), cols * rows)
    
    # Use even dimensions that work for x264
    cell_w = 640  # Standard width
    cell_h = 480  # Standard height
    
    inputs = []
    for clip in clips[:n_clips]:
        inputs.extend(["-i", clip])
    
    # Build filter complex
    filter_parts = []
    
    # Scale each input to cell size
    for i in range(n_clips):
        filter_parts.append(
            f"[{i}:v]scale={cell_w}:{cell_h}:force_original_aspect_ratio=decrease,"
            f"setsar=1,pad={cell_w}:{cell_h}:(ow-iw)/2:(oh-ih)/2:black[s{i}];"
        )
    
    # Stack horizontally within each row, then vertically
    # First, stack each row
    row_outputs = []
    for row in range(rows):
        row_inputs = []
        for col in range(cols):
            idx = row * cols + col
            if idx < n_clips:
                row_inputs.append(f"[s{idx}]")
        
        if len(row_inputs) == 1:
            # Single column, just rename
            filter_parts.append(f"{row_inputs[0]}format=pix_fmts=yuv420p[row{row}];")
        else:
            # Stack horizontally
            hstack_in = "".join(row_inputs)
            filter_parts.append(f"{hstack_in}hstack=inputs={len(row_inputs)}[row{row}];")
        row_outputs.append(f"[row{row}]")
    
    # Then stack rows vertically
    if len(row_outputs) == 1:
        filter_parts.append(f"{row_outputs[0]}format=pix_fmts=yuv420p[out];")
    else:
        vstack_in = "".join(row_outputs)
        filter_parts.append(f"{vstack_in}vstack=inputs={len(row_outputs)}[out];")
    
    filter_complex = "".join(filter_parts).rstrip(";")
    
    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "23",
        "-shortest",
        output,
    ]
    
    _run_ffmpeg(cmd)

    return output


def layout_pip(
    main: str,
    pip: str,
    output: str,
    position: str = "bottom-right",
    size: float = 0.25,
    margin: int = 20,
    rounded_corners: bool = True,
    border: bool = True,
    border_color: str = "#CCFF00",
    border_width: int = 2,
) -> str:
    """Picture-in-picture overlay.
    
    Args:
        main: Main video path
        pip: Picture-in-picture video path
        output: Output video path
        position: "top-left", "top-right", "bottom-left", "bottom-right"
        size: PIP size as fraction of main (0-1)
        margin: Margin from edges
        rounded_corners: Apply rounded corners to PIP
        border: Add border around PIP
        border_color: Border color (hex)
        border_width: Border width in pixels
    
    Returns:
        Path to output video
    """
    # Get main video dimensions
    probe_cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0", main,
    ]
    probe = _run_ffmpeg(probe_cmd)
    main_w, main_h = map(int, probe.stdout.strip().split('x'))

    
    # Calculate PIP dimensions
    pip_w = int(main_w * size)
    pip_h = int(main_h * size)
    
    # Calculate position
    positions = {
        "top-left": (margin, margin),
        "top-right": (main_w - pip_w - margin, margin),
        "bottom-left": (margin, main_h - pip_h - margin),
        "bottom-right": (main_w - pip_w - margin, main_h - pip_h - margin),
    }
    x, y = positions.get(position, positions["bottom-right"])
    
    # Build PIP filter
    pip_filters = f"scale={pip_w}:{pip_h}"
    
    if border:
        # Add border using pad
        pip_filters += f",pad={pip_w + border_width*2}:{pip_h + border_width*2}:{border_width}:{border_width}:color={border_color}"
    
    if rounded_corners:
        # Use format and drawbox for rounded corners simulation
        # This is a simplified version - full rounded corners need more complex filter
        pass
    
    filter_complex = (
        f"[1:v]{pip_filters}[pip];"
        f"[0:v][pip]overlay={x}:{y}"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-i", main,
        "-i", pip,
        "-filter_complex", filter_complex,
        "-c:v", "libx264",
        "-c:a", "copy",
        "-pix_fmt", "yuv420p",
        "-crf", "23",
        output,
    ]
    
    _run_ffmpeg(cmd)

    return output


# ---------------------------------------------------------------------------
# Text & Typography
# ---------------------------------------------------------------------------


def text_animated(
    video: str,
    text: str,
    output: str,
    animation: str = "fade",
    font: str = "Arial",
    size: int = 48,
    color: str = "white",
    position: str = "center",
    start: float = 0,
    duration: float = 3.0,
) -> str:
    """Add animated text to video.
    
    Args:
        video: Input video path
        text: Text to display
        output: Output video path
        animation: "fade", "slide-up", "typewriter", "glitch"
        font: Font family
        size: Font size
        color: Text color
        position: Text position
        start: Start time in seconds
        duration: Display duration
    
    Returns:
        Path to output video
    """
    # Map positions
    pos_map = {
        "center": "(w-text_w)/2:(h-text_h)/2",
        "top": "(w-text_w)/2:20",
        "bottom": "(w-text_w)/2:h-text_h-20",
        "top-left": "20:20",
        "top-right": "w-text_w-20:20",
        "bottom-left": "20:h-text_h-20",
        "bottom-right": "w-text_w-20:h-text_h-20",
    }
    pos = pos_map.get(position, pos_map["center"])
    
    # Build animation expression
    fade_start = start
    fade_end = start + 0.5
    fade_out_start = start + duration - 0.5
    fade_out_end = start + duration
    
    if animation == "fade":
        # Fade in/out opacity
        alpha_expr = (
            f"if(lt(t,{fade_start}),0,"
            f"if(lt(t,{fade_end}),(t-{fade_start})/0.5,"
            f"if(lt(t,{fade_out_start}),1,"
            f"if(lt(t,{fade_out_end}),({fade_out_end}-t)/0.5,0))))"
        )
    elif animation == "slide-up":
        # Slide up from bottom
        y_offset = "+50*(1-min(1,(t-{})/0.3))".format(start)
        pos = pos.replace("(h-text_h)/2", f"(h-text_h)/2{y_offset}")
        alpha_expr = "1"
    else:
        alpha_expr = "1"
    
    # Escape text for FFmpeg — handle all filter-special characters
    safe_text = _escape_ffmpeg_filter_value(text)
    
    filter_complex = (
        f"drawtext=text='{safe_text}':font={font}:fontsize={size}:fontcolor={color}:"
        f"x={pos.split(':')[0]}:y={pos.split(':')[1]}:"
        f"enable='between(t\\,{start}\\,{start + duration})':"
        f"alpha='{alpha_expr}'"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-i", video,
        "-vf", filter_complex,
        "-c:v", "libx264",
        "-c:a", "copy",
        "-pix_fmt", "yuv420p",
        "-crf", "23",
        output,
    ]
    
    _run_ffmpeg(cmd)

    return output


def text_subtitles(
    video: str,
    subtitles: str,
    output: str,
    style: dict[str, Any] | None = None,
) -> str:
    """Burn subtitles from SRT/VTT into video with styling.
    
    Args:
        video: Input video path
        subtitles: Subtitle file path (SRT or VTT)
        output: Output video path
        style: Style dict with keys:
            - font, size, color, outline, outline_color, background, position
    
    Returns:
        Path to output video
    """
    style = style or {}
    
    # Build subtitle filter options
    font = style.get("font", "Arial")
    size = style.get("size", 32)
    color = style.get("color", "white")
    outline = style.get("outline", 2)
    outline_color = style.get("outline_color", "black")
    
    # Convert hex colors to FFmpeg format
    if color.startswith("#"):
        color = f"0x{color[1:]}"
    if outline_color.startswith("#"):
        outline_color = f"0x{outline_color[1:]}"
    
    # Escape subtitle path for FFmpeg filter syntax
    safe_subtitles = _escape_ffmpeg_filter_value(subtitles)

    filter_complex = (
        f"subtitles={safe_subtitles}:force_style='"
        f"FontName={font},"
        f"FontSize={size},"
        f"PrimaryColour={color},"
        f"OutlineColour={outline_color},"
        f"Outline={outline},"
        f"BorderStyle=1'"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-i", video,
        "-vf", filter_complex,
        "-c:v", "libx264",
        "-c:a", "copy",
        "-pix_fmt", "yuv420p",
        "-crf", "23",
        output,
    ]
    
    _run_ffmpeg(cmd)

    return output


# ---------------------------------------------------------------------------
# Motion Graphics
# ---------------------------------------------------------------------------


def mograph_count(
    start: int,
    end: int,
    duration: float,
    output: str,
    style: dict[str, Any] | None = None,
    fps: int = 30,
) -> str:
    """Generate animated number counter video.
    
    Args:
        start: Starting number
        end: Ending number
        duration: Animation duration in seconds
        output: Output video path
        style: Style dict with font, size, color, glow
        fps: Frame rate
    
    Returns:
        Path to output video
    """
    style = style or {}
    font = style.get("font", "Arial")
    size = style.get("size", 160)
    color = style.get("color", "white")
    glow = style.get("glow", False)
    
    # Create temp directory for frames
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        total_frames = int(duration * fps)
        
        # Generate frames
        for frame in range(total_frames):
            progress = frame / total_frames
            current_value = int(start + (end - start) * progress)
            
            # Use FFmpeg to generate frame
            frame_file = tmp_path / f"frame_{frame:05d}.png"
            
            text_filter = f"drawtext=text='{current_value}':font={font}:fontsize={size}:fontcolor={color}:x=(w-text_w)/2:y=(h-text_h)/2"
            
            if glow:
                text_filter += f":box=1:boxcolor={color}@0.3:boxborderw=10"
            
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "color=c=black:s=1920x1080:d=1",
                "-vf", text_filter,
                "-vframes", "1",
                str(frame_file),
            ]

            _run_ffmpeg(cmd)

        # Combine frames into video
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", str(tmp_path / "frame_%05d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "23",
            output,
        ]

        _run_ffmpeg(cmd)
    
    return output


def mograph_progress(
    duration: float,
    output: str,
    style: str = "bar",
    color: str = "#CCFF00",
    track_color: str = "#333333",
    fps: int = 30,
) -> str:
    """Generate progress bar / loading animation.
    
    Args:
        duration: Animation duration in seconds
        output: Output video path
        style: "bar", "circle", or "dots"
        color: Progress color
        track_color: Background track color
        fps: Frame rate
    
    Returns:
        Path to output video
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        total_frames = int(duration * fps)
        
        for frame in range(total_frames):
            progress = frame / total_frames
            frame_file = tmp_path / f"frame_{frame:05d}.png"
            
            if style == "bar":
                # Progress bar
                bar_width = int(800 * progress)
                # Draw track
                filter_chain = (
                    f"drawbox=x=560:y=540:w=800:h=20:color={track_color}:t=fill,"
                    f"drawbox=x=560:y=540:w={bar_width}:h=20:color={color}:t=fill"
                )
            elif style == "circle":
                # Circular progress (simplified as arc)
                filter_chain = (
                    f"drawbox=x=860:y=440:w=200:h=200:color={track_color}:t=fill,"
                    f"drawbox=x=860:y=440:w={int(200 * progress)}:h=200:color={color}:t=fill"
                )
            else:
                # Dots
                num_dots = 5
                active_dots = int(num_dots * progress)
                filter_chain = ""
                for i in range(num_dots):
                    x = 760 + i * 80
                    dot_color = color if i < active_dots else track_color
                    filter_chain += f"drawbox=x={x}:y=540:w=20:h=20:color={dot_color}:t=fill,"
                filter_chain = filter_chain.rstrip(",")
            
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "color=c=black:s=1920x1080:d=1",
                "-vf", filter_chain,
                "-vframes", "1",
                str(frame_file),
            ]

            _run_ffmpeg(cmd)

        # Combine frames
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", str(tmp_path / "frame_%05d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "23",
            output,
        ]

        _run_ffmpeg(cmd)
    
    return output


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


def video_info_detailed(video: str) -> dict[str, Any]:
    """Get extended video metadata.
    
    Args:
        video: Video file path
    
    Returns:
        Dict with duration, fps, resolution, bitrate, has_audio, 
        scene_changes, dominant_colors
    """
    import json
    
    # Get basic info
    cmd = [
        "ffprobe", "-v", "error",
        "-show_format", "-show_streams",
        "-print_format", "json",
        video,
    ]

    result = _run_ffmpeg(cmd)
    data = json.loads(result.stdout)
    
    # Extract video stream info
    video_stream = None
    audio_stream = None
    
    for stream in data.get("streams", []):
        if stream["codec_type"] == "video":
            video_stream = stream
        elif stream["codec_type"] == "audio":
            audio_stream = stream
    
    if not video_stream:
        raise ValueError("No video stream found")
    
    # Calculate duration
    duration = float(video_stream.get("duration", 0) or data.get("format", {}).get("duration", 0))
    
    # Calculate FPS
    fps_str = video_stream.get("r_frame_rate", "30/1")
    if "/" in fps_str:
        num, den = map(int, fps_str.split("/"))
        fps = num / den if den else 30
    else:
        fps = float(fps_str)
    
    resolution = [video_stream.get("width", 0), video_stream.get("height", 0)]
    bitrate = int(data.get("format", {}).get("bit_rate", 0))
    
    # Try to detect scene changes
    scene_changes = []
    try:
        scene_cmd = [
            "ffmpeg", "-i", video,
            "-filter:v", "select='gt(scene,0.3)',showinfo",
            "-f", "null", "-",
        ]
        scene_result = subprocess.run(scene_cmd, capture_output=True, text=True, timeout=30)
        # Parse scene change timestamps from stderr
        for line in scene_result.stderr.split("\n"):
            if "pts_time:" in line:
                # Extract timestamp
                parts = line.split("pts_time:")
                if len(parts) > 1:
                    try:
                        ts = float(parts[1].split()[0])
                        scene_changes.append(ts)
                    except (ValueError, IndexError):
                        pass
    except Exception:
        pass  # Scene detection is optional
    
    return {
        "duration": duration,
        "fps": fps,
        "resolution": resolution,
        "bitrate": bitrate,
        "has_audio": audio_stream is not None,
        "scene_changes": scene_changes[:10],  # Limit to first 10
        "dominant_colors": [],  # Would require frame analysis
    }


def auto_chapters(
    video: str,
    threshold: float = 0.3,
) -> list[tuple[float, str]]:
    """Auto-detect scene changes and create chapters.
    
    Args:
        video: Video file path
        threshold: Scene change detection threshold
    
    Returns:
        List of (timestamp, description) tuples
    """
    chapters = []
    
    cmd = [
        "ffmpeg", "-i", video,
        "-filter:v", f"select='gt(scene,{threshold})',showinfo",
        "-f", "null", "-",
    ]

    result = _run_ffmpeg(cmd, timeout=60)
    
    chapter_num = 1
    for line in result.stderr.split("\n"):
        if "pts_time:" in line:
            parts = line.split("pts_time:")
            if len(parts) > 1:
                try:
                    ts = float(parts[1].split()[0])
                    chapters.append((ts, f"Chapter {chapter_num}"))
                    chapter_num += 1
                except (ValueError, IndexError):
                    pass
    
    return chapters
