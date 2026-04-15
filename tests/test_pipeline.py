from pathlib import Path

from thermal_data_engine.common.models import EdgeConfig
from thermal_data_engine.edge import pipeline


def test_build_job_payload_keeps_frame_bound_for_normal_fps(tmp_path, monkeypatch):
    source_path = tmp_path / "input.mp4"
    source_path.write_bytes(b"mp4")
    datasets_root = tmp_path / "datasets"
    incoming_root = datasets_root / "incoming"
    incoming_root.mkdir(parents=True)
    dataset_source = incoming_root / "input.mp4"
    dataset_source.write_bytes(b"mp4")

    monkeypatch.setattr(pipeline, "DATASETS_ROOT", datasets_root)
    monkeypatch.setattr(pipeline, "probe_video_metadata", lambda path: {"fps": 30.0})

    payload, windowing = pipeline._build_job_payload(EdgeConfig(), dataset_source)

    assert payload["max_frames"] == 2000
    assert payload["max_duration_sec"] is None
    assert windowing["decision"]["mode"] == "configured"


def test_build_job_payload_switches_to_duration_for_suspicious_fps(tmp_path, monkeypatch):
    datasets_root = tmp_path / "datasets"
    incoming_root = datasets_root / "incoming"
    incoming_root.mkdir(parents=True)
    dataset_source = incoming_root / "input.mp4"
    dataset_source.write_bytes(b"mp4")

    config = EdgeConfig()
    config.vision_request.max_frames = 600
    config.vision_request.max_duration_sec = None
    config.vision_request.suspicious_fps_threshold = 120.0
    config.vision_request.min_duration_sec_on_suspicious_fps = 5.0

    monkeypatch.setattr(pipeline, "DATASETS_ROOT", datasets_root)
    monkeypatch.setattr(pipeline, "probe_video_metadata", lambda path: {"fps": 1000.0, "avg_frame_rate": "1000/1"})

    payload, windowing = pipeline._build_job_payload(config, dataset_source)

    assert payload["max_frames"] is None
    assert payload["max_duration_sec"] == 5.0
    assert windowing["decision"]["mode"] == "auto_duration_override"
    assert windowing["decision"]["reason"] == "suspicious_high_fps"
