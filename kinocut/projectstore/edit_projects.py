"""Phase-1 durable edit-project repository (internal, additive). A revision append writes three JSONL
files (revision, event, head) with exception-atomic rollback only: targets are snapshotted and fully restored
when an append raises. It is not cross-file crash-atomic — a process crash can leave unreferenced pre-head
revision/event records persisted before the head advanced, while the superseding head remains the source of truth."""

from __future__ import annotations

import contextlib
import re
import secrets
from datetime import UTC, datetime
from typing import Any

from kinocut.contracts._errors import INVALID_RECORD, contract_error
from kinocut.contracts.adapter import validate_record
from kinocut.contracts.trusted_execution import (
    EditProjectRecord,
    EditRevisionRecord,
    KernelEventRecord,
)
from kinocut.projectstore import layout
from kinocut.projectstore.store import (
    Project,
    _mapped_os_errors,
    _project_lock,
    _with_record_id,
    _write_atomically,
    append_record_locked,
    read_records,
    safe_target,
)

__all__ = ["append_revision", "create_edit_project", "get_edit_project"]

_EDIT_PROJECT_ID_RE = re.compile(r"^edit_project:[0-9a-f]{64}$")


def _now() -> str:
    """Informational UTC timestamp (excluded from the canonical id)."""
    return datetime.now(UTC).isoformat()


def _require_edit_project_id(value: Any) -> None:
    if not isinstance(value, str) or _EDIT_PROJECT_ID_RE.fullmatch(value) is None:
        raise contract_error("edit_project_id is not a valid identity", INVALID_RECORD)


def _find_edit_project(project: Project, edit_project_id: str) -> EditProjectRecord | None:
    """Return the current linear head: the record no other supersedes (one per chain)."""
    matching = [r for r in read_records(project, "edit_project") if r.edit_project_id == edit_project_id]
    if not matching:
        return None
    superseded = {r.supersedes for r in matching if r.supersedes}
    heads = [r for r in matching if r.record_id not in superseded]
    if len(heads) != 1:
        raise contract_error("edit project has an ambiguous head", INVALID_RECORD)
    return heads[0]


def _next_event_id(project: Project) -> int:
    """Next monotonic kernel event id for this project store."""
    events = read_records(project, "kernel_event")
    return 1 if not events else max(e.event_id for e in events) + 1


def _restore_bytes(path, prior: bytes | None) -> None:
    """Restore ``path`` to its pre-transaction bytes, or remove it if absent then."""
    if prior is None:
        with _mapped_os_errors(), contextlib.suppress(FileNotFoundError):
            path.unlink()
    else:
        _write_atomically(path, lambda writer: writer.write(prior), binary=True)


def _append_transaction(project: Project, records: list) -> None:
    """Append each record to its own JSONL file with exception-atomic rollback; records target distinct kinds."""
    targets = [safe_target(project, layout.records_relative_path(r.record_kind)) for r in records]
    with _mapped_os_errors():
        snapshots = [(t, (t.read_bytes() if t.exists() else None)) for t in targets]
    written = 0
    try:
        for record in records:
            append_record_locked(project, record)
            written += 1
    except BaseException:
        for index in range(written):
            target, prior = snapshots[index]
            _restore_bytes(target, prior)
        raise


def create_edit_project(
    project: Project,
    *,
    edit_project_id: str | None = None,
    created_by: str = "agent",
) -> EditProjectRecord:
    """Create one durable edit-project identity (revision 0, no head); re-creating returns its head unchanged."""
    if edit_project_id is not None:
        _require_edit_project_id(edit_project_id)
    identity = edit_project_id or f"edit_project:{secrets.token_hex(32)}"
    with _project_lock(project):
        existing = _find_edit_project(project, identity)
        if existing is not None:
            return existing
        record = validate_record(
            EditProjectRecord,
            {
                "edit_project_id": identity,
                "revision_number": 0,
                "head_revision_id": None,
                "project_id": project.project_id,
                "created_by": created_by,
                "created_at": _now(),
            },
        )
        return append_record_locked(project, record)


def get_edit_project(project: Project, edit_project_id: str) -> EditProjectRecord:
    """Return the current linear head for ``edit_project_id``."""
    _require_edit_project_id(edit_project_id)
    head = _find_edit_project(project, edit_project_id)
    if head is None:
        raise contract_error("edit project not found", INVALID_RECORD)
    return head


def append_revision(
    project: Project,
    edit_project_id: str,
    *,
    operation_ids: tuple[str, ...] = (),
    base_revision_id: str | None = None,
    created_by: str = "agent",
) -> EditRevisionRecord:
    """Append one linear revision snapshot and advance the head by exactly one. ``base_revision_id`` must
    equal the head's ``head_revision_id`` (``None`` for the first revision) or it fails closed as stale; the
    revision, event, and head append with exception-atomic rollback only."""
    _require_edit_project_id(edit_project_id)
    with _project_lock(project):
        head = _find_edit_project(project, edit_project_id)
        if head is None:
            raise contract_error("edit project not found", INVALID_RECORD)
        if base_revision_id != head.head_revision_id:
            raise contract_error("supplied base revision does not match the current head", INVALID_RECORD)
        next_number = head.revision_number + 1
        parent = head.head_revision_id  # None only for the first revision
        revision = validate_record(
            EditRevisionRecord,
            {
                "edit_project_id": edit_project_id,
                "revision_number": next_number,
                "parent_revision_id": parent,
                "operation_ids": operation_ids,
                "project_id": project.project_id,
                "created_by": created_by,
                "created_at": _now(),
            },
        )
        revision, revision_id = _with_record_id(revision)
        event = validate_record(
            KernelEventRecord,
            {
                "event_id": _next_event_id(project),
                "event_kind": "revision.created",
                "edit_project_id": edit_project_id,
                "revision_id": revision_id,
                "job_id": None,
                "subject_record_id": revision_id,
                "project_id": project.project_id,
                "created_by": created_by,
                "created_at": _now(),
            },
        )
        new_head = validate_record(
            EditProjectRecord,
            {
                "edit_project_id": edit_project_id,
                "revision_number": next_number,
                "head_revision_id": revision_id,
                "project_id": project.project_id,
                "created_by": created_by,
                "created_at": _now(),
                "supersedes": head.record_id,
            },
        )
        _append_transaction(project, [revision, event, new_head])
        return revision
