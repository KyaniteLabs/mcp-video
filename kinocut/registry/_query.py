"""Approved-clip and reusable-bed query APIs over the project store.

These read-only queries compose the durable registry records (``ClipRecord``,
``BedRecord``) with the verdict, rights, and consent records already in the
project store. They never mutate state, never load whole files into memory, and
return deterministically ordered, paginated results suitable for later semantic
and beat-planning layers.

Filtering policy (design §4.4 / §4.9):

* **Verdict** — only clips whose bound ``ClipVerdict`` has an approved
  disposition (``approved`` or ``approved_with_trim``) enter the result.
* **Rights** — only clips/beds whose ``usage_rights_status`` is ``cleared``
  by default; a caller may widen the filter with ``rights_filter``.
* **Consent** — only clips/beds whose ``review_decision_id`` resolves to a
  fresh human ``approve`` decision bound to the clip/bed asset enter the result.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from kinocut.contracts._common import canonical_record_id
from kinocut.contracts.asset import UsageRightsStatus
from kinocut.contracts.review import DecisionType, ReviewDecision
from kinocut.contracts.verdict import ClipVerdict
from kinocut.projectstore.store import Project, read_records
from kinocut.contracts.registry import BedRecord, ClipRecord

#: The default rights posture required to enter an approved-only result.
_DEFAULT_RIGHTS = frozenset({UsageRightsStatus.CLEARED})

#: Maximum page size to prevent unbounded reads.
_MAX_LIMIT = 500


@dataclass(frozen=True)
class QueryPage:
    """One deterministically ordered, paginated slice of registry records."""

    records: tuple[ClipRecord | BedRecord, ...]
    total: int
    offset: int
    limit: int


def _validate_pagination(limit: int, offset: int) -> None:
    """Enforce bounded, non-negative pagination parameters."""

    if limit < 1:
        raise ValueError("limit must be at least one")
    if limit > _MAX_LIMIT:
        raise ValueError(f"limit must not exceed {_MAX_LIMIT}")
    if offset < 0:
        raise ValueError("offset must be non-negative")


def _index_verdicts(project: Project) -> dict[str, ClipVerdict]:
    """Return a canonical-id → verdict index of all clip verdicts."""

    return {
        canonical_record_id(verdict): verdict
        for verdict in read_records(project, "clip_verdict")
        if isinstance(verdict, ClipVerdict)
    }


def _index_decisions(project: Project) -> dict[str, ReviewDecision]:
    """Return a canonical-id → decision index of all review decisions."""

    return {
        canonical_record_id(decision): decision
        for decision in read_records(project, "review_decision")
        if isinstance(decision, ReviewDecision)
    }


def _verdict_is_approved(verdict: ClipVerdict | None) -> bool:
    """True when a verdict exists and has an approved disposition."""

    return verdict is not None and verdict.enters_approved_search()


def _consent_is_valid(
    decision: ReviewDecision | None,
    *,
    target_asset: str,
) -> bool:
    """True when a fresh human approve targets the given asset."""

    if decision is None:
        return False
    if type(decision) is not ReviewDecision:
        return False
    if decision.record_id is not None and decision.record_id != canonical_record_id(decision):
        return False
    if decision.decision is not DecisionType.APPROVE:
        return False
    if decision.actor != "human" or not decision.created_by.startswith("human"):
        return False
    return decision.target_ref == target_asset


def _matches_tags(tags: tuple[str, ...], wanted: frozenset[str] | None) -> bool:
    """True when every wanted tag is present on the record (AND semantics)."""

    if wanted is None:
        return True
    return wanted.issubset(set(tags))


def query_approved_clips(
    project: Project,
    *,
    tags: Iterable[str] | None = None,
    rights_filter: Iterable[UsageRightsStatus] | None = None,
    limit: int = 50,
    offset: int = 0,
) -> QueryPage:
    """Return approved clips filtered by verdict, rights, consent, and tags.

    Ordering is deterministic: records are sorted by their canonical
    ``record_id`` (a content-addressed digest), so the same store always yields
    the same order. Pagination is stable: ``(limit, offset)`` slices the sorted
    full match list.
    """

    _validate_pagination(limit, offset)
    wanted = frozenset(tags) if tags is not None else None
    rights = _rights_or_default(rights_filter)
    verdicts = _index_verdicts(project)
    decisions = _index_decisions(project)

    all_clips = [
        record for record in read_records(project, "clip_record") if isinstance(record, ClipRecord)
    ]
    matched = [
        clip
        for clip in all_clips
        if clip.usage_rights_status in rights
        and _verdict_is_approved(verdicts.get(clip.verdict_id))
        and _consent_is_valid(
            decisions.get(clip.review_decision_id), target_asset=clip.asset_id
        )
        and _matches_tags(clip.tags, wanted)
    ]
    return _paginate(matched, limit, offset, key=lambda clip: clip.record_id)


def query_reusable_beds(
    project: Project,
    *,
    tags: Iterable[str] | None = None,
    mood: str | None = None,
    rights_filter: Iterable[UsageRightsStatus] | None = None,
    limit: int = 50,
    offset: int = 0,
) -> QueryPage:
    """Return reusable beds filtered by rights, consent, tags, and mood."""

    _validate_pagination(limit, offset)
    wanted = frozenset(tags) if tags is not None else None
    rights = _rights_or_default(rights_filter)
    decisions = _index_decisions(project)

    all_beds = [
        record for record in read_records(project, "bed_record") if isinstance(record, BedRecord)
    ]
    matched = [
        bed
        for bed in all_beds
        if bed.usage_rights_status in rights
        and _consent_is_valid(decisions.get(bed.review_decision_id), target_asset=bed.asset_id)
        and _matches_tags(bed.tags, wanted)
        and (mood is None or bed.mood == mood)
    ]
    return _paginate(matched, limit, offset, key=lambda bed: bed.record_id)


def _rights_or_default(
    rights_filter: Iterable[UsageRightsStatus] | None,
) -> frozenset[UsageRightsStatus]:
    """Return the caller's rights filter, or the default cleared-only set."""

    if rights_filter is None:
        return _DEFAULT_RIGHTS
    return frozenset(rights_filter)


def _paginate(
    records: list[ClipRecord | BedRecord],
    limit: int,
    offset: int,
    *,
    key,
) -> QueryPage:
    """Sort by ``key``, slice, and return a page with total count."""

    records.sort(key=key)
    total = len(records)
    page = tuple(records[offset : offset + limit])
    return QueryPage(records=page, total=total, offset=offset, limit=limit)
