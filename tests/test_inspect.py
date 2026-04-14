import json

from thermal_data_engine.agent_tools.inspect import ambiguous_clips, detector_summary, edge_status, model_version, recent_clips, recent_runs


def _write_manifest(path, created_at, selection_reason, selected=True, model_version_value="yolo11_person_v1"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "clip_id": path.parent.name,
                "created_at": created_at,
                "selection_reason": selection_reason,
                "selected": selected,
                "model_version": model_version_value,
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
                "upload": {"status": "skipped", "uri": "", "backend": "local_copy"},
            }
        )
    )
    (root / "uploads").mkdir(parents=True, exist_ok=True)

    recent = recent_clips(str(root), limit=1)
    ambiguous = ambiguous_clips(str(root), limit=5)
    summary = detector_summary(str(root))
    versions = model_version(str(root))
    runs = recent_runs(str(root), limit=5)
    status = edge_status(str(root))

    assert recent[0]["clip_id"] == "clip-b"
    assert ambiguous[0]["clip_id"] == "clip-b"
    assert summary["bundle_count"] == 2
    assert summary["selected_count"] == 2
    assert versions["latest_model_version"] == "yolo11_person_v1"
    assert runs[0]["clip_id"] == "clip-c"
    assert runs[0]["selected"] is False
    assert status["bundle_count"] == 2
    assert status["run_count"] == 1
    assert status["upload_dir_exists"] is True
    assert status["latest_run"]["selection_reason"] == "no_detections"
    assert status["latest_run"]["frame_count"] == 42
    assert status["latest_run"]["frame_window"]["fps"] == 9.0
    assert status["latest_run"]["job_detection_summary"]["frame_count"] == 42
    assert status["latest_run"]["upload"]["status"] == "skipped"
    assert status["latest_run"]["upload"]["backend"] == "local_copy"
