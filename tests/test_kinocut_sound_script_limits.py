"""Resource ceilings for hostile standalone script inputs."""

from kinocut_sound.limits import (
    MAX_SCRIPT_ACTORS,
    MAX_SCRIPT_BEATS_PER_SCENE,
    MAX_SCRIPT_EVENTS_PER_SCENE,
    MAX_SCRIPT_LINES_PER_SCENE,
    MAX_SCRIPT_SCENES,
    MAX_SCRIPT_TEXT_LENGTH_CHARS,
    MAX_SCRIPT_TURNS_PER_SCENE,
)


def test_script_input_limits_are_positive_and_internally_consistent() -> None:
    limits = (
        MAX_SCRIPT_ACTORS,
        MAX_SCRIPT_SCENES,
        MAX_SCRIPT_LINES_PER_SCENE,
        MAX_SCRIPT_BEATS_PER_SCENE,
        MAX_SCRIPT_TURNS_PER_SCENE,
        MAX_SCRIPT_EVENTS_PER_SCENE,
        MAX_SCRIPT_TEXT_LENGTH_CHARS,
    )

    assert all(isinstance(value, int) and value > 0 for value in limits)
    assert MAX_SCRIPT_EVENTS_PER_SCENE >= MAX_SCRIPT_LINES_PER_SCENE
    assert MAX_SCRIPT_EVENTS_PER_SCENE >= MAX_SCRIPT_BEATS_PER_SCENE
