"""Python client adapters for the human-gated long-form shorts product surface.

Five thin methods that mirror the MCP ``shorts_*`` tools exactly — every call
is a kwargs pass-through to :mod:`kinocut.product.shorts`. No business logic
lives here. Status reads stay on the existing ``get_render_job`` tool; this
mixin deliberately registers no ``Kinocut.shorts.status`` method.
"""

from __future__ import annotations

from typing import Any


def _run(operation: str, **kwargs: Any) -> dict[str, Any]:
    """Dispatch to ``kinocut.product.shorts`` — single source of truth."""
    from ..product import shorts

    return getattr(shorts, operation)(**kwargs)


class ClientShortsMixin:
    """Human-gated long-form stream-to-shorts product operations.

    Thin adapters — all kwargs pass through to ``kinocut.product.shorts``,
    which owns intake, transcription, discovery, the review ledger, render
    planning, and packaging. The default path stops after proposals; no
    render runs without an explicit approved decision. Status is read
    through ``get_render_job``.
    """

    def shorts_plan(
        self,
        project_dir: str,
        source_path: str,
        platforms: list[str] | None = None,
        *,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Intake a long-form source and produce a strict proposal-only plan."""
        return _run(
            "shorts_plan",
            project_dir=project_dir,
            source_path=source_path,
            platforms=platforms,
            config=config,
        )

    def shorts_propose(
        self,
        project_dir: str,
        candidate_id: str,
        plan: dict[str, Any],
        edits: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Append one review decision to the canonical review ledger."""
        return _run(
            "shorts_propose",
            project_dir=project_dir,
            candidate_id=candidate_id,
            plan=plan,
            edits=edits,
        )

    def shorts_review(
        self,
        project_dir: str,
        candidate_id: str,
        decision: dict[str, Any],
        evidence_ref: str,
    ) -> dict[str, Any]:
        """Record one review decision with an explicit evidence reference."""
        return _run(
            "shorts_review",
            project_dir=project_dir,
            candidate_id=candidate_id,
            decision=decision,
            evidence_ref=evidence_ref,
        )

    def shorts_render(
        self,
        project_dir: str,
        candidate_id: str,
        output_path: str,
        *,
        render_options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Render an approved clip (no retranscription on re-render)."""
        return _run(
            "shorts_render",
            project_dir=project_dir,
            candidate_id=candidate_id,
            output_path=output_path,
            render_options=render_options,
        )

    def shorts_package(
        self,
        project_dir: str,
        candidate_id: str,
        package_dir: str,
    ) -> dict[str, Any]:
        """Materialise the per-clip package (video + subtitles + thumbnail + manifest)."""
        return _run(
            "shorts_package",
            project_dir=project_dir,
            candidate_id=candidate_id,
            package_dir=package_dir,
        )
