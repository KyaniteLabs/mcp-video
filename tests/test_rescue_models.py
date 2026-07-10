"""Contract tests for versioned rescue plans and receipts."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from mcp_video.rescue._errors import RESCUE_PLAN_MISMATCH, rescue_error
from mcp_video.rescue.models import (
    Disposition,
    Metric,
    PackageIntent,
    Repair,
    RescuePlan,
    canonical_payload,
)

_HASH_A = "sha256:" + "a" * 64


def _metric() -> Metric:
    return Metric(
        name="integrated_loudness",
        value=-27.0,
        unit="LUFS",
        definition="Integrated program loudness measured over the complete audio stream.",
    )


def _repair(disposition: Disposition = Disposition.SAFE_REPAIR) -> Repair:
    return Repair(
        id="audio_loudness:primary",
        type="audio_loudness",
        disposition=disposition,
        confidence=0.96,
        confidence_rationale="Integrated loudness was measured from the complete audio stream.",
        evidence=[_metric()],
        parameters={"target_lufs": -16.0, "lra": 11.0},
        expected_benefit="Make speech consistently audible.",
        tradeoffs=["Audio is re-encoded."],
        executor="ffmpeg.loudnorm",
        promotable=True,
    )


def _minimal_plan(repairs: list[Repair]) -> dict:
    return {
        "schema_version": 1,
        "receipt_kind": "rescue_plan",
        "tool": "video_rescue_plan",
        "status": "planned",
        "workspace_root": "..",
        "output_root": "rescue-output",
        "source": {
            "path": "incoming/clip.mov",
            "sha256": _HASH_A,
            "size_bytes": 1234,
            "streams": [],
        },
        "policy": {
            "id": "local_content_preserving",
            "version": 1,
            "local_only": True,
            "timeline_locked": True,
        },
        "findings": [],
        "safe_repairs": repairs,
        "recommendations": [],
        "unavailable_repairs": [],
        "blocked_repairs": [],
        "package_intents": [
            PackageIntent(kind="master", required=True, status="available"),
            PackageIntent(kind="sharing_copy", required=True, status="available"),
            PackageIntent(kind="receipt", required=True, status="available"),
        ],
        "preview_artifacts": [],
        "estimate": {"seconds": 3.2, "hardware": {}, "confidence": "low"},
        "capabilities": {"local_only": True},
        "versions": {"mcp_video": "1.6.0", "ffmpeg": "8.0"},
        "created_at": "2026-07-09T00:00:00Z",
        "observed_planning_seconds": 0.4,
        "plan_sha256": None,
    }


def test_metric_requires_an_explicit_unit():
    with pytest.raises(ValidationError):
        Metric(
            name="integrated_loudness",
            value=-27.0,
            unit="",
            definition="Integrated program loudness.",
        )


def test_metric_requires_an_explicit_definition():
    with pytest.raises(ValidationError):
        Metric(name="integrated_loudness", value=-27.0, unit="LUFS", definition="")


def test_plan_rejects_duplicate_repair_ids():
    repair = _repair()
    with pytest.raises(ValidationError, match="repair ids must be unique"):
        RescuePlan.model_validate(_minimal_plan([repair, repair]))


def test_plan_rejects_repair_in_wrong_disposition_bucket():
    plan = _minimal_plan([_repair(Disposition.RECOMMENDATION)])
    with pytest.raises(ValidationError, match="safe_repairs must contain only safe_repair"):
        RescuePlan.model_validate(plan)


def test_plan_rejects_absolute_workspace_reference():
    plan = _minimal_plan([])
    plan["workspace_root"] = "/private/workspace"
    with pytest.raises(ValidationError, match="must be relative"):
        RescuePlan.model_validate(plan)


def test_written_v1_contracts_reject_unknown_fields():
    plan = _minimal_plan([])
    plan["future_field"] = True
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        RescuePlan.model_validate(plan)


def test_canonical_payload_is_stable_and_excludes_volatile_fields():
    first = RescuePlan.model_validate(_minimal_plan([]))
    changed = _minimal_plan([])
    changed["created_at"] = "2026-07-10T00:00:00Z"
    changed["observed_planning_seconds"] = 99.0
    changed["plan_sha256"] = _HASH_A
    second = RescuePlan.model_validate(changed)

    assert canonical_payload(first) == canonical_payload(second)
    decoded = json.loads(canonical_payload(first))
    assert "created_at" not in decoded
    assert "observed_planning_seconds" not in decoded
    assert "plan_sha256" not in decoded


def test_rescue_error_exposes_stable_code():
    error = rescue_error("plan changed", RESCUE_PLAN_MISMATCH)
    assert error.code == "rescue_plan_mismatch"
    assert error.suggested_action["auto_fix"] is False
