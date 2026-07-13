"""Standalone, deterministic script parsing for sound episode planning.

Only hashes and bounded routing metadata leave this module. Raw script text is
validated and hashed in-memory, then discarded before the typed record is
returned.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import Any, Literal

from pydantic import Field, ValidationError, field_validator, model_validator

from kinocut_sound._canonical import (
    BoundedCode,
    FrozenModel,
    RecordBase,
    Sha256,
    canonical_digest,
    canonical_record_id,
)
from kinocut_sound._errors import SoundContractError
from kinocut_sound.lines import Emotion, Line, ProfileRef, Prosody
from kinocut_sound.limits import MIN_TIME_SECONDS, MIN_VERSION


class ScriptParseError(SoundContractError):
    """A bounded, privacy-safe script parsing failure."""


class ScriptLineKind(StrEnum):
    """Closed routing intents for spoken screenplay lines."""

    DIALOGUE = "dialogue"
    CONFESSIONAL = "confessional"
    OFF_SCREEN = "off_screen"
    NARRATION = "narration"


class ActorRoute(FrozenModel):
    """A fully resolved actor-to-voice and spatial route."""

    actor_id: str = Field(min_length=1)
    profile: ProfileRef
    dialogue_spatial_preset: str = Field(min_length=1)
    confessional_spatial_preset: str = Field(min_length=1)
    off_screen_spatial_preset: str = Field(min_length=1)
    narration_spatial_preset: str = Field(min_length=1)
    prosody: Prosody
    emotion: Emotion
    inherit_loudness: bool = Field(strict=True)

    @field_validator(
        "actor_id",
        "dialogue_spatial_preset",
        "confessional_spatial_preset",
        "off_screen_spatial_preset",
        "narration_spatial_preset",
    )
    @classmethod
    def _codes_are_bounded(cls, value: str) -> str:
        return BoundedCode(value)


class ParsedLine(FrozenModel):
    """One privacy-safe parsed line plus deterministic cue metadata."""

    scene_id: str = Field(min_length=1)
    line_index: int = Field(ge=MIN_VERSION, strict=True)
    cue_id: str = Field(min_length=1)
    pause_after_seconds: float = Field(ge=MIN_TIME_SECONDS, strict=True)
    line: Line

    @field_validator("scene_id", "cue_id")
    @classmethod
    def _codes_are_bounded(cls, value: str) -> str:
        return BoundedCode(value)

    @field_validator("line_index", mode="before")
    @classmethod
    def _line_index_is_strict(cls, value: object) -> object:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("line_index must be an integer")
        return value

    @field_validator("pause_after_seconds")
    @classmethod
    def _pause_is_not_boolean(cls, value: float) -> float:
        if isinstance(value, bool):
            raise ValueError("pause_after_seconds must not be a boolean")
        return value


class ParsedScene(FrozenModel):
    """A validated scene with ordered line ids and declared trailing pause."""

    scene_id: str = Field(min_length=1)
    line_ids: tuple[str, ...]
    pause_after_seconds: float = Field(ge=MIN_TIME_SECONDS, strict=True)

    @field_validator("scene_id")
    @classmethod
    def _scene_id_is_bounded(cls, value: str) -> str:
        return BoundedCode(value)

    @field_validator("line_ids")
    @classmethod
    def _line_ids_are_bounded(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value:
            raise ValueError("scene must contain at least one line")
        for line_id in value:
            BoundedCode(line_id)
        return value

    @field_validator("pause_after_seconds")
    @classmethod
    def _pause_is_not_boolean(cls, value: float) -> float:
        if isinstance(value, bool):
            raise ValueError("pause_after_seconds must not be a boolean")
        return value


class ParsedScript(RecordBase):
    """Canonical, privacy-safe result of parsing one structured episode."""

    record_kind: Literal["parsed_script"] = "parsed_script"
    episode_id: str = Field(min_length=1)
    source_hash: Sha256
    scenes: tuple[ParsedScene, ...]
    parsed_lines: tuple[ParsedLine, ...]
    cue_order: tuple[str, ...]

    @field_validator("episode_id")
    @classmethod
    def _episode_id_is_bounded(cls, value: str) -> str:
        return BoundedCode(value)

    @model_validator(mode="after")
    def _ordering_is_self_consistent(self) -> ParsedScript:
        cue_ids = tuple(item.cue_id for item in self.parsed_lines)
        if cue_ids != self.cue_order or len(set(cue_ids)) != len(cue_ids):
            raise ValueError("cue_order must exactly match unique parsed line cues")
        scene_ids = tuple(scene.scene_id for scene in self.scenes)
        if len(set(scene_ids)) != len(scene_ids):
            raise ValueError("scene ids must be unique")
        return self

    def canonical_id(self) -> str:
        """Return the canonical semantic digest for receipt compatibility."""

        return canonical_record_id(self)


class _LineInput(FrozenModel):
    actor_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    kind: ScriptLineKind
    pause_after_seconds: float = Field(ge=MIN_TIME_SECONDS, strict=True)

    @field_validator("actor_id")
    @classmethod
    def _actor_id_is_bounded(cls, value: str) -> str:
        return BoundedCode(value)

    @field_validator("text")
    @classmethod
    def _text_is_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("line text must not be blank")
        return value

    @field_validator("pause_after_seconds")
    @classmethod
    def _pause_is_not_boolean(cls, value: float) -> float:
        if isinstance(value, bool):
            raise ValueError("pause_after_seconds must not be a boolean")
        return value


class _SceneInput(FrozenModel):
    scene_id: str = Field(min_length=1)
    pause_after_seconds: float = Field(ge=MIN_TIME_SECONDS, strict=True)
    lines: tuple[_LineInput, ...]

    @field_validator("scene_id")
    @classmethod
    def _scene_id_is_bounded(cls, value: str) -> str:
        return BoundedCode(value)

    @field_validator("lines")
    @classmethod
    def _scene_has_lines(cls, value: tuple[_LineInput, ...]) -> tuple[_LineInput, ...]:
        if not value:
            raise ValueError("scene must contain at least one line")
        return value

    @field_validator("pause_after_seconds")
    @classmethod
    def _pause_is_not_boolean(cls, value: float) -> float:
        if isinstance(value, bool):
            raise ValueError("pause_after_seconds must not be a boolean")
        return value


class _ScriptInput(FrozenModel):
    episode_id: str = Field(min_length=1)
    scenes: tuple[_SceneInput, ...]

    @field_validator("episode_id")
    @classmethod
    def _episode_id_is_bounded(cls, value: str) -> str:
        return BoundedCode(value)

    @field_validator("scenes")
    @classmethod
    def _episode_has_scenes(cls, value: tuple[_SceneInput, ...]) -> tuple[_SceneInput, ...]:
        if not value:
            raise ValueError("episode must contain at least one scene")
        return value


def _parse_error(message: str, code: str) -> ScriptParseError:
    return ScriptParseError(message, code=code, suggested_action={"auto_fix": False})


def _validation_code(exc: ValidationError) -> str:
    locations = tuple(part for error in exc.errors() for part in error["loc"])
    if "lines" in locations or "text" in locations:
        return "invalid_line"
    if "scene_id" in locations:
        return "invalid_scene"
    return "invalid_script"


def _actor_index(actors: tuple[ActorRoute, ...]) -> dict[str, ActorRoute]:
    actor_ids = tuple(actor.actor_id for actor in actors)
    if len(set(actor_ids)) != len(actor_ids):
        raise _parse_error("actor roster contains duplicate actor ids", "invalid_actor_roster")
    return {actor.actor_id: actor for actor in actors}


def _spatial_preset(route: ActorRoute, kind: ScriptLineKind) -> str:
    return {
        ScriptLineKind.DIALOGUE: route.dialogue_spatial_preset,
        ScriptLineKind.CONFESSIONAL: route.confessional_spatial_preset,
        ScriptLineKind.OFF_SCREEN: route.off_screen_spatial_preset,
        ScriptLineKind.NARRATION: route.narration_spatial_preset,
    }[kind]


def _build_line(
    source: _LineInput,
    route: ActorRoute,
    *,
    scene_id: str,
    scene_index: int,
    line_index: int,
) -> ParsedLine:
    line_id = f"line_{scene_index:04d}_{line_index:04d}"
    cue_id = f"cue_{scene_index:04d}_{line_index:04d}"
    line = Line(
        line_id=line_id,
        character_id=route.actor_id,
        profile=route.profile,
        text_hash=canonical_digest({"text": source.text}),
        text_length_chars=len(source.text),
        prosody=route.prosody,
        emotion=route.emotion,
        spatial_preset=_spatial_preset(route, source.kind),
        pronunciation_overrides=(),
        inherit_loudness=route.inherit_loudness,
    )
    return ParsedLine(
        scene_id=scene_id,
        line_index=line_index,
        cue_id=cue_id,
        pause_after_seconds=source.pause_after_seconds,
        line=line,
    )


def _build_scene(
    scene: _SceneInput,
    *,
    scene_index: int,
    actors: dict[str, ActorRoute],
) -> tuple[ParsedScene, tuple[ParsedLine, ...]]:
    parsed_lines: list[ParsedLine] = []
    for line_index, source in enumerate(scene.lines, start=1):
        route = actors.get(source.actor_id)
        if route is None:
            raise _parse_error("line references an unknown actor id", "unknown_actor")
        parsed_lines.append(
            _build_line(
                source,
                route,
                scene_id=scene.scene_id,
                scene_index=scene_index,
                line_index=line_index,
            )
        )
    line_ids = tuple(item.line.line_id for item in parsed_lines)
    parsed_scene = ParsedScene(
        scene_id=scene.scene_id,
        line_ids=line_ids,
        pause_after_seconds=scene.pause_after_seconds,
    )
    return parsed_scene, tuple(parsed_lines)


def parse_episode_script(
    document: Mapping[str, Any],
    *,
    project_id: str,
    created_by: str,
    actors: tuple[ActorRoute, ...],
) -> ParsedScript:
    """Parse structured episode data into a canonical, privacy-safe record."""

    actor_map = _actor_index(actors)
    try:
        script = _ScriptInput.model_validate(document)
    except ValidationError as exc:
        raise _parse_error("script input failed strict structural validation", _validation_code(exc)) from exc
    scene_ids = tuple(scene.scene_id for scene in script.scenes)
    if len(set(scene_ids)) != len(scene_ids):
        raise _parse_error("episode contains duplicate scene ids", "invalid_scene")
    scenes: list[ParsedScene] = []
    lines: list[ParsedLine] = []
    for scene_index, scene in enumerate(script.scenes, start=1):
        parsed_scene, parsed_lines = _build_scene(
            scene, scene_index=scene_index, actors=actor_map
        )
        scenes.append(parsed_scene)
        lines.extend(parsed_lines)
    try:
        return ParsedScript(
            project_id=project_id,
            created_by=created_by,
            episode_id=script.episode_id,
            source_hash=canonical_digest(script.model_dump(mode="json")),
            scenes=tuple(scenes),
            parsed_lines=tuple(lines),
            cue_order=tuple(line.cue_id for line in lines),
        )
    except ValidationError as exc:
        raise _parse_error("parsed script failed canonical validation", "invalid_script") from exc
