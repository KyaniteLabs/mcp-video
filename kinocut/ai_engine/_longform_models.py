"""Strict pydantic models for the long-form transcription path (PR1).

Subclass :class:`kinocut.contracts._common.ValueObject` so each model
inherits ``extra="forbid"``, ``frozen=True``, and ``allow_inf_nan=False``.
Field-level bounds come from pydantic ``Field``; cross-field invariants
come from ``model_validator(mode="after")``.
"""

from __future__ import annotations

from pydantic import Field, model_validator

from ..contracts._common import ValueObject


class LongformChunk(ValueObject):
    """One planned chunk. ``duration`` may exceed ``end - start`` (overlap tail)."""

    index: int = Field(ge=0)
    start: float = Field(ge=0.0)
    end: float = Field(ge=0.0)
    duration: float = Field(gt=0.0)
    anchor: str = "fixed"  # one of: "fixed", "scene"

    @model_validator(mode="after")
    def _chunk_invariants(self) -> LongformChunk:
        if self.end <= self.start:
            raise ValueError(f"LongformChunk end ({self.end}) must be greater than start ({self.start})")
        covered = self.end - self.start
        if self.duration + 1e-9 < covered:
            raise ValueError(f"LongformChunk duration ({self.duration}) must cover end - start ({covered})")
        return self


class LongformWord(ValueObject):
    """One word with globally remapped timestamps (seconds, source-time)."""

    word: str = Field(min_length=1)
    start: float = Field(ge=0.0)
    end: float = Field(ge=0.0)
    chunk_index: int = Field(ge=0)
    probability: float | None = Field(default=None, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _word_has_positive_width(self) -> LongformWord:
        if self.end <= self.start:
            raise ValueError(f"LongformWord end ({self.end}) must be greater than start ({self.start})")
        return self


class LongformSegment(ValueObject):
    """One transcript segment, globally remapped and dedup-overlapped."""

    start: float = Field(ge=0.0)
    end: float = Field(ge=0.0)
    text: str = Field(min_length=1)
    chunk_index: int = Field(ge=0)
    avg_logprob: float | None = Field(default=None, le=0.0)
    no_speech_prob: float | None = Field(default=None, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _segment_has_positive_width(self) -> LongformSegment:
        if self.end <= self.start:
            raise ValueError(f"LongformSegment end ({self.end}) must be greater than start ({self.start})")
        return self


class LongformTranscribePlan(ValueObject):
    """Deterministic plan returned by the planner."""

    video_path: str = Field(min_length=1)
    duration: float = Field(ge=0.0)
    chunk_seconds: int = Field(gt=0)
    overlap_seconds: int = Field(ge=0)
    chunks: list[LongformChunk]

    @model_validator(mode="after")
    def _overlap_strictly_smaller_than_chunk(self) -> LongformTranscribePlan:
        if self.overlap_seconds >= self.chunk_seconds:
            raise ValueError(
                f"overlap_seconds ({self.overlap_seconds}) must be strictly smaller "
                f"than chunk_seconds ({self.chunk_seconds})"
            )
        return self


class LongformTranscribeResult(ValueObject):
    """Strict-model result of a long-form transcription run."""

    video_path: str = Field(min_length=1)
    duration: float = Field(ge=0.0)
    language: str = Field(min_length=1)
    transcript: str
    segments: list[LongformSegment]
    words: list[LongformWord]
    chunk_count: int = Field(ge=0)
    model: str = Field(min_length=1)
    plan: LongformTranscribePlan

    @model_validator(mode="after")
    def _chunk_count_and_duration_match_plan(self) -> LongformTranscribeResult:
        if self.chunk_count != len(self.plan.chunks):
            raise ValueError(f"chunk_count ({self.chunk_count}) must equal len(plan.chunks) ({len(self.plan.chunks)})")
        if self.duration != self.plan.duration:
            raise ValueError(f"duration ({self.duration}) must equal plan.duration ({self.plan.duration})")
        return self


__all__ = [
    "LongformChunk",
    "LongformSegment",
    "LongformTranscribePlan",
    "LongformTranscribeResult",
    "LongformWord",
]
