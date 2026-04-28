import json

from thermal_data_engine.agent_tools.inspect import (
    ambiguous_clips,
    clip_artifact_summary,
    detector_summary,
    edge_status,
    model_version,
    recent_clips,
    recent_runs,
    upload_summary,
    validate_ultralytics_package,
    validate_video_clip_package,
)


def _write_manifest(
    path,
    created_at,
    selection_reason,
    selected=True,
    model_version_value="yolo11_person_v1",
    clip_write_mode="source_copy",
):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "clip_id": path.parent.name,
                "created_at": created_at,
                "selection_reason": selection_reason,
                "selected": selected,
                "model_version": model_version_value,
                "extra": {"clip_artifact": {"write_mode": clip_write_mode}},
            }
        )
    )


def test_inspection_helpers_read_saved_bundle_manifests(tmp_path):
    root = tmp_path / "outputs"
    _write_manifest(root / "bundles" / "clip-a" / "clip_manifest.json", "2026-04-14T17:00:00Z", "high_confidence_track")
    _write_manifest(root / "bundles" / "clip-b" / "clip_manifest.json", "2026-04-14T17:05:00Z", "unstable_track_motion")
    run_dir = root / "runs" / "run-1"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "pipeline_summary.json").write_text(
        json.dumps(
            {
                "clip_id": "clip-c",
                "run_id": "run-1",
                "run_started_at": "2026-04-14T17:06:00Z",
                "run_completed_at": "2026-04-14T17:06:30Z",
                "selected": False,
                "selection_reason": "no_detections",
                "vision_job_id": "job-1",
                "bundle_dir": str(root / "bundles" / "clip-c"),
                "source_path": "/tmp/input.mp4",
                "model_version": "yolo11_person_v1",
                "frame_window": {
                    "fps": 9.0,
                    "frame_count": 42,
                    "width": 640,
                    "height": 512,
                    "start_ts": "0.0",
                    "end_ts": "4.6",
                },
                "frame_count": 42,
                "detection_count": 0,
                "track_count": 0,
                "job_detection_summary": {"fps": 9.0, "frame_count": 42},
                "bundle": {"status": "not_written", "clip_write_mode": None},
                "upload": {"status": "skipped", "uri": "", "backend": "local_copy"},
            }
        )
    )
    (root / "uploads").mkdir(parents=True, exist_ok=True)

    recent = recent_clips(str(root), limit=1)
    ambiguous = ambiguous_clips(str(root), limit=5)
    summary = detector_summary(str(root))
    versions = model_version(str(root))
    clip_artifacts = clip_artifact_summary(str(root))
    uploads = upload_summary(str(root), limit=5)
    runs = recent_runs(str(root), limit=5)
    status = edge_status(str(root))

    assert recent[0]["clip_id"] == "clip-b"
    assert ambiguous[0]["clip_id"] == "clip-b"
    assert summary["bundle_count"] == 2
    assert summary["selected_count"] == 2
    assert versions["latest_model_version"] == "yolo11_person_v1"
    assert clip_artifacts["clip_write_modes"]["source_copy"] == 2
    assert uploads["recent_run_count"] == 1
    assert uploads["upload_statuses"]["skipped"] == 1
    assert runs[0]["clip_id"] == "clip-c"
    assert runs[0]["selected"] is False
    assert status["bundle_count"] == 2
    assert status["run_count"] == 1
    assert status["upload_dir_exists"] is True
    assert status["latest_run"]["selection_reason"] == "no_detections"
    assert status["latest_run"]["frame_count"] == 42
    assert status["latest_run"]["frame_window"]["fps"] == 9.0
    assert status["latest_run"]["job_detection_summary"]["frame_count"] == 42
    assert status["latest_run"]["bundle"]["status"] == "not_written"
    assert status["latest_run"]["upload"]["status"] == "skipped"
    assert status["latest_run"]["upload"]["backend"] == "local_copy"
    assert status["clip_artifacts"]["clip_write_modes"]["source_copy"] == 2
    assert status["uploads"]["recent_run_count"] == 1
    assert status["uploads"]["upload_statuses"]["skipped"] == 1


def test_recent_runs_prefers_run_completion_timestamp(tmp_path):
    root = tmp_path / "outputs"
    older_run_dir = root / "runs" / "run-z"
    older_run_dir.mkdir(parents=True, exist_ok=True)
    (older_run_dir / "pipeline_summary.json").write_text(
        json.dumps(
            {
                "clip_id": "clip-older",
                "run_id": "run-z",
                "run_completed_at": "2026-04-14T17:00:00Z",
                "selected": False,
            }
        )
    )
    newer_run_dir = root / "runs" / "run-a"
    newer_run_dir.mkdir(parents=True, exist_ok=True)
    (newer_run_dir / "pipeline_summary.json").write_text(
        json.dumps(
            {
                "clip_id": "clip-newer",
                "run_id": "run-a",
                "run_completed_at": "2026-04-14T17:10:00Z",
                "selected": True,
            }
        )
    )

    runs = recent_runs(str(root), limit=2)

    assert [item["clip_id"] for item in runs] == ["clip-newer", "clip-older"]


def test_recent_runs_falls_back_to_run_id_timestamp_suffix(tmp_path):
    root = tmp_path / "outputs"
    older_run_dir = root / "runs" / "clip-z-older"
    older_run_dir.mkdir(parents=True, exist_ok=True)
    (older_run_dir / "pipeline_summary.json").write_text(
        json.dumps(
            {
                "clip_id": "clip-z",
                "run_id": "clip-z-20260414T214812Z",
                "selected": False,
            }
        )
    )
    newer_run_dir = root / "runs" / "clip-a-newer"
    newer_run_dir.mkdir(parents=True, exist_ok=True)
    (newer_run_dir / "pipeline_summary.json").write_text(
        json.dumps(
            {
                "clip_id": "clip-a",
                "run_id": "clip-a-20260415T005348Z",
                "selected": True,
            }
        )
    )

    runs = recent_runs(str(root), limit=2)
    status = edge_status(str(root))

    assert [item["clip_id"] for item in runs] == ["clip-a", "clip-z"]
    assert status["latest_run"]["clip_id"] == "clip-a"
    assert status["latest_run"]["selected"] is True



def test_validate_ultralytics_package_reports_ready_dataset(tmp_path):
    dataset_root = tmp_path / "dataset"
    (dataset_root / "images").mkdir(parents=True, exist_ok=True)
    (dataset_root / "labels").mkdir(parents=True, exist_ok=True)
    (dataset_root / "splits").mkdir(parents=True, exist_ok=True)
    (dataset_root / "images" / "frame-001.jpg").write_bytes(b"jpg")
    (dataset_root / "labels" / "frame-001.txt").write_text("0 0.5 0.5 0.25 0.25\n")
    (dataset_root / "splits" / "train.txt").write_text("images/frame-001.jpg\n")
    (dataset_root / "splits" / "val.txt").write_text("images/frame-001.jpg\n")
    (dataset_root / "dataset.yaml").write_text(
        "path: .\ntrain: splits/train.txt\nval: splits/val.txt\nnames: ['person']\n"
    )
    (dataset_root / "manifest.json").write_text("{}")

    result = validate_ultralytics_package(str(dataset_root))

    assert result["ok"] is True
    assert result["split_counts"] == {"train": 1, "val": 1}
    assert result["image_count"] == 2
    assert result["label_count"] == 2
    assert result["object_count"] == 2
    assert result["errors"] == []



def test_validate_ultralytics_package_reports_missing_labels_and_bad_coords(tmp_path):
    dataset_root = tmp_path / "dataset"
    (dataset_root / "images").mkdir(parents=True, exist_ok=True)
    (dataset_root / "labels").mkdir(parents=True, exist_ok=True)
    (dataset_root / "splits").mkdir(parents=True, exist_ok=True)
    (dataset_root / "images" / "frame-001.jpg").write_bytes(b"jpg")
    (dataset_root / "images" / "frame-002.jpg").write_bytes(b"jpg")
    (dataset_root / "labels" / "frame-001.txt").write_text("0 1.5 0.5 0.25 0.25\n")
    (dataset_root / "splits" / "train.txt").write_text("images/frame-001.jpg\nimages/frame-002.jpg\n")
    (dataset_root / "splits" / "val.txt").write_text("images/frame-001.jpg\n")
    (dataset_root / "dataset.yaml").write_text(
        "path: .\ntrain: splits/train.txt\nval: splits/val.txt\nnames: ['person']\n"
    )

    result = validate_ultralytics_package(str(dataset_root))

    assert result["ok"] is False
    assert any("coordinate outside [0, 1]" in error for error in result["errors"])
    assert any("missing label for image" in error for error in result["errors"])
    assert any("manifest.json missing" in warning for warning in result["warnings"])



def test_validate_ultralytics_package_accepts_mapping_style_names(tmp_path):
    dataset_root = tmp_path / "dataset"
    (dataset_root / "images").mkdir(parents=True, exist_ok=True)
    (dataset_root / "labels").mkdir(parents=True, exist_ok=True)
    (dataset_root / "splits").mkdir(parents=True, exist_ok=True)
    (dataset_root / "images" / "frame-001.jpg").write_bytes(b"jpg")
    (dataset_root / "labels" / "frame-001.txt").write_text("0 0.5 0.5 0.25 0.25\n")
    (dataset_root / "splits" / "train.txt").write_text("images/frame-001.jpg\n")
    (dataset_root / "splits" / "val.txt").write_text("images/frame-001.jpg\n")
    (dataset_root / "dataset.yaml").write_text(
        "path: .\ntrain: splits/train.txt\nval: splits/val.txt\nnames:\n  0: person\n"
    )

    result = validate_ultralytics_package(str(dataset_root))

    assert result["ok"] is True
    assert result["dataset_fields"]["names"] == "0: person"
    assert result["errors"] == []


def test_validate_video_clip_package_reports_ready_package(tmp_path):
    package_root = tmp_path / "video-package"
    clip_dir = package_root / "clips" / "01_alpha__clip-alpha"
    clip_dir.mkdir(parents=True, exist_ok=True)
    (clip_dir / "clip.mp4").write_bytes(b"mp4")
    (clip_dir / "detections.parquet").write_bytes(b"parquet")
    (clip_dir / "tracks.parquet").write_bytes(b"parquet")
    (clip_dir / "clip_manifest.json").write_text(
        json.dumps(
            {
                "clip_id": "clip-alpha",
                "run_id": "run-alpha",
                "vision_job_id": "job-alpha",
                "track_count": 1,
                "detection_count": 3,
                "tracker_type": "iou_greedy_v1",
                "selected": True,
            }
        )
    )
    (package_root / "manifest.json").write_text(
        json.dumps(
            {
                "package_type": "thermal_video_clip_dataset",
                "package_version": "v1",
                "source_count": 1,
                "clip_count": 1,
                "sources": [
                    {
                        "source_path": "/tmp/alpha.mp4",
                        "clip_id": "clip-alpha",
                        "run_id": "run-alpha",
                        "vision_job_id": "job-alpha",
                        "included_in_package": True,
                    }
                ],
                "clips": [
                    {
                        "package_clip_id": "01_alpha__clip-alpha",
                        "package_clip_dir": "clips/01_alpha__clip-alpha",
                        "source_path": "/tmp/alpha.mp4",
                        "clip_id": "clip-alpha",
                        "run_id": "run-alpha",
                        "vision_job_id": "job-alpha",
                        "track_count": 1,
                        "detection_count": 3,
                        "artifacts": {
                            "clip_path": "clips/01_alpha__clip-alpha/clip.mp4",
                            "detections_path": "clips/01_alpha__clip-alpha/detections.parquet",
                            "tracks_path": "clips/01_alpha__clip-alpha/tracks.parquet",
                            "manifest_path": "clips/01_alpha__clip-alpha/clip_manifest.json",
                        },
                    }
                ],
            }
        )
    )

    result = validate_video_clip_package(str(package_root))

    assert result["ok"] is True
    assert result["clip_count"] == 1
    assert result["selected_source_count"] == 1
    assert result["errors"] == []
