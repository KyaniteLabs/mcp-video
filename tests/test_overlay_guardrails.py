"""Tests for overlay/watermark/chroma key guardrails."""

import pytest

from mcp_video.validation import _validate_normalized_float, _validate_timing_against_duration
from mcp_video.errors import MCPVideoError


class TestValidateNormalizedFloat:
    def test_valid_midpoint(self):
        assert _validate_normalized_float(0.5) == 0.5

    def test_zero(self):
        assert _validate_normalized_float(0.0) == 0.0

    def test_one(self):
        assert _validate_normalized_float(1.0) == 1.0

    def test_negative_raises(self):
        with pytest.raises(MCPVideoError, match=r"between 0\.0 and 1\.0"):
            _validate_normalized_float(-0.1)

    def test_over_one_raises(self):
        with pytest.raises(MCPVideoError, match=r"between 0\.0 and 1\.0"):
            _validate_normalized_float(1.5)

    def test_custom_name_in_error(self):
        with pytest.raises(MCPVideoError, match="similarity"):
            _validate_normalized_float(2.0, "similarity")

    def test_non_numeric_raises(self):
        with pytest.raises(MCPVideoError, match="must be a number"):
            _validate_normalized_float("big", "opacity")

    def test_custom_range(self):
        assert _validate_normalized_float(5.0, "value", lo=0.0, hi=10.0) == 5.0
        with pytest.raises(MCPVideoError):
            _validate_normalized_float(11.0, "value", lo=0.0, hi=10.0)


class TestValidateTiming:
    def test_clean_timing(self):
        assert _validate_timing_against_duration(0.5, 1.0, 5.0) == []

    def test_none_times_clean(self):
        assert _validate_timing_against_duration(None, None, 5.0) == []

    def test_start_past_end_warns(self):
        warnings = _validate_timing_against_duration(10.0, 1.0, 5.0)
        assert any("never appear" in w for w in warnings)

    def test_end_past_duration_warns(self):
        warnings = _validate_timing_against_duration(0.0, 10.0, 5.0)
        assert any("disappear early" in w for w in warnings)

    def test_start_at_duration_warns(self):
        warnings = _validate_timing_against_duration(5.1, None, 5.0)
        assert any("never appear" in w for w in warnings)
