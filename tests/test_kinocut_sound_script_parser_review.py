"""Hostile review regressions for S4 script parsing contracts."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from kinocut_sound.lines import Emotion, ProfileRef, Prosody
from kinocut_sound import script_parser as parser


def _actor(actor_id: str, profile_id: str) -> parser.ActorRoute:
    return parser.ActorRoute(
        actor_id=actor_id,
        profile=ProfileRef(profile_id=profile_id, version=1),
        dialogue_spatial_preset="medium_room",
        confessional_spatial_preset="close_mic_dry",
        off_screen_spatial_preset="off_screen_distance",
        narration_spatial_preset="medium_room",
        prosody=Prosody(),
        emotion=Emotion(label="neutral", intensity=0.0),
        inherit_loudness=True,
    )


def _generic_document():
    return {
        "episode_id": "episode_review",
        "scenes": [
            {
                "scene_id": "scene_review",
                "pause_after_seconds": 0.0,
                "lines": [
                    {
                        "actor_id": "narrator",
                        "text": "A door opens in the dark.",
                        "kind": "action",
                        "pause_after_seconds": 0.0,
                    },
                    {
                        "actor_id": "actor_a",
                        "text": "I remember this place.",
                        "kind": "voiceover",
                        "pause_after_seconds": 0.0,
                    },
                ],
                "beats": [
                    {
                        "kind": "foley",
                        "text": "Door latch",
                        "after_line_index": 1,
                        "duration_seconds": 0.4,
                        "asset_ref": "foley/door_latch.wav",
                        "asset_hash": "sha256:" + "a" * 64,
                    },
                    {
                        "kind": "designed_silence",
                        "text": "Held breath",
                        "after_line_index": 1,
                        "duration_seconds": 0.3,
                        "silence_quality": "held_breath",
                    },
                    {
                        "kind": "pace",
                        "text": "Memory settles",
                        "after_line_index": 2,
                        "duration_seconds": 0.2,
                    },
                ],
            }
        ],
    }


def _generic_parsed() -> parser.ParsedScript:
    return parser.parse_episode_script(
        _generic_document(),
        project_id="project_alpha",
        created_by="agent:worker_1",
        actors=(
            _actor("narrator", "voice_narrator"),
            _actor("actor_a", "voice_a"),
        ),
    )
def _two_scene_parsed() -> parser.ParsedScript:
    document = _generic_document()
    first_scene = document["scenes"][0]
    first_scene["lines"] = first_scene["lines"][:1]
    first_scene["beats"] = first_scene["beats"][:1]
    document["scenes"].append(
        {
            "scene_id": "scene_other",
            "pause_after_seconds": 0.0,
            "lines": [
                {
                    "actor_id": "actor_a",
                    "text": "Across the hall.",
                    "kind": "dialogue",
                    "pause_after_seconds": 0.0,
                }
            ],
        }
    )
    return parser.parse_episode_script(
        document,
        project_id="project_alpha",
        created_by="agent:worker_1",
        actors=(
            _actor("narrator", "voice_narrator"),
            _actor("actor_a", "voice_a"),
        ),
    )


def _chapter_only_parsed() -> parser.ParsedScript:
    return parser.parse_wf_episode_script(
        {
            "episode_id": "wf_chapter_review",
            "scenes": [
                {
                    "scene_id": "wf_scene",
                    "turns": [
                        {
                            "character": "Narrator",
                            "text": "Chapter One",
                            "confessional": False,
                        }
                    ],
                }
            ],
        },
        project_id="project_alpha",
        created_by="agent:worker_1",
        actors=(),
        character_routes={},
        narrator_character="Narrator",
    )




def test_generic_parser_represents_action_narration_voiceover_and_beats_in_source_order():
    parsed = _generic_parsed()

    assert tuple(item.performance_kind.value for item in parsed.parsed_lines) == (
        "action",
        "voiceover",
    )
    assert tuple(beat.kind.value for beat in parsed.beats) == (
        "foley",
        "designed_silence",
        "pace",
    )
    assert parsed.scenes[0].event_ids == (
        "line_0001_0001",
        "beat_0001_0001",
        "beat_0001_0002",
        "line_0001_0002",
        "beat_0001_0003",
    )
    assert tuple(item.line.spatial_preset for item in parsed.parsed_lines) == (
        "medium_room",
        "medium_room",
    )
    serialized = parsed.model_dump_json()
    assert "A door opens in the dark" not in serialized
    assert "Door latch" not in serialized
    assert "/home/" not in serialized


def test_wf_parser_maps_turns_and_keeps_narrator_as_hashed_chapter_card_only():
    document = {
        "episode_id": "wf_episode",
        "scenes": [
            {
                "scene_id": "wf_scene",
                "turns": [
                    {"character": "Narrator", "text": "Chapter One", "confessional": False},
                    {"character": "Alice", "text": "Hello.", "confessional": False},
                    {"character": "Bob", "text": "Privately.", "confessional": True},
                ],
            }
        ],
    }

    parsed = parser.parse_wf_episode_script(
        document,
        project_id="project_alpha",
        created_by="agent:worker_1",
        actors=(_actor("alice", "voice_alice"), _actor("bob", "voice_bob")),
        character_routes={"Alice": "alice", "Bob": "bob"},
        narrator_character="Narrator",
    )

    assert tuple(item.line.character_id for item in parsed.parsed_lines) == ("alice", "bob")
    assert tuple(item.performance_kind.value for item in parsed.parsed_lines) == (
        "dialogue",
        "confessional",
    )
    assert len(parsed.chapter_cards) == 1
    assert parsed.chapter_cards[0].text_hash.startswith("sha256:")
    assert parsed.scenes[0].event_ids == (
        "chapter_0001_0001",
        "line_0001_0001",
        "line_0001_0002",
    )
    serialized = parsed.model_dump_json()
    assert "Chapter One" not in serialized
    assert "Privately" not in serialized
    assert "Narrator" not in tuple(item.line.character_id for item in parsed.parsed_lines)


@pytest.mark.parametrize("defect", ["duplicate_line", "missing_membership", "reordered_membership"])
def test_parsed_script_model_rejects_referential_integrity_defects(defect):
    payload = _generic_parsed().model_dump(mode="json")
    if defect == "duplicate_line":
        payload["parsed_lines"][1]["line"]["line_id"] = payload["parsed_lines"][0]["line"]["line_id"]
    elif defect == "missing_membership":
        payload["scenes"][0]["line_ids"] = payload["scenes"][0]["line_ids"][:1]
    else:
        payload["scenes"][0]["line_ids"] = list(reversed(payload["scenes"][0]["line_ids"]))

    with pytest.raises(ValidationError):
        parser.ParsedScript.model_validate(payload)


@pytest.mark.parametrize("defect", ["event_scene", "beat_scene"])
def test_parsed_script_rejects_event_or_beat_scene_ownership_mismatch(defect):
    payload = _generic_parsed().model_dump(mode="json")
    if defect == "event_scene":
        payload["events"][0]["scene_id"] = "scene_other"
    else:
        payload["beats"][0]["scene_id"] = "scene_other"

    with pytest.raises(ValidationError):
        parser.ParsedScript.model_validate(payload)


@pytest.mark.parametrize(("event_index", "wrong_kind"), [(0, "beat"), (1, "line")])
def test_parsed_script_rejects_line_or_beat_event_kind_mismatch(event_index, wrong_kind):
    payload = _generic_parsed().model_dump(mode="json")
    payload["events"][event_index]["kind"] = wrong_kind

    with pytest.raises(ValidationError):
        parser.ParsedScript.model_validate(payload)


def test_parsed_script_rejects_chapter_event_kind_mismatch():
    payload = _chapter_only_parsed().model_dump(mode="json")
    payload["events"][0]["kind"] = "line"

    with pytest.raises(ValidationError):
        parser.ParsedScript.model_validate(payload)


def test_parsed_script_rejects_beat_after_line_from_another_scene():
    payload = _two_scene_parsed().model_dump(mode="json")
    payload["beats"][0]["after_line_id"] = "line_0002_0001"

    with pytest.raises(ValidationError):
        parser.ParsedScript.model_validate(payload)


def test_parsed_script_rejects_chapter_card_scene_ownership_mismatch():
    payload = _chapter_only_parsed().model_dump(mode="json")
    payload["chapter_cards"][0]["scene_id"] = "scene_other"

    with pytest.raises(ValidationError):
        parser.ParsedScript.model_validate(payload)
