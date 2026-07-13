"""Pure deterministic planning for sound episode assembly.

This module performs no I/O and imports no rendering or vendor runtime. It
turns a parsed-script record plus fake-or-real hashed clip/cue references into
an authoritative timeline and explicit routing plan.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import Field, ValidationError, field_validator, model_validator

from kinocut_sound._canonical import (
    BoundedCode,
    FrozenModel,
    RecordBase,
    Sha256,
    canonical_record_id,
    location_violation,
)
from kinocut_sound._errors import SoundContractError
from kinocut_sound.lines import ProfileRef
from kinocut_sound.limits import MIN_TIME_SECONDS
from kinocut_sound.script_parser import ParsedLine, ParsedScript
from kinocut_sound.timeline import Cue, CueKind, Timeline


class AssemblyPlanningError(SoundContractError):
    """A bounded, privacy-safe episode planning failure."""


class SilenceQuality(StrEnum):
    """Closed qualities for explicit designed silence."""

    DEAD = "dead"
    ROOM_TONE = "room_tone"
    HELD_BREATH = "held_breath"


class ClipRef(FrozenModel):
    """A privacy-safe rendered-line artifact reference."""

    line_id: str = Field(min_length=1)
    artifact_hash: Sha256
    source_ref: str = Field(min_length=1)
    duration_seconds: float = Field(gt=MIN_TIME_SECONDS, strict=True)

    @field_validator("line_id")
    @classmethod
    def _line_id_is_bounded(cls, value: str) -> str:
        return BoundedCode(value)

    @field_validator("source_ref")
    @classmethod
    def _source_ref_is_safe(cls, value: str) -> str:
        reason = location_violation(value)
        if reason is not None:
            raise ValueError(f"source_ref {reason}")
        return value

    @field_validator("duration_seconds")
    @classmethod
    def _duration_is_not_boolean(cls, value: float) -> float:
        if isinstance(value, bool):
            raise ValueError("duration_seconds must not be a boolean")
        return value


class FoleyCueIntent(FrozenModel):
    """A deterministic Foley cue spotted relative to a parsed line."""

    cue_id: str = Field(min_length=1)
    after_line_id: str = Field(min_length=1)
    asset_ref: str = Field(min_length=1)
    asset_hash: Sha256
    duration_seconds: float = Field(gt=MIN_TIME_SECONDS, strict=True)

    @field_validator("cue_id", "after_line_id")
    @classmethod
    def _ids_are_bounded(cls, value: str) -> str:
        return BoundedCode(value)

    @field_validator("asset_ref")
    @classmethod
    def _asset_ref_is_safe(cls, value: str) -> str:
        reason = location_violation(value)
        if reason is not None:
            raise ValueError(f"asset_ref {reason}")
        return value

    @field_validator("duration_seconds")
    @classmethod
    def _duration_is_not_boolean(cls, value: float) -> float:
        if isinstance(value, bool):
            raise ValueError("duration_seconds must not be a boolean")
        return value


class DesignedSilenceIntent(FrozenModel):
    """One explicit designed-silence cue relative to a parsed line."""

    cue_id: str = Field(min_length=1)
    after_line_id: str = Field(min_length=1)
    quality: SilenceQuality
    duration_seconds: float = Field(gt=MIN_TIME_SECONDS, strict=True)

    @field_validator("cue_id", "after_line_id")
    @classmethod
    def _ids_are_bounded(cls, value: str) -> str:
        return BoundedCode(value)

    @field_validator("duration_seconds")
    @classmethod
    def _duration_is_not_boolean(cls, value: float) -> float:
        if isinstance(value, bool):
            raise ValueError("duration_seconds must not be a boolean")
        return value


class AssemblyRoute(FrozenModel):
    """Resolved line routing intent in final script order."""

    line_id: str = Field(min_length=1)
    cue_id: str = Field(min_length=1)
    profile: ProfileRef
    spatial_preset: str = Field(min_length=1)

    @field_validator("line_id", "cue_id", "spatial_preset")
    @classmethod
    def _codes_are_bounded(cls, value: str) -> str:
        return BoundedCode(value)


class EpisodeAssembly(RecordBase):
    """Canonical, privacy-safe output of pure episode assembly planning."""

    record_kind: Literal["episode_assembly"] = "episode_assembly"
    episode_id: str = Field(min_length=1)
    parsed_script_id: Sha256
    timeline: Timeline
    line_cue_order: tuple[str, ...]
    routes: tuple[AssemblyRoute, ...]
    clip_hashes: tuple[Sha256, ...]
    foley_hashes: tuple[Sha256, ...]

    @field_validator("episode_id")
    @classmethod
    def _episode_id_is_bounded(cls, value: str) -> str:
        return BoundedCode(value)

    @model_validator(mode="after")
    def _route_order_matches_line_cues(self) -> EpisodeAssembly:
        if tuple(route.cue_id for route in self.routes) != self.line_cue_order:
            raise ValueError("route order must match line cue order")
        if self.parsed_script_id not in self.source_record_ids:
            raise ValueError("parsed script id must be a source record id")
        return self

    def canonical_id(self) -> str:
        """Return the canonical semantic digest for receipt compatibility."""

        return canonical_record_id(self)


def _planning_error(message: str, code: str) -> AssemblyPlanningError:
    return AssemblyPlanningError(message, code=code, suggested_action={"auto_fix": False})


def _unique_index(
    values: tuple[ClipRef, ...],
) -> dict[str, ClipRef]:
    line_ids = tuple(value.line_id for value in values)
    if len(set(line_ids)) != len(line_ids):
        raise _planning_error("clip inputs contain a duplicate line id", "duplicate_clip")
    return {value.line_id: value for value in values}


def _validate_cue_contracts(
    parsed: ParsedScript,
    foley_cues: tuple[FoleyCueIntent, ...],
    designed_silences: tuple[DesignedSilenceIntent, ...],
) -> None:
    line_ids = {item.line.line_id for item in parsed.parsed_lines}
    intents = (*foley_cues, *designed_silences)
    cue_ids = tuple(intent.cue_id for intent in intents)
    if len(set(cue_ids)) != len(cue_ids):
        raise _planning_error("cue contracts contain a duplicate cue id", "invalid_cue_contract")
    if any(intent.after_line_id not in line_ids for intent in intents):
        raise _planning_error("cue contract references an unknown line id", "invalid_cue_contract")


CueIntent = FoleyCueIntent | DesignedSilenceIntent


def _group_by_line(values: tuple[CueIntent, ...]) -> dict[str, tuple[CueIntent, ...]]:
    grouped: dict[str, list[CueIntent]] = {}
    for value in values:
        line_id = value.after_line_id
        grouped.setdefault(line_id, []).append(value)
    return {
        line_id: tuple(sorted(items, key=lambda item: item.cue_id))
        for line_id, items in grouped.items()
    }


def _append_cue(
    cues: list[Cue],
    *,
    cue_id: str,
    start_seconds: float,
    duration_seconds: float,
    kind: CueKind,
    source_ref: str,
) -> float:
    cues.append(
        Cue(
            cue_id=cue_id,
            start_seconds=start_seconds,
            duration_seconds=duration_seconds,
            kind=kind,
            source_ref=source_ref,
        )
    )
    return start_seconds + duration_seconds


def _line_route(item: ParsedLine) -> AssemblyRoute:
    return AssemblyRoute(
        line_id=item.line.line_id,
        cue_id=item.cue_id,
        profile=item.line.profile,
        spatial_preset=item.line.spatial_preset,
    )


def _plan_line_extras(
    item: ParsedLine,
    current: float,
    cues: list[Cue],
    silences: tuple[DesignedSilenceIntent, ...],
    foley: tuple[FoleyCueIntent, ...],
) -> float:
    if item.pause_after_seconds > MIN_TIME_SECONDS:
        current = _append_cue(
            cues,
            cue_id=f"pause_{item.line.line_id}",
            start_seconds=current,
            duration_seconds=item.pause_after_seconds,
            kind=CueKind.SILENCE,
            source_ref="silence/line_pause.json",
        )
    for intent in silences:
        current = _append_cue(
            cues,
            cue_id=intent.cue_id,
            start_seconds=current,
            duration_seconds=intent.duration_seconds,
            kind=CueKind.SILENCE,
            source_ref=f"silence/{intent.quality.value}.json",
        )
    for intent in foley:
        current = _append_cue(
            cues,
            cue_id=intent.cue_id,
            start_seconds=current,
            duration_seconds=intent.duration_seconds,
            kind=CueKind.FOLEY,
            source_ref=intent.asset_ref,
        )
    return current


def _build_timeline(
    parsed: ParsedScript,
    clips: dict[str, ClipRef],
    foley_by_line: dict[str, tuple[CueIntent, ...]],
    silence_by_line: dict[str, tuple[CueIntent, ...]],
) -> tuple[Timeline, tuple[AssemblyRoute, ...]]:
    parsed_by_id = {item.line.line_id: item for item in parsed.parsed_lines}
    cues: list[Cue] = []
    routes: list[AssemblyRoute] = []
    current = MIN_TIME_SECONDS
    for scene in parsed.scenes:
        for line_id in scene.line_ids:
            item = parsed_by_id[line_id]
            clip = clips[line_id]
            current = _append_cue(
                cues,
                cue_id=item.cue_id,
                start_seconds=current,
                duration_seconds=clip.duration_seconds,
                kind=CueKind.LINE,
                source_ref=clip.source_ref,
            )
            routes.append(_line_route(item))
            current = _plan_line_extras(
                item,
                current,
                cues,
                silence_by_line.get(line_id, ()),
                foley_by_line.get(line_id, ()),
            )
        if scene.pause_after_seconds > MIN_TIME_SECONDS:
            current = _append_cue(
                cues,
                cue_id=f"pause_{scene.scene_id}",
                start_seconds=current,
                duration_seconds=scene.pause_after_seconds,
                kind=CueKind.SILENCE,
                source_ref="silence/scene_pause.json",
            )
    return Timeline(cues=tuple(cues)), tuple(routes)


def plan_episode_assembly(
    parsed: ParsedScript,
    *,
    clips: tuple[ClipRef, ...],
    foley_cues: tuple[FoleyCueIntent, ...],
    designed_silences: tuple[DesignedSilenceIntent, ...],
    created_by: str,
    cancellation_requested: bool,
) -> EpisodeAssembly:
    """Return an all-or-nothing deterministic episode assembly plan."""
    if not isinstance(cancellation_requested, bool):
        raise _planning_error("cancellation flag must be a boolean", "invalid_assembly")

    if cancellation_requested:
        raise _planning_error("episode assembly planning was cancelled", "assembly_cancelled")
    clip_index = _unique_index(clips)
    expected_line_ids = tuple(item.line.line_id for item in parsed.parsed_lines)
    if set(clip_index) != set(expected_line_ids):
        raise _planning_error("clip inputs do not exactly match parsed lines", "clip_set_mismatch")
    _validate_cue_contracts(parsed, foley_cues, designed_silences)
    foley_by_line = _group_by_line(foley_cues)
    silence_by_line = _group_by_line(designed_silences)
    try:
        timeline, routes = _build_timeline(
            parsed, clip_index, foley_by_line, silence_by_line
        )
        parsed_id = parsed.canonical_id()
        return EpisodeAssembly(
            project_id=parsed.project_id,
            created_by=created_by,
            source_record_ids=(parsed_id,),
            episode_id=parsed.episode_id,
            parsed_script_id=parsed_id,
            timeline=timeline,
            line_cue_order=parsed.cue_order,
            routes=routes,
            clip_hashes=tuple(clip_index[line_id].artifact_hash for line_id in expected_line_ids),
            foley_hashes=tuple(
                cue.asset_hash for cue in sorted(foley_cues, key=lambda item: item.cue_id)
            ),
        )
    except (ValidationError, KeyError) as exc:
        raise _planning_error("episode timeline failed canonical validation", "invalid_assembly") from exc
