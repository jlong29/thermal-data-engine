import json

from thermal_data_engine.agent_tools.inspect import ambiguous_clips, detector_summary, edge_status, model_version, recent_clips


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
    (root / "runs" / "run-1").mkdir(parents=True, exist_ok=True)
    (root / "uploads").mkdir(parents=True, exist_ok=True)

    recent = recent_clips(str(root), limit=1)
    ambiguous = ambiguous_clips(str(root), limit=5)
    summary = detector_summary(str(root))
    versions = model_version(str(root))
    status = edge_status(str(root))

    assert recent[0]["clip_id"] == "clip-b"
    assert ambiguous[0]["clip_id"] == "clip-b"
    assert summary["bundle_count"] == 2
    assert summary["selected_count"] == 2
    assert versions["latest_model_version"] == "yolo11_person_v1"
    assert status["bundle_count"] == 2
    assert status["run_count"] == 1
    assert status["upload_dir_exists"] is True
