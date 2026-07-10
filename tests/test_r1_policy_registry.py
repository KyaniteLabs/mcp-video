from __future__ import annotations

import pytest

from mcp_video.rescue.r1.models import PolicyPermissions, PolicyProfile
from mcp_video.rescue.r1.policy_registry import POLICY_REGISTRY, PolicyRegistry


def test_local_content_preserving_profile_is_explicit_and_immutable() -> None:
    profile = POLICY_REGISTRY.resolve("local_content_preserving", 1)

    assert profile.permissions == PolicyPermissions(
        timeline=False,
        crop=False,
        synthesis=False,
        network=False,
        source_overwrite=False,
    )
    with pytest.raises(TypeError):
        POLICY_REGISTRY.profiles[("local_content_preserving", 1)] = profile  # type: ignore[index]


def test_policy_registry_rejects_duplicate_versions() -> None:
    profile = PolicyProfile(
        id="toy_visual_crop",
        version=1,
        description="Toy crop policy.",
        permissions=PolicyPermissions(crop=True),
        gating_checks=("toy_crop_bounds",),
    )

    with pytest.raises(ValueError, match="duplicate policy profile"):
        PolicyRegistry((profile, profile))

