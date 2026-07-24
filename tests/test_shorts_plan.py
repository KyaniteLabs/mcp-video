from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

import kinocut.product.shorts_plan as plan_module
from kinocut.errors import MCPVideoError
from kinocut.product.models import CandidateMoment, TranscriptSegment, canonical_dedup_key
from kinocut.product.shorts_plan import IntakeReport, ReviewDecision, ShortsPlan, load_shorts_plan, save_shorts_plan


def _candidate() -> CandidateMoment:
    excerpt = "A complete candidate thought."
    return CandidateMoment(
        candidate_id="candidate_01",
        start=10.0,
        end=20.0,
        transcript_excerpt=excerpt,
        suggested_title="A useful clip",
        suggested_hook="Start here",
        rationale="Complete thought",
        confidence=0.9,
        dedup_key=canonical_dedup_key(start=10.0, end=20.0, excerpt=excerpt, sensitivity="none"),
    )


def _plan(output_dir: Path, **updates) -> ShortsPlan:
    values = {
        "job_id": "shorts_0123456789abcdef",
        "project_dir": str(output_dir.parent),
        "output_dir": str(output_dir),
        "intake": IntakeReport(
            source_path="/tmp/source.mp4",
            source_sha256="0" * 64,
            duration=60.0,
            width=1920,
            height=1080,
            audio_available=True,
        ),
        "platforms": ("youtube-shorts", "instagram-reel"),
        "config": {},
        "transcript": (TranscriptSegment(segment_id="segment_01", start=0.0, end=30.0, text="Transcript"),),
        "proposals": (_candidate(),),
    }
    values.update(updates)
    return ShortsPlan.model_validate(values)


def test_plan_save_load_is_source_free(tmp_path):
    plan = _plan(tmp_path / "plans")
    save_shorts_plan(plan)
    path = Path(plan.output_dir) / f"{plan.job_id}.plan.json"
    assert load_shorts_plan(str(path)) == plan


def test_plan_directory_lookup_requires_exactly_one_plan(tmp_path):
    first = _plan(tmp_path, job_id="shorts_0123456789abcdef")
    second = _plan(tmp_path, job_id="shorts_fedcba9876543210")
    save_shorts_plan(first)
    save_shorts_plan(second)
    with pytest.raises(MCPVideoError) as exc:
        load_shorts_plan(str(tmp_path))
    assert exc.value.code == "shorts_plan_ambiguous"


def test_plan_load_rejects_malformed_receipt(tmp_path):
    path = tmp_path / "shorts_0123456789abcdef.plan.json"
    path.write_text(json.dumps({"schema_version": 1}))
    with pytest.raises(MCPVideoError) as exc:
        load_shorts_plan(str(path))
    assert exc.value.code == "shorts_plan_malformed"


@pytest.mark.parametrize(
    "payload",
    (
        {"candidate_id": "candidate_01", "action": "trim", "start": 9.0, "end": 8.0},
        {"candidate_id": "candidate_01", "action": "approve", "title": "not allowed"},
        {"candidate_id": "candidate_01", "action": "title_hook_edit"},
        {"candidate_id": "candidate_01", "action": "sensitive_unsuitable", "sensitive": True, "start": 1.0},
    ),
)
def test_review_decision_rejects_action_shape_mismatches(payload):
    with pytest.raises(ValidationError):
        ReviewDecision.model_validate(payload)


def test_plan_save_rejects_intermediate_symlink(tmp_path):
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    linked_dir = tmp_path / "linked"
    linked_dir.symlink_to(real_dir)
    with pytest.raises(MCPVideoError) as exc:
        save_shorts_plan(_plan(linked_dir / "plans"))
    assert exc.value.code == "unsafe_path"


def test_plan_save_cleans_temp_file_after_serialization_failure(tmp_path, monkeypatch):
    plan = _plan(tmp_path / "plans")

    def fail_serialization(_plan):
        raise OSError("disk full")

    monkeypatch.setattr(plan_module, "_plan_to_json", fail_serialization)
    with pytest.raises(OSError, match="disk full"):
        save_shorts_plan(plan)
    assert list(Path(plan.output_dir).iterdir()) == []
