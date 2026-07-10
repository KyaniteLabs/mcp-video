"""Closed, bounded operation adapters for approved rescue repairs."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from mcp_video.engine_probe import probe
from mcp_video.errors import MCPVideoError
from mcp_video.ffmpeg_helpers import _run_ffprobe_json
from mcp_video.rescue.models import Disposition, Metric, Repair, RepairType
from mcp_video.rescue.operations import (
    OPERATION_REGISTRY,
    execute_repair,
    make_master,
    make_universal_copy,
)


def _hash(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _repair(repair_type: str, parameters: dict, *, disposition: Disposition = Disposition.SAFE_REPAIR) -> Repair:
    return Repair(
        id=f"{repair_type}:test",
        type=repair_type,
        disposition=disposition,
        confidence=1.0,
        confidence_rationale="Operation fixture.",
        evidence=[Metric(name="fixture", value=1, unit="ratio", definition="Operation fixture metric.")],
        parameters=parameters,
        expected_benefit="Exercise a bounded adapter.",
        tradeoffs=[],
        executor=f"ffmpeg.{repair_type}",
        promotable=disposition is Disposition.SAFE_REPAIR,
    )


def test_operation_registry_rejects_unknown_parameters(tmp_path, sample_video):
    repair = _repair("audio_loudness", {"target_lufs": -16.0, "raw_filter": "volume=99"})

    with pytest.raises(MCPVideoError) as caught:
        execute_repair(repair, sample_video, str(tmp_path / "out.mp4"))

    assert caught.value.code == "rescue_policy_violation"
    assert not (tmp_path / "out.mp4").exists()


def test_operation_registry_rejects_non_safe_repair(tmp_path, sample_video):
    repair = _repair("audio_loudness", {"target_lufs": -16.0, "lra": 11.0}, disposition=Disposition.RECOMMENDATION)

    with pytest.raises(MCPVideoError) as caught:
        execute_repair(repair, sample_video, str(tmp_path / "out.mp4"))

    assert caught.value.code == "rescue_policy_violation"


def test_timeline_and_package_operations_have_no_registry_entry():
    assert RepairType.TIMELINE_EDIT not in OPERATION_REGISTRY
    assert RepairType.SYNTHETIC_CONTENT not in OPERATION_REGISTRY
    assert RepairType.CLOUD_PROCESSING not in OPERATION_REGISTRY
    assert RepairType.UNIVERSAL_MP4 not in OPERATION_REGISTRY
    assert RepairType.CAPTIONS_TRANSCRIPT not in OPERATION_REGISTRY


def test_exposure_adapter_rejects_out_of_policy_level(tmp_path, sample_video):
    repair = _repair("exposure", {"level": 0.5})

    with pytest.raises(MCPVideoError) as caught:
        execute_repair(repair, sample_video, str(tmp_path / "out.mp4"))

    assert caught.value.code == "rescue_policy_violation"


def test_rotation_operation_swaps_dimensions(tmp_path, sample_video):
    output = tmp_path / "rotated.mp4"

    result = execute_repair(_repair("rotation", {"angle": 90}), sample_video, str(output))

    before = probe(sample_video)
    after = probe(str(output))
    assert (after.width, after.height) == (before.height, before.width)
    assert result.sha256.startswith("sha256:")


def test_loudness_operation_produces_decodable_output(tmp_path, sample_video):
    output = tmp_path / "normalized.mp4"

    execute_repair(
        _repair("audio_loudness", {"target_lufs": -16.0, "lra": 11.0}),
        sample_video,
        str(output),
    )

    assert probe(str(output)).audio_codec is not None


def test_master_without_repairs_is_an_exact_source_copy(tmp_path, sample_video):
    master = tmp_path / "master.mp4"

    result = make_master(sample_video, [], str(master))

    assert _hash(master) == _hash(sample_video)
    assert result.sha256 == f"sha256:{_hash(master)}"


def test_universal_copy_is_h264_aac_yuv420p(tmp_path, sample_video):
    share = tmp_path / "sharing.mp4"

    make_universal_copy(sample_video, str(share))

    raw = _run_ffprobe_json(str(share))
    video = next(stream for stream in raw["streams"] if stream["codec_type"] == "video")
    audio = next(stream for stream in raw["streams"] if stream["codec_type"] == "audio")
    assert video["codec_name"] == "h264"
    assert video["pix_fmt"] == "yuv420p"
    assert audio["codec_name"] == "aac"
