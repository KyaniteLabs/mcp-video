"""Tests for design guardrails — visual quality checks for text overlays."""

from __future__ import annotations

import pytest

from mcp_video.design_guardrails import (
    TextOverlaySpec,
    calculate_stacked_positions,
    contrast_ratio,
    validate_single_text,
    validate_text_layout,
)


class TestContrastRatio:
    def test_white_on_black(self):
        ratio = contrast_ratio("#FFFFFF", "#000000")
        assert ratio == pytest.approx(21.0, abs=0.1)

    def test_black_on_white(self):
        ratio = contrast_ratio("black", "white")
        assert ratio == pytest.approx(21.0, abs=0.1)

    def test_grey_on_grey(self):
        ratio = contrast_ratio("#808080", "#808080")
        assert ratio == pytest.approx(1.0, abs=0.1)

    def test_named_colors(self):
        ratio = contrast_ratio("red", "white")
        assert ratio > 3.0


class TestValidateSingleText:
    def test_clean_text_no_warnings(self):
        warnings = validate_single_text(
            text="Hello World",
            position="center",
            size=48,
            color="white",
            shadow=True,
            background_color="black",
        )
        assert len(warnings) == 0

    def test_low_contrast_warning(self):
        warnings = validate_single_text(
            text="Hello",
            position="center",
            size=48,
            color="#333333",
            shadow=False,
            background_color="black",
        )
        assert any(w.code == "low_contrast" for w in warnings)

    def test_text_too_small_warning(self):
        warnings = validate_single_text(
            text="Tiny",
            position="center",
            size=8,
            color="white",
            background_color="black",
        )
        assert any(w.code == "text_too_small" for w in warnings)

    def test_text_too_large_warning(self):
        warnings = validate_single_text(
            text="Huge",
            position="center",
            size=400,
            color="white",
            background_color="black",
        )
        assert any(w.code == "text_too_large" for w in warnings)

    def test_missing_shadow_info(self):
        warnings = validate_single_text(
            text="No shadow",
            position="center",
            size=48,
            color="#444444",
            shadow=False,
            background_color="black",
        )
        assert any(w.code == "missing_shadow" for w in warnings)


class TestValidateTextLayout:
    def test_overlapping_texts_detected(self):
        overlays = [
            TextOverlaySpec(text="Headline", position="center", size=120, color="white"),
            TextOverlaySpec(text="Subtitle", position="center", size=36, color="white"),
        ]
        warnings = validate_text_layout(overlays, background_color="black")
        assert any(w.code == "text_overlap" for w in warnings)

    def test_non_overlapping_texts_clean(self):
        overlays = [
            TextOverlaySpec(text="Top", position="top-center", size=48, color="white"),
            TextOverlaySpec(text="Bottom", position="bottom-center", size=48, color="white"),
        ]
        warnings = validate_text_layout(overlays, background_color="black")
        assert not any(w.code == "text_overlap" for w in warnings)

    def test_excessive_overlays_warning(self):
        overlays = [TextOverlaySpec(text=f"Text {i}", position="top-left", size=24, color="white") for i in range(6)]
        warnings = validate_text_layout(overlays, background_color="black")
        assert any(w.code == "excessive_overlays" for w in warnings)

    def test_time_separated_no_overlap(self):
        overlays = [
            TextOverlaySpec(text="A", position="center", size=120, color="white", start_time=0, duration=2),
            TextOverlaySpec(text="B", position="center", size=120, color="white", start_time=3, duration=2),
        ]
        warnings = validate_text_layout(overlays, background_color="black")
        assert not any(w.code == "text_overlap" for w in warnings)


class TestCalculateStackedPositions:
    def test_two_lines_centered(self):
        texts = [("Line 1", 48), ("Line 2", 36)]
        positions = calculate_stacked_positions(texts, base_position="center")
        assert len(positions) == 2
        assert positions[0]["y"] < positions[1]["y"]

    def test_top_position_stacks_downward(self):
        texts = [("Line 1", 48), ("Line 2", 36)]
        positions = calculate_stacked_positions(texts, base_position="top-center")
        assert len(positions) == 2
        assert positions[0]["y"] < positions[1]["y"]

    def test_bottom_position_stacks_upward(self):
        texts = [("Line 1", 48), ("Line 2", 36)]
        positions = calculate_stacked_positions(texts, base_position="bottom-center")
        assert len(positions) == 2
        # For bottom positions, the block grows upward
        assert positions[0]["y"] < positions[1]["y"]
