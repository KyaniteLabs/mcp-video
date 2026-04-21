"""AI-powered video processing using machine learning models.

Optional dependencies:
    - openai-whisper: For speech-to-text transcription
    - imagehash: For AI-enhanced scene detection
    - Pillow: For image processing in scene detection
"""

from __future__ import annotations

import hashlib
import logging
import subprocess
import tempfile
from pathlib import Path

from ..errors import InputFileError, MCPVideoError, ProcessingError
from ..limits import DEFAULT_FFMPEG_TIMEOUT

logger = logging.getLogger(__name__)

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

    from mcp_video.errors import MCPVideoError

    # FSRCNN is much faster than EDSR for CPU inference
    model_urls = {
        2: "https://github.com/Saafke/FSRCNN_Tensorflow/raw/master/models/FSRCNN_x2.pb",
        4: "https://github.com/Saafke/FSRCNN_Tensorflow/raw/master/models/FSRCNN_x4.pb",
    }

    if scale not in model_urls:
        raise MCPVideoError(
            f"Scale must be 2 or 4, got {scale}", error_type="validation_error", code="invalid_parameter"
        )

    # Setup model path in cache directory
    cache_dir = Path.home() / ".cache" / "mcp-video" / "models"
    cache_dir.mkdir(parents=True, exist_ok=True)
    model_path = cache_dir / f"FSRCNN_x{scale}.pb"

    # Download model if not exists (FSRCNN is ~57KB vs EDSR's 38MB!)
    model_filename = f"FSRCNN_x{scale}.pb"
    if model_filename not in _MODEL_HASHES:
        raise MCPVideoError(
            f"No known hash for model {model_filename}", error_type="validation_error", code="invalid_parameter"
        )
    expected_hash = _MODEL_HASHES[model_filename]

    if not model_path.exists():
        import urllib.request

        url = model_urls[scale]
        print(f"Downloading FSRCNN x{scale} model...")
        tmp_model = model_path.with_suffix(".tmp")
        max_model_bytes = 500 * (1 << 20)  # 500 MiB limit
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=120) as resp, open(tmp_model, "wb") as fh:
            total = 0
            while True:
                chunk = resp.read(1 << 20)  # 1 MiB
                if not chunk:
                    break
                total += len(chunk)
                if total > max_model_bytes:
                    tmp_model.unlink(missing_ok=True)
                    raise MCPVideoError(
                        f"Model download exceeded {max_model_bytes >> 20} MiB size limit",
                        error_type="resource_error",
                        code="download_size_limit",
                    )
                fh.write(chunk)
        tmp_model.rename(model_path)
        print(f"Model saved to {model_path}")

    # Verify integrity of the model file (catches corrupted downloads or tampering)
    _verify_model_hash(model_path, expected_hash)

    # Initialize DNN Super Resolution with FSRCNN (fast for CPU)
    if not hasattr(cv2, "dnn_superres"):
        raise MCPVideoError(
            "OpenCV was built without dnn_superres module. Install opencv-contrib-python for full AI support.",
            error_type="dependency_error",
            code="missing_opencv_contrib",
        )
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
        cmd = ["ffmpeg", "-y", "-i", str(video_file), "-vsync", "0", str(frame_pattern)]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=DEFAULT_FFMPEG_TIMEOUT)
        except subprocess.TimeoutExpired:
            raise ProcessingError(f"Operation timed out after {DEFAULT_FFMPEG_TIMEOUT}s") from None
        if result.returncode != 0:
            raise ProcessingError(" ".join(cmd), result.returncode, result.stderr)

        frames = sorted(frames_dir.glob("frame_*.png"))
        if not frames:
            raise ProcessingError(cmd[0], 1, "No frames extracted from video")

        # Upscale each frame using OpenCV DNN
        for i, frame_path in enumerate(frames, 1):
            # Load frame with OpenCV
            img = cv2.imread(str(frame_path))
            if img is None:
                raise ProcessingError("cv2.imread", 1, f"Failed to load frame: {frame_path}")

            # Upscale using DNN
            result_img = sr.upsample(img)

            # Save upscaled frame
            output_frame_path = upscaled_dir / f"frame_{i:04d}.png"
            cv2.imwrite(str(output_frame_path), result_img)

        # Reconstruct video
        upscaled_pattern = upscaled_dir / "frame_%04d.png"
        cmd = [
            "ffmpeg",
            "-y",
            "-framerate",
            str(fps),
            "-i",
            str(upscaled_pattern),
        ]

        if has_audio:
            # Copy audio from original
            cmd.extend(["-i", str(video_file), "-c:a", "copy", "-shortest"])

        cmd.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", str(output_file)])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=DEFAULT_FFMPEG_TIMEOUT)
        except subprocess.TimeoutExpired:
            raise ProcessingError(f"Operation timed out after {DEFAULT_FFMPEG_TIMEOUT}s") from None
        if result.returncode != 0:
            raise ProcessingError(" ".join(cmd), result.returncode, result.stderr)

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
    if "\x00" in video:
        raise InputFileError(video, "Invalid path: contains null bytes")

    # Validate input file
    video_path = Path(video)
    if not video_path.exists():
        raise InputFileError(video)

    # Try to use Real-ESRGAN if available, otherwise use OpenCV DNN fallback
    # NOTE: basicsr <= 1.4.2 has CVE-2024-27763 (command injection via SLURM_NODELIST).
    # Our usage only imports the RRDBNet architecture class for inference.
    # We do not execute the vulnerable scontrol path in basicsr/utils/dist_util.py.
    try:
        from realesrgan import RealESRGANer
        from basicsr.archs.rrdbnet_arch import RRDBNet

        has_realesrgan = True
    except ImportError:
        has_realesrgan = False

    # Validate scale parameter
    if scale not in (2, 4):
        raise MCPVideoError(
            f"Scale must be 2 or 4, got {scale}", error_type="validation_error", code="invalid_parameter"
        )

    output_path = Path(output)

    # Fallback: Use OpenCV DNN Super Resolution
    if not has_realesrgan:
        try:
            return _ai_upscale_opencv(str(video_path), str(output_path), scale)
        except ImportError:
            raise MCPVideoError(
                "AI upscaling requires either realesrgan or opencv-contrib-python (cv2). "
                "Install with: pip install realesrgan or pip install opencv-contrib-python",
                error_type="dependency_error",
                code="missing_upscale_dep",
            ) from None

    # Map model names to RRDBNet configurations
    model_configs = {
        "realesrgan": {"num_block": 23, "num_feat": 64},
        "bsrgan": {"num_block": 23, "num_feat": 64},
        "swinir": {"num_block": 23, "num_feat": 64},  # Simplified - swinir uses different arch
    }

    if model not in model_configs:
        raise MCPVideoError(
            f"Unknown model: {model}. Choose from: {list(model_configs.keys())}",
            error_type="validation_error",
            code="invalid_parameter",
        )

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
        cmd = ["ffmpeg", "-y", "-i", str(video_path), "-vsync", "0", str(frame_pattern)]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=DEFAULT_FFMPEG_TIMEOUT)
        except subprocess.TimeoutExpired:
            raise ProcessingError(f"Operation timed out after {DEFAULT_FFMPEG_TIMEOUT}s") from None
        if result.returncode != 0:
            raise ProcessingError(" ".join(cmd), result.returncode, result.stderr)

        # Get list of extracted frames
        frames = sorted(frames_dir.glob("frame_*.png"))
        if not frames:
            raise ProcessingError(cmd[0], 1, "No frames extracted from video")

        # Step 3: Initialize Real-ESRGAN model
        config = model_configs[model]
        rrdb_net = RRDBNet(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=config["num_feat"],
            num_block=config["num_block"],
            num_grow_ch=32,
            scale=scale,
        )

        # Determine model URL/path based on model and scale
        # RealESRGANer handles auto-download when model_path is None
        upsampler = RealESRGANer(
            scale=scale,
            model_path=None,  # Auto-download
            model=rrdb_net,
            tile=256,  # Process in 256x256 tiles to limit memory usage
            tile_pad=10,
            pre_pad=0,
            half=False,  # Use FP32
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
                "ffmpeg",
                "-y",
                "-i",
                str(video_path),
                "-vn",  # No video
                "-c:a",
                "copy",
                str(audio_path),
            ]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=DEFAULT_FFMPEG_TIMEOUT)
            except subprocess.TimeoutExpired:
                raise ProcessingError(f"Operation timed out after {DEFAULT_FFMPEG_TIMEOUT}s") from None
            if result.returncode != 0:
                audio_path = None  # Continue without audio

        # Step 6: Reconstruct video from upscaled frames
        upscaled_pattern = upscaled_dir / "frame_%04d.png"

        if fps is None:
            fps = 30  # Default fallback

        if audio_path and audio_path.exists():
            # Reconstruct with audio
            cmd = [
                "ffmpeg",
                "-y",
                "-framerate",
                str(fps),
                "-i",
                str(upscaled_pattern),
                "-i",
                str(audio_path),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "copy",
                "-shortest",
                str(output_path),
            ]
        else:
            # Reconstruct without audio
            cmd = [
                "ffmpeg",
                "-y",
                "-framerate",
                str(fps),
                "-i",
                str(upscaled_pattern),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(output_path),
            ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=DEFAULT_FFMPEG_TIMEOUT)
        except subprocess.TimeoutExpired:
            raise ProcessingError(f"Operation timed out after {DEFAULT_FFMPEG_TIMEOUT}s") from None
        if result.returncode != 0:
            raise ProcessingError(" ".join(cmd), result.returncode, result.stderr)

    return str(output_path)


def _get_video_fps(video_path: str) -> float | None:
    """Get video frame rate using ffprobe."""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=r_frame_rate",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=DEFAULT_FFMPEG_TIMEOUT)
    except subprocess.TimeoutExpired:
        raise ProcessingError(f"Operation timed out after {DEFAULT_FFMPEG_TIMEOUT}s") from None
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
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "a",
        "-show_entries",
        "stream=codec_type",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=DEFAULT_FFMPEG_TIMEOUT)
    except subprocess.TimeoutExpired:
        raise ProcessingError(f"Operation timed out after {DEFAULT_FFMPEG_TIMEOUT}s") from None
    return result.returncode == 0 and "audio" in result.stdout.lower()
