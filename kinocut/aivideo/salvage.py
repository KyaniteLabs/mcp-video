"""Guarded, lineage-bound derivatives for five bounded salvage recipes."""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import tempfile
from enum import StrEnum
from pathlib import Path
from typing import Any, cast

from pydantic import Field, TypeAdapter, ValidationError, model_validator

from kinocut.aivideo.protection import (
    MutationIntent,
    MutationOperation,
    assert_no_protected_collision,
)
from kinocut.aivideo.salvage_checks import (
    PreservationCheck,
    _audio_removed_check,
    _clean_edges_origin_check,
    _crop_origin_check,
    _duration_check,
    _freeze_checks,
    _region_crop_origin_check,
    _salvage_error,
    _source_unchanged_check,
    _still_frame_origin_check,
)
from kinocut.aivideo.salvage_render import _probe_source, _render
from kinocut.contracts._common import NormalizedRegion, Sha256, ValueObject
from kinocut.contracts.asset import AssetRecord, GenerationLineage, MediaKind
from kinocut.contracts.verdict import ClipVerdict, Disposition
from kinocut.engine_body_swap import _audio_fingerprint
from kinocut.engine_probe import probe
from kinocut.errors import MCPVideoError
from kinocut.ffmpeg_helpers import _run_command
from kinocut.projectstore import Project, append_record, ingest_asset, layout, read_records, store
from kinocut.rescue.operations import _sha256
from kinocut.source_identity import SourceIdentity, VerifiedSource, copy_verified_snapshot


class SalvageRecipe(StrEnum):
    CLEAN_EDGES = "clean_edges"
    FREEZE_EXTENSION = "freeze_extension"
    STILL_FRAME = "still_frame"
    REGION_CROP = "region_crop"
    BACKGROUND_ONLY = "background_only"


class _CleanEdges(ValueObject):
    trim_start: float = Field(ge=0.0)
    trim_end: float = Field(ge=0.0)

    @model_validator(mode="after")
    def _changes_an_edge(self) -> _CleanEdges:
        if self.trim_start == 0.0 and self.trim_end == 0.0:
            raise ValueError("at least one edge must be trimmed")
        return self


class _FreezeExtension(ValueObject):
    extension_seconds: float = Field(gt=0.0)


class _StillFrame(ValueObject):
    timestamp: float = Field(ge=0.0)


class _RegionCrop(ValueObject):
    region: NormalizedRegion

    @model_validator(mode="after")
    def _changes_the_frame(self) -> _RegionCrop:
        if self.region == NormalizedRegion(x=0.0, y=0.0, width=1.0, height=1.0):
            raise ValueError("crop must be smaller than the full frame")
        return self


class _BackgroundOnly(_RegionCrop):
    """A caller-declared background region, not semantic subject removal."""


class SalvageResult(ValueObject):
    recipe: SalvageRecipe
    policy: dict[str, Any]
    policy_hash: Sha256
    output_hash: Sha256
    lineage_artifact_id: Sha256
    lineage_artifact_location: str
    asset: AssetRecord
    verdict: ClipVerdict
    preservation_checks: tuple[PreservationCheck, ...]


_POLICY_MODELS = {
    SalvageRecipe.CLEAN_EDGES: _CleanEdges,
    SalvageRecipe.FREEZE_EXTENSION: _FreezeExtension,
    SalvageRecipe.STILL_FRAME: _StillFrame,
    SalvageRecipe.REGION_CROP: _RegionCrop,
    SalvageRecipe.BACKGROUND_ONLY: _BackgroundOnly,
}
_SHA_ADAPTER = TypeAdapter(Sha256)
_SALVAGE_OPERATIONS = {
    SalvageRecipe.CLEAN_EDGES: MutationOperation.SALVAGE_CLEAN_EDGES,
    SalvageRecipe.FREEZE_EXTENSION: MutationOperation.SALVAGE_FREEZE_EXTENSION,
    SalvageRecipe.STILL_FRAME: MutationOperation.SALVAGE_STILL_FRAME,
    SalvageRecipe.REGION_CROP: MutationOperation.SALVAGE_REGION_CROP,
    SalvageRecipe.BACKGROUND_ONLY: MutationOperation.SALVAGE_BACKGROUND_ONLY,
}


def _canonical(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode(
        "utf-8"
    )


def _digest(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _validated_policy(recipe: Any, policy: Any) -> tuple[SalvageRecipe, dict[str, Any], str]:
    try:
        selected = SalvageRecipe(recipe)
        model = _POLICY_MODELS[selected].model_validate(policy)
    except (TypeError, ValueError, ValidationError) as exc:
        raise _salvage_error("salvage policy is invalid", "invalid_salvage_policy") from exc
    payload = {"recipe": selected.value, **model.model_dump(mode="json")}
    return selected, payload, _digest(_canonical(payload))


def _mutation_intent(
    recipe: SalvageRecipe,
    policy: dict[str, Any],
    source_asset_id: str,
    audio_stream_id: str,
    authorization_decision_ids: tuple[str, ...],
) -> MutationIntent:
    """Build the exact engine-owned dependency footprint for one recipe."""

    policy_hash = _digest(_canonical(policy))
    values: dict[str, Any] = {
        "operation": _SALVAGE_OPERATIONS[recipe],
        "source_asset": source_asset_id,
        "audio_stream": audio_stream_id,
        "authorization_decision_ids": authorization_decision_ids,
    }
    if recipe in {SalvageRecipe.CLEAN_EDGES, SalvageRecipe.STILL_FRAME}:
        values["clip_range"] = policy_hash
    elif recipe is SalvageRecipe.FREEZE_EXTENSION:
        values["timing_map"] = policy_hash
    else:
        values["render_parameter_set"] = policy_hash
    return MutationIntent(**values)


def _salvage_audio_fingerprint(source: Path, *, pass_fds: tuple[int, ...] = ()) -> str:
    """Return exact audio identity, including a stable no-audio sentinel."""

    if _probe_source(source, pass_fds=pass_fds).audio_codec is None:
        return _digest(b"kinocut.salvage.no-audio.v1")
    return _audio_fingerprint(str(source), pass_fds=pass_fds)


@contextlib.contextmanager
def _verified_source_snapshot(source: Path, expected: SourceIdentity, workspace: Path):
    """Yield the held anonymous descriptor for one verified source snapshot."""

    held = copy_verified_snapshot(str(source), workspace / ".source-copy", expected)
    try:
        yield held
    finally:
        held.close()


def _checked_hash(path: Path, *, missing_message: str) -> str:
    """Hash one existing in-store file with privacy-safe filesystem errors."""

    with store._mapped_os_errors():
        if not path.is_file():
            raise _salvage_error(missing_message, "salvage_integrity_failed")
        return _sha256(path)


def _active_source(project: Project, asset_id: str) -> tuple[AssetRecord, Path]:
    records = [r for r in read_records(project, "asset_record") if type(r) is AssetRecord]
    superseded = {r.supersedes for r in records if r.supersedes is not None}
    matches = [r for r in records if r.asset_id == asset_id and r.record_id not in superseded]
    if len(matches) != 1:
        raise _salvage_error("source asset is missing or ambiguous", "salvage_source_invalid")
    source = matches[0]
    path = store.safe_target(project, source.original_location)
    if _checked_hash(path, missing_message="source asset is missing") != source.asset_id:
        raise _salvage_error("source asset integrity check failed", "salvage_integrity_failed")
    if source.media_kind is not MediaKind.VIDEO:
        raise _salvage_error("salvage source must be a video", "salvage_source_invalid")
    return source, path


def _checks(
    recipe: SalvageRecipe,
    policy: dict[str, Any],
    source: Path,
    output: Path,
    source_hash: str,
    *,
    verified_source: VerifiedSource,
    pass_fds: tuple[int, ...] = (),
) -> tuple[PreservationCheck, ...]:
    _run_command(["ffmpeg", "-v", "error", "-i", str(output), "-f", "null", "-"])
    source_info = _probe_source(source, pass_fds=pass_fds)
    output_info = probe(str(output))
    observed_source = verified_source.verify().asset_id
    checks = [_source_unchanged_check(source_hash, observed_source)]
    if recipe is SalvageRecipe.CLEAN_EDGES:
        expected = source_info.duration - policy["trim_start"] - policy["trim_end"]
        checks.append(_duration_check(output_info.duration, expected))
        checks.append(_clean_edges_origin_check(source, output, policy, pass_fds=pass_fds))
    elif recipe is SalvageRecipe.FREEZE_EXTENSION:
        checks.append(_duration_check(output_info.duration, source_info.duration + policy["extension_seconds"]))
        checks.extend(_freeze_checks(source, output, pass_fds=pass_fds))
        checks.append(_audio_removed_check(output_info))
    elif recipe is SalvageRecipe.REGION_CROP:
        region = policy["region"]
        expected = f"{round(source_info.width * region['width'])}x{round(source_info.height * region['height'])}"
        checks.append(
            PreservationCheck(
                claim="requested_region_dimensions",
                passed=output_info.resolution == expected,
                expected=expected,
                observed=output_info.resolution,
            )
        )
        checks.append(_region_crop_origin_check(source, output, region, pass_fds=pass_fds))
    elif recipe is SalvageRecipe.BACKGROUND_ONLY:
        region = policy["region"]
        expected_dimensions = (
            f"{round(source_info.width * region['width'])}x{round(source_info.height * region['height'])}"
        )
        checks.append(
            PreservationCheck(
                claim="declared_background_region_dimensions",
                passed=output_info.resolution == expected_dimensions,
                expected=expected_dimensions,
                observed=output_info.resolution,
            )
        )
        checks.append(
            _crop_origin_check(
                source, output, region, claim="declared_background_region_pixels", pass_fds=pass_fds
            )
        )
        checks.append(_audio_removed_check(output_info))
        checks.append(_duration_check(output_info.duration, source_info.duration))
    else:
        checks.append(
            PreservationCheck(
                claim="still_frame_created",
                passed=output_info.width > 0,
                expected="decodable_image",
                observed="decodable_image" if output_info.width > 0 else "invalid",
            )
        )
        checks.append(
            _still_frame_origin_check(source, output, policy["timestamp"], pass_fds=pass_fds)
        )
    if not all(check.passed for check in checks):
        raise _salvage_error("render did not satisfy its preservation claims", "salvage_verification_failed")
    verified_source.verify()
    return tuple(checks)


def _checks_from_descriptor(
    recipe: SalvageRecipe,
    policy: dict[str, Any],
    source: VerifiedSource,
    output: Path,
    source_hash: str,
) -> tuple[PreservationCheck, ...]:
    return _checks(
        recipe,
        policy,
        Path(source.path),
        output,
        source_hash,
        verified_source=source,
        pass_fds=source.pass_fds,
    )


def _active_derivative(
    project: Project,
    source_asset_id: str,
    policy_hash: str,
) -> AssetRecord | None:
    """Find the unique already-published derivative for this exact intent."""

    records = [r for r in read_records(project, "asset_record") if type(r) is AssetRecord]
    superseded = {r.supersedes for r in records if r.supersedes is not None}
    matches = [
        r
        for r in records
        if r.record_id not in superseded
        and r.lineage is not None
        and r.lineage.generator_model == "kinocut.salvage.v1"
        and r.lineage.generation_settings_hash == policy_hash
        and r.lineage.source_asset_ids == (source_asset_id,)
    ]
    if len(matches) > 1:
        raise _salvage_error("salvage lineage is ambiguous", "salvage_integrity_failed")
    return matches[0] if matches else None


def _read_prior_derivative(
    project: Project,
    source_asset_id: str,
    policy: dict[str, Any],
    policy_hash: str,
) -> tuple[AssetRecord, str, str, tuple[PreservationCheck, ...]] | None:
    """Validate and return a prior publication; never reconstruct missing bytes."""

    asset = _active_derivative(project, source_asset_id, policy_hash)
    if asset is None:
        return None
    output = store.safe_target(project, asset.original_location)
    if _checked_hash(output, missing_message="published derivative is missing") != asset.asset_id:
        raise _salvage_error("derivative integrity check failed", "salvage_integrity_failed")
    if len(asset.derived_artifact_ids) != 1:
        raise _salvage_error("lineage artifact reference is invalid", "salvage_integrity_failed")
    artifact_id = asset.derived_artifact_ids[0]
    rel = layout.artifact_relative_path(artifact_id, "salvage-lineage.json")
    artifact = store.safe_target(project, rel)
    if _checked_hash(artifact, missing_message="published lineage artifact is missing") != artifact_id:
        raise _salvage_error("lineage artifact integrity check failed", "salvage_integrity_failed")
    try:
        with store._mapped_os_errors():
            payload = json.loads(artifact.read_text(encoding="utf-8"))
        checks = tuple(PreservationCheck.model_validate(item) for item in payload["preservation_checks"])
    except (KeyError, TypeError, json.JSONDecodeError, ValidationError) as exc:
        raise _salvage_error("lineage artifact is invalid", "salvage_integrity_failed") from exc
    expected = {
        "operation": policy["recipe"],
        "policy": policy,
        "policy_hash": policy_hash,
        "source_asset_id": source_asset_id,
        "output_hash": asset.asset_id,
    }
    if any(payload.get(key) != value for key, value in expected.items()) or not all(check.passed for check in checks):
        raise _salvage_error("lineage artifact does not match its asset", "salvage_integrity_failed")
    return asset, artifact_id, str(rel), checks


def _install_manifest(project: Project, payload: dict[str, Any]) -> tuple[str, str]:
    content = _canonical(payload)
    artifact_id = _digest(content)
    rel = layout.artifact_relative_path(artifact_id, "salvage-lineage.json")
    destination = store.safe_target(project, rel)
    with store._mapped_os_errors():
        destination.parent.mkdir(parents=True, exist_ok=True)
        exists = destination.exists()
    if exists:
        if _checked_hash(destination, missing_message="lineage artifact is missing") != artifact_id:
            raise _salvage_error("lineage artifact integrity check failed", "salvage_integrity_failed")
        return artifact_id, str(rel)
    with store._mapped_os_errors():
        fd, name = tempfile.mkstemp(dir=destination.parent, prefix=".salvage.", suffix=".tmp")
        temp = Path(name)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.link(temp, destination)
            except FileExistsError:
                if _sha256(destination) != artifact_id:
                    raise _salvage_error(
                        "lineage artifact integrity check failed",
                        "salvage_integrity_failed",
                    ) from None
            store._fsync_dir(destination.parent)
        finally:
            with contextlib.suppress(OSError):
                temp.unlink(missing_ok=True)
    return artifact_id, str(rel)


def _enrich_asset(project: Project, asset: AssetRecord, source: AssetRecord, artifact_id: str) -> AssetRecord:
    if asset.parent_asset_id == source.asset_id and artifact_id in asset.derived_artifact_ids:
        return asset
    enriched = asset.model_copy(
        update={
            "record_id": None,
            "supersedes": asset.record_id,
            "parent_asset_id": source.asset_id,
            "variant_of": source.asset_id,
            "derived_artifact_ids": (artifact_id,),
        }
    )
    try:
        return cast(AssetRecord, append_record(project, enriched))
    except MCPVideoError:
        records = [r for r in read_records(project, "asset_record") if type(r) is AssetRecord]
        superseded = {r.supersedes for r in records if r.supersedes is not None}
        matches = [r for r in records if r.asset_id == asset.asset_id and r.record_id not in superseded]
        if (
            len(matches) == 1
            and matches[0].parent_asset_id == source.asset_id
            and artifact_id in matches[0].derived_artifact_ids
        ):
            return matches[0]
        raise


def _verdict(project: Project, asset_id: str, acceptance_spec_id: str) -> ClipVerdict:
    candidate = ClipVerdict(
        project_id=project.project_id,
        created_by="tool:salvage",
        asset_hash=asset_id,
        disposition=Disposition.REPAIRABLE,
        acceptance_spec_id=acceptance_spec_id,
        reviewer="salvage-slot",
        rationale="Derivative requires fresh human editorial review",
    )
    existing = [r for r in read_records(project, "clip_verdict") if type(r) is ClipVerdict]
    match = next(
        (
            r
            for r in existing
            if r.model_dump(exclude={"record_id", "created_at"})
            == candidate.model_dump(exclude={"record_id", "created_at"})
        ),
        None,
    )
    if match is not None:
        return match
    try:
        return cast(ClipVerdict, append_record(project, candidate))
    except MCPVideoError:
        existing = [r for r in read_records(project, "clip_verdict") if type(r) is ClipVerdict]
        match = next(
            (
                r
                for r in existing
                if r.model_dump(exclude={"record_id", "created_at"})
                == candidate.model_dump(exclude={"record_id", "created_at"})
            ),
            None,
        )
        if match is not None:
            return match
        raise


def _result(
    recipe: SalvageRecipe,
    policy: dict[str, Any],
    policy_hash: str,
    asset: AssetRecord,
    artifact_id: str,
    artifact_location: str,
    verdict: ClipVerdict,
    checks: tuple[PreservationCheck, ...],
) -> SalvageResult:
    return SalvageResult(
        recipe=recipe,
        policy=policy,
        policy_hash=policy_hash,
        output_hash=asset.asset_id,
        lineage_artifact_id=artifact_id,
        lineage_artifact_location=artifact_location,
        asset=asset,
        verdict=verdict,
        preservation_checks=checks,
    )


def create_salvage_derivative(
    project: Project,
    *,
    source_asset_id: str,
    recipe: SalvageRecipe | str,
    policy: dict[str, Any],
    acceptance_spec_id: str,
    authorization_decision_ids: tuple[str, ...] = (),
) -> SalvageResult:
    """Render one immutable derivative and persist its exact lineage + review slot."""

    selected, validated, policy_hash = _validated_policy(recipe, policy)
    try:
        _SHA_ADAPTER.validate_python(acceptance_spec_id)
    except ValidationError as exc:
        raise _salvage_error("acceptance spec id is invalid", "invalid_salvage_policy") from exc
    source, source_path = _active_source(project, source_asset_id)
    prior = _read_prior_derivative(project, source.asset_id, validated, policy_hash)
    if prior is not None:
        asset, artifact_id, artifact_location, checks = prior
        verdict = _verdict(project, asset.asset_id, acceptance_spec_id)
        return _result(selected, validated, policy_hash, asset, artifact_id, artifact_location, verdict, checks)
    work_root = store.safe_target(project, layout.artifacts_dir())
    suffix = (
        ".png"
        if selected is SalvageRecipe.STILL_FRAME
        else ".mkv"
        if selected is SalvageRecipe.FREEZE_EXTENSION
        else ".mkv"
        if selected is SalvageRecipe.BACKGROUND_ONLY
        else ".mp4"
    )
    with store._mapped_os_errors(), tempfile.TemporaryDirectory(dir=work_root, prefix=".salvage-render.") as work:
        workspace = Path(work)
        expected = SourceIdentity(source.asset_id, source.byte_size)
        with _verified_source_snapshot(source_path, expected, workspace) as held:
            snapshot = Path(held.path)
            intent = _mutation_intent(
                selected,
                validated,
                source.asset_id,
                _salvage_audio_fingerprint(snapshot, pass_fds=held.pass_fds),
                authorization_decision_ids,
            )
            assert_no_protected_collision(project, intent)
            rendered = workspace / f"derivative{suffix}"
            _render(selected, validated, snapshot, rendered, pass_fds=held.pass_fds)
            checks = _checks_from_descriptor(selected, validated, held, rendered, source.asset_id)
        output_hash = _checked_hash(rendered, missing_message="salvage render is missing")
        manifest = {
            "schema_version": 1,
            "operation": selected.value,
            "policy": validated,
            "policy_hash": policy_hash,
            "source_asset_id": source.asset_id,
            "output_hash": output_hash,
            "preservation_checks": [item.model_dump(mode="json") for item in checks],
        }
        artifact_id, artifact_location = _install_manifest(project, manifest)
        lineage = GenerationLineage(
            generator_model="kinocut.salvage.v1",
            provider_id="local_ffmpeg",
            generation_settings_hash=policy_hash,
            source_asset_ids=(source.asset_id,),
        )
        asset = ingest_asset(
            project,
            rendered,
            lineage=lineage,
            usage_rights_status=source.usage_rights_status,
            usage_rights_evidence_ref=source.usage_rights_evidence_ref,
        )
    asset = _enrich_asset(project, asset, source, artifact_id)
    stored_output = store.safe_target(project, asset.original_location)
    if _checked_hash(stored_output, missing_message="published derivative is missing") != asset.asset_id:
        raise _salvage_error("derivative integrity check failed", "salvage_integrity_failed")
    verdict = _verdict(project, asset.asset_id, acceptance_spec_id)
    return _result(selected, validated, policy_hash, asset, artifact_id, artifact_location, verdict, checks)
