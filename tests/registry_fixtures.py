"""Canonical valid/invalid kwargs builders for registry contract tests.

Builders return **primitive** kwargs only (str/int/float/tuple/dict) and never
import the domain contract modules directly, mirroring the pattern in
``tests/contracts_fixtures.py``.
"""

from __future__ import annotations

from typing import Any

# Canonical sha256-shaped constants reused across builders.
_SHA = "sha256:" + "a" * 64
_SHA_B = "sha256:" + "b" * 64
_SHA_C = "sha256:" + "c" * 64
_ASSET = "sha256:" + "d" * 64
_ASSET_B = "sha256:" + "e" * 64
_ASSET_C = "sha256:" + "f" * 64


def clip_technical_kwargs(**overrides: Any) -> dict[str, Any]:
    """Kwargs for valid ``ClipTechnicalMetadata``."""

    kwargs: dict[str, Any] = {
        "duration_seconds": 5.0,
        "width": 1920,
        "height": 1080,
        "fps": 30.0,
        "codec": "h264",
        "has_audio": True,
    }
    kwargs.update(overrides)
    return kwargs


def bed_technical_kwargs(**overrides: Any) -> dict[str, Any]:
    """Kwargs for valid ``BedTechnicalMetadata``."""

    kwargs: dict[str, Any] = {
        "duration_seconds": 30.0,
        "sample_rate": 48000,
        "channels": 2,
        "codec": "aac",
    }
    kwargs.update(overrides)
    return kwargs


def _base(created_by: str = "human", **overrides: Any) -> dict[str, Any]:
    """Shared provenance kwargs every registry record needs."""

    kwargs: dict[str, Any] = {"project_id": "proj-alpha", "created_by": created_by}
    kwargs.update(overrides)
    return kwargs


def clip_record_kwargs(**overrides: Any) -> dict[str, Any]:
    """Kwargs for a valid ``ClipRecord``."""

    kwargs = _base(
        created_by="tool",
        asset_id=_ASSET,
        source_asset_id=_ASSET,
        verdict_id=_SHA,
        review_decision_id=_SHA_B,
        usage_rights_status="cleared",
        technical=clip_technical_kwargs(),
        tags=(),
        embedding_ref=_SHA_C,
        semantic_span_id=None,
    )
    kwargs.update(overrides)
    return kwargs


def bed_record_kwargs(**overrides: Any) -> dict[str, Any]:
    """Kwargs for a valid ``BedRecord``."""

    kwargs = _base(
        created_by="tool",
        asset_id=_ASSET,
        usage_rights_status="cleared",
        review_decision_id=_SHA_B,
        technical=bed_technical_kwargs(),
        mood="upbeat",
        tempo_bpm=120,
        musical_key="C_major",
        tags=(),
        family_id=None,
        embedding_ref=_SHA_C,
    )
    kwargs.update(overrides)
    return kwargs


def lineage_link_kwargs(**overrides: Any) -> dict[str, Any]:
    """Kwargs for a valid ``LineageLink``."""

    kwargs = _base(
        created_by="tool",
        derivative_asset_id=_ASSET,
        source_asset_ids=(_ASSET_B,),
        relation="generated_from",
        family_id=None,
        lineage_value=None,
        prompt_outcome_id=None,
    )
    kwargs.update(overrides)
    return kwargs
