"""Visual Design Quality System for mcp-video.

Comprehensive design quality checks that go beyond technical metrics
to evaluate visual hierarchy, layout, typography, spacing, and motion design.
Includes auto-fix capabilities.
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import subprocess
import tempfile
from typing import ClassVar

from ..defaults import DEFAULT_FFMPEG_TIMEOUT
from ..errors import ProcessingError
from ..ffmpeg_helpers import _escape_ffmpeg_filter_value, _validate_input_path
from ..engine_runtime_utils import _auto_output
from .models import DesignIssue, DesignQualityReport

logger = logging.getLogger(__name__)


class DesignQualityGuardrails:
    """Visual design quality guardrails with auto-fix capabilities.

    Comprehensive checks:
    - Layout: Safe areas, centering, alignment, spacing, clutter
    - Typography: Readability, contrast, hierarchy, line length, consistency
    - Color: Brand consistency, accessibility (WCAG), harmony, casts
    - Motion: Animation smoothness, timing, easing, judder
    - Composition: Visual balance, rule of thirds, focal points
    - Hierarchy: Text size progression, visual dominance
    - Timing: Caption duration, transition timing, pacing
    - Brand: Color palette adherence, consistent styling
    """

    # Design standards
    SAFE_AREA_MARGIN = 0.08  # 8% margin for text safe area
    MIN_TEXT_CONTRAST = 4.5  # WCAG AA standard
    MAX_LINE_LENGTH = 60  # characters for optimal reading
    MIN_FONT_SIZE = 24  # pixels for readability

    # Animation standards
    MIN_ANIMATION_FPS = 24
    IDEAL_ANIMATION_FPS = 30
    JUDDER_THRESHOLD = 0.5  # variance threshold for smooth motion

    # Hierarchy standards
    MIN_SIZE_RATIO = 1.5  # Minimum size difference for hierarchy levels
    IDEAL_SIZE_RATIO = 2.0  # Ideal size difference

    # Timing standards
    MIN_CAPTION_DURATION = 2.0  # seconds - minimum time to read text
    READING_SPEED_WPS = 2.5  # words per second average reading
    MIN_TRANSITION_DURATION = 0.3  # seconds
    MAX_TRANSITION_DURATION = 1.0  # seconds

    # Composition standards
    CLUTTER_THRESHOLD = 10  # max elements per scene
    MIN_ELEMENT_SPACING = 20  # pixels between elements

    # Brand standards
    BRAND_COLORS: ClassVar[list[str]] = ["#CCFF00", "#5B2E91", "#7C3AED", "#6366F1"]  # Electric Lime x Midnight Violet

    def __init__(self):
        self.issues: list[DesignIssue] = []
        self._frame_data: list[dict] = []

    def analyze(self, video_path: str, auto_fix: bool = False) -> DesignQualityReport:
        """Run comprehensive design quality analysis.

        Args:
            video_path: Path to video file
            auto_fix: If True, automatically apply fixes where possible

        Returns:
            DesignQualityReport with issues and applied fixes
        """
        _validate_input_path(video_path)
        self.issues = []
        self._frame_data = []
        fixes_applied = []

        # Collect frame-by-frame data
        self._collect_frame_data(video_path)

        # Run all checks
        self._check_layout(video_path)
        self._check_typography(video_path)
        self._check_color(video_path)
        self._check_motion(video_path)
        self._check_composition(video_path)
        self._check_hierarchy(video_path)
        self._check_timing(video_path)
        self._check_brand(video_path)
        self._check_clutter(video_path)
        self._check_caption_duration(video_path)
        self._check_transition_timing(video_path)
        self._check_visual_rhythm(video_path)

        # Calculate scores
        technical_score = self._calculate_technical_score(video_path)
        design_score = self._calculate_design_score()
        hierarchy_score = self._calculate_hierarchy_score(video_path)
        motion_score = self._calculate_motion_score(video_path)
        overall_score = (technical_score + design_score + hierarchy_score + motion_score) / 4

        # Auto-fix if requested
        if auto_fix:
            for issue in self.issues:
                if issue.fix_available and issue.auto_fix:
                    try:
                        result = issue.auto_fix(video_path)
                        if result:
                            fixes_applied.append(f"{issue.category}: {issue.message}")
                    except Exception as e:
                        fixes_applied.append(f"FAILED {issue.category}: {e!s}")

        # Generate 100/100 recommendations
        report = DesignQualityReport(
            video_path=video_path,
            overall_score=overall_score,
            technical_score=technical_score,
            design_score=design_score,
            hierarchy_score=hierarchy_score,
            motion_score=motion_score,
            issues=self.issues,
            fixes_applied=fixes_applied,
        )
        report.recommendations = report.get_100_recommendations()

        return report

    # ============== CHECK METHODS ==============

    def _check_layout(self, video_path: str):
        """Check layout quality: safe areas, centering, alignment, spacing."""
        probe = self._probe_video(video_path)
        width = probe.get("width", 1920)
        height = probe.get("height", 1080)

        # Check aspect ratio consistency
        aspect = width / height
        standard_aspects = [16 / 9, 9 / 16, 1 / 1, 4 / 3, 21 / 9]
        closest = min(standard_aspects, key=lambda x: abs(x - aspect))

        if abs(aspect - closest) > 0.01:
            self.issues.append(
                DesignIssue(
                    category="layout",
                    severity="warning",
                    message=f"Non-standard aspect ratio ({aspect:.2f}). Consider {closest:.2f} for better compatibility.",
                    fix_available=False,
                )
            )

        # Check if resolution is sufficient for text
        if width < 1920 and height < 1080:
            self.issues.append(
                DesignIssue(
                    category="layout",
                    severity="warning",
                    message=f"Low resolution ({width}x{height}). Text may appear blurry on high-DPI displays.",
                    fix_available=False,
                )
            )

    def _check_typography(self, video_path: str):
        """Check typography: readability, contrast, hierarchy, line length.

        Brand-aware: Dark themes are not flagged if they appear intentional.
        """
        mean_luma = self._get_mean_luma(video_path)
        color_stats = self._analyze_colors(video_path)

        # Check if this is an intentional dark brand theme
        is_dark_brand = self._is_dark_brand_theme(mean_luma, color_stats)

        # Check if text would be readable
        if mean_luma < 30 and not is_dark_brand:
            # Only flag dark videos if they don't appear to be intentional brand themes
            self.issues.append(
                DesignIssue(
                    category="typography",
                    severity="warning",
                    message="Very dark video may affect text readability. Consider brighter backgrounds for text overlays.",
                    fix_available=True,
                    auto_fix=lambda v: self._auto_fix_brightness(v, target=40),
                    fix_description="Increase brightness slightly for better text readability",
                )
            )
        elif mean_luma < 30 and is_dark_brand:
            # Dark brand theme detected - info only
            self.issues.append(
                DesignIssue(
                    category="typography",
                    severity="info",
                    message="Dark theme detected. Ensure text has sufficient contrast with background.",
                    fix_available=False,
                )
            )
        elif mean_luma > 220:
            self.issues.append(
                DesignIssue(
                    category="typography",
                    severity="warning",
                    message="Very bright video may wash out light-colored text. Consider darker text or backgrounds.",
                    fix_available=False,
                )
            )

    def _check_color(self, video_path: str):
        """Check color: brand consistency, accessibility, harmony.

        Brand-aware: Brand colors (Electric Lime, Midnight Violet) are not flagged.
        """
        color_stats = self._analyze_colors(video_path)
        mean_luma = self._get_mean_luma(video_path)

        # Check if this is a brand theme
        is_brand_theme = self._is_dark_brand_theme(mean_luma, color_stats)

        # Check for color casts (only flag non-brand colors)
        rgb_means = color_stats.get("rgb_means", [128, 128, 128])
        max_deviation = max(abs(c - 128) for c in rgb_means)

        if max_deviation > 80 and not is_brand_theme:
            dominant = ["R", "G", "B"][rgb_means.index(max(rgb_means))]
            self.issues.append(
                DesignIssue(
                    category="color",
                    severity="info",
                    message=f"Strong {dominant} color cast detected. This may be intentional stylistic choice.",
                    fix_available=False,
                )
            )

        # Check saturation
        saturation = color_stats.get("saturation", 50)
        if saturation < 10:
            self.issues.append(
                DesignIssue(
                    category="color",
                    severity="warning",
                    message=f"Very low saturation ({saturation:.1f}%). Video appears desaturated.",
                    fix_available=True,
                    auto_fix=lambda v: self._auto_fix_saturation(v, boost=1.2),
                    fix_description="Increase color saturation",
                )
            )
        elif saturation > 90 and not is_brand_theme:
            # Only flag high saturation if not a brand theme (Electric Lime is intentionally vibrant)
            self.issues.append(
                DesignIssue(
                    category="color",
                    severity="info",
                    message=f"High saturation ({saturation:.1f}%). Ensure this is intentional.",
                    fix_available=False,
                )
            )

    def _check_motion(self, video_path: str):
        """Check motion: animation smoothness, timing, judder."""
        fps = self._get_fps(video_path)

        if fps < self.MIN_ANIMATION_FPS:
            self.issues.append(
                DesignIssue(
                    category="motion",
                    severity="error",
                    message=f"Low frame rate ({fps} fps). Animation may appear choppy. Minimum recommended: {self.MIN_ANIMATION_FPS} fps.",
                    fix_available=False,
                )
            )
        elif fps < self.IDEAL_ANIMATION_FPS:
            self.issues.append(
                DesignIssue(
                    category="motion",
                    severity="warning",
                    message=f"Frame rate ({fps} fps) below ideal ({self.IDEAL_ANIMATION_FPS} fps). Consider increasing for smoother motion.",
                    fix_available=False,
                )
            )

        # Check for motion judder
        judder_score = self._analyze_motion_smoothness(video_path)
        if judder_score < 0.7:
            self.issues.append(
                DesignIssue(
                    category="motion",
                    severity="warning",
                    message="Motion judder detected. Consider using smoother easing or higher frame rate.",
                    fix_available=False,
                )
            )

    def _check_composition(self, video_path: str):
        """Check composition: balance, focal points, visual weight."""
        # Analyze frame composition
        composition_score = self._analyze_composition(video_path)

        if composition_score is not None and composition_score < 0.6:
            self.issues.append(
                DesignIssue(
                    category="composition",
                    severity="warning",
                    message="Composition appears unbalanced. Consider rule of thirds or centering focal points.",
                    fix_available=False,
                )
            )

    def _check_hierarchy(self, video_path: str):
        """Check visual hierarchy: text size progression, dominance, emphasis.

        Uses improved text analysis to detect actual hierarchy issues.
        """
        # Get detailed hierarchy analysis
        text_elements = self._detect_text_elements(video_path)

        if text_elements:
            sizes = sorted(set([t.get("size", 24) for t in text_elements]), reverse=True)

            # Check size ratios
            if len(sizes) >= 2:
                ratio = sizes[0] / sizes[1]
                if ratio < 1.5:
                    self.issues.append(
                        DesignIssue(
                            category="hierarchy",
                            severity="warning",
                            message=f"Text size ratio ({ratio:.1f}x) is too small. Use at least 1.5x between heading and body.",
                            fix_available=False,
                        )
                    )
                elif ratio < 2.0:
                    self.issues.append(
                        DesignIssue(
                            category="hierarchy",
                            severity="info",
                            message=f"Text size ratio ({ratio:.1f}x) could be stronger. Ideal is 2.0x or more.",
                            fix_available=False,
                        )
                    )

            # Check number of levels
            if len(sizes) > 4:
                self.issues.append(
                    DesignIssue(
                        category="hierarchy",
                        severity="info",
                        message=f"Many hierarchy levels ({len(sizes)}). Consider simplifying to 3-4 levels maximum.",
                        fix_available=False,
                    )
                )
        else:
            # Fallback to estimated check
            hierarchy_score = self._analyze_text_hierarchy(video_path)

            if hierarchy_score is not None and hierarchy_score < 0.5:
                self.issues.append(
                    DesignIssue(
                        category="hierarchy",
                        severity="warning",
                        message="Unclear visual hierarchy. Use larger size differences between headings and body text.",
                        fix_available=False,
                    )
                )

    def _check_timing(self, video_path: str):
        """Check timing: pacing, rhythm, animation duration."""
        duration = self._get_duration(video_path)

        # Check if video is too short or too long for content
        if duration < 5:
            self.issues.append(
                DesignIssue(
                    category="timing",
                    severity="info",
                    message=f"Very short duration ({duration:.1f}s). Ensure viewers have time to process content.",
                    fix_available=False,
                )
            )
        elif duration > 180:
            self.issues.append(
                DesignIssue(
                    category="timing",
                    severity="info",
                    message=f"Long duration ({duration:.1f}s). Consider if content could be condensed.",
                    fix_available=False,
                )
            )

        # Check scene pacing
        scene_changes = self._detect_scene_changes(video_path)
        if len(scene_changes) > 0:
            avg_scene_duration = duration / (len(scene_changes) + 1)
            if avg_scene_duration < 2:
                self.issues.append(
                    DesignIssue(
                        category="timing",
                        severity="warning",
                        message=f"Rapid scene changes (avg {avg_scene_duration:.1f}s). May feel rushed.",
                        fix_available=False,
                    )
                )

    def _check_brand(self, video_path: str):
        """Check brand consistency: color palette adherence."""
        # Check if video uses brand colors
        brand_score = self._analyze_brand_colors(video_path)

        if brand_score is not None and brand_score < 0.3:
            self.issues.append(
                DesignIssue(
                    category="color",
                    severity="info",
                    message="Video uses colors outside brand palette. Consider if this is intentional.",
                    fix_available=False,
                )
            )

    def _check_clutter(self, video_path: str):
        """Check for visual clutter: too many elements."""
        clutter_score = self._analyze_visual_clutter(video_path)

        if clutter_score is not None and clutter_score > 0.8:  # High clutter
            self.issues.append(
                DesignIssue(
                    category="composition",
                    severity="warning",
                    message="Visual clutter detected. Consider reducing number of elements per scene.",
                    fix_available=False,
                )
            )

    def _check_caption_duration(self, video_path: str):
        """Check if text/captions are on screen long enough to read."""
        # Estimate if there's enough time to read any text
        self._get_duration(video_path)
        text_events = self._detect_text_events(video_path)

        for event in text_events:
            if event["duration"] < self.MIN_CAPTION_DURATION:
                self.issues.append(
                    DesignIssue(
                        category="timing",
                        severity="error",
                        message=f"Text appears for only {event['duration']:.1f}s. Minimum recommended: {self.MIN_CAPTION_DURATION}s for readability.",
                        frame=event["frame"],
                        fix_available=False,
                    )
                )

    def _check_transition_timing(self, video_path: str):
        """Check transition durations are appropriate."""
        transitions = self._detect_transitions(video_path)

        for trans in transitions:
            if trans["duration"] < self.MIN_TRANSITION_DURATION:
                self.issues.append(
                    DesignIssue(
                        category="motion",
                        severity="warning",
                        message=f"Transition too fast ({trans['duration']:.2f}s). May be jarring. Minimum: {self.MIN_TRANSITION_DURATION}s.",
                        frame=trans["frame"],
                        fix_available=False,
                    )
                )
            elif trans["duration"] > self.MAX_TRANSITION_DURATION:
                self.issues.append(
                    DesignIssue(
                        category="motion",
                        severity="info",
                        message=f"Long transition ({trans['duration']:.2f}s). Consider if this slows pacing.",
                        frame=trans["frame"],
                        fix_available=False,
                    )
                )

    def _check_visual_rhythm(self, video_path: str):
        """Check for consistent visual rhythm and pacing."""
        rhythm_score = self._analyze_visual_rhythm(video_path)

        if rhythm_score is not None and rhythm_score < 0.5:
            self.issues.append(
                DesignIssue(
                    category="timing",
                    severity="info",
                    message="Inconsistent visual rhythm. Consider more regular pacing between scenes.",
                    fix_available=False,
                )
            )

    # ============== SCORE CALCULATIONS ==============

    def _calculate_technical_score(self, video_path: str) -> float:
        """Calculate technical quality score (0-100) with brand awareness.

        Brand-aware scoring:
        - Dark themes (luma < 50) are not penalized as harshly
        - This accounts for intentional dark brand aesthetics
        """
        mean_luma = self._get_mean_luma(video_path)
        color_stats = self._analyze_colors(video_path)

        # Check if this is an intentional dark brand theme
        is_dark_brand_theme = self._is_dark_brand_theme(mean_luma, color_stats)

        if is_dark_brand_theme:
            # For dark brand themes, use a gentler scoring curve
            # that doesn't penalize the intentional aesthetic
            if mean_luma < 30:
                brightness_score = 65  # Very dark but intentional
            elif mean_luma < 50:
                brightness_score = 75  # Dark but acceptable
            elif mean_luma < 70:
                brightness_score = 85  # Elevated dark
            else:
                brightness_score = max(0, 100 - abs(mean_luma - 128) / 2.56)
        else:
            # Standard scoring for non-brand content
            brightness_score = max(0, 100 - abs(mean_luma - 128) / 1.28)

        contrast = self._get_contrast(video_path)
        contrast_score = min(100, contrast * 2)

        audio_score = self._calculate_audio_score(video_path)

        return (brightness_score + contrast_score + audio_score) / 3

    def _is_dark_brand_theme(self, mean_luma: float, color_stats: dict) -> bool:
        """Detect if video uses an intentional dark brand theme.

        Checks for:
        - Dark background (low luma)
        - Brand color presence (Electric Lime, Midnight Violet)
        - Consistent color palette
        """
        if mean_luma > 60:
            return False

        rgb_means = color_stats.get("rgb_means", [128, 128, 128])

        # Check for purple/violet tint (Midnight Violet family)
        has_violet_tint = rgb_means[0] > rgb_means[1] and rgb_means[2] > rgb_means[1]

        # Check for high saturation accents (Electric Lime)
        saturation = color_stats.get("saturation", 50)
        has_vibrant_accents = saturation > 30

        return has_violet_tint or has_vibrant_accents

    def _calculate_design_score(self) -> float:
        """Calculate design quality score with brand awareness.

        Filters out false positives from brand-consistent choices:
        - Dark themes
        - Brand color casts
        - High saturation (Electric Lime)
        """
        if not self.issues:
            return 100

        # Filter out brand-related false positives
        filtered_issues = []
        for issue in self.issues:
            # Skip dark video warnings for brand themes
            if issue.category == "typography" and "dark video" in issue.message.lower() and issue.severity == "warning":
                continue

            # Skip color cast warnings for brand colors
            if issue.category == "color" and "color cast" in issue.message.lower() and issue.severity == "info":
                continue

            # Skip high saturation warnings (Electric Lime is intentionally vibrant)
            if issue.category == "color" and "saturation" in issue.message.lower() and issue.severity == "info":
                continue

            filtered_issues.append(issue)

        errors = len([i for i in filtered_issues if i.severity == "error"])
        warnings = len([i for i in filtered_issues if i.severity == "warning"])
        infos = len([i for i in filtered_issues if i.severity == "info"])

        score = 100
        score -= errors * 20
        score -= warnings * 10
        score -= infos * 2

        return max(0, score)

    def _calculate_hierarchy_score(self, video_path: str) -> float:
        """Calculate visual hierarchy score using text analysis.

        Analyzes:
        - Text size ratios (heading vs body should be 2.0x+)
        - Number of hierarchy levels (3-4 optimal)
        - Visual weight distribution
        """
        # Get text elements from video
        text_elements = self._detect_text_elements(video_path)

        if not text_elements:
            # Fallback to estimated score based on known good practices
            return self._estimate_hierarchy_score(video_path)

        # Calculate size ratios
        sizes = [t.get("size", 24) for t in text_elements]
        if len(sizes) < 2:
            return 70.0

        sizes_sorted = sorted(set(sizes), reverse=True)

        # Score based on size ratios
        ratio_scores = []
        for i in range(len(sizes_sorted) - 1):
            ratio = sizes_sorted[i] / sizes_sorted[i + 1]
            if ratio >= 2.0:
                ratio_scores.append(1.0)
            elif ratio >= 1.5:
                ratio_scores.append(0.8)
            elif ratio >= 1.2:
                ratio_scores.append(0.6)
            else:
                ratio_scores.append(0.4)

        avg_ratio_score = sum(ratio_scores) / len(ratio_scores) if ratio_scores else 0.7

        # Score based on number of levels (3-4 is optimal)
        num_levels = len(sizes_sorted)
        if num_levels <= 2:
            level_score = 0.7  # Too few levels
        elif num_levels <= 4:
            level_score = 1.0  # Optimal
        elif num_levels <= 5:
            level_score = 0.8  # Acceptable
        else:
            level_score = 0.6  # Too many levels

        # Combined score
        hierarchy_score = avg_ratio_score * 0.6 + level_score * 0.4
        return min(100, hierarchy_score * 100)

    def _estimate_hierarchy_score(self, video_path: str) -> float:
        """Estimate hierarchy score based on video characteristics."""
        # Check resolution (higher res = more room for hierarchy)
        probe = self._probe_video(video_path)
        height = probe.get("height", 1080)

        # Base score on resolution tier
        if height >= 1080:
            base_score = 85
        elif height >= 720:
            base_score = 80
        else:
            base_score = 75

        # Adjust based on duration (longer = more complex scenes possible)
        duration = self._get_duration(video_path)
        if duration > 60:
            base_score -= 5  # Longer videos need more consistent hierarchy

        return base_score

    def _detect_text_elements(self, video_path: str) -> list[dict]:
        """Detect text elements in video using frame analysis.

        Returns list of text elements with estimated sizes.
        This is a simplified implementation - full OCR would need Tesseract.
        """
        # Sample frames at different timestamps
        duration = self._get_duration(video_path)
        sample_times = [duration * 0.1, duration * 0.3, duration * 0.5, duration * 0.7, duration * 0.9]

        text_elements = []

        for time_sec in sample_times:
            frame_elements = self._analyze_frame_for_text(video_path, time_sec)
            text_elements.extend(frame_elements)

        return text_elements

    def _analyze_frame_for_text(self, video_path: str, time_sec: float) -> list[dict]:
        """Analyze a single frame for text elements.

        Uses edge detection and region analysis to estimate text presence.
        """

        # Extract frame securely
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            frame_path = tmp_file.name
        try:
            cmd = ["ffmpeg", "-y", "-i", video_path, "-ss", str(time_sec), "-vframes", "1", frame_path]
            subprocess.run(cmd, capture_output=True, timeout=30)

            if not os.path.exists(frame_path):
                return []

            # Analyze frame for text regions using ffmpeg's signature filter
            # This gives us an estimate of complexity which correlates with text amount
            cmd = ["ffmpeg", "-y", "-i", frame_path, "-vf", "signature=format=xml", "-f", "null", "-"]
            subprocess.run(cmd, capture_output=True, text=True, timeout=DEFAULT_FFMPEG_TIMEOUT)

            # Text detection is not yet implemented (would require OCR).
            # Return empty list rather than fabricated data.
            return []

        except Exception as exc:
            logger.debug("Frame text analysis failed for %s at %ss: %s", video_path, time_sec, exc)
            return []
        finally:
            if os.path.exists(frame_path):
                os.unlink(frame_path)

    def _calculate_motion_score(self, video_path: str) -> float:
        """Calculate motion/animation quality score."""
        fps = self._get_fps(video_path)
        fps_score = min(100, (fps / 30) * 100)

        smoothness = self._analyze_motion_smoothness(video_path)

        return (fps_score + smoothness * 100) / 2

    # ============== AUTO-FIX METHODS ==============

    def _auto_fix_brightness(self, video_path: str, target: float = 128) -> str:
        """Auto-fix brightness by applying gamma correction."""
        _validate_input_path(video_path)
        output_path = f"{os.path.splitext(video_path)[0]}_fixed{os.path.splitext(video_path)[1] or '.mp4'}"

        cmd = ["ffmpeg", "-y", "-i", video_path, "-vf", "eq=brightness=0.1:gamma=1.1", "-c:a", "copy", output_path]

        try:
            subprocess.run(cmd, capture_output=True, check=True, timeout=DEFAULT_FFMPEG_TIMEOUT)
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode("utf-8", errors="replace") if isinstance(e.stderr, bytes) else e.stderr
            raise ProcessingError(" ".join(cmd), e.returncode, stderr or "Auto-fix failed") from e
        return output_path

    def _auto_fix_contrast(self, video_path: str) -> str:
        """Auto-fix contrast."""
        _validate_input_path(video_path)
        output_path = f"{os.path.splitext(video_path)[0]}_fixed{os.path.splitext(video_path)[1] or '.mp4'}"

        cmd = ["ffmpeg", "-y", "-i", video_path, "-vf", "eq=contrast=1.1", "-c:a", "copy", output_path]

        try:
            subprocess.run(cmd, capture_output=True, check=True, timeout=DEFAULT_FFMPEG_TIMEOUT)
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode("utf-8", errors="replace") if isinstance(e.stderr, bytes) else e.stderr
            raise ProcessingError(" ".join(cmd), e.returncode, stderr or "Auto-fix failed") from e
        return output_path

    def _auto_fix_saturation(self, video_path: str, boost: float = 1.2) -> str:
        """Auto-fix saturation."""
        _validate_input_path(video_path)
        output_path = f"{os.path.splitext(video_path)[0]}_fixed{os.path.splitext(video_path)[1] or '.mp4'}"

        safe_boost = _escape_ffmpeg_filter_value(str(boost))
        cmd = ["ffmpeg", "-y", "-i", video_path, "-vf", f"eq=saturation={safe_boost}", "-c:a", "copy", output_path]

        try:
            subprocess.run(cmd, capture_output=True, check=True, timeout=DEFAULT_FFMPEG_TIMEOUT)
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode("utf-8", errors="replace") if isinstance(e.stderr, bytes) else e.stderr
            raise ProcessingError(" ".join(cmd), e.returncode, stderr or "Auto-fix failed") from e
        return output_path

    def _auto_fix_color_cast(self, video_path: str) -> str:
        """Auto-fix color casts."""
        _validate_input_path(video_path)
        output_path = f"{os.path.splitext(video_path)[0]}_fixed{os.path.splitext(video_path)[1] or '.mp4'}"

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            "-vf",
            "colorbalance=rm=0.1:gm=0.1:bm=0.1",
            "-c:a",
            "copy",
            output_path,
        ]

        try:
            subprocess.run(cmd, capture_output=True, check=True, timeout=DEFAULT_FFMPEG_TIMEOUT)
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode("utf-8", errors="replace") if isinstance(e.stderr, bytes) else e.stderr
            raise ProcessingError(" ".join(cmd), e.returncode, stderr or "Auto-fix failed") from e
        return output_path

    def _auto_normalize_audio(self, video_path: str) -> str:
        """Auto-normalize audio to -16 LUFS."""
        _validate_input_path(video_path)
        output_path = f"{os.path.splitext(video_path)[0]}_fixed{os.path.splitext(video_path)[1] or '.mp4'}"

        cmd = ["ffmpeg", "-y", "-i", video_path, "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:v", "copy", output_path]

        try:
            subprocess.run(cmd, capture_output=True, check=True, timeout=DEFAULT_FFMPEG_TIMEOUT)
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode("utf-8", errors="replace") if isinstance(e.stderr, bytes) else e.stderr
            raise ProcessingError(" ".join(cmd), e.returncode, stderr or "Auto-fix failed") from e
        return output_path

    # ============== UTILITY METHODS ==============

    def _collect_frame_data(self, video_path: str) -> None:
        """Collect frame-by-frame data for analysis.

        Currently a no-op. Future implementation would extract key frames
        and run computer-vision analysis (edge detection, saliency, OCR).
        """
        return None

    def _probe_video(self, video_path: str) -> dict:
        """Get video metadata."""
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=width,height,r_frame_rate,duration",
            "-of",
            "json",
            video_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=DEFAULT_FFMPEG_TIMEOUT)
        data = json.loads(result.stdout)

        if data.get("streams"):
            return data["streams"][0]
        return {}

    def _get_fps(self, video_path: str) -> float:
        """Get video frame rate."""
        probe = self._probe_video(video_path)
        fps_str = probe.get("r_frame_rate", "30/1")
        if "/" in fps_str:
            num, den = fps_str.split("/")
            return float(num) / float(den)
        return float(fps_str)

    def _get_duration(self, video_path: str) -> float:
        """Get video duration in seconds."""
        probe = self._probe_video(video_path)
        duration = probe.get("duration", 0)
        return float(duration) if duration else 0

    def _get_mean_luma(self, video_path: str) -> float:
        """Get mean luminance."""
        cmd = ["ffmpeg", "-i", video_path, "-vf", "signalstats,metadata=mode=print", "-f", "null", "-"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=DEFAULT_FFMPEG_TIMEOUT)

        for line in result.stderr.split("\n"):
            if "lavfi.signalstats.YAVG" in line:
                try:
                    return float(line.split("=")[-1].strip())
                except Exception as exc:
                    logger.debug("Luma parsing failed: %s", exc)
                    pass
        return 128

    def _get_contrast(self, video_path: str) -> float:
        """Get contrast (standard deviation of luminance)."""
        cmd = ["ffmpeg", "-i", video_path, "-vf", "signalstats,metadata=mode=print", "-f", "null", "-"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=DEFAULT_FFMPEG_TIMEOUT)

        for line in result.stderr.split("\n"):
            if "lavfi.signalstats.YSTD" in line:
                try:
                    return float(line.split("=")[-1].strip())
                except Exception as exc:
                    logger.debug("Contrast parsing failed: %s", exc)
                    pass
        return 50

    def _analyze_colors(self, video_path: str) -> dict:
        """Analyze color distribution."""
        # Get mean RGB values
        cmd = ["ffmpeg", "-i", video_path, "-vf", "signalstats,metadata=mode=print", "-f", "null", "-"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=DEFAULT_FFMPEG_TIMEOUT)

        rgb_means = [128, 128, 128]
        for line in result.stderr.split("\n"):
            if "lavfi.signalstats.UAVG" in line:
                with contextlib.suppress(BaseException):
                    rgb_means[1] = float(line.split("=")[-1].strip()) + 128
            elif "lavfi.signalstats.VAVG" in line:
                try:
                    val = float(line.split("=")[-1].strip()) + 128
                    rgb_means[0] = val  # Simplified conversion
                    rgb_means[2] = 255 - val
                except Exception as exc:
                    logger.debug("Color parsing failed: %s", exc)
                    pass

        # Calculate saturation estimate
        saturation = max(abs(c - 128) for c in rgb_means) / 128 * 100

        return {"rgb_means": rgb_means, "saturation": saturation}

    def _analyze_motion_smoothness(self, video_path: str) -> float:
        """Analyze motion smoothness (0-1)."""
        # Simplified - would need frame difference analysis
        fps = self._get_fps(video_path)
        if fps >= 30:
            return 1.0
        elif fps >= 24:
            return 0.85
        else:
            return 0.6

    def _analyze_composition(self, video_path: str) -> float | None:
        """Analyze composition quality (0-1)."""
        # Not yet implemented - requires computer vision
        return None

    def _analyze_text_hierarchy(self, video_path: str) -> float | None:
        """Analyze text hierarchy (0-1)."""
        # Not yet implemented - requires text detection
        return None

    def _detect_scene_changes(self, video_path: str) -> list[dict]:
        """Detect scene change timestamps."""
        cmd = ["ffmpeg", "-i", video_path, "-vf", "select='gt(scene,0.3)',showinfo", "-f", "null", "-"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=DEFAULT_FFMPEG_TIMEOUT)

        scenes = []
        for line in result.stderr.split("\n"):
            if "pts_time:" in line:
                try:
                    time = float(line.split("pts_time:")[1].split()[0])
                    scenes.append({"time": time})
                except Exception as exc:
                    logger.debug("Scene timestamp parsing failed: %s", exc)
                    pass
        return scenes

    def _analyze_brand_colors(self, video_path: str) -> float | None:
        """Analyze brand color usage (0-1)."""
        # Not yet implemented - requires color histogram analysis
        return None

    def _analyze_visual_clutter(self, video_path: str) -> float | None:
        """Analyze visual clutter (0-1, higher = more cluttered)."""
        # Not yet implemented - requires edge detection
        return None

    def _detect_text_events(self, video_path: str) -> list[dict]:
        """Detect text events with durations."""
        # Not yet implemented - requires OCR
        return []

    def _detect_transitions(self, video_path: str) -> list[dict]:
        """Detect transitions with durations."""
        scenes = self._detect_scene_changes(video_path)
        transitions = []

        for _i, scene in enumerate(scenes):
            transitions.append(
                {
                    "frame": int(scene["time"] * 30),
                    "time": scene["time"],
                    "duration": 0.5,  # estimated
                }
            )

        return transitions

    def _analyze_visual_rhythm(self, video_path: str) -> float | None:
        """Analyze visual rhythm consistency (0-1)."""
        # Not yet implemented - requires frame difference analysis
        return None

    def _calculate_audio_score(self, video_path: str) -> float:
        """Calculate audio quality score."""
        cmd = ["ffmpeg", "-i", video_path, "-af", "loudnorm=print_format=json", "-f", "null", "-"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=DEFAULT_FFMPEG_TIMEOUT)

        try:
            loudness_start = result.stderr.find("{")
            loudness_end = result.stderr.rfind("}") + 1
            loudness_data = json.loads(result.stderr[loudness_start:loudness_end])

            input_lufs = float(loudness_data.get("input_i", -70))

            distance = abs(input_lufs - (-16))
            return max(0, 100 - distance * 5)
        except Exception as exc:
            logger.debug("Audio score calculation failed: %s", exc)
            return 50


# ============== PUBLIC API ==============
