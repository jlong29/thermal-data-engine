import json
from pathlib import Path

import pytest

from thermal_data_engine.common.models import BundleManifest, DetectionRecord, TrackSummary
from thermal_data_engine.edge import bundle as bundle_module


@pytest.fixture
def sample_manifest():
    return BundleManifest(
        clip_id="clip-1",
        source_device_id="nx-01",
        source_path="/tmp/source.mp4",
        start_ts="0.0",
        end_ts="1.0",
        fps=5.0,
        frame_count=3,
        width=320,
        height=240,
        model_version="yolo11_person_v1",
        tracker_type="iou_greedy_v1",
        storage_uri="/tmp/bundles/clip-1",
        created_at="2026-04-14T17:00:00Z",
        selection_reason="high_confidence_track",
        selected=True,
        vision_job_id="job-1",
        run_id="run-1",
        track_count=1,
        detection_count=3,
        extra={},
    )


@pytest.fixture
def sample_detections():
    return [
        DetectionRecord(
            clip_id="clip-1",
            frame_idx=0,
            source_frame_num=0,
            timestamp_sec=0.0,
            track_id="track-0001",
            class_id=0,
            class_name="person",
            confidence=0.9,
            bbox_left=10.0,
            bbox_top=10.0,
            bbox_right=40.0,
            bbox_bottom=50.0,
            bbox_width=30.0,
            bbox_height=40.0,
            area_px=1200.0,
            source_id=0,
            image_width=320,
            image_height=240,
            is_target_class=True,
        )
    ]


@pytest.fixture
def sample_tracks():
    return [
        TrackSummary(
            clip_id="clip-1",
            track_id="track-0001",
            class_name="person",
            class_id=0,
            duration_frames=3,
            start_frame_idx=0,
            end_frame_idx=2,
            mean_conf=0.9,
            min_conf=0.88,
            max_conf=0.92,
            bbox_area_mean=1200.0,
            bbox_jitter=0.2,
            edge_fraction=0.0,
            detection_density=1.0,
            selection_reason="high_confidence_track",
            selected=True,
        )
    ]


def test_write_bundle_raises_when_parquet_backend_missing(tmp_path, monkeypatch, sample_manifest, sample_detections, sample_tracks):
    source_clip = tmp_path / "source.mp4"
    source_clip.write_bytes(b"fake-mp4")

    monkeypatch.setattr(bundle_module, "parquet_backend", lambda: (None, None))

    with pytest.raises(RuntimeError, match="PARQUET_BACKEND_MISSING"):
        bundle_module.write_bundle(tmp_path / "bundle", source_clip, sample_manifest, sample_detections, sample_tracks)


@pytest.mark.skipif(bundle_module.parquet_backend()[0] is None, reason="pyarrow not installed")
def test_write_bundle_writes_expected_files(tmp_path, sample_manifest, sample_detections, sample_tracks):
    source_clip = tmp_path / "source.mp4"
    source_clip.write_bytes(b"fake-mp4")

    result = bundle_module.write_bundle(tmp_path / "bundle", source_clip, sample_manifest, sample_detections, sample_tracks)

    assert set(result.keys()) == {"clip_path", "detections_path", "tracks_path", "manifest_path", "clip_write_mode"}
    assert (tmp_path / "bundle" / "clip.mp4").exists()
    manifest_payload = json.loads((tmp_path / "bundle" / "clip_manifest.json").read_text())
    assert manifest_payload["clip_id"] == "clip-1"
    assert manifest_payload["extra"]["clip_artifact"]["write_mode"] == result["clip_write_mode"]
    assert manifest_payload["extra"]["clip_artifact"]["source_path"] == str(source_clip)
    assert (tmp_path / "bundle" / "detections.parquet").exists()
    assert (tmp_path / "bundle" / "tracks.parquet").exists()


def test_extract_clip_segment_returns_false_without_valid_time_window(tmp_path):
    source_clip = tmp_path / "source.mp4"
    source_clip.write_bytes(b"fake-mp4")

    assert bundle_module.extract_clip_segment(source_clip, tmp_path / "clip.mp4", None, "1.0") is False
    assert bundle_module.extract_clip_segment(source_clip, tmp_path / "clip.mp4", "2.0", "1.0") is False


def test_write_bundle_falls_back_to_copy_when_segment_extraction_fails(
    tmp_path, monkeypatch, sample_manifest, sample_detections, sample_tracks
):
    source_clip = tmp_path / "source.mp4"
    source_clip.write_bytes(b"fake-mp4")

    copied = []

    def fake_extract(*args, **kwargs):
        return False

    def fake_copy(source_path, destination_path):
        copied.append((Path(source_path), Path(destination_path)))
        Path(destination_path).write_bytes(b"copied")

    monkeypatch.setattr(bundle_module, "extract_clip_segment", fake_extract)
    monkeypatch.setattr(bundle_module, "copy_clip", fake_copy)

    result = bundle_module.write_bundle(tmp_path / "bundle", source_clip, sample_manifest, sample_detections, sample_tracks)

    assert copied == [(source_clip, tmp_path / "bundle" / "clip.mp4")]
    assert result["clip_write_mode"] == "source_copy"
    assert sample_manifest.extra["clip_artifact"]["write_mode"] == "source_copy"
    assert (tmp_path / "bundle" / "clip.mp4").read_bytes() == b"copied"
