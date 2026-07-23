from __future__ import annotations

import pytest
from pydantic import ValidationError

from kinocut.product.config import (
    AudioFinishingConfig,
    CANONICAL_EXTERNAL_PLATFORMS,
    IntakeConfig,
    RenderConfig,
    ShortsConfig,
    config_from_mapping,
    externalise_platform,
    normalise_platform,
    normalise_platforms,
)


@pytest.mark.parametrize(
    ("raw", "internal", "external"),
    [
        ("youtube-shorts", "youtube_shorts", "youtube-shorts"),
        ("instagram-reel", "instagram_reels", "instagram-reel"),
        ("youtube_shorts", "youtube_shorts", "youtube-shorts"),
    ],
)
def test_platform_round_trip(raw: str, internal: str, external: str) -> None:
    assert normalise_platform(raw) == internal
    assert externalise_platform(internal) == external


@pytest.mark.parametrize("value", ["tiktok", "youtube_short"])
def test_normalise_platform_rejects_unknown(value: str) -> None:
    with pytest.raises(ValueError, match="unknown platform"):
        normalise_platform(value)
    with pytest.raises(ValueError, match="unknown platform"):
        externalise_platform(value)


def test_normalise_platforms_dedupes_and_canonical_listing() -> None:
    assert normalise_platforms(["youtube-shorts", "youtube_shorts", "instagram-reel"]) == (
        "youtube_shorts",
        "instagram_reels",
    )
    assert set(CANONICAL_EXTERNAL_PLATFORMS) == {"youtube-shorts", "instagram-reel"}


def test_shorts_config_defaults_normalisation_and_unknown_rejection() -> None:
    cfg = ShortsConfig()
    assert cfg.platforms == ("youtube_shorts", "instagram_reels")
    assert cfg.intake.resolution_policy == "warn"
    assert cfg.render.audio.fade_seconds == 0.05
    normalised = ShortsConfig(platforms=("youtube-shorts", "youtube_shorts", "instagram-reel"))
    assert normalised.platforms == ("youtube_shorts", "instagram_reels")
    with pytest.raises(ValidationError, match="unknown platform"):
        ShortsConfig(platforms=("tiktok",))
    with pytest.raises(ValidationError, match="at least one platform"):
        ShortsConfig(platforms=())
    for unsafe in ("/tmp/output", "../output", "safe/../../output", "bad\x00path"):
        with pytest.raises(ValidationError, match="project-relative"):
            ShortsConfig(output_dir=unsafe)


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"min_clip_seconds": 0}, "greater than 0"),
        ({"min_clip_seconds": 30, "max_clip_seconds": 30}, "strictly greater"),
    ],
)
def test_window_validation(kwargs: dict[str, float], match: str) -> None:
    with pytest.raises(ValidationError, match=match):
        ShortsConfig(**kwargs)
    with pytest.raises(ValidationError, match=match):
        IntakeConfig(**{k.replace("clip", "duration"): v for k, v in kwargs.items()})


def test_audio_defaults_and_unknown_field_rejection() -> None:
    audio = AudioFinishingConfig()
    assert audio.lufs == -14.0
    assert audio.fade_seconds == 0.05
    for field in ("true_peak_db", "declick", "noise_reduction"):
        with pytest.raises(ValidationError):
            AudioFinishingConfig.model_validate({field: -1.0})


@pytest.mark.parametrize(
    ("lufs", "fade"),
    [(-40.0, 0.05), (-14.0, 3.0)],
)
def test_audio_out_of_range_rejected(lufs: float, fade: float) -> None:
    with pytest.raises(ValidationError):
        AudioFinishingConfig(lufs=lufs, fade_seconds=fade)


def test_config_from_mapping_none_nested_and_unknown_keys() -> None:
    assert config_from_mapping(None) == ShortsConfig()
    existing = ShortsConfig(platforms=("instagram-reel",))
    assert config_from_mapping(existing) is existing
    cfg = config_from_mapping(
        {
            "platforms": ["youtube-shorts"],
            "intake": {"resolution_policy": "reject"},
            "render": {"burned_captions": True, "audio": {"lufs": -12.0}},
        }
    )
    assert cfg.platforms == ("youtube_shorts",)
    assert cfg.intake.resolution_policy == "reject"
    assert cfg.render.audio.lufs == -12.0
    with pytest.raises(ValidationError):
        config_from_mapping({"platforms": ["youtube-shorts"], "rogue_field": True})
    with pytest.raises(ValidationError):
        RenderConfig.model_validate({"subject_reframe": True})


def test_models_are_frozen_and_strict_with_json_round_trip() -> None:
    cfg = ShortsConfig(platforms=("youtube-shorts",), output_dir="out")
    payload = cfg.model_dump_json()
    assert payload == cfg.model_dump_json()
    assert ShortsConfig.model_validate_json(payload) == cfg
    with pytest.raises(ValidationError):
        cfg.platforms = ()  # type: ignore[misc]
    with pytest.raises(ValidationError):
        ShortsConfig.model_validate({"platforms": ["youtube-shorts"], "extra": 1})
