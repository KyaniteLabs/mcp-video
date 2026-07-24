"""Product-level workflow contracts (additive).

Public surface for the long-form stream-to-shorts workflow: strict,
JSON-serialisable data contracts plus the deterministic package writer.
"""

from .package import package_approved_clip
from .package_models import *  # noqa: F403

__all__ = [  # noqa: F405
    "PackageAsset",
    "PackageConfig",
    "PackageLineage",
    "PackagedClipResult",
    "PerformanceIdentifier",
    "PerformanceStatus",
    "ShortsPackageManifest",
    "ThumbnailSpec",
    "canonical_manifest_bytes",
    "manifest_artifact_digest",
    "package_approved_clip",
    "package_kind",
    "parse_package_manifest",
]
