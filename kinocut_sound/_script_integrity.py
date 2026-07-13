"""Private cross-record integrity checks for parsed sound scripts."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any


def validate_script_relationships(
    *,
    scenes: Sequence[Any],
    parsed_lines: Sequence[Any],
    beats: Sequence[Any],
    chapter_cards: Sequence[Any],
    events: Sequence[Any],
) -> None:
    """Reject cross-object ownership and event-type inconsistencies."""
    targets = {
        item.line.line_id: ("line", item.scene_id) for item in parsed_lines
    }
    targets.update({item.beat_id: ("beat", item.scene_id) for item in beats})
    targets.update(
        {item.chapter_id: ("chapter_card", item.scene_id) for item in chapter_cards}
    )
    event_by_id = {event.event_id: event for event in events}

    for scene in scenes:
        for event_id in scene.event_ids:
            event = event_by_id[event_id]
            target_kind, target_scene_id = targets[event_id]
            if event.scene_id != scene.scene_id or target_scene_id != scene.scene_id:
                raise ValueError(
                    "event and target scene ownership must match the containing scene"
                )
            if event.kind.value != target_kind:
                raise ValueError("event kind must match its referenced target type")

    line_scene_by_id = {
        item.line.line_id: item.scene_id for item in parsed_lines
    }
    for beat in beats:
        if (
            beat.after_line_id is not None
            and line_scene_by_id.get(beat.after_line_id) != beat.scene_id
        ):
            raise ValueError("beat after_line_id must reference a line in the same scene")
