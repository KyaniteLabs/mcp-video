"""Immutable registry for separately versioned feature policies."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from types import MappingProxyType

from .models import PolicyPermissions, PolicyProfile

PolicyKey = tuple[str, int]


class PolicyRegistry:
    def __init__(self, profiles: Iterable[PolicyProfile] = ()) -> None:
        indexed: dict[PolicyKey, PolicyProfile] = {}
        for profile in profiles:
            key = (profile.id, profile.version)
            if key in indexed:
                raise ValueError(f"duplicate policy profile: {profile.id}@{profile.version}")
            indexed[key] = profile
        self._profiles = MappingProxyType(indexed)

    @property
    def profiles(self) -> Mapping[PolicyKey, PolicyProfile]:
        return self._profiles

    def resolve(self, policy_id: str, version: int) -> PolicyProfile:
        try:
            return self._profiles[(policy_id, version)]
        except KeyError as exc:
            raise KeyError(f"unknown policy profile: {policy_id}@{version}") from exc

    def extend(self, *profiles: PolicyProfile) -> PolicyRegistry:
        return PolicyRegistry((*self._profiles.values(), *profiles))


POLICY_REGISTRY = PolicyRegistry(
    (
        PolicyProfile(
            id="local_content_preserving",
            version=1,
            description="Local-only rescue with timeline, crop, synthesis, network, and overwrite locked.",
            permissions=PolicyPermissions(),
            gating_checks=(),
        ),
    )
)

