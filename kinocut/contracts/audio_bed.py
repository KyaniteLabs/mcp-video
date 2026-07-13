"""Edit-receipt v1 contract for the governed audio-bed primitive.

This receipt follows the shared edit-receipt-v1 substrate described in the
field-wishlist design: ``schema_version: 1``, ``receipt_kind: "edit"``, ordered
inputs with privacy-safe display names and content hashes, normalized
parameters, output identity, toolchain fingerprint, warning codes, and a
deterministic receipt hash. Absolute source paths are structurally
unrepresentable — every identity-like field is a content hash or a bounded
safe display name (basename only, no directory components).

The whole receipt is a frozen :class:`~pydantic.BaseModel` so it can be
canonicalised for the deterministic receipt hash without mutation risk.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from kinocut.contracts._common import Sha256

# A bounded safe display name: basename only, alphanumerics plus a small set of
# separator characters. No slashes, no absolute paths, no spaces — a host path
# or URL simply cannot match this pattern, enforcing privacy structurally.
_SAFE_DISPLAY_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")

# Bounded warning codes: alphanumerics plus underscore/hyphen, no prose.
_SAFE_CODE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")

# Bounded toolchain key.
_SAFE_TOOLCHAIN_KEY_RE = re.compile(r"^[a-z][a-z0-9_]{0,31}$")


class AudioBedInput(BaseModel):
    """One ordered input to the audio-bed operation, identified by content hash."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    role: Literal["voice_source", "music_bed"]
    content_sha256: Sha256
    probed_duration_seconds: float = Field(ge=0.0)
    display_name: str = Field(min_length=1, max_length=128)
    has_audio_stream: bool

    @field_validator("display_name")
    @classmethod
    def _safe_display(cls, value: str) -> str:
        if not _SAFE_DISPLAY_NAME_RE.match(value):
            raise ValueError("display_name must be a bounded basename (no paths or prose)")
        return value


class AudioBedParameters(BaseModel):
    """Normalized, bounded parameters bound to the audio-bed render."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    loop: bool
    loop_crossfade_seconds: float = Field(ge=0.0, le=30.0)
    fade_in_seconds: float = Field(ge=0.0, le=30.0)
    fade_out_seconds: float = Field(ge=0.0, le=30.0)
    target_lufs: float = Field(ge=-70.0, le=-5.0)
    duck_threshold: float = Field(gt=0.0, le=1.0)
    duck_ratio: float = Field(ge=1.0, le=20.0)
    duck_attack_ms: float = Field(ge=1.0, le=2000.0)
    duck_release_ms: float = Field(ge=1.0, le=9000.0)
    duration_policy: Literal["keep_video"] = "keep_video"


class AudioBedReceipt(BaseModel):
    """Edit-receipt v1 emitted by the governed audio-bed primitive."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    schema_version: Literal[1] = 1
    receipt_kind: Literal["edit"] = "edit"
    operation: Literal["audio_bed"] = "audio_bed"
    inputs: tuple[AudioBedInput, ...] = Field(min_length=2, max_length=2)
    parameters: AudioBedParameters
    output_content_sha256: Sha256
    output_duration_seconds: float = Field(ge=0.0)
    output_display_name: str = Field(min_length=1, max_length=128)
    ducking_engaged: bool
    loudness_filter: Literal["loudnorm"] = "loudnorm"
    warnings: tuple[str, ...] = ()
    human_review_required: bool = True
    toolchain: tuple[tuple[str, str | None], ...] = ()
    receipt_sha256: Sha256 | None = None

    @field_validator("output_display_name")
    @classmethod
    def _safe_output_display(cls, value: str) -> str:
        if not _SAFE_DISPLAY_NAME_RE.match(value):
            raise ValueError("output_display_name must be a bounded basename (no paths or prose)")
        return value

    @field_validator("warnings")
    @classmethod
    def _safe_warnings(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        for v in values:
            if not _SAFE_CODE_RE.match(v):
                raise ValueError("warning codes must be bounded identifiers")
        return values

    @field_validator("toolchain")
    @classmethod
    def _safe_toolchain(cls, values: tuple[tuple[str, str | None], ...]) -> tuple[tuple[str, str | None], ...]:
        for key, _val in values:
            if not _SAFE_TOOLCHAIN_KEY_RE.match(key):
                raise ValueError("toolchain keys must be bounded identifiers")
        return values
