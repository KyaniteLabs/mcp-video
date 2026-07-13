"""Contract tests for ClipRecord, BedRecord, and LineageLink (backlog #36, #38, #41).

Verifies the strict privacy posture: raw prompts, transcripts, PII, and host
paths are structurally unrepresentable. Media identity is always a content
hash; embeddings are referenced by artifact hash; provenance is stored by hash
only; tags are bounded lowercase labels.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from kinocut.contracts._common import RecordBase, canonical_record_id
from kinocut.contracts.registry import (
    BedRecord,
    BedTechnicalMetadata,
    ClipRecord,
    ClipTechnicalMetadata,
    LineageLink,
    LineageRelation,
)
from tests.registry_fixtures import (
    bed_record_kwargs,
    bed_technical_kwargs,
    clip_record_kwargs,
    clip_technical_kwargs,
    lineage_link_kwargs,
)

_ASSET = "sha256:" + "d" * 64
_ASSET_B = "sha256:" + "e" * 64
_SHA = "sha256:" + "a" * 64


# ---- ClipRecord ----------------------------------------------------------


def test_clip_record_is_a_record():
    clip = ClipRecord(**clip_record_kwargs())
    assert isinstance(clip, RecordBase)
    assert canonical_record_id(clip).startswith("sha256:")


def test_clip_record_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        ClipRecord(**clip_record_kwargs(surprise=True))


def test_clip_record_is_frozen():
    clip = ClipRecord(**clip_record_kwargs())
    with pytest.raises(ValidationError):
        clip.asset_id = _ASSET_B


def test_clip_record_asset_id_must_be_sha256():
    with pytest.raises(ValidationError):
        ClipRecord(**clip_record_kwargs(asset_id="not-a-hash"))


def test_clip_record_verdict_id_must_be_sha256():
    with pytest.raises(ValidationError):
        ClipRecord(**clip_record_kwargs(verdict_id="bad"))


def test_clip_record_review_decision_id_must_be_sha256():
    with pytest.raises(ValidationError):
        ClipRecord(**clip_record_kwargs(review_decision_id="bad"))


def test_clip_record_embedding_ref_must_be_sha256_or_none():
    with pytest.raises(ValidationError):
        ClipRecord(**clip_record_kwargs(embedding_ref="not-a-hash"))
    # None is valid.
    clip = ClipRecord(**clip_record_kwargs(embedding_ref=None))
    assert clip.embedding_ref is None


def test_clip_record_has_no_prompt_or_transcript_field():
    """Raw prompts and transcripts are structurally unrepresentable."""

    assert "prompt" not in ClipRecord.model_fields
    assert "prompt_hash" not in ClipRecord.model_fields
    assert "transcript" not in ClipRecord.model_fields
    assert "transcript_hash" not in ClipRecord.model_fields
    assert "original_location" not in ClipRecord.model_fields
    assert "file_path" not in ClipRecord.model_fields


def test_clip_record_tag_must_be_bounded_lowercase():
    with pytest.raises(ValidationError):
        ClipRecord(**clip_record_kwargs(tags=("UPPER",)))
    with pytest.raises(ValidationError):
        ClipRecord(**clip_record_kwargs(tags=("",)))
    with pytest.raises(ValidationError):
        ClipRecord(**clip_record_kwargs(tags=("has space",)))


def test_clip_record_tags_must_be_unique():
    with pytest.raises(ValidationError):
        ClipRecord(**clip_record_kwargs(tags=("intro", "intro")))


def test_clip_record_too_many_tags_rejected():
    too_many = tuple(f"tag{i}" for i in range(33))
    with pytest.raises(ValidationError):
        ClipRecord(**clip_record_kwargs(tags=too_many))


def test_clip_technical_metadata_rejects_negative_duration():
    with pytest.raises(ValidationError):
        ClipTechnicalMetadata(**clip_technical_kwargs(duration_seconds=-1.0))


def test_clip_technical_metadata_rejects_zero_resolution():
    with pytest.raises(ValidationError):
        ClipTechnicalMetadata(**clip_technical_kwargs(width=0))
    with pytest.raises(ValidationError):
        ClipTechnicalMetadata(**clip_technical_kwargs(height=0))


def test_clip_record_semantic_span_id_is_bounded():
    with pytest.raises(ValidationError):
        ClipRecord(**clip_record_kwargs(semantic_span_id="has spaces"))
    # A bounded id is valid.
    clip = ClipRecord(**clip_record_kwargs(semantic_span_id="shot.001:01"))
    assert clip.semantic_span_id == "shot.001:01"


# ---- BedRecord -----------------------------------------------------------


def test_bed_record_is_a_record():
    bed = BedRecord(**bed_record_kwargs())
    assert isinstance(bed, RecordBase)
    assert canonical_record_id(bed).startswith("sha256:")


def test_bed_record_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        BedRecord(**bed_record_kwargs(surprise=True))


def test_bed_record_has_no_prompt_or_transcript_field():
    assert "prompt" not in BedRecord.model_fields
    assert "transcript" not in BedRecord.model_fields
    assert "original_location" not in BedRecord.model_fields


def test_bed_record_tag_validation_matches_clip():
    with pytest.raises(ValidationError):
        BedRecord(**bed_record_kwargs(tags=("UPPER",)))
    with pytest.raises(ValidationError):
        BedRecord(**bed_record_kwargs(tags=("dup", "dup")))


def test_bed_record_tempo_bpm_is_bounded():
    with pytest.raises(ValidationError):
        BedRecord(**bed_record_kwargs(tempo_bpm=0))
    with pytest.raises(ValidationError):
        BedRecord(**bed_record_kwargs(tempo_bpm=999))


def test_bed_record_family_id_is_bounded():
    with pytest.raises(ValidationError):
        BedRecord(**bed_record_kwargs(family_id="UPPER"))
    bed = BedRecord(**bed_record_kwargs(family_id="upbeat_family_1"))
    assert bed.family_id == "upbeat_family_1"


def test_bed_technical_metadata_rejects_negative_duration():
    with pytest.raises(ValidationError):
        BedTechnicalMetadata(**bed_technical_kwargs(duration_seconds=-1.0))


# ---- LineageLink ---------------------------------------------------------


def test_lineage_link_is_a_record():
    link = LineageLink(**lineage_link_kwargs())
    assert isinstance(link, RecordBase)
    assert canonical_record_id(link).startswith("sha256:")


def test_lineage_relation_is_closed_enum():
    assert {r.value for r in LineageRelation} == {
        "generated_from",
        "variant_of",
        "repair_of",
        "derived_from",
        "family_member",
    }


def test_lineage_link_requires_at_least_one_source():
    with pytest.raises(ValidationError):
        LineageLink(**lineage_link_kwargs(source_asset_ids=()))


def test_lineage_link_rejects_duplicate_sources():
    with pytest.raises(ValidationError):
        LineageLink(**lineage_link_kwargs(source_asset_ids=(_ASSET_B, _ASSET_B)))


def test_lineage_link_rejects_self_derivation_on_directed_edge():
    with pytest.raises(ValidationError):
        LineageLink(
            **lineage_link_kwargs(
                derivative_asset_id=_ASSET,
                source_asset_ids=(_ASSET,),
                relation="generated_from",
            )
        )


def test_lineage_link_allows_self_reference_on_family_member():
    """FAMILY_MEMBER is undirected grouping, not derivation."""

    link = LineageLink(
        **lineage_link_kwargs(
            derivative_asset_id=_ASSET,
            source_asset_ids=(_ASSET,),
            relation="family_member",
        )
    )
    assert link.relation is LineageRelation.FAMILY_MEMBER


def test_lineage_link_has_no_prompt_or_transcript_field():
    assert "prompt" not in LineageLink.model_fields
    assert "transcript" not in LineageLink.model_fields
    assert "original_location" not in LineageLink.model_fields


def test_lineage_link_provenance_is_hash_only():
    """The embedded GenerationLineage stores prompt_hash, never raw text."""

    link = LineageLink(
        **lineage_link_kwargs(
            lineage_value={
                "generator_model": "veo-3",
                "provider_id": "provider-x",
                "prompt_hash": _SHA,
                "generation_settings_hash": _SHA,
                "source_asset_ids": (),
                "reference_asset_ids": (),
            }
        )
    )
    assert link.lineage_value is not None
    assert link.lineage_value.prompt_hash == _SHA
