from __future__ import annotations

from kinocut.product.highlight_discovery import discover_highlights
from kinocut.product.models import HighlightDiscoveryConfig, SourceSignal, TranscriptSegment


def _segment(
    segment_id: str,
    start: float,
    end: float,
    text: str,
    *,
    silence: bool = False,
    confidence: float | None = 0.9,
) -> TranscriptSegment:
    return TranscriptSegment(
        segment_id=segment_id,
        start=start,
        end=end,
        text=text,
        confidence=confidence,
        is_silence=silence,
    )


def _config(*, minimum: float = 8, maximum: float = 30, clips: int = 8) -> HighlightDiscoveryConfig:
    return HighlightDiscoveryConfig(
        min_duration=minimum,
        max_duration=maximum,
        max_clips=clips,
    )


def _realistic_transcript() -> tuple[TranscriptSegment, ...]:
    return (
        _segment("intro", 12, 24, "The first lesson is to begin with the audience's actual problem."),
        _segment("example", 24, 36, "For example, our smallest experiment revealed the largest source of delay."),
        _segment("turn", 36, 48, "That changed the plan because evidence beat our original assumption."),
        _segment("payoff", 48, 60, "The payoff is a process that gets faster whenever it learns."),
    )


def test_discovery_is_repeatable_and_json_stable() -> None:
    transcript = _realistic_transcript()
    signal = SourceSignal(kind="scene_change", timestamp=30, score=0.8)

    first = discover_highlights(transcript, signals=(signal,), config=_config())
    second = discover_highlights(transcript, signals=(signal,), config=_config())

    assert first == second
    assert first.model_dump_json() == second.model_dump_json()


def test_realistic_transcript_produces_at_least_three_distinct_candidates() -> None:
    result = discover_highlights(_realistic_transcript(), config=_config(clips=3))

    assert len(result.candidates) >= 3
    assert len({candidate.dedup_key for candidate in result.candidates}) == len(result.candidates)


def test_empty_transcript_has_no_candidates() -> None:
    result = discover_highlights((), config=_config())

    assert result.candidates == ()


def test_all_silence_has_no_candidates() -> None:
    transcript = (
        _segment("silence-1", 0, 10, "[silence]", silence=True),
        _segment("silence-2", 10, 20, "[silence]", silence=True),
    )

    assert discover_highlights(transcript, config=_config()).candidates == ()


def test_window_extends_to_complete_thought_payoff() -> None:
    transcript = (
        _segment("setup", 0, 10, "The useful result begins with a constraint"),
        _segment("bridge", 10, 20, "and the initial attempt still falls short,"),
        _segment("answer", 20, 30, "but the final comparison reveals the answer."),
    )

    candidate = next(
        item
        for item in discover_highlights(transcript, config=_config(minimum=15, maximum=35)).candidates
        if item.start == 0
    )

    assert candidate.end == 30
    assert candidate.transcript_excerpt.endswith("answer.")


def test_window_without_complete_thought_is_rejected() -> None:
    transcript = (
        _segment("setup", 0, 10, "This explanation continues"),
        _segment("middle", 10, 20, "through another unfinished clause,"),
    )

    assert discover_highlights(transcript, config=_config(minimum=8, maximum=25)).candidates == ()


def test_leading_silence_is_trimmed_from_candidate() -> None:
    transcript = (
        _segment("silence", 40, 48, "[silence]", silence=True),
        _segment("speech", 48, 58, "The spoken idea begins here and reaches its conclusion."),
    )

    candidate = discover_highlights(transcript, config=_config(minimum=5)).candidates[0]

    assert candidate.start == 48
    assert "silence" not in candidate.transcript_excerpt.lower()


def test_candidates_respect_source_bounds_duration_and_max_clips() -> None:
    transcript = (
        _segment("one", 100, 110, "A bounded window starts at the source offset"),
        _segment("two", 110, 120, "and closes with a complete result."),
        _segment("three", 120, 140, "A second self-contained explanation also ends cleanly."),
    )
    config = _config(minimum=10, maximum=25, clips=1)

    result = discover_highlights(transcript, config=config)

    assert len(result.candidates) == 1
    assert all(100 <= item.start < item.end <= 140 for item in result.candidates)
    assert all(config.min_duration <= item.end - item.start <= config.max_duration for item in result.candidates)


def test_duplicate_windows_collapse_by_canonical_key() -> None:
    transcript = (
        _segment("copy-a", 0, 10, "The same bounded thought finishes here."),
        _segment("copy-b", 0, 10, "The same bounded thought finishes here."),
    )

    result = discover_highlights(transcript, config=_config(minimum=5))

    assert len(result.candidates) == 1


def test_candidates_are_sorted_by_descending_score() -> None:
    transcript = (
        _segment("short", 0, 10, "A concise result lands."),
        _segment(
            "dense",
            10,
            20,
            "A detailed explanation connects evidence, constraints, tradeoffs, audience needs, "
            "implementation choices, and the measurable result.",
        ),
        _segment("medium", 20, 30, "A useful intermediate explanation reaches a clear result."),
    )

    candidates = discover_highlights(transcript, config=_config(minimum=5)).candidates

    assert [item.confidence for item in candidates] == sorted((item.confidence for item in candidates), reverse=True)
