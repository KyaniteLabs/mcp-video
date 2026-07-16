"""Deterministic derived-artifact cache digests over the CAS blob store."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from kinocut.contracts._errors import INVALID_RECORD, contract_error
from kinocut.projectstore import store
from kinocut.projectstore.cas import resolve_blob

_SOURCE_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def _canonical_derived_frame(
    source_digest: str,
    operation_params: object,
    toolchain_version: str,
    output_profile: str,
) -> bytes:
    """Canonical UTF-8 bytes over the derived-key frame, or fail closed.

    Tuples and lists both encode as ordered JSON arrays; mapping keys are
    sorted; non-finite floats (NaN/Inf) and unsupported values (sets, bytes,
    custom objects) are rejected by ``allow_nan=False`` / ``TypeError``.
    """

    frame = {
        "source_digest": source_digest,
        "operation_params": operation_params,
        "toolchain_version": toolchain_version,
        "output_profile": output_profile,
    }
    try:
        encoded = json.dumps(
            frame,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        return encoded.encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise contract_error("operation_params contains a non-canonical JSON value", INVALID_RECORD) from exc


def derived_cache_digest(
    source_digest: object,
    operation_params: object,
    toolchain_version: object,
    output_profile: object,
) -> str:
    """Return ``sha256:<hex>`` deterministically derived from canonical inputs.

    The digest is a pure function of ``(source_digest, operation_params,
    toolchain_version, output_profile)``. ``source_digest`` must be a strict
    ``sha256:<64 hex>`` value; ``toolchain_version`` / ``output_profile`` must
    be strings. Any malformed or non-canonical input fails closed with a
    contract error instead of producing an unstable digest.
    """

    if not isinstance(source_digest, str) or _SOURCE_DIGEST_RE.match(source_digest) is None:
        raise contract_error("source_digest must be a sha256:<hex> digest", INVALID_RECORD)
    if not isinstance(toolchain_version, str):
        raise contract_error("toolchain_version must be a string", INVALID_RECORD)
    if not isinstance(output_profile, str):
        raise contract_error("output_profile must be a string", INVALID_RECORD)
    frame = _canonical_derived_frame(source_digest, operation_params, toolchain_version, output_profile)
    return "sha256:" + hashlib.sha256(frame).hexdigest()


def resolve_artifact(project: store.Project, digest: str) -> Path:
    """Resolve a derived artifact, reusing the CAS blob integrity check.

    Derived artifacts share the canonical blob store in this slice; this typed
    alias names a derived output while paying for exactly one
    content-addressed integrity check — no duplicated blob storage.
    """

    return resolve_blob(project, digest)


__all__ = ["derived_cache_digest", "resolve_artifact"]
