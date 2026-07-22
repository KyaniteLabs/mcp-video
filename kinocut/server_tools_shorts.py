"""MCP adapters for the human-gated long-form stream-to-shorts product surface.

Five thin tools — every ``shorts_*`` handler here is a pass-through to the
public callables in :mod:`kinocut.product.shorts`. Business logic (intake,
transcription, discovery, review ledger, render planning, package) lives
exclusively in that module; these handlers exist only to expose the surface
through FastMCP and to convert exceptions into structured error results via
``_safe_tool``. Status is read through the existing ``get_render_job`` tool;
this module deliberately registers no ``shorts_status`` tool.
"""

from __future__ import annotations

from typing import Any

from .server_app import _safe_tool, mcp


def _run(operation: str, **kwargs: Any) -> dict[str, Any]:
    """Dispatch to ``kinocut.product.shorts`` — single source of truth."""
    from .product import shorts

    return getattr(shorts, operation)(**kwargs)


@mcp.tool()
@_safe_tool
def shorts_plan(
    project_dir: str,
    source_path: str,
    platforms: list[str] | None = None,
    *,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Intake a long-form source and produce a strict proposal-only plan.

    Defaults stop after proposals — no render, no re-transcription. The
    returned payload is JSON-serialisable and decoupled from any engine
    state. Status, when relevant, is read through ``get_render_job`` — this
    tool deliberately registers no shorts-specific status handler.
    """
    return _run(
        "shorts_plan",
        project_dir=project_dir,
        source_path=source_path,
        platforms=platforms,
        config=config,
    )


@mcp.tool()
@_safe_tool
def shorts_propose(
    project_dir: str,
    candidate_id: str,
    plan: dict[str, Any],
    edits: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append one review decision (preview/approve/reject/trim/title-hook/sensitive).

    Decisions are append-only; the orchestrator returns the updated plan and a
    fresh revision pointer. No render is triggered from this verb.
    """
    return _run(
        "shorts_propose",
        project_dir=project_dir,
        candidate_id=candidate_id,
        plan=plan,
        edits=edits,
    )


@mcp.tool()
@_safe_tool
def shorts_review(
    project_dir: str,
    candidate_id: str,
    decision: dict[str, Any],
    evidence_ref: str,
) -> dict[str, Any]:
    """Record a narrow review decision with an explicit evidence reference.

    Delegates to the same append-only review ledger as ``shorts_propose``;
    kept as a separate verb so calling agents can target review without
    re-asserting the full plan payload.
    """
    return _run(
        "shorts_review",
        project_dir=project_dir,
        candidate_id=candidate_id,
        decision=decision,
        evidence_ref=evidence_ref,
    )


@mcp.tool()
@_safe_tool
def shorts_render(
    project_dir: str,
    candidate_id: str,
    output_path: str,
    *,
    render_options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Render an approved clip; only approved candidates are eligible.

    Re-render of an edited clip does not retranscribe. Progress is read
    through ``get_render_job``; this tool intentionally exposes no
    shorts-specific status handler.
    """
    return _run(
        "shorts_render",
        project_dir=project_dir,
        candidate_id=candidate_id,
        output_path=output_path,
        render_options=render_options,
    )


@mcp.tool()
@_safe_tool
def shorts_package(
    project_dir: str,
    candidate_id: str,
    package_dir: str,
) -> dict[str, Any]:
    """Materialise the per-clip package (video + subtitles + thumbnail + manifest).

    Hands off to ``kinocut.product.package.package_approved_clip``. Never
    posts publicly; status read remains on ``get_render_job``.
    """
    return _run(
        "shorts_package",
        project_dir=project_dir,
        candidate_id=candidate_id,
        package_dir=package_dir,
    )
