from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import kinocut.product.package as package_module
from kinocut.errors import MCPVideoError
from kinocut.product.captions import build_caption_artifact
from kinocut.product.models import CandidateMoment, canonical_dedup_key
from kinocut.product.package import package_approved_clip
from kinocut.product.package_models import PackageConfig, ThumbnailSpec


def _candidate(*, warning: str | None = "review this") -> CandidateMoment:
    excerpt = "A complete thought prepared for a short clip."
    return CandidateMoment(
        candidate_id="candidate_01",
        start=10.0,
        end=20.0,
        transcript_excerpt=excerpt,
        suggested_title="A useful clip",
        suggested_hook="Start here",
        rationale="Complete thought",
        confidence=0.9,
        sensitivity="none",
        dedup_key=canonical_dedup_key(start=10.0, end=20.0, excerpt=excerpt, sensitivity="none"),
        review_warning=warning,
    )


def _caption():
    return build_caption_artifact(
        [
            {"word": "Start", "start": 0.0, "end": 0.4, "probability": 0.95},
            {"word": "here", "start": 0.45, "end": 0.9, "probability": 0.95},
        ]
    )


def _inputs(tmp_path: Path):
    video = tmp_path / "render.mp4"
    thumbnail = tmp_path / "frame.jpg"
    video.write_bytes(b"approved vertical render")
    thumbnail.write_bytes(b"approved thumbnail")
    return video, thumbnail


def test_package_writes_complete_portable_artifact_set(tmp_path):
    video, thumbnail = _inputs(tmp_path)
    result = package_approved_clip(
        package_dir=str(tmp_path / "package"),
        vertical_video_path=str(video),
        expected_video_sha256=hashlib.sha256(video.read_bytes()).hexdigest(),
        caption_artifact=_caption(),
        candidate=_candidate(),
        thumbnail=ThumbnailSpec(image_path=str(thumbnail), timestamp=12.0),
    )
    assert {Path(path).name for path in result.asset_paths} == {
        "vertical.mp4",
        "captions.srt",
        "thumbnail.jpg",
        "metadata.json",
        Path(result.manifest_path).name,
    }
    assert all(Path(path).parent == Path(result.package_root) for path in result.asset_paths)


def test_package_records_verified_video_checksum(tmp_path):
    video, thumbnail = _inputs(tmp_path)
    result = package_approved_clip(
        package_dir=str(tmp_path / "package"),
        vertical_video_path=str(video),
        caption_artifact=_caption(),
        candidate=_candidate(),
        thumbnail=ThumbnailSpec(image_path=str(thumbnail), timestamp=12.0),
    )
    metadata = json.loads((Path(result.package_root) / "metadata.json").read_text())
    assert (
        metadata["vertical_video_sha256"]
        == hashlib.sha256((Path(result.package_root) / "vertical.mp4").read_bytes()).hexdigest()
    )


def test_package_rejects_checksum_mismatch_before_writing(tmp_path):
    video, thumbnail = _inputs(tmp_path)
    with pytest.raises(MCPVideoError) as exc:
        package_approved_clip(
            package_dir=str(tmp_path / "package"),
            vertical_video_path=str(video),
            expected_video_sha256="0" * 64,
            caption_artifact=_caption(),
            candidate=_candidate(),
            thumbnail=ThumbnailSpec(image_path=str(thumbnail), timestamp=12.0),
        )
    assert exc.value.code == "source_checksum_mismatch"


def test_package_refuses_collision_unless_overwrite_is_explicit(tmp_path):
    video, thumbnail = _inputs(tmp_path)
    kwargs = {
        "package_dir": str(tmp_path / "package"),
        "vertical_video_path": str(video),
        "caption_artifact": _caption(),
        "candidate": _candidate(),
        "thumbnail": ThumbnailSpec(image_path=str(thumbnail), timestamp=12.0),
    }
    package_approved_clip(**kwargs)
    with pytest.raises(MCPVideoError) as exc:
        package_approved_clip(**kwargs)
    assert exc.value.code == "package_write_conflict"
    assert package_approved_clip(**kwargs, config=PackageConfig(overwrite_package=True)).manifest.package_id.startswith(
        "pkg_"
    )


def test_package_rejects_symlinked_output_without_touching_target(tmp_path):
    video, thumbnail = _inputs(tmp_path)
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text("preserve")
    (package_dir / "metadata.json").symlink_to(outside)
    with pytest.raises(MCPVideoError) as exc:
        package_approved_clip(
            package_dir=str(package_dir),
            vertical_video_path=str(video),
            caption_artifact=_caption(),
            candidate=_candidate(),
            thumbnail=ThumbnailSpec(image_path=str(thumbnail), timestamp=12.0),
        )
    assert exc.value.code == "unsafe_path"
    assert outside.read_text() == "preserve"


def test_package_cleans_staging_files_after_midwrite_failure(tmp_path, monkeypatch):
    video, thumbnail = _inputs(tmp_path)
    original = package_module._stage_bytes
    calls = 0

    def fail_second_write(payload, directory):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("disk full")
        return original(payload, directory)

    monkeypatch.setattr(package_module, "_stage_bytes", fail_second_write)
    package_dir = tmp_path / "package"
    with pytest.raises(OSError, match="disk full"):
        package_approved_clip(
            package_dir=str(package_dir),
            vertical_video_path=str(video),
            caption_artifact=_caption(),
            candidate=_candidate(),
            thumbnail=ThumbnailSpec(image_path=str(thumbnail), timestamp=12.0),
        )
    assert list(package_dir.iterdir()) == []
