"""Visual design quality guardrails for video output.

Automated quality checks similar to code linting, but for video/visual output.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class QualityReport:
    """Report from a single quality check."""

    check_name: str
    passed: bool
    score: float  # 0-100
    message: str
    details: dict[str, Any] = field(default_factory=dict)


class VisualQualityGuardrails:
    """Automated visual quality checks for video output."""

    # Quality thresholds
    BRIGHTNESS_MIN = 16  # Avoid crushed blacks
    BRIGHTNESS_MAX = 235  # Avoid blown highlights
    BRIGHTNESS_TARGET_MIN = 40
    BRIGHTNESS_TARGET_MAX = 200

    CONTRAST_MIN = 20  # Avoid flat images
    CONTRAST_MAX = 100  # Avoid excessive contrast

    SATURATION_MIN = 10  # Avoid desaturation
    SATURATION_MAX = 120  # Avoid oversaturation

    AUDIO_LUFS_TARGET = -16  # YouTube standard
    AUDIO_LUFS_MIN = -20
    AUDIO_LUFS_MAX = -12
    AUDIO_TRUE_PEAK_MAX = -1  # dBTP

    def _run_ffprobe(self, video: str, filter_name: str) -> dict[str, Any]:
        """Run ffprobe with signalstats filter and parse results."""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-f", "lavfi",
            "-i", f"movie={video},signalstats",
            "-show_entries", f"frame_tags={filter_name}",
            "-of", "json",
        ]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60
            )
            if result.returncode != 0:
                return {}
            data = json.loads(result.stdout)
            frames = data.get("frames", [])
            if not frames:
                return {}
            # Average across all frames
            values = []
            for frame in frames:
                tags = frame.get("tags", {})
                if filter_name in tags:
                    try:
                        values.append(float(tags[filter_name]))
                    except (ValueError, TypeError):
                        continue
            if not values:
                return {}
            return {"mean": sum(values) / len(values), "values": values}
        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
            return {}

    def _run_ffmpeg_signalstats(self, video: str) -> dict[str, Any]:
        """Run ffmpeg with signalstats filter to get video statistics."""
        cmd = [
            "ffmpeg",
            "-i", video,
            "-vf", "signalstats",
            "-f", "null",
            "-",
        ]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120
            )
            # Parse stderr for signalstats output
            stderr = result.stderr
            stats = {}

            # Extract mean values from the output
            for line in stderr.split("\n"):
                if "YUV AVG:" in line or "YAVG:" in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if "YAVG=" in part or "YUV" in part:
                            try:
                                # Try to find numeric value
                                for p in parts[i:]:
                                    if "=" in p:
                                        key, val = p.split("=", 1)
                                        try:
                                            stats[key.lower()] = float(val)
                                        except ValueError:
                                            pass
                            except (ValueError, IndexError):
                                continue
            return stats
        except subprocess.TimeoutExpired:
            return {}
        except Exception:
            return {}

    def _analyze_loudnorm(self, video: str) -> dict[str, Any]:
        """Analyze audio loudness using loudnorm filter."""
        cmd = [
            "ffmpeg",
            "-i", video,
            "-af", "loudnorm=print_format=json",
            "-f", "null",
            "-",
        ]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120
            )
            # Parse JSON from the output (it's embedded in stderr)
            stderr = result.stderr

            # Find the JSON portion
            json_start = stderr.find("{")
            json_end = stderr.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = stderr[json_start:json_end]
                return json.loads(json_str)
            return {}
        except subprocess.TimeoutExpired:
            return {}
        except json.JSONDecodeError:
            return {}
        except Exception:
            return {}

    def _get_rgb_means(self, video: str) -> dict[str, float] | None:
        """Get mean RGB values for color balance analysis."""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-f", "lavfi",
            "-i", f"movie={video},signalstats",
            "-show_entries", "frame_tags=lavfi.signalstats.RAVG,lavfi.signalstats.GAVG,lavfi.signalstats.BAVG",
            "-of", "json",
        ]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60
            )
            if result.returncode != 0:
                return None

            data = json.loads(result.stdout)
            frames = data.get("frames", [])
            if not frames:
                return None

            # Average RGB across frames
            r_vals, g_vals, b_vals = [], [], []
            for frame in frames:
                tags = frame.get("tags", {})
                if "lavfi.signalstats.RAVG" in tags:
                    try:
                        r_vals.append(float(tags["lavfi.signalstats.RAVG"]))
                    except (ValueError, TypeError):
                        pass
                if "lavfi.signalstats.GAVG" in tags:
                    try:
                        g_vals.append(float(tags["lavfi.signalstats.GAVG"]))
                    except (ValueError, TypeError):
                        pass
                if "lavfi.signalstats.BAVG" in tags:
                    try:
                        b_vals.append(float(tags["lavfi.signalstats.BAVG"]))
                    except (ValueError, TypeError):
                        pass

            if not (r_vals and g_vals and b_vals):
                return None

            return {
                "r": sum(r_vals) / len(r_vals),
                "g": sum(g_vals) / len(g_vals),
                "b": sum(b_vals) / len(b_vals),
            }
        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
            return None

    def check_brightness(self, video: str) -> QualityReport:
        """Check video brightness is in acceptable range."""
        stats = self._run_ffprobe(video, "lavfi.signalstats.YAVG")

        if not stats or "mean" not in stats:
            # Try alternative method
            stats = self._run_ffmpeg_signalstats(video)
            if not stats or "yavg" not in stats:
                return QualityReport(
                    check_name="brightness",
                    passed=False,
                    score=0.0,
                    message="Could not analyze brightness (no video stream or analysis failed)",
                    details={},
                )
            y_avg = stats["yavg"]
        else:
            y_avg = stats["mean"]

        # Y values range from 0-255 in 8-bit video
        passed = self.BRIGHTNESS_TARGET_MIN <= y_avg <= self.BRIGHTNESS_TARGET_MAX

        # Calculate score (100 = perfect at 128, linear falloff)
        target = 128
        deviation = abs(y_avg - target)
        score = float(max(0, 100 - (deviation / target) * 100))

        if y_avg < self.BRIGHTNESS_MIN:
            message = f"Video has crushed blacks (brightness: {y_avg:.1f}). Consider lifting shadows."
        elif y_avg > self.BRIGHTNESS_MAX:
            message = f"Video has blown highlights (brightness: {y_avg:.1f}). Consider lowering exposure."
        elif y_avg < self.BRIGHTNESS_TARGET_MIN:
            message = f"Video is quite dark (brightness: {y_avg:.1f}). Consider slight brightness increase."
        elif y_avg > self.BRIGHTNESS_TARGET_MAX:
            message = f"Video is quite bright (brightness: {y_avg:.1f}). Consider slight brightness decrease."
        else:
            message = f"Brightness is well-balanced (brightness: {y_avg:.1f})"

        return QualityReport(
            check_name="brightness",
            passed=passed,
            score=score,
            message=message,
            details={"y_avg": y_avg, "target_range": [self.BRIGHTNESS_TARGET_MIN, self.BRIGHTNESS_TARGET_MAX]},
        )

    def check_contrast(self, video: str) -> QualityReport:
        """Check video has adequate contrast."""
        stats = self._run_ffprobe(video, "lavfi.signalstats.YSTDV")

        if not stats or "mean" not in stats:
            return QualityReport(
                check_name="contrast",
                passed=False,
                score=0.0,
                message="Could not analyze contrast (analysis failed)",
                details={},
            )

        y_std = stats["mean"]  # Standard deviation of luminance

        # Standard deviation indicates contrast (higher = more contrast)
        passed = self.CONTRAST_MIN <= y_std <= self.CONTRAST_MAX

        # Calculate score
        optimal_contrast = 50
        deviation = abs(y_std - optimal_contrast)
        score = float(max(0, 100 - (deviation / optimal_contrast) * 100))

        if y_std < self.CONTRAST_MIN:
            message = f"Video has low contrast (std dev: {y_std:.1f}). Image may appear flat. Consider increasing contrast."
        elif y_std > self.CONTRAST_MAX:
            message = f"Video has very high contrast (std dev: {y_std:.1f}). May lose detail in shadows/highlights."
        else:
            message = f"Contrast is good (std dev: {y_std:.1f})"

        return QualityReport(
            check_name="contrast",
            passed=passed,
            score=score,
            message=message,
            details={"y_std": y_std, "target_range": [self.CONTRAST_MIN, self.CONTRAST_MAX]},
        )

    def check_saturation(self, video: str) -> QualityReport:
        """Check saturation levels."""
        # Analyze chroma channels (U and V in YUV)
        u_stats = self._run_ffprobe(video, "lavfi.signalstats.UAVG")
        v_stats = self._run_ffprobe(video, "lavfi.signalstats.VAVG")

        if not u_stats or not v_stats:
            return QualityReport(
                check_name="saturation",
                passed=False,
                score=0.0,
                message="Could not analyze saturation (analysis failed)",
                details={},
            )

        u_mean = u_stats.get("mean", 128)
        v_mean = v_stats.get("mean", 128)

        # Chroma deviation from neutral gray (128) indicates saturation
        # Calculate distance from neutral in UV plane
        saturation = ((u_mean - 128) ** 2 + (v_mean - 128) ** 2) ** 0.5

        # Scale to approximate percentage (typical max ~60)
        saturation_pct = (saturation / 60) * 100

        passed = self.SATURATION_MIN <= saturation_pct <= self.SATURATION_MAX

        # Calculate score
        optimal_sat = 50
        deviation = abs(saturation_pct - optimal_sat)
        score = float(max(0, 100 - (deviation / optimal_sat) * 100))

        if saturation_pct < self.SATURATION_MIN:
            message = f"Video appears desaturated (estimated: {saturation_pct:.1f}%). Consider increasing saturation."
        elif saturation_pct > self.SATURATION_MAX:
            message = f"Video appears oversaturated (estimated: {saturation_pct:.1f}%). Consider reducing saturation."
        else:
            message = f"Saturation is well-balanced (estimated: {saturation_pct:.1f}%)"

        return QualityReport(
            check_name="saturation",
            passed=passed,
            score=score,
            message=message,
            details={"saturation_pct": saturation_pct, "u_mean": u_mean, "v_mean": v_mean},
        )

    def check_audio_levels(self, video: str) -> QualityReport:
        """Check audio isn't clipping or too quiet."""
        loudness_data = self._analyze_loudnorm(video)

        if not loudness_data:
            # Check if video has audio
            cmd = [
                "ffprobe",
                "-v", "error",
                "-select_streams", "a:0",
                "-show_entries", "stream=codec_type",
                "-of", "csv=p=0",
                video,
            ]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if "audio" not in result.stdout.lower():
                    return QualityReport(
                        check_name="audio_levels",
                        passed=True,
                        score=100.0,
                        message="No audio stream detected in video",
                        details={"has_audio": False},
                    )
            except Exception:
                pass

            return QualityReport(
                check_name="audio_levels",
                passed=False,
                score=0.0,
                message="Could not analyze audio levels (analysis failed)",
                details={},
            )

        # Parse loudnorm output
        input_i = float(loudness_data.get("input_i", "-70"))  # Integrated LUFS
        input_tp = float(loudness_data.get("input_tp", "-10"))  # True peak dBTP
        input_lra = float(loudness_data.get("input_lra", "1"))  # Loudness range

        # Check against thresholds
        loudness_ok = self.AUDIO_LUFS_MIN <= input_i <= self.AUDIO_LUFS_MAX
        peak_ok = input_tp <= self.AUDIO_TRUE_PEAK_MAX

        passed = loudness_ok and peak_ok

        # Calculate score
        target_lufs = self.AUDIO_LUFS_TARGET
        deviation = abs(input_i - target_lufs)
        score = float(max(0, 100 - (deviation / 10) * 20))  # 20 points per dB deviation

        if input_tp > self.AUDIO_TRUE_PEAK_MAX:
            score = float(score * 0.5)  # Penalize clipping heavily

        messages = []
        if input_i < self.AUDIO_LUFS_MIN:
            messages.append(f"Audio is too quiet ({input_i:.1f} LUFS). Target: {self.AUDIO_LUFS_TARGET} LUFS")
        elif input_i > self.AUDIO_LUFS_MAX:
            messages.append(f"Audio is too loud ({input_i:.1f} LUFS). Target: {self.AUDIO_LUFS_TARGET} LUFS")
        else:
            messages.append(f"Audio loudness is good ({input_i:.1f} LUFS)")

        if input_tp > self.AUDIO_TRUE_PEAK_MAX:
            messages.append(f"Audio is clipping ({input_tp:.1f} dBTP). Reduce volume to prevent distortion.")

        return QualityReport(
            check_name="audio_levels",
            passed=passed,
            score=score,
            message=" ".join(messages),
            details={
                "lufs": input_i,
                "true_peak": input_tp,
                "loudness_range": input_lra,
                "target_lufs": self.AUDIO_LUFS_TARGET,
            },
        )

    def check_color_balance(self, video: str) -> QualityReport:
        """Check for color casts (RGB balance)."""
        rgb = self._get_rgb_means(video)

        if rgb is None:
            return QualityReport(
                check_name="color_balance",
                passed=False,
                score=0.0,
                message="Could not analyze color balance (analysis failed)",
                details={},
            )

        r, g, b = rgb["r"], rgb["g"], rgb["b"]

        # Calculate deviation from neutral gray (all channels should be similar)
        avg = (r + g + b) / 3
        if avg == 0:
            avg = 1  # Prevent division by zero

        r_dev = abs(r - avg) / avg * 100
        g_dev = abs(g - avg) / avg * 100
        b_dev = abs(b - avg) / avg * 100

        max_deviation = max(r_dev, g_dev, b_dev)

        # Threshold for color cast detection (15% deviation)
        threshold = 15.0
        passed = max_deviation < threshold

        # Calculate score
        score = float(max(0, 100 - max_deviation * 3))  # 3 points per % deviation

        # Determine color cast
        cast = []
        if r > avg * 1.1:
            cast.append("red")
        elif r < avg * 0.9:
            cast.append("cyan")

        if g > avg * 1.1:
            cast.append("green")
        elif g < avg * 0.9:
            cast.append("magenta")

        if b > avg * 1.1:
            cast.append("blue")
        elif b < avg * 0.9:
            cast.append("yellow")

        if cast:
            cast_str = "/".join(cast)
            message = f"Color cast detected: {cast_str} (max deviation: {max_deviation:.1f}%). Consider white balance correction."
        else:
            message = f"Color balance is good (max deviation: {max_deviation:.1f}%)"

        return QualityReport(
            check_name="color_balance",
            passed=passed,
            score=score,
            message=message,
            details={
                "r_mean": r,
                "g_mean": g,
                "b_mean": b,
                "max_deviation": max_deviation,
                "color_cast": cast if cast else None,
            },
        )

    def run_all_checks(self, video: str) -> list[QualityReport]:
        """Run all quality checks and return reports."""
        checks = [
            self.check_brightness(video),
            self.check_contrast(video),
            self.check_saturation(video),
            self.check_audio_levels(video),
            self.check_color_balance(video),
        ]
        return checks

    def generate_report(self, video: str) -> dict[str, Any]:
        """Generate comprehensive quality report."""
        checks = self.run_all_checks(video)
        overall_score = sum(c.score for c in checks) / len(checks)
        all_passed = all(c.passed for c in checks)

        return {
            "video": video,
            "overall_score": round(overall_score, 1),
            "all_passed": all_passed,
            "checks": [
                {
                    "name": c.check_name,
                    "passed": c.passed,
                    "score": round(c.score, 1),
                    "message": c.message,
                    "details": c.details,
                }
                for c in checks
            ],
            "recommendations": [
                c.message for c in checks if not c.passed
            ],
        }


def quality_check(video: str, fail_on_warning: bool = False) -> dict[str, Any]:
    """Public API for quality checking a video.

    Args:
        video: Path to video file
        fail_on_warning: If True, treat warnings as failures

    Returns:
        Quality report dictionary
    """
    guardrails = VisualQualityGuardrails()
    report = guardrails.generate_report(video)

    if fail_on_warning:
        # Any score below 80 is considered a failure
        report["all_passed"] = report["overall_score"] >= 80

    return report
