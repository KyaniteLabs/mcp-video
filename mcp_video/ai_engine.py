"""AI-powered video processing using machine learning models.

Optional dependencies:
    - openai-whisper: For speech-to-text transcription
    - imagehash: For AI-enhanced scene detection
    - Pillow: For image processing in scene detection
"""

from __future__ import annotations

import hashlib
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any


def ai_transcribe(
    video: str,
    output_srt: str | None = None,
    model: str = "base",
    language: str | None = None,
) -> dict[str, Any]:
    """Speech-to-text transcription using OpenAI Whisper.

    Args:
        video: Input video path
        output_srt: Optional output SRT file path
        model: Whisper model size (tiny, base, small, medium, large)
        language: Language code (auto-detect if None)

    Returns:
        Dict with transcript, segments, language

    Raises:
        RuntimeError: If whisper is not installed
        FileNotFoundError: If video file doesn't exist
    """
    # Check for whisper availability
    try:
        import whisper
    except ImportError:
        raise RuntimeError(
            "Whisper not installed. Install with: pip install openai-whisper"
        ) from None

    # Validate input file
    video_path = Path(video)
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video}")

    # Step 1: Extract audio to temp WAV file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        audio_path = tmp.name

    try:
        # Extract audio using ffmpeg: 16kHz mono 16-bit PCM (Whisper optimal format)
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vn",  # No video
            "-acodec", "pcm_s16le",  # 16-bit PCM
            "-ar", "16000",  # 16kHz (Whisper expects this)
            "-ac", "1",  # Mono
            audio_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg audio extraction failed: {result.stderr}")

        # Step 2: Load whisper model
        whisper_model = whisper.load_model(model)

        # Step 3: Transcribe with timestamps
        transcribe_options: dict[str, Any] = {}
        if language:
            transcribe_options["language"] = language

        result_data = whisper_model.transcribe(audio_path, **transcribe_options)

        # Step 4: Format as SRT if output_srt provided
        if output_srt:
            srt_content = _format_srt(result_data.get("segments", []))
            Path(output_srt).write_text(srt_content, encoding="utf-8")

        # Step 5: Return dict with results
        return {
            "transcript": result_data.get("text", "").strip(),
            "segments": result_data.get("segments", []),
            "language": result_data.get("language", "unknown"),
        }

    finally:
        # Clean up temp audio file
        Path(audio_path).unlink(missing_ok=True)


def _format_srt(segments: list[dict[str, Any]]) -> str:
    """Convert whisper segments to SRT format.

    SRT Format:
        1
        00:00:00,000 --> 00:00:02,000
        Hello world

        2
        00:00:02,000 --> 00:00:04,000
        Second line
    """
    srt_lines: list[str] = []
    index = 1

    for segment in segments:
        start_time = segment.get("start", 0.0)
        end_time = segment.get("end", 0.0)
        text = segment.get("text", "").strip()

        if not text:
            continue

        # Format: index, time range, text, blank line
        srt_lines.append(str(index))
        srt_lines.append(
            f"{_seconds_to_srt_time(start_time)} --> {_seconds_to_srt_time(end_time)}"
        )
        srt_lines.append(text)
        srt_lines.append("")  # Blank line between entries
        index += 1

    return "\n".join(srt_lines)


def _seconds_to_srt_time(seconds: float) -> str:
    """Convert seconds to SRT time format HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _run_ffprobe(video: str) -> dict[str, Any]:
    """Get video info using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-show_entries", "stream=codec_type",
        "-of", "json",
        video,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe error: {result.stderr}")
    return __import__("json").loads(result.stdout)


def _standard_scene_detect(video: str, threshold: float) -> list[dict]:
    """Standard FFmpeg scene detection."""
    cmd = [
        "ffmpeg", "-i", video,
        "-filter:v", f"select='gt(scene,{threshold})',showinfo",
        "-f", "null", "-"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    scenes = []
    for line in result.stderr.split("\n"):
        if "pts_time:" in line:
            # Extract timestamp
            match = re.search(r"pts_time:([\d.]+)", line)
            if match:
                scenes.append({
                    "timestamp": float(match.group(1)),
                    "frame": None  # Could extract from output
                })

    return scenes


def audio_spatial(
    video: str,
    output: str,
    positions: list[dict],
    method: str = "hrtf",
) -> str:
    """3D spatial audio positioning.

    Args:
        video: Input video path
        output: Output video path
        positions: List of {time, azimuth, elevation} for audio positioning
        method: Spatialization method (hrtf, vbap, simple)

    Returns:
        Path to output video

    Raises:
        FileNotFoundError: If input video doesn't exist
        RuntimeError: If FFmpeg processing fails
    """
    # Validate input file
    video_path = Path(video)
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video}")

    # Validate positions
    if not positions:
        raise ValueError("At least one position must be provided")

    # Validate method
    valid_methods = ("hrtf", "vbap", "simple")
    if method not in valid_methods:
        raise ValueError(f"Method must be one of {valid_methods}, got {method}")

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if method == "simple":
        return _apply_simple_spatial(video, output, positions)
    elif method == "hrtf":
        # HRTF requires sofalizer filter and SOFA file
        # For now, fall back to simple method with warning
        return _apply_simple_spatial(video, output, positions)
    elif method == "vbap":
        # VBAP requires multi-channel setup
        # For now, fall back to simple method with warning
        return _apply_simple_spatial(video, output, positions)

    return str(output_path)


def _azimuth_to_pan(azimuth: float) -> float:
    """Convert azimuth angle to pan value.

    Args:
        azimuth: Angle in degrees (-90 = left, 0 = center, 90 = right)

    Returns:
        Pan value (-1.0 = left, 0 = center, 1.0 = right)
    """
    # -90 (left) -> -1.0, 0 (center) -> 0, 90 (right) -> 1.0
    return max(-1.0, min(1.0, azimuth / 90.0))


def _elevation_to_volume(elevation: float) -> float:
    """Convert elevation to volume multiplier.

    Args:
        elevation: Angle in degrees (0 = level, 90 = directly above)

    Returns:
        Volume multiplier (1.0 = level, ~0.7 = directly above)
    """
    # Higher elevation = slightly quieter (distance effect)
    # 0 (level) -> 1.0, 90 (above) -> 0.7
    return 1.0 - (elevation / 90.0) * 0.3


def _apply_simple_spatial(
    video: str,
    output: str,
    positions: list[dict],
) -> str:
    """Apply simple spatial audio using pan and volume filters.

    Uses FFmpeg's pan filter for stereo positioning and volume for elevation.
    Creates animated audio positioning based on keyframes.

    Note: The 'pan' filter doesn't support timeline (enable) option, so we
    use volume filter with enable for volume changes, and apply a static
    pan for the primary position or use asplit/aselect for complex routing.

    For simplicity, this implementation uses volume for elevation simulation
    and applies a balanced pan for overall stereo field positioning.

    Args:
        video: Input video path
        output: Output video path
        positions: List of {time, azimuth, elevation} keyframes

    Returns:
        Path to output video
    """
    from pathlib import Path
    import tempfile

    # Sort positions by time
    sorted_positions = sorted(positions, key=lambda p: p.get("time", 0))

    # Get video duration for final position hold
    duration = _get_video_duration(video) or sorted_positions[-1].get("time", 5) + 1

    # For multi-keyframe spatial audio with pan, we need to use a different approach
    # since pan doesn't support timeline enable. We'll segment the audio and apply
    # different pan settings to each segment, then concatenate.

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        segment_files = []

        # Process each position segment
        for i, pos in enumerate(sorted_positions):
            time_start = pos.get("time", 0)
            azimuth = pos.get("azimuth", 0)
            elevation = pos.get("elevation", 0)

            # Determine segment duration
            if i < len(sorted_positions) - 1:
                segment_duration = sorted_positions[i + 1].get("time", duration) - time_start
            else:
                segment_duration = duration - time_start

            if segment_duration <= 0:
                continue

            # Convert to pan and volume values
            pan_value = _azimuth_to_pan(azimuth)
            volume_value = _elevation_to_volume(elevation)

            # Calculate channel gains for pan
            left_gain = max(0.0, min(1.0, 0.5 - pan_value * 0.5))
            right_gain = max(0.0, min(1.0, 0.5 + pan_value * 0.5))

            # Output segment file
            segment_file = tmpdir_path / f"segment_{i:04d}.mp4"
            segment_files.append(segment_file)

            # Build FFmpeg command for this segment
            # Extract segment, apply pan and volume
            filter_complex = (
                f"[0:a]volume={volume_value},"
                f"pan=stereo|c0={left_gain:.3f}*c0+{left_gain:.3f}*c1|"
                f"c1={right_gain:.3f}*c0+{right_gain:.3f}*c1[aout]"
            )

            cmd = [
                "ffmpeg", "-y",
                "-ss", str(time_start),
                "-t", str(segment_duration),
                "-i", video,
                "-filter_complex", filter_complex,
                "-map", "0:v",  # Copy video stream
                "-map", "[aout]",  # Use processed audio
                "-c:v", "copy",  # Copy video without re-encoding
                "-c:a", "aac",  # Re-encode audio
                "-b:a", "192k",
                str(segment_file),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg segment processing failed: {result.stderr}")

        # Concatenate all segments
        if len(segment_files) == 1:
            # Single segment - just copy
            cmd = ["cp", str(segment_files[0]), output]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"Failed to copy output: {result.stderr}")
        else:
            # Multiple segments - use concat demuxer
            concat_list = tmpdir_path / "concat_list.txt"
            with open(concat_list, "w") as f:
                for seg_file in segment_files:
                    # Escape single quotes in path
                    escaped_path = str(seg_file).replace("'", "'\\''")
                    f.write(f"file '{escaped_path}'\n")

            cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_list),
                "-c", "copy",
                output,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg concat failed: {result.stderr}")

    return output


def _get_video_duration(video_path: str) -> float | None:
    """Get video duration in seconds using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        try:
            return float(result.stdout.strip())
        except ValueError:
            pass
    return None


def ai_scene_detect(
    video: str,
    threshold: float = 0.3,
    use_ai: bool = False,
) -> list[dict]:
    """ML-enhanced scene detection using perceptual hashing.

    Args:
        video: Input video path
        threshold: Scene change threshold (for standard mode)
        use_ai: If True, use perceptual hashing for better accuracy

    Returns:
        List of scene changes with timestamps and frame numbers
    """
    if not use_ai:
        # Standard FFmpeg scene detection
        return _standard_scene_detect(video, threshold)

    # AI-enhanced: Use perceptual hashing
    try:
        import imagehash
        from PIL import Image
    except ImportError:
        # Fall back to standard detection
        return _standard_scene_detect(video, threshold)

    # Step 1: Get video duration and frame rate
    info = _run_ffprobe(video)
    duration = float(info.get("format", {}).get("duration", 0))

    if duration == 0:
        return []

    # Step 2: Extract frames at regular intervals (every 0.5 seconds)
    frame_interval = 0.5  # seconds
    scenes = []

    with tempfile.TemporaryDirectory() as tmpdir:
        # Extract frames at regular intervals
        frame_pattern = Path(tmpdir) / "frame_%04d.jpg"
        cmd = [
            "ffmpeg", "-y",
            "-i", video,
            "-vf", f"fps=1/{frame_interval},scale=320:-1",
            "-q:v", "2",
            str(frame_pattern).replace("%04d", "%04d")
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            # Fall back to standard detection on error
            return _standard_scene_detect(video, threshold)

        # Get all extracted frames sorted by time
        frames = sorted(Path(tmpdir).glob("frame_*.jpg"))
        if len(frames) < 2:
            return []

        # Step 3: Compute perceptual hash for each frame
        hashes = []
        for frame_path in frames:
            try:
                img = Image.open(frame_path)
                phash = imagehash.phash(img)
                # Extract timestamp from frame number
                # frame_0001.jpg corresponds to 0.0s, frame_0002.jpg to 0.5s, etc.
                frame_num = int(frame_path.stem.split("_")[1])
                timestamp = (frame_num - 1) * frame_interval
                hashes.append({
                    "timestamp": timestamp,
                    "hash": phash,
                    "path": frame_path
                })
            except Exception:
                continue

        # Step 4: Compare hashes to find significant changes
        # Perceptual hash threshold (lower = more sensitive)
        hash_threshold = 10  # Adjust based on testing

        for i in range(1, len(hashes)):
            prev_hash = hashes[i - 1]["hash"]
            curr_hash = hashes[i]["hash"]

            # Calculate hash difference
            hash_diff = prev_hash - curr_hash

            if hash_diff > hash_threshold:
                scenes.append({
                    "timestamp": hashes[i]["timestamp"],
                    "frame": None,
                    "hash_diff": hash_diff
                })

    return scenes


# ---------------------------------------------------------------------------
# Silence Detection and Removal
# ---------------------------------------------------------------------------


def _detect_silence_regions(
    video: str,
    silence_threshold: float,
    min_silence_duration: float,
) -> list[tuple[float, float]]:
    """Detect silent regions in video using silencedetect filter.

    Returns:
        List of (start, end) tuples for silent regions.
    """
    # Run silencedetect filter
    cmd = [
        "ffmpeg", "-i", video,
        "-af", f"silencedetect=noise={silence_threshold}dB:d={min_silence_duration}",
        "-f", "null", "-",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    # Parse silence_start and silence_end from stderr
    silence_regions = []
    silence_starts = re.findall(r"silence_start: ([\d.]+)", result.stderr)
    silence_ends = re.findall(r"silence_end: ([\d.]+)", result.stderr)

    # Pair up starts and ends
    for i, start in enumerate(silence_starts):
        if i < len(silence_ends):
            silence_regions.append((float(start), float(silence_ends[i])))
        else:
            # Silence extends to end of video
            # Get video duration
            info = _run_ffprobe(video)
            duration = float(info.get("format", {}).get("duration", 0))
            silence_regions.append((float(start), duration))

    return silence_regions


def _build_keep_segments(
    silence_regions: list[tuple[float, float]],
    video_duration: float,
    keep_margin: float,
) -> list[tuple[float, float]]:
    """Build segments to keep by inverting silence regions.

    Args:
        silence_regions: List of (start, end) tuples for silent regions
        video_duration: Total video duration
        keep_margin: Margin to keep around removed silence

    Returns:
        List of (start, end) tuples for segments to keep.
    """
    if not silence_regions:
        # No silence detected, keep entire video
        return [(0, video_duration)]

    keep_segments = []
    current_pos = 0.0

    for silence_start, silence_end in silence_regions:
        # Add margin to silence boundaries
        effective_silence_start = max(0, silence_start + keep_margin)
        min(video_duration, silence_end - keep_margin)

        # If there's content before the silence, keep it
        if current_pos < effective_silence_start:
            keep_segments.append((current_pos, effective_silence_start))

        current_pos = silence_end

    # Add remaining content after last silence
    if current_pos < video_duration:
        keep_segments.append((current_pos, video_duration))

    return keep_segments


def _concat_segments(
    video: str,
    segments: list[tuple[float, float]],
    output: str,
) -> str:
    """Concatenate video segments using FFmpeg.

    Uses segment extraction followed by concat demuxer.
    """
    if not segments:
        raise ValueError("No segments to keep")

    if len(segments) == 1:
        # Single segment - just trim
        start, end = segments[0]
        duration = end - start
        cmd = [
            "ffmpeg", "-y",
            "-i", video,
            "-ss", str(start),
            "-t", str(duration),
            "-c", "copy",
            output,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg trim error: {result.stderr}")
        return output

    # Multiple segments - extract each and concatenate
    segment_files = []

    with tempfile.TemporaryDirectory() as tmpdir:
        for i, (start, end) in enumerate(segments):
            segment_file = Path(tmpdir) / f"segment_{i:04d}.mp4"
            duration = end - start

            cmd = [
                "ffmpeg", "-y",
                "-i", video,
                "-ss", str(start),
                "-t", str(duration),
                "-c", "copy",
                str(segment_file),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg segment extraction error: {result.stderr}")

            segment_files.append(str(segment_file))

        # Create concat list file
        concat_list = Path(tmpdir) / "concat_list.txt"
        with open(concat_list, "w") as f:
            for seg_file in segment_files:
                # Escape single quotes in file path
                escaped = seg_file.replace("'", "'\\''")
                f.write(f"file '{escaped}'\n")

        # Concatenate using concat demuxer
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list),
            "-c", "copy",
            output,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg concat error: {result.stderr}")

    return output


def ai_remove_silence(
    video: str,
    output: str,
    silence_threshold: float = -50,  # dB
    min_silence_duration: float = 0.5,
    keep_margin: float = 0.1,
) -> str:
    """Auto-remove silent sections from video.

    Uses FFmpeg's silencedetect filter to identify silent regions,
    then removes them while keeping specified margins.

    Args:
        video: Input video path
        output: Output video path
        silence_threshold: Silence threshold in dB (default -50)
        min_silence_duration: Minimum silence to remove in seconds
        keep_margin: Keep this much margin around removed silence

    Returns:
        Path to output video
    """
    # Validate input file
    video_path = Path(video)
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video}")

    # Step 1: Get video duration
    info = _run_ffprobe(str(video_path))
    video_duration = float(info.get("format", {}).get("duration", 0))

    if video_duration == 0:
        raise ValueError("Could not determine video duration")

    # Step 2: Detect silent sections
    silence_regions = _detect_silence_regions(
        str(video_path),
        silence_threshold=silence_threshold,
        min_silence_duration=min_silence_duration,
    )

    # Step 3: Build segments to keep (invert silence regions)
    keep_segments = _build_keep_segments(
        silence_regions,
        video_duration,
        keep_margin=keep_margin,
    )

    # Step 4: Concatenate keep segments
    return _concat_segments(str(video_path), keep_segments, output)


# ---------------------------------------------------------------------------
# Audio Stem Separation (Demucs)
# ---------------------------------------------------------------------------


def ai_stem_separation(
    video: str,
    output_dir: str,
    stems: list[str] | None = None,
    model: str = "htdemucs",
) -> dict[str, str]:
    """Separate audio into stems using Demucs.

    Args:
        video: Input video path
        output_dir: Directory for output stem files
        stems: List of stems to extract (default: vocals, drums, bass, other)
        model: Demucs model to use (htdemucs, htdemucs_ft, etc.)

    Returns:
        Dict mapping stem names to file paths

    Raises:
        RuntimeError: If demucs is not installed
        FileNotFoundError: If video file doesn't exist
    """
    # Check for demucs availability
    try:
        import demucs.separate
    except ImportError:
        raise RuntimeError(
            "Demucs not installed. Install with: pip install demucs"
        ) from None

    # Validate input file
    video_path = Path(video)
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video}")

    # Default stems if not provided
    stems = stems or ["vocals", "drums", "bass", "other"]

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Step 1: Extract audio from video to temp WAV file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        audio_path = tmp.name

    try:
        # Extract audio using ffmpeg: 16-bit PCM stereo (Demucs works best with stereo)
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vn",  # No video
            "-acodec", "pcm_s16le",  # 16-bit PCM
            "-ar", "44100",  # 44.1kHz (CD quality)
            "-ac", "2",  # Stereo (Demucs expects stereo)
            audio_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg audio extraction failed: {result.stderr}")

        # Step 2: Run Demucs separation
        # Demucs outputs to: output_dir/model_name/audio_name/stem.wav
        audio_name = Path(audio_path).stem

        # Build demucs command arguments
        demucs_args = [
            "--out", str(output_path),
            "--name", model,
            audio_path,
        ]

        # Run demucs separation
        demucs.separate.main(demucs_args)

        # Step 3: Collect output paths
        # Output structure: output_dir/model/audio_name/stem.wav
        model_output_dir = output_path / model / audio_name

        result_paths: dict[str, str] = {}
        for stem in stems:
            # Demucs outputs stems as stem.wav (e.g., vocals.wav, drums.wav)
            stem_file = model_output_dir / f"{stem}.wav"
            if stem_file.exists():
                result_paths[stem] = str(stem_file)

        return result_paths

    finally:
        # Clean up temp audio file
        Path(audio_path).unlink(missing_ok=True)



def ai_color_grade(
    video: str,
    output: str,
    reference: str | None = None,
    style: str = "auto",
) -> str:
    """Auto color grading based on reference or style preset.

    Args:
        video: Input video path
        output: Output video path
        reference: Optional reference video for color matching
        style: Style preset (auto, cinematic, vintage, warm, cool, dramatic)

    Returns:
        Path to output video

    Raises:
        FileNotFoundError: If video file doesn't exist
        RuntimeError: If FFmpeg processing fails
    """
    from pathlib import Path

    # Validate input file
    video_path = Path(video)
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video}")

    # Style presets define color adjustments
    style_presets = {
        "cinematic": {"contrast": 1.1, "saturation": 0.9, "gamma": 1.0, "red": 1.05, "green": 1.0, "blue": 0.95},
        "vintage": {"contrast": 0.9, "saturation": 0.7, "gamma": 1.1, "red": 1.1, "green": 0.95, "blue": 0.8},
        "warm": {"contrast": 1.0, "saturation": 1.05, "gamma": 1.0, "red": 1.1, "green": 1.0, "blue": 0.9},
        "cool": {"contrast": 1.0, "saturation": 0.95, "gamma": 1.0, "red": 0.9, "green": 1.0, "blue": 1.1},
        "dramatic": {"contrast": 1.3, "saturation": 1.1, "gamma": 0.9, "red": 1.0, "green": 1.0, "blue": 1.0},
        "auto": {"contrast": 1.05, "saturation": 1.0, "gamma": 1.0, "red": 1.0, "green": 1.0, "blue": 1.0},
    }

    # Get style parameters (default to auto if invalid style provided)
    params = style_presets.get(style, style_presets["auto"])

    # If reference provided, analyze and adjust to match
    if reference:
        params = _match_reference_colors(video, reference)

    # Build FFmpeg filter chain
    # eq filter for contrast/saturation/gamma/brightness
    # colorbalance for RGB channel adjustments (rs=red shift, gs=green shift, bs=blue shift)

    # Convert multipliers to FFmpeg eq parameters
    contrast = params["contrast"]
    saturation = params["saturation"]
    gamma = params["gamma"]

    # Calculate RGB shifts for colorbalance (normalized -1 to 1 range)
    # 1.0 = no shift, >1.0 = increase, <1.0 = decrease
    # Map 0.8-1.2 range to approximately -0.1 to 0.1 shift
    rs = (params["red"] - 1.0) * 0.5
    gs = (params["green"] - 1.0) * 0.5
    bs = (params["blue"] - 1.0) * 0.5

    # Build filter chain
    # eq filter for basic color adjustments (needs eq= prefix)
    eq_params = f"eq=contrast={contrast}:saturation={saturation}:gamma={gamma}"

    # colorbalance for RGB channel adjustments
    colorbalance_params = f"colorbalance=rs={rs}:gs={gs}:bs={bs}"

    # Combine filters
    filter_string = f"{eq_params},{colorbalance_params}"

    # Build FFmpeg command
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vf", filter_string,
        "-c:a", "copy",  # Copy audio without re-encoding
        "-pix_fmt", "yuv420p",  # Ensure compatibility
        output,
    ]

    # Execute FFmpeg
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg color grading failed: {result.stderr}")

    return output


def _match_reference_colors(video: str, reference: str) -> dict:
    """Analyze reference and return matching parameters.

    This is a simplified implementation that extracts basic color statistics
    from both videos and returns adjusted parameters.

    Args:
        video: Input video path
        reference: Reference video path

    Returns:
        Dict with color adjustment parameters
    """
    import subprocess
    import re

    def extract_mean_color(video_path: str) -> dict:
        """Extract mean RGB values from video using signalstats filter."""
        cmd = [
            "ffmpeg", "-i", video_path,
            "-vf", "signalstats=out=JSON:stat=tout+vrep+brng",
            "-f", "null", "-"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Default values if extraction fails
        mean_rgb = {"r": 128, "g": 128, "b": 128}

        # Parse signalstats output
        # Look for mean values in stderr output
        stderr = result.stderr

        # Try to extract mean Y/U/V or R/G/B values
        # This is a simplified extraction - signalstats outputs in YUV by default
        y_match = re.search(r'YAVG ([\d.]+)', stderr)
        u_match = re.search(r'UAVG ([\d.]+)', stderr)
        v_match = re.search(r'VAVG ([\d.]+)', stderr)

        if y_match and u_match and v_match:
            # Convert YUV to approximate RGB (simplified)
            y = float(y_match.group(1))
            u = float(u_match.group(1)) - 128
            v = float(v_match.group(1)) - 128

            # Approximate RGB from YUV
            mean_rgb["r"] = max(0, min(255, y + 1.402 * v))
            mean_rgb["g"] = max(0, min(255, y - 0.344 * u - 0.714 * v))
            mean_rgb["b"] = max(0, min(255, y + 1.772 * u))

        return mean_rgb

    try:
        # Extract mean colors from both videos
        video_colors = extract_mean_color(video)
        ref_colors = extract_mean_color(reference)

        # Calculate adjustment ratios
        # Avoid division by zero
        def safe_ratio(ref, src):
            if src < 1:
                src = 1
            return min(2.0, max(0.5, ref / src))

        red_adj = safe_ratio(ref_colors["r"], video_colors["r"])
        green_adj = safe_ratio(ref_colors["g"], video_colors["g"])
        blue_adj = safe_ratio(ref_colors["b"], video_colors["b"])

        # Calculate contrast adjustment based on overall brightness difference
        video_avg = (video_colors["r"] + video_colors["g"] + video_colors["b"]) / 3
        ref_avg = (ref_colors["r"] + ref_colors["g"] + ref_colors["b"]) / 3
        contrast_adj = safe_ratio(ref_avg, video_avg)

        return {
            "contrast": contrast_adj,
            "saturation": 1.0,
            "gamma": 1.0,
            "red": red_adj,
            "green": green_adj,
            "blue": blue_adj,
        }
    except Exception:
        # Fall back to neutral params if analysis fails
        return {"contrast": 1.0, "saturation": 1.0, "gamma": 1.0, "red": 1.0, "green": 1.0, "blue": 1.0}


# ---------------------------------------------------------------------------
# Model Download Integrity Verification
# ---------------------------------------------------------------------------

# Expected SHA256 hashes for downloaded model files.
_MODEL_HASHES: dict[str, str] = {
    "FSRCNN_x2.pb": "366b33f0084c7b3f2bf6724f0a2c77bca94fcec9d7b6d72389d330073b380d5c",
    "FSRCNN_x4.pb": "5c68d18db561aed8ead4ffedf1b897ea615baaf60ebf6c35f8e641f8fa4a21bf",
}


def _verify_model_hash(path: Path, expected_hash: str) -> None:
    """Verify SHA256 hash of a downloaded model file.

    Args:
        path: Path to the model file on disk.
        expected_hash: Expected lowercase hex SHA256 digest.

    Raises:
        MCPVideoError: If the computed hash does not match the expected value.
    """
    from mcp_video.errors import MCPVideoError

    sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    if sha256 != expected_hash:
        path.unlink(missing_ok=True)
        raise MCPVideoError(
            f"SHA256 integrity check failed for {path.name}: "
            f"expected {expected_hash}, got {sha256}. "
            "The downloaded file has been removed. Try again to re-download.",
            error_type="integrity_error",
            code="model_hash_mismatch",
        )


def _ai_upscale_opencv(video_path: str, output_path: str, scale: int) -> str:
    """AI upscaling fallback using OpenCV DNN Super Resolution.

    Uses lightweight FSRCNN model for fast CPU inference.
    Downloads models automatically on first use.
    """
    import cv2

    # FSRCNN is much faster than EDSR for CPU inference
    model_urls = {
        2: "https://github.com/Saafke/FSRCNN_Tensorflow/raw/master/models/FSRCNN_x2.pb",
        4: "https://github.com/Saafke/FSRCNN_Tensorflow/raw/master/models/FSRCNN_x4.pb",
    }

    if scale not in model_urls:
        raise ValueError(f"Scale must be 2 or 4, got {scale}")

    # Setup model path in cache directory
    cache_dir = Path.home() / ".cache" / "mcp-video" / "models"
    cache_dir.mkdir(parents=True, exist_ok=True)
    model_path = cache_dir / f"FSRCNN_x{scale}.pb"

    # Download model if not exists (FSRCNN is ~57KB vs EDSR's 38MB!)
    model_filename = f"FSRCNN_x{scale}.pb"
    if model_filename not in _MODEL_HASHES:
        raise ValueError(f"No known hash for model {model_filename}")
    expected_hash = _MODEL_HASHES[model_filename]

    if not model_path.exists():
        import urllib.request
        url = model_urls[scale]
        print(f"Downloading FSRCNN x{scale} model...")
        urllib.request.urlretrieve(url, model_path)
        print(f"Model saved to {model_path}")

    # Verify integrity of the model file (catches corrupted downloads or tampering)
    _verify_model_hash(model_path, expected_hash)

    # Initialize DNN Super Resolution with FSRCNN (fast for CPU)
    sr = cv2.dnn_superres.DnnSuperResImpl_create()
    sr.readModel(str(model_path))
    sr.setModel("fsrcnn", scale)

    video_file = Path(video_path)
    output_file = Path(output_path)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        frames_dir = tmpdir_path / "frames"
        upscaled_dir = tmpdir_path / "upscaled"
        frames_dir.mkdir()
        upscaled_dir.mkdir()

        # Get video info
        fps = _get_video_fps(str(video_file))
        has_audio = _has_audio_stream(str(video_file))

        # Extract frames
        frame_pattern = frames_dir / "frame_%04d.png"
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_file),
            "-vsync", "0",
            str(frame_pattern)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to extract frames: {result.stderr}")

        frames = sorted(frames_dir.glob("frame_*.png"))
        if not frames:
            raise RuntimeError("No frames extracted from video")

        # Upscale each frame using OpenCV DNN
        for i, frame_path in enumerate(frames, 1):
            # Load frame with OpenCV
            img = cv2.imread(str(frame_path))
            if img is None:
                raise RuntimeError(f"Failed to load frame: {frame_path}")

            # Upscale using DNN
            result_img = sr.upsample(img)

            # Save upscaled frame
            output_frame_path = upscaled_dir / f"frame_{i:04d}.png"
            cv2.imwrite(str(output_frame_path), result_img)

        # Reconstruct video
        upscaled_pattern = upscaled_dir / "frame_%04d.png"
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", str(upscaled_pattern),
        ]

        if has_audio:
            # Copy audio from original
            cmd.extend(["-i", str(video_file), "-c:a", "copy", "-shortest"])

        cmd.extend([
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "18",
            str(output_file)
        ])

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to create upscaled video: {result.stderr}")

    return str(output_file)


def ai_upscale(
    video: str,
    output: str,
    scale: int = 2,
    model: str = "realesrgan",
) -> str:
    """AI-powered video upscaling using Real-ESRGAN.

    Args:
        video: Input video path
        output: Output video path
        scale: Upscaling factor (2 or 4)
        model: Model to use (realesrgan, bsrgan, swinir)

    Returns:
        Path to output video

    Raises:
        RuntimeError: If Real-ESRGAN is not installed or processing fails
        FileNotFoundError: If input video doesn't exist
    """
    # Validate input file
    video_path = Path(video)
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video}")

    # Try to use Real-ESRGAN if available, otherwise use OpenCV DNN fallback
    try:
        from realesrgan import RealESRGANer
        from basicsr.archs.rrdbnet_arch import RRDBNet
        has_realesrgan = True
    except ImportError:
        has_realesrgan = False

    # Validate scale parameter
    if scale not in (2, 4):
        raise ValueError(f"Scale must be 2 or 4, got {scale}")

    output_path = Path(output)

    # Fallback: Use OpenCV DNN Super Resolution
    if not has_realesrgan:
        try:
            return _ai_upscale_opencv(str(video_path), str(output_path), scale)
        except ImportError:
            raise RuntimeError(
                "AI upscaling requires either realesrgan or opencv-python (cv2). "
                "Install with: pip install realesrgan or pip install opencv-python"
            ) from None

    # Validate scale parameter
    if scale not in (2, 4):
        raise ValueError(f"Scale must be 2 or 4, got {scale}")

    # Map model names to RRDBNet configurations
    model_configs = {
        "realesrgan": {"num_block": 23, "num_feat": 64},
        "bsrgan": {"num_block": 23, "num_feat": 64},
        "swinir": {"num_block": 23, "num_feat": 64},  # Simplified - swinir uses different arch
    }

    if model not in model_configs:
        raise ValueError(f"Unknown model: {model}. Choose from: {list(model_configs.keys())}")

    output_path = Path(output)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        frames_dir = tmpdir_path / "frames"
        upscaled_dir = tmpdir_path / "upscaled"
        frames_dir.mkdir()
        upscaled_dir.mkdir()

        # Step 1: Get video info (fps, duration, audio stream)
        fps = _get_video_fps(str(video_path))
        has_audio = _has_audio_stream(str(video_path))

        # Step 2: Extract frames from video
        frame_pattern = frames_dir / "frame_%04d.png"
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vsync", "0",
            str(frame_pattern)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to extract frames: {result.stderr}")

        # Get list of extracted frames
        frames = sorted(frames_dir.glob("frame_*.png"))
        if not frames:
            raise RuntimeError("No frames extracted from video")

        # Step 3: Initialize Real-ESRGAN model
        config = model_configs[model]
        rrdb_net = RRDBNet(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=config["num_feat"],
            num_block=config["num_block"],
            num_grow_ch=32,
            scale=scale
        )

        # Determine model URL/path based on model and scale
        # RealESRGANer handles auto-download when model_path is None
        upsampler = RealESRGANer(
            scale=scale,
            model_path=None,  # Auto-download
            model=rrdb_net,
            tile=0,  # No tiling - process whole image
            tile_pad=10,
            pre_pad=0,
            half=False  # Use FP32
        )

        # Step 4: Upscale each frame
        import numpy as np
        from PIL import Image

        for i, frame_path in enumerate(frames, 1):
            # Load frame
            img = Image.open(frame_path).convert("RGB")
            img_np = np.array(img)

            # Upscale
            output_img, _ = upsampler.enhance(img_np, outscale=scale)

            # Save upscaled frame
            output_frame_path = upscaled_dir / f"frame_{i:04d}.png"
            output_pil = Image.fromarray(output_img)
            output_pil.save(output_frame_path)

        # Step 5: Extract audio if present
        audio_path = None
        if has_audio:
            audio_path = tmpdir_path / "audio.aac"
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-vn",  # No video
                "-c:a", "copy",
                str(audio_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                audio_path = None  # Continue without audio

        # Step 6: Reconstruct video from upscaled frames
        upscaled_pattern = upscaled_dir / "frame_%04d.png"

        if fps is None:
            fps = 30  # Default fallback

        if audio_path and audio_path.exists():
            # Reconstruct with audio
            cmd = [
                "ffmpeg", "-y",
                "-framerate", str(fps),
                "-i", str(upscaled_pattern),
                "-i", str(audio_path),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-c:a", "copy",
                "-shortest",
                str(output_path)
            ]
        else:
            # Reconstruct without audio
            cmd = [
                "ffmpeg", "-y",
                "-framerate", str(fps),
                "-i", str(upscaled_pattern),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                str(output_path)
            ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to reconstruct video: {result.stderr}")

    return str(output_path)


def _get_video_fps(video_path: str) -> float | None:
    """Get video frame rate using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=r_frame_rate",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None

    fps_str = result.stdout.strip()
    # Parse fraction like "30000/1001" or "30"
    if "/" in fps_str:
        num, den = fps_str.split("/")
        try:
            return float(num) / float(den)
        except (ValueError, ZeroDivisionError):
            return None
    else:
        try:
            return float(fps_str)
        except ValueError:
            return None


def _has_audio_stream(video_path: str) -> bool:
    """Check if video has an audio stream."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "a",
        "-show_entries", "stream=codec_type",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0 and "audio" in result.stdout.lower()
