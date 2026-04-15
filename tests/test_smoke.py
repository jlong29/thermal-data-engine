from thermal_data_engine.edge import pipeline


def test_smoke_test_overrides_runtime_window(monkeypatch, tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    captured = {}

    def fake_process_file(**kwargs):
        captured.update(kwargs)
        return {
            "clip_id": "clip-123",
            "run_id": "run-123",
            "run_dir": str(run_dir),
            "selected": True,
            "selection_reason": "edge_activity",
            "bundle_dir": str(tmp_path / "bundle"),
            "vision_job_id": "job-123",
            "frame_count": 12,
            "detection_count": 3,
            "track_count": 2,
            "upload": {"status": "disabled", "uri": ""},
        }

    def fake_read_json(path):
        assert path == run_dir / "pipeline_summary.json"
        return {
            "job_detection_summary": {"frames_with_target_detections": 2},
            "windowing_decision": {"decision": {"mode": "configured"}},
        }

    monkeypatch.setattr(pipeline, "process_file", fake_process_file)
    monkeypatch.setattr(pipeline, "read_json", fake_read_json)

    result = pipeline.smoke_test(
        source="/tmp/input.mp4",
        edge_config_path="configs/edge/default.yaml",
        policy_config_path="configs/data/clip_policy.yaml",
        start_time_sec=12.0,
        max_duration_sec=4.0,
        frame_stride=9,
    )

    assert captured["edge_config_overrides"]["vision_request"]["max_frames"] is None
    assert captured["edge_config_overrides"]["vision_request"]["max_duration_sec"] == 4.0
    assert captured["edge_config_overrides"]["vision_request"]["start_time_sec"] == 12.0
    assert captured["edge_config_overrides"]["vision_request"]["frame_stride"] == 9
    assert result["ok"] is True
    assert result["job_detection_summary"]["frames_with_target_detections"] == 2
    assert result["windowing_decision"]["decision"]["mode"] == "configured"
    assert result["requested_window"]["mode"] == "smoke_override"


def test_smoke_test_can_use_edge_window_profile(monkeypatch, tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    captured = {}

    def fake_process_file(**kwargs):
        captured.update(kwargs)
        return {
            "clip_id": "clip-456",
            "run_id": "run-456",
            "run_dir": str(run_dir),
            "selected": False,
            "selection_reason": "insufficient_activity",
            "bundle_dir": str(tmp_path / "bundle"),
            "vision_job_id": "job-456",
            "frame_count": 8,
            "detection_count": 0,
            "track_count": 0,
            "upload": {"status": "skipped", "uri": ""},
        }

    def fake_read_json(path):
        assert path == run_dir / "pipeline_summary.json"
        return {
            "job_detection_summary": {"frames_with_target_detections": 0},
            "windowing_decision": {"decision": {"mode": "configured"}},
        }

    monkeypatch.setattr(pipeline, "process_file", fake_process_file)
    monkeypatch.setattr(pipeline, "read_json", fake_read_json)

    result = pipeline.smoke_test(
        source="/tmp/input.mp4",
        edge_config_path="configs/edge/low_memory.yaml",
        policy_config_path="configs/data/clip_policy.yaml",
        use_edge_window=True,
    )

    overrides = captured["edge_config_overrides"]["vision_request"]
    assert overrides["output_mode"] == "dataset_package"
    assert overrides["generate_preview_video"] is False
    assert "max_frames" not in overrides
    assert "max_duration_sec" not in overrides
    assert "frame_stride" not in overrides
    assert result["requested_window"]["mode"] == "edge_config"
