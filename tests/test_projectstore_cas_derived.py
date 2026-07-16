"""Determinism, fail-closed, and integrity tests for the derived CAS digest.

Covers G008 slice 1: ``derived_cache_digest`` (canonical JSON normalization +
strict sha256 source validation) and ``resolve_artifact`` (integrity-checked
alias over the existing CAS blob store). No proxy/GC behavior is exercised.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from kinocut.errors import MCPVideoError
from kinocut.projectstore import ingest_blob, open_project
from kinocut.projectstore.cas_derived import derived_cache_digest, resolve_artifact

_GOOD = "sha256:" + "a" * 64


# ---------------------------------------------------------------------------
# Determinism / canonical normalization
# ---------------------------------------------------------------------------


def test_digest_is_idempotent_for_identical_inputs():
    a = derived_cache_digest(_GOOD, {"gain": 1.0, "curve": "log"}, "ffmpeg-6.0", "h264-1080p")
    b = derived_cache_digest(_GOOD, {"gain": 1.0, "curve": "log"}, "ffmpeg-6.0", "h264-1080p")
    assert a == b
    assert a.startswith("sha256:")
    assert len(a) == len("sha256:") + 64  # well-formed sha256 digest


def test_digest_is_invariant_under_mapping_key_reorder():
    ordered = derived_cache_digest(_GOOD, {"a": 1, "b": 2, "c": 3}, "v1", "p1")
    reordered = derived_cache_digest(_GOOD, {"c": 3, "a": 1, "b": 2}, "v1", "p1")
    assert ordered == reordered


def test_digest_is_invariant_under_nested_mapping_key_reorder():
    ordered = derived_cache_digest(_GOOD, {"outer": {"z": 1, "a": 2}}, "v1", "p1")
    reordered = derived_cache_digest(_GOOD, {"outer": {"a": 2, "z": 1}}, "v1", "p1")
    assert ordered == reordered


# ---------------------------------------------------------------------------
# Value / order / toolchain / profile distinctions
# ---------------------------------------------------------------------------


def test_digest_distinguishes_param_values():
    one = derived_cache_digest(_GOOD, {"k": 1}, "v1", "p1")
    two = derived_cache_digest(_GOOD, {"k": 2}, "v1", "p1")
    assert one != two


def test_digest_distinguishes_list_order():
    forward = derived_cache_digest(_GOOD, [1, 2, 3], "v1", "p1")
    reverse = derived_cache_digest(_GOOD, [3, 2, 1], "v1", "p1")
    assert forward != reverse


def test_digest_treats_tuple_and_list_as_ordered_array():
    """Both tuples and lists encode as canonical JSON arrays (order matters)."""

    as_list = derived_cache_digest(_GOOD, [1, 2, 3], "v1", "p1")
    as_tuple = derived_cache_digest(_GOOD, (1, 2, 3), "v1", "p1")
    assert as_list == as_tuple


def test_digest_distinguishes_source_toolchain_and_profile():
    base = derived_cache_digest(_GOOD, {}, "v1", "p1")
    assert derived_cache_digest("sha256:" + "b" * 64, {}, "v1", "p1") != base
    assert derived_cache_digest(_GOOD, {}, "v2", "p1") != base
    assert derived_cache_digest(_GOOD, {}, "v1", "p2") != base


# ---------------------------------------------------------------------------
# Fail-closed malformed input
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad",
    ["", "sha256:abc", "SHA256:" + "a" * 64, "x" * 64, "sha256:" + "A" * 64, None, 123, []],
)
def test_digest_rejects_malformed_source_digest(bad):
    with pytest.raises(MCPVideoError):
        derived_cache_digest(bad, {}, "v1", "p1")


@pytest.mark.parametrize(
    "bad_params",
    [
        {"k": {1, 2, 3}},
        {"k": b"bytes"},
        [math.nan],
        [math.inf],
        [math.nan * -1],
        {"k": object()},
        {"k": (1, {9, 8})},
    ],
)
def test_digest_rejects_non_canonical_params(bad_params):
    with pytest.raises(MCPVideoError):
        derived_cache_digest(_GOOD, bad_params, "v1", "p1")


@pytest.mark.parametrize("bad", [None, 123, [], {}, 1.5])
def test_digest_rejects_non_string_toolchain_and_profile(bad):
    with pytest.raises(MCPVideoError):
        derived_cache_digest(_GOOD, {}, bad, "p1")
    with pytest.raises(MCPVideoError):
        derived_cache_digest(_GOOD, {}, "v1", bad)


def test_digest_error_does_not_echo_offending_value():
    """Fail-closed messages must not leak the offending input (privacy)."""

    with pytest.raises(MCPVideoError) as exc_info:
        derived_cache_digest(_GOOD, {"k": {1, 2, 3}}, "v1", "p1")
    assert "{1, 2, 3}" not in str(exc_info.value)


# ---------------------------------------------------------------------------
# resolve_artifact: reopen survival + corruption fail-closed
# ---------------------------------------------------------------------------


def test_resolve_artifact_survives_project_reopen(tmp_path: Path):
    source = tmp_path / "src.bin"
    source.write_bytes(b"derived-source-bytes")
    project = open_project(tmp_path / "project")
    manifest = ingest_blob(project, source)
    # The derived cache key is a pure function — stable across "sessions".
    key = derived_cache_digest(manifest.digest, {"op": "encode"}, "v1", "profile-a")
    reopened = open_project(project.root)
    assert resolve_artifact(reopened, manifest.digest).read_bytes() == source.read_bytes()
    assert derived_cache_digest(manifest.digest, {"op": "encode"}, "v1", "profile-a") == key


def test_resolve_artifact_fails_closed_after_blob_corruption(tmp_path: Path):
    source = tmp_path / "src.bin"
    source.write_bytes(b"trusted-derived")
    project = open_project(tmp_path / "project")
    manifest = ingest_blob(project, source)
    resolve_artifact(project, manifest.digest).write_bytes(b"tampered")
    with pytest.raises(MCPVideoError, match="integrity"):
        resolve_artifact(open_project(project.root), manifest.digest)


def test_resolve_artifact_fails_closed_for_unknown_digest(tmp_path: Path):
    project = open_project(tmp_path / "project")
    unknown = "sha256:" + "0" * 64
    with pytest.raises(MCPVideoError):
        resolve_artifact(project, unknown)
