"""Visual Design Quality System for mcp-video."""

from __future__ import annotations

from ..ffmpeg_helpers import _validate_input_path
from .guardrails import DesignQualityGuardrails
from .models import DesignIssue, DesignQualityReport


def design_quality_check(
    video: str,
    auto_fix: bool = False,
    strict: bool = False,
) -> DesignQualityReport:
    _validate_input_path(video)
    guardrails = DesignQualityGuardrails(strict=strict)
    return guardrails.check(video, auto_fix=auto_fix)


def fix_design_issues(video: str, output: str | None = None) -> str:
    _validate_input_path(video)
    guardrails = DesignQualityGuardrails()
    return guardrails.fix_all(video, output=output)
