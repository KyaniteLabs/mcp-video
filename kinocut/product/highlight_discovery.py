"""Deterministic transcript-only highlight candidate discovery."""

from __future__ import annotations

import re
from collections.abc import Sequence
from itertools import pairwise

from .models import (
    CandidateMoment,
    HighlightDiscoveryConfig,
    HighlightDiscoveryResult,
    SourceSignal,
    TranscriptSegment,
    canonical_dedup_key,
)

_TERMINAL_RE = re.compile(r"[.!?](?:[\"')\]]+)?\s*$")


def discover_highlights(
    transcript: Sequence[TranscriptSegment],
    *,
    signals: Sequence[SourceSignal] = (),
    config: HighlightDiscoveryConfig | None = None,
) -> HighlightDiscoveryResult:
    """Discover bounded, complete-thought candidates from ordered segments.

    Candidate confidence is deliberately transcript-only. Signals that fall in a
    selected window are preserved as evidence for a later enrichment stage, but
    do not change discovery or ordering in this core slice.
    """
    cfg = config or HighlightDiscoveryConfig()
    segments = tuple(transcript)
    source_signals = tuple(signals)
    if any(current.start < previous.start for previous, current in pairwise(segments)):
        raise ValueError("transcript segments must be monotonic by start offset")

    candidates: list[CandidateMoment] = []
    for anchor_index, anchor in enumerate(segments):
        if anchor.is_silence or not anchor.text.strip():
            continue
        candidate = _candidate_for_anchor(segments, anchor_index, source_signals, cfg)
        if candidate is not None:
            candidates.append(candidate)

    by_key: dict[str, CandidateMoment] = {}
    for candidate in candidates:
        existing = by_key.get(candidate.dedup_key)
        if existing is None or _sort_key(candidate) < _sort_key(existing):
            by_key[candidate.dedup_key] = candidate
    ordered = sorted(by_key.values(), key=_sort_key)[: cfg.max_clips]
    return HighlightDiscoveryResult(
        candidates=tuple(ordered),
        config=cfg,
        source_segment_count=len(segments),
        discovered_at_offsets=tuple(round(candidate.start, 3) for candidate in ordered),
    )


def _candidate_for_anchor(
    segments: tuple[TranscriptSegment, ...],
    anchor_index: int,
    signals: tuple[SourceSignal, ...],
    config: HighlightDiscoveryConfig,
) -> CandidateMoment | None:
    anchor = segments[anchor_index]
    parts: list[str] = []
    end_index: int | None = None

    for index in range(anchor_index, len(segments)):
        segment = segments[index]
        if segment.end - anchor.start > config.max_duration:
            break
        if segment.is_silence or not segment.text.strip():
            continue
        parts.append(segment.text.strip())
        if segment.end - anchor.start >= config.min_duration and _is_complete(segment.text):
            end_index = index
            break

    if end_index is None:
        return None
    end_segment = segments[end_index]
    excerpt = " ".join(parts)
    confidence = _transcript_score(excerpt)
    key = canonical_dedup_key(
        start=anchor.start,
        end=end_segment.end,
        excerpt=excerpt,
        sensitivity="none",
    )
    title = _excerpt_lead(excerpt, 80)
    hook = _excerpt_lead(excerpt, 120)
    window_signals = tuple(
        sorted(
            (signal for signal in signals if anchor.start <= signal.timestamp <= end_segment.end),
            key=lambda signal: (signal.timestamp, signal.kind, -signal.score, signal.label or ""),
        )
    )
    return CandidateMoment(
        candidate_id=_candidate_id(anchor.segment_id, key),
        start=anchor.start,
        end=end_segment.end,
        transcript_excerpt=excerpt,
        suggested_title=title,
        suggested_hook=hook,
        rationale=(
            f"Transcript window from {anchor.start:.2f}s to {end_segment.end:.2f}s "
            "meets the duration bounds and ends at a complete thought."
        ),
        confidence=confidence,
        dedup_key=key,
        sensitivity="none",
        unsuitable=False,
        source_signals=window_signals,
    )


def _is_complete(text: str) -> bool:
    return bool(_TERMINAL_RE.search(text.rstrip()))


def _transcript_score(excerpt: str) -> float:
    words = len(excerpt.split())
    terminals = sum(1 for token in excerpt.split() if _is_complete(token))
    density = min(1.0, words / 60.0)
    completeness = min(1.0, terminals / 2.0)
    return round(min(1.0, 0.6 * density + 0.4 * completeness), 4)


def _excerpt_lead(excerpt: str, limit: int) -> str:
    match = re.search(r"[.!?]", excerpt)
    lead = excerpt[: match.end()] if match else excerpt
    return lead[:limit].strip()


def _candidate_id(segment_id: str, dedup_key: str) -> str:
    prefix = re.sub(r"[^A-Za-z0-9._-]", "_", segment_id)
    return f"{prefix[:57]}-{dedup_key[:6]}"


def _sort_key(candidate: CandidateMoment) -> tuple[float, float, float, str]:
    return (-candidate.confidence, candidate.start, candidate.end, candidate.candidate_id)
