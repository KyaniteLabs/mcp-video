"""Hostile review regressions for S4 assembly planning contracts."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from kinocut_sound import episode_assembly as assembly
from kinocut_sound import script_parser as parser
from kinocut_sound.lines import Emotion, ProfileRef, Prosody
from kinocut_sound.timeline import CueKind


def _actor() -> parser.ActorRoute:
    return parser.ActorRoute(
        actor_id="actor_a",
        profile=ProfileRef(profile_id="voice_a", version=1),
        dialogue_spatial_preset="medium_room",
        confessional_spatial_preset="close_mic_dry",
        off_screen_spatial_preset="off_screen_distance",
        narration_spatial_preset="medium_room",
        prosody=Prosody(),
        emotion=Emotion(label="neutral", intensity=0.0),
        inherit_loudness=True,
    )


def _document(scene_id: str = "scene_review", scene_pause: float = 0.0):
    return {
        "episode_id": "episode_review",
        "scenes": [
            {
                "scene_id": scene_id,
                "pause_after_seconds": scene_pause,
                "lines": [
                    {
                        "actor_id": "actor_a",
                        "text": "First.",
                        "kind": "dialogue",
                        "pause_after_seconds": 0.0,
                    },
                    {
                        "actor_id": "actor_a",
                        "text": "Second.",
                        "kind": "dialogue",
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
                        "asset_hash": "sha256:" + "c" * 64,
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
                        "text": "Pause",
                        "after_line_index": 2,
                        "duration_seconds": 0.2,
                    },
                ],
            }
        ],
    }


def _parsed(scene_id: str = "scene_review", scene_pause: float = 0.0):
    return parser.parse_episode_script(
        _document(scene_id, scene_pause),
        project_id="project_alpha",
        created_by="agent:worker_1",
        actors=(_actor(),),
    )


def _clips(parsed):
    return tuple(
        assembly.ClipRef(
            line_id=item.line.line_id,
            artifact_hash="sha256:" + marker * 64,
            source_ref=f"clips/{item.line.line_id}.wav",
            duration_seconds=1.0,
        )
        for item, marker in zip(parsed.parsed_lines, ("a", "b"), strict=True)
    )


def test_planner_derives_source_order_foley_designed_silence_and_pacing_from_script():
    parsed = _parsed()

    plan = assembly.plan_episode_assembly(
        parsed,
        clips=_clips(parsed),
        created_by="agent:worker_1",
        cancellation_requested=False,
    )

    assert tuple(cue.kind for cue in plan.timeline.cues) == (
        CueKind.LINE,
        CueKind.FOLEY,
        CueKind.SILENCE,
        CueKind.LINE,
        CueKind.SILENCE,
    )
    assert tuple(cue.source_ref for cue in plan.timeline.cues) == (
        "clips/line_0001_0001.wav",
        "foley/door_latch.wav",
        "silence/held_breath.json",
        "clips/line_0001_0002.wav",
        "silence/pace.json",
    )
    assert plan.timeline.authoritative_duration_seconds == pytest.approx(2.9)


def test_scene_pause_cue_id_stays_bounded_for_maximum_valid_scene_id():
    scene_id = "s" * 64
    parsed = _parsed(scene_id=scene_id, scene_pause=0.5)

    plan = assembly.plan_episode_assembly(
        parsed,
        clips=_clips(parsed),
        created_by="agent:worker_1",
        cancellation_requested=False,
    )

    scene_pause = plan.timeline.cues[-1]
    assert scene_pause.kind == CueKind.SILENCE
    assert len(scene_pause.cue_id) <= 64
    assert scene_pause.source_ref == "silence/scene_pause.json"


def _plan(parsed=None):
    parsed = parsed or _parsed()
    return assembly.plan_episode_assembly(
        parsed,
        clips=_clips(parsed),
        created_by="agent:worker_1",
        cancellation_requested=False,
    )


def test_planner_revalidates_poisoned_parsed_script_at_public_boundary():
    parsed = _parsed()
    poisoned_card = parser.ChapterCard.model_construct(
        chapter_id="chapter_poison",
        scene_id=parsed.scenes[0].scene_id,
        text_hash="RAW_SECRET_NOT_A_HASH",
        text_length_chars=6,
    )
    poisoned = parsed.model_copy(update={"chapter_cards": (poisoned_card,)})

    with pytest.raises(assembly.AssemblyPlanningError):
        _plan(poisoned)


def test_planner_translates_wrong_clip_runtime_type_to_custom_error():
    with pytest.raises(assembly.AssemblyPlanningError):
        assembly.plan_episode_assembly(
            _parsed(),
            clips=(object(),),
            created_by="agent:worker_1",
            cancellation_requested=False,
        )


@pytest.mark.parametrize(
    "defect",
    ["clip_hashes", "route_line_id", "line_cue_kind", "foley_hashes"],
)
def test_episode_assembly_rejects_artifact_timeline_integrity_defects(defect):
    payload = _plan().model_dump(mode="json")
    if defect == "clip_hashes":
        payload["clip_hashes"] = []
    elif defect == "route_line_id":
        payload["routes"][0]["line_id"] = "line_other"
    elif defect == "line_cue_kind":
        line_cue = next(cue for cue in payload["timeline"]["cues"] if cue["kind"] == "line")
        line_cue["kind"] = "silence"
    else:
        payload["foley_hashes"] = []

    with pytest.raises(ValidationError):
        assembly.EpisodeAssembly.model_validate(payload)
