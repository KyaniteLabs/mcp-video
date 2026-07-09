"""mcp-video Python client — agent workflow-engine methods."""

from __future__ import annotations

from typing import Any


class ClientWorkflowMixin:
    """Agent workflow-engine operations mixin."""

    def workflow_validate(self, spec: str | dict) -> dict[str, Any]:
        """Validate a workflow job-spec without rendering any media.

        Args:
            spec: Path to a workflow job-spec JSON file, or the spec as a dict.

        Returns:
            A structured validation verdict (``{"valid": True, ...}``).

        Raises:
            MCPVideoError: on any structural violation (fail-closed).
        """
        from ..workflow import validate_workflow_spec

        if isinstance(spec, dict):
            import json
            import os
            import tempfile

            with tempfile.TemporaryDirectory(prefix="mcp_video_workflow_") as tmpdir:
                spec_path = os.path.join(tmpdir, "workflow.json")
                with open(spec_path, "w", encoding="utf-8") as handle:
                    json.dump(spec, handle)
                return validate_workflow_spec(spec_path)
        return validate_workflow_spec(spec)

    def workflow_plan(
        self, spec: str | dict, save_plan: str | None = None, variant: str | None = None
    ) -> dict[str, Any]:
        """Produce a no-render plan artifact for a workflow job-spec.

        Validates the spec first (fail-closed) and returns the dry-run plan:
        ordered op graph, per-source probe results + hashes where the file
        exists, output intents, variant summary, versions, and warnings. No
        media is rendered; only the optional ``save_plan`` JSON is written.

        Pass ``variant`` to plan a single declared batch variant: the plan shows
        that variant's effective (post-override) steps and auto-named outputs and
        records ``workflow.variant``.

        Args:
            spec: Path to a workflow job-spec JSON file, or the spec as a dict.
            save_plan: Optional path to write the plan artifact as JSON.
            variant: Optional declared variant id to plan its effective steps.

        Returns:
            The plan artifact (``{"receipt_kind": "workflow_plan", ...}``).

        Raises:
            MCPVideoError: on any structural violation (fail-closed).
        """
        from ..workflow import plan_workflow

        if isinstance(spec, dict):
            import json
            import os
            import tempfile

            with tempfile.TemporaryDirectory(prefix="mcp_video_workflow_") as tmpdir:
                spec_path = os.path.join(tmpdir, "workflow.json")
                with open(spec_path, "w", encoding="utf-8") as handle:
                    json.dump(spec, handle)
                return plan_workflow(spec_path, save_plan, variant)
        return plan_workflow(spec, save_plan, variant)

    def workflow_render(
        self,
        spec: str | dict,
        resume_receipt: str | None = None,
        save_receipt: str | None = None,
        keep_intermediates: bool = False,
        variant: str | None = None,
        all_variants: bool = False,
        save_receipt_dir: str | None = None,
    ) -> dict[str, Any]:
        """Execute a workflow job-spec sequentially and return the receipt.

        Validates the spec first (fail-closed), runs each allowlisted op in spec
        order via the backing engine, hashing every consumed input and produced
        output, and returns a workflow receipt (``receipt_kind: "workflow"``).
        Intermediates are written to a per-run ``@work`` directory (cleaned on
        success unless ``keep_intermediates``, kept on failure). Only the optional
        ``save_receipt`` JSON is written outside the workspace's declared paths.

        Batch variants: ``variant=<id>`` renders one declared variant (overrides
        applied, output auto-named with the variant id, ``workflow.variant``
        recorded); ``all_variants=True`` renders every declared variant and returns
        a ``workflow_batch`` summary, optionally writing each receipt into
        ``save_receipt_dir``. ``variant`` and ``all_variants`` are mutually exclusive.

        Pass ``resume_receipt`` (a prior render receipt from a failed job whose
        intermediates were kept) to RESUME: the current spec_hash must equal the
        receipt's and, for a variant, the receipt's variant must match (else
        fail-closed); completed steps whose recorded input/output hashes still match
        are skipped, and the first step failing any check plus everything after it
        re-runs.

        Args:
            spec: Path to a workflow job-spec JSON file, or the spec as a dict.
            resume_receipt: Optional path to a prior render receipt to resume from.
            save_receipt: Optional path to write the workflow receipt as JSON.
            keep_intermediates: Retain @work intermediates even on success.
            variant: Optional declared variant id to render a single variant.
            all_variants: Render every declared variant and return a batch summary.
            save_receipt_dir: With all_variants, directory for per-variant receipts.

        Returns:
            The workflow receipt (``{"receipt_kind": "workflow", ...}``), or a batch
            summary (``{"receipt_kind": "workflow_batch", ...}``) for all_variants.

        Raises:
            MCPVideoError: on any structural violation or failing step (fail-closed).
        """
        from ..workflow import render_workflow

        if isinstance(spec, dict):
            import json
            import os
            import tempfile

            with tempfile.TemporaryDirectory(prefix="mcp_video_workflow_") as tmpdir:
                spec_path = os.path.join(tmpdir, "workflow.json")
                with open(spec_path, "w", encoding="utf-8") as handle:
                    json.dump(spec, handle)
                return render_workflow(
                    spec_path,
                    resume_receipt,
                    save_receipt,
                    keep_intermediates,
                    variant,
                    all_variants,
                    save_receipt_dir,
                )
        return render_workflow(
            spec,
            resume_receipt,
            save_receipt,
            keep_intermediates,
            variant,
            all_variants,
            save_receipt_dir,
        )

    def workflow_inspect(self, receipt: str) -> dict[str, Any]:
        """Summarize any project receipt with a read-only integrity check.

        Reads a workflow render receipt, a dry-run ``workflow_plan`` artifact, or a
        ``layer_plan`` receipt (legacy v1 without ``receipt_kind`` or v2) and
        returns a normalized inspection: kind (inferred from the ``tool`` field
        when ``receipt_kind`` is absent), schema_version, tool, versions, a status
        summary, a hash presence/integrity report (which recorded hashes still
        match on-disk files now), outputs, warnings, cleanup state, plus
        human-review pointers and known limitations. Nothing is rendered.

        Args:
            receipt: Path to the receipt JSON file to inspect.

        Returns:
            The normalized inspection dict.

        Raises:
            MCPVideoError: on a malformed/unreadable receipt (``invalid_workflow_receipt``).
        """
        from ..workflow import inspect_receipt

        return inspect_receipt(receipt)
