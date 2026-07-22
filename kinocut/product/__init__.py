"""Long-form stream-to-shorts product domain (additive).

Public surface for the shorts/highlight discovery workflow. Everything here is
strict, JSON-serialisable, and deterministic: callers consume plain models and
plain plans, never mutable engine state. The render operations emitted by these
models always live inside the existing ``kinocut.workflow.OP_ADAPTERS`` allowlist;
analysis (transcription, scene detection, audio probing) stays outside the render
op cursor.
"""

from __future__ import annotations

from .highlight_discovery import (
    discover_highlights as discover_highlights,
)
from .models import (
    CandidateMoment as CandidateMoment,
    HighlightDiscoveryConfig as HighlightDiscoveryConfig,
    HighlightDiscoveryResult as HighlightDiscoveryResult,
    SourceSignal as SourceSignal,
    TranscriptSegment as TranscriptSegment,
    canonical_dedup_key as canonical_dedup_key,
)

__all__ = [
    "CandidateMoment",
    "HighlightDiscoveryConfig",
    "HighlightDiscoveryResult",
    "SourceSignal",
    "TranscriptSegment",
    "discover_highlights",
]
