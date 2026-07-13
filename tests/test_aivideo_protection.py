"""Protected-element mutation precheck."""

from __future__ import annotations

import pytest

from kinocut.aivideo.protection import (
    MutationIntent,
    assert_no_protected_collision,
    mutation_fingerprint,
    protect,
    touched_dependencies,
)
from kinocut.contracts.protection import ElementType, ProtectedElement
from kinocut.contracts.review import ReviewDecision
from kinocut.engine_body_swap import _body_swap_parameters_fingerprint
from kinocut.errors import MCPVideoError
from kinocut.projectstore import append_record, open_project
from tests.contracts_fixtures import protection_kwargs, review_decision_kwargs


@pytest.fixture
def project(tmp_path):
    return open_project(tmp_path / "project")


def _element(project, **overrides) -> ProtectedElement:
    return ProtectedElement(**protection_kwargs(project_id=project.project_id, **overrides))


def _mutation_touching(lock: ProtectedElement, **overrides) -> MutationIntent:
    values = {
        "operation": "body_swap",
        "source_asset": "sha256:" + "b" * 64,
        "audio_stream": lock.dependency_fingerprint,
        "operation_parameters": _body_swap_parameters_fingerprint(None),
    }
    values.update(overrides)
    return MutationIntent(**values)


def _protected_with_original(project, *, original_created_by="human"):
    fingerprint = "sha256:" + "a" * 64
    original = append_record(
        project,
        ReviewDecision(
            **review_decision_kwargs(
                project_id=project.project_id,
                created_by=original_created_by,
                target_ref=fingerprint,
                dependency_fingerprint=fingerprint,
            )
        ),
    )
    lock = protect(project, _element(project, human_approval_ref=original.record_id))
    return lock, original


def test_protected_collision_fails_without_new_human_decision(project):
    lock = protect(project, _element(project))
    op = _mutation_touching(lock)
    with pytest.raises(MCPVideoError) as excinfo:
        assert_no_protected_collision(project, op)
    assert excinfo.value.code == "protected_element_change"


def test_explicitly_allowed_operation_does_not_collide(project):
    lock = protect(project, _element(project, allowed_operations=("body_swap",)))
    assert_no_protected_collision(project, _mutation_touching(lock))


def test_new_stored_human_decision_authorizes_collision(project):
    lock, original = _protected_with_original(project)
    op = _mutation_touching(lock)
    intent_fingerprint = mutation_fingerprint(op)
    decision = append_record(
        project,
        ReviewDecision(
            **review_decision_kwargs(
                project_id=project.project_id,
                target_ref=intent_fingerprint,
                dependency_fingerprint=intent_fingerprint,
                source_record_ids=(lock.record_id, original.record_id),
            )
        ),
    )
    op = op.model_copy(update={"authorization_decision_ids": (decision.record_id,)})
    assert_no_protected_collision(project, op)


def test_authorization_for_one_mutation_policy_cannot_be_replayed(project):
    lock, original = _protected_with_original(project)
    authorized = _mutation_touching(lock)
    intent_fingerprint = mutation_fingerprint(authorized)
    decision = append_record(
        project,
        ReviewDecision(
            **review_decision_kwargs(
                project_id=project.project_id,
                target_ref=intent_fingerprint,
                dependency_fingerprint=intent_fingerprint,
                source_record_ids=(lock.record_id, original.record_id),
            )
        ),
    )
    replay = MutationIntent(
        operation="body_swap",
        source_asset="sha256:" + "c" * 64,
        audio_stream=lock.dependency_fingerprint,
        operation_parameters=_body_swap_parameters_fingerprint(None),
        authorization_decision_ids=(decision.record_id,),
    )

    with pytest.raises(MCPVideoError) as excinfo:
        assert_no_protected_collision(project, replay)

    assert excinfo.value.code == "protected_element_change"


def test_mutation_intent_has_no_force_path():
    assert "force" not in MutationIntent.model_fields


def test_touched_dependencies_is_a_deduplicated_set():
    source = "sha256:" + "b" * 64
    audio = "sha256:" + "a" * 64
    op = MutationIntent(
        operation="body_swap",
        source_asset=source,
        audio_stream=audio,
        operation_parameters=_body_swap_parameters_fingerprint(None),
    )
    assert touched_dependencies(op) == {
        (ElementType.SOURCE_ASSET, source),
        (ElementType.AUDIO_STREAM, audio),
    }


def test_omitted_footprint_cannot_bypass_known_collision(project):
    protect(project, _element(project))
    with pytest.raises(MCPVideoError) as excinfo:
        assert_no_protected_collision(
            project,
            {"operation": "body_swap", "source_asset": "sha256:" + "b" * 64},
        )
    assert excinfo.value.code == "invalid_mutation_intent"


def test_empty_footprint_cannot_bypass_known_collision(project):
    protect(project, _element(project))
    with pytest.raises(MCPVideoError) as excinfo:
        assert_no_protected_collision(
            project,
            {"operation": "body_swap", "source_asset": "", "audio_stream": ""},
        )
    assert excinfo.value.code == "invalid_mutation_intent"


def test_arbitrary_footprint_and_unknown_operation_fail_closed(project):
    protect(project, _element(project))
    arbitrary = {
        "operation": "body_swap",
        "dependency_fingerprints": ("sha256:" + "b" * 64,),
    }
    with pytest.raises(MCPVideoError) as excinfo:
        assert_no_protected_collision(project, arbitrary)
    assert excinfo.value.code == "invalid_mutation_intent"
    with pytest.raises(MCPVideoError) as excinfo:
        assert_no_protected_collision(
            project,
            {"operation": "custom", "source_asset": "sha256:" + "b" * 64},
        )
    assert excinfo.value.code == "invalid_mutation_intent"


def test_different_exact_target_does_not_collide(project):
    protect(project, _element(project))
    operation = MutationIntent(
        operation="body_swap",
        source_asset="sha256:" + "b" * 64,
        audio_stream="sha256:" + "c" * 64,
        operation_parameters=_body_swap_parameters_fingerprint(None),
    )
    assert_no_protected_collision(project, operation)


def test_agent_authored_original_approval_cannot_authorize_change(project):
    lock, original = _protected_with_original(project, original_created_by="agent")
    decision = append_record(
        project,
        ReviewDecision(
            **review_decision_kwargs(
                project_id=project.project_id,
                target_ref=lock.dependency_fingerprint,
                dependency_fingerprint=lock.dependency_fingerprint,
                source_record_ids=(lock.record_id, original.record_id),
            )
        ),
    )
    with pytest.raises(MCPVideoError) as excinfo:
        assert_no_protected_collision(
            project,
            _mutation_touching(lock, authorization_decision_ids=(decision.record_id,)),
        )
    assert excinfo.value.code == "protected_element_change"


def test_agent_authored_new_approval_cannot_authorize_change(project):
    lock, original = _protected_with_original(project)
    decision = append_record(
        project,
        ReviewDecision(
            **review_decision_kwargs(
                project_id=project.project_id,
                created_by="agent",
                target_ref=lock.dependency_fingerprint,
                dependency_fingerprint=lock.dependency_fingerprint,
                source_record_ids=(lock.record_id, original.record_id),
            )
        ),
    )
    with pytest.raises(MCPVideoError) as excinfo:
        assert_no_protected_collision(
            project,
            _mutation_touching(lock, authorization_decision_ids=(decision.record_id,)),
        )
    assert excinfo.value.code == "protected_element_change"


def test_unrelated_preexisting_approval_cannot_authorize_change(project):
    lock, _original = _protected_with_original(project)
    unrelated = append_record(
        project,
        ReviewDecision(
            **review_decision_kwargs(
                project_id=project.project_id,
                target_ref=lock.dependency_fingerprint,
                dependency_fingerprint=lock.dependency_fingerprint,
                rationale="unrelated earlier approval",
            )
        ),
    )
    with pytest.raises(MCPVideoError) as excinfo:
        assert_no_protected_collision(
            project,
            _mutation_touching(lock, authorization_decision_ids=(unrelated.record_id,)),
        )
    assert excinfo.value.code == "protected_element_change"


def test_two_protected_dependencies_of_same_kind_are_exact_target_scoped(project):
    first = protect(
        project,
        _element(project, allowed_operations=("body_swap",)),
    )
    protect(
        project,
        _element(project, dependency_fingerprint="sha256:" + "c" * 64),
    )
    assert_no_protected_collision(project, _mutation_touching(first))


_ELEMENT_OPERATION_CASES = (
    (ElementType.SOURCE_ASSET, "replace_source", "source_asset"),
    (ElementType.AUDIO_STREAM, "normalize_audio", "audio_stream"),
    (ElementType.CLIP_RANGE, "trim_clip", "clip_range"),
    (ElementType.TIMELINE_RANGE, "edit_timeline", "timeline_range"),
    (ElementType.GRAPHIC, "edit_graphic", "graphic"),
    (ElementType.SUBTITLE_SET, "edit_subtitles", "subtitle_set"),
    (ElementType.TIMING_MAP, "retime", "timing_map"),
    (ElementType.MIX, "remix", "mix"),
    (
        ElementType.RENDER_PARAMETER_SET,
        "change_render_parameters",
        "render_parameter_set",
    ),
)


@pytest.mark.parametrize(("element_type", "operation", "field"), _ELEMENT_OPERATION_CASES)
def test_every_element_kind_participates_in_exact_footprint(
    project,
    element_type,
    operation,
    field,
):
    lock = protect(project, _element(project, element_type=element_type))
    with pytest.raises(MCPVideoError) as excinfo:
        assert_no_protected_collision(
            project,
            {"operation": operation, field: lock.dependency_fingerprint},
        )
    assert excinfo.value.code == "protected_element_change"


def test_unrelated_element_kind_does_not_collide(project):
    protect(project, _element(project, element_type="graphic"))
    assert_no_protected_collision(
        project,
        {
            "operation": "normalize_audio",
            "audio_stream": "sha256:" + "a" * 64,
        },
    )


def test_operation_that_cannot_derive_complete_footprint_fails_closed(project):
    protect(project, _element(project))
    with pytest.raises(MCPVideoError) as excinfo:
        assert_no_protected_collision(
            project,
            {
                "operation": "body_swap",
                "source_asset": "sha256:" + "b" * 64,
                "graphic": "sha256:" + "c" * 64,
            },
        )
    assert excinfo.value.code == "invalid_mutation_intent"


# ---------------------------------------------------------------------------
# Shared active-human-approval resolver: one predicate consumed by both the
# protected-collision gate and the salvage-lineage replay verifier.
# ---------------------------------------------------------------------------

_FINGERPRINT = "sha256:" + "a" * 64


def _stored_approval(project, **overrides):
    from kinocut.projectstore import append_record
    from tests.contracts_fixtures import review_decision_kwargs

    values = {
        "project_id": project.project_id,
        "target_ref": _FINGERPRINT,
        "dependency_fingerprint": _FINGERPRINT,
    }
    values.update(overrides)
    return append_record(project, ReviewDecision(**review_decision_kwargs(**values)))


def test_resolver_accepts_valid_active_human_approval(project):
    from kinocut.aivideo.protection import active_human_approval_bound_to, decision_history

    decision = _stored_approval(project)
    decisions, active_ids = decision_history(project)
    result = active_human_approval_bound_to(
        decisions.get(decision.record_id), decision.record_id, active_ids, _FINGERPRINT
    )
    assert result is not None
    assert result.record_id == decision.record_id


def test_resolver_rejects_hostile_target_ref_mismatch(project):
    from kinocut.aivideo.protection import active_human_approval_bound_to, decision_history

    decision = _stored_approval(project, target_ref="sha256:" + "b" * 64)
    decisions, active_ids = decision_history(project)
    result = active_human_approval_bound_to(
        decisions.get(decision.record_id), decision.record_id, active_ids, _FINGERPRINT
    )
    assert result is None


def test_resolver_rejects_superseded_stale_decision(project):
    from kinocut.aivideo.protection import active_human_approval_bound_to, decision_history

    original = _stored_approval(project)
    _stored_approval(project, supersedes=original.record_id)
    decisions, active_ids = decision_history(project)
    result = active_human_approval_bound_to(
        decisions.get(original.record_id), original.record_id, active_ids, _FINGERPRINT
    )
    assert result is None


def test_resolver_rejects_subclass_lookalike(project):
    from kinocut.aivideo.protection import active_human_approval_bound_to

    class Lookalike(ReviewDecision):
        pass

    lookalike = Lookalike(
        **review_decision_kwargs(
            project_id=project.project_id,
            target_ref=_FINGERPRINT,
            dependency_fingerprint=_FINGERPRINT,
        )
    )
    result = active_human_approval_bound_to(lookalike, "fake-id", {"fake-id"}, _FINGERPRINT)
    assert result is None


def test_resolver_rejects_agent_authored_decision(project):
    from kinocut.aivideo.protection import active_human_approval_bound_to, decision_history

    decision = _stored_approval(project, created_by="agent")
    decisions, active_ids = decision_history(project)
    result = active_human_approval_bound_to(
        decisions.get(decision.record_id), decision.record_id, active_ids, _FINGERPRINT
    )
    assert result is None


def test_resolver_rejects_reject_decision(project):
    from kinocut.aivideo.protection import active_human_approval_bound_to, decision_history

    decision = _stored_approval(project, decision="reject")
    decisions, active_ids = decision_history(project)
    result = active_human_approval_bound_to(
        decisions.get(decision.record_id), decision.record_id, active_ids, _FINGERPRINT
    )
    assert result is None
