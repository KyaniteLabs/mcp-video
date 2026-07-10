from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from mcp_video.remote import (
    AdapterMapping,
    ApprovedLocalPlan,
    DeletionRecord,
    DownloadedArtifact,
    FakeDeliveryAdapter,
    FakeHostingAdapter,
    FakeRenderAdapter,
    LocalArtifactVerification,
    Money,
    NetworkApproval,
    RemoteExecutionSelection,
    RemoteJobReceipt,
    approve_egress,
    create_fake_remote_receipt,
    map_fake_remote_job,
    plan_delivery,
    plan_egress,
    plan_hosting,
    prepare_remote_job,
    promote_downloaded_artifact,
    select_execution,
    verify_local_promotion,
)


HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64
HASH_C = "sha256:" + "c" * 64
FIXED_TIME = datetime(2026, 7, 9, 20, 0, tzinfo=UTC)


def _egress_documents(*, provider: str = "fake-render") -> tuple[dict, dict]:
    manifest = plan_egress(
        files=[
            {
                "path": "plans/approved.json",
                "sha256": HASH_A,
                "size_bytes": 20,
                "media_type": "application/json",
                "metadata": {},
            }
        ],
        metadata={"purpose": "explicit remote operation"},
        provider=provider,
        region_known=True,
        region="us-west-2",
        retention={"mode": "delete_after_download", "maximum_days": 1},
        estimated_cost={"amount": "1.25", "currency": "USD"},
    )
    approval = approve_egress(
        manifest,
        approved_by="operator",
        approved_at="2026-07-09T20:00:00Z",
    )
    return manifest, approval


def _local_plan() -> ApprovedLocalPlan:
    return ApprovedLocalPlan.create(
        plan={
            "schema_version": 1,
            "steps": [{"id": "render", "op": "approved_composite", "duration": 12.0}],
        },
        creative_intent_sha256=HASH_B,
        creative_approval_sha256=HASH_C,
    )


def _selection(*, provider: str = "fake-render", kind: str = "render") -> RemoteExecutionSelection:
    return RemoteExecutionSelection.create(
        provider=provider,
        kind=kind,
        selected_by="operator",
        selected_at=FIXED_TIME,
    )


def test_fake_render_mapping_preserves_the_approved_plan_and_creative_intent() -> None:
    manifest_json, approval_json = _egress_documents()
    local_plan = _local_plan()
    job = prepare_remote_job(
        adapter=FakeRenderAdapter(provider="fake-render"),
        local_plan=local_plan,
        manifest=manifest_json,
        network_approval=NetworkApproval.model_validate(approval_json),
        selection=_selection(),
    )

    assert job.kind == "render"
    assert job.local_plan_sha256 == local_plan.plan_sha256
    assert job.creative_intent_sha256 == local_plan.creative_intent_sha256
    assert job.creative_approval_sha256 == local_plan.creative_approval_sha256
    assert job.mapping.approved_plan == local_plan.plan
    assert job.egress_manifest_sha256 == manifest_json["manifest_sha256"]


def test_adapter_cannot_change_the_approved_plan_or_creative_intent() -> None:
    class IntentMutatingAdapter:
        provider = "fake-render"
        adapter_version = "malicious-v1"
        kind = "render"

        def map_approved_plan(self, local_plan, manifest):
            return AdapterMapping(
                approved_plan={"steps": [{"op": "different_edit"}]},
                parameters={"creative_intent_sha256": HASH_A},
            )

    manifest, approval = _egress_documents()
    with pytest.raises(ValueError, match="creative intent"):
        prepare_remote_job(
            adapter=IntentMutatingAdapter(),
            local_plan=_local_plan(),
            manifest=manifest,
            network_approval=NetworkApproval.model_validate(approval),
            selection=_selection(),
        )


def test_delivery_and_hosting_are_explicit_distinct_adapter_contracts() -> None:
    local_plan = _local_plan()
    delivery_manifest, delivery_approval = _egress_documents(provider="fake-delivery")
    hosting_manifest, hosting_approval = _egress_documents(provider="fake-hosting")

    delivery = prepare_remote_job(
        adapter=FakeDeliveryAdapter(provider="fake-delivery", destination="review/team-7"),
        local_plan=local_plan,
        manifest=delivery_manifest,
        network_approval=NetworkApproval.model_validate(delivery_approval),
        selection=_selection(provider="fake-delivery", kind="delivery"),
    )
    hosting = prepare_remote_job(
        adapter=FakeHostingAdapter(provider="fake-hosting", destination="sites/project-7"),
        local_plan=local_plan,
        manifest=hosting_manifest,
        network_approval=NetworkApproval.model_validate(hosting_approval),
        selection=_selection(provider="fake-hosting", kind="hosting"),
    )

    assert delivery.kind == "delivery"
    assert delivery.mapping.parameters["destination"] == "review/team-7"
    assert hosting.kind == "hosting"
    assert hosting.mapping.parameters["destination"] == "sites/project-7"


def test_cloud_is_never_selected_as_fallback_for_a_missing_local_executor() -> None:
    with pytest.raises(ValueError, match="cloud fallback is disabled"):
        select_execution(local_executor=None, explicit_remote_selection=None)

    local = select_execution(local_executor="ffmpeg-local", explicit_remote_selection=None)
    remote = select_execution(local_executor=None, explicit_remote_selection=_selection())

    assert local == {"mode": "local", "executor": "ffmpeg-local"}
    assert remote["mode"] == "remote"
    assert remote["selection_sha256"].startswith("sha256:")


def test_remote_receipt_records_provider_cost_retries_downloads_and_deletion() -> None:
    manifest, approval = _egress_documents()
    job = prepare_remote_job(
        adapter=FakeRenderAdapter(provider="fake-render"),
        local_plan=_local_plan(),
        manifest=manifest,
        network_approval=NetworkApproval.model_validate(approval),
        selection=_selection(),
    )
    download = DownloadedArtifact(
        provider_artifact_id="artifact-1",
        path="downloads/final.mp4",
        sha256=HASH_A,
        size_bytes=123,
        media_type="video/mp4",
    )
    receipt = RemoteJobReceipt.create(
        job=job,
        provider_job_id="job-123",
        provider_job_version="provider-api-2026-07",
        status="completed",
        actual_cost=Money(amount=Decimal("1.10"), currency="USD"),
        retries=2,
        downloads=(download,),
        deletion=DeletionRecord(status="confirmed", confirmation_id="deleted-123"),
        provider_metadata={"api_key": "sk-" + "x" * 32, "queue": "standard"},
    )

    assert receipt.provider == "fake-render"
    assert receipt.provider_job_id == "job-123"
    assert receipt.provider_job_version == "provider-api-2026-07"
    assert receipt.adapter_version == "fake-v1"
    assert receipt.actual_cost.amount == Decimal("1.10")
    assert receipt.retries == 2
    assert receipt.downloads[0].sha256 == HASH_A
    assert receipt.deletion.status == "confirmed"
    assert "sk-" not in receipt.model_dump_json()


def test_download_promotion_requires_passing_hash_bound_local_verification() -> None:
    download = DownloadedArtifact(
        provider_artifact_id="artifact-1",
        path="downloads/final.mp4",
        sha256=HASH_A,
        size_bytes=123,
        media_type="video/mp4",
    )
    failed = LocalArtifactVerification.create(
        download=download,
        verifier_id="local.package_verifier",
        verifier_version="1",
        passed=False,
        checks=("decode", "persisted_hash"),
        verified_at=FIXED_TIME,
    )
    wrong_hash = failed.model_copy(update={"artifact_sha256": HASH_B, "passed": True})
    passed = LocalArtifactVerification.create(
        download=download,
        verifier_id="local.package_verifier",
        verifier_version="1",
        passed=True,
        checks=("decode", "persisted_hash"),
        verified_at=FIXED_TIME,
    )

    with pytest.raises(ValueError, match="did not pass"):
        promote_downloaded_artifact(download, failed, destination="packages/final.mp4")
    with pytest.raises(ValueError, match="hash does not match"):
        promote_downloaded_artifact(download, wrong_hash, destination="packages/final.mp4")

    promotion = promote_downloaded_artifact(download, passed, destination="packages/final.mp4")
    assert promotion.source_sha256 == HASH_A
    assert promotion.destination == "packages/final.mp4"
    assert promotion.local_verification_sha256 == passed.verification_sha256


def test_public_facade_maps_jobs_receipts_delivery_and_verified_promotion_from_json() -> None:
    plan = _local_plan().model_dump(mode="json")
    manifest, approval = _egress_documents()
    job = map_fake_remote_job(
        plan,
        manifest,
        approval,
        adapter_kind="render",
        selected_by="operator",
        selected_at="2026-07-09T20:00:00Z",
    )
    receipt = create_fake_remote_receipt(
        job,
        provider_job_version="fake-api-v1",
        actual_cost={"amount": "1.10", "currency": "USD"},
        retries=0,
        downloads=[
            {
                "provider_artifact_id": "artifact-1",
                "path": "downloads/final.mp4",
                "sha256": HASH_A,
                "size_bytes": 123,
                "media_type": "video/mp4",
            }
        ],
        deletion={"status": "confirmed", "confirmation_id": "deleted-1"},
    )
    verification = LocalArtifactVerification.create(
        download=DownloadedArtifact.model_validate(receipt["downloads"][0]),
        verifier_id="local.package_verifier",
        verifier_version="1",
        passed=True,
        checks=("decode", "persisted_hash"),
        verified_at=FIXED_TIME,
    ).model_dump(mode="json")
    promotion = verify_local_promotion(
        receipt["downloads"][0],
        verification,
        destination="packages/final.mp4",
    )

    delivery_manifest, delivery_approval = _egress_documents(provider="fake-delivery")
    delivery = plan_delivery(
        plan,
        delivery_manifest,
        delivery_approval,
        destination="review/team-7",
        selected_by="operator",
        selected_at="2026-07-09T20:00:00Z",
    )
    hosting_manifest, hosting_approval = _egress_documents(provider="fake-hosting")
    hosting = plan_hosting(
        plan,
        hosting_manifest,
        hosting_approval,
        destination="sites/project-7",
        selected_by="operator",
        selected_at="2026-07-09T20:00:00Z",
    )

    assert job["creative_intent_sha256"] == HASH_B
    assert receipt["provider_job_id"].startswith("fake-job-")
    assert promotion["destination"] == "packages/final.mp4"
    assert delivery["kind"] == "delivery"
    assert hosting["kind"] == "hosting"
