from pathlib import Path

from thermal_data_engine.common.models import EdgeConfig
from thermal_data_engine.agent_tools.inspect import validate_ultralytics_package
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


def test_process_directory_combines_dataset_packages(tmp_path, monkeypatch):
    incoming_root = tmp_path / "incoming"
    incoming_root.mkdir()
    source_paths = [incoming_root / "alpha.mp4", incoming_root / "beta.mp4"]
    for path in source_paths:
        path.write_bytes(b"mp4")

    output_root = tmp_path / "output"

    def fake_load_edge_config(path, overrides=None):
        config = EdgeConfig()
        config.output_root = str(output_root)
        config.vision_api_url = "http://127.0.0.1:8000"
        return config

    def fake_process_file(**kwargs):
        source_path = Path(kwargs["source"])
        dataset_root = tmp_path / "jobs" / source_path.stem / "dataset"
        (dataset_root / "images").mkdir(parents=True, exist_ok=True)
        (dataset_root / "labels").mkdir(parents=True, exist_ok=True)
        (dataset_root / "splits").mkdir(parents=True, exist_ok=True)

        image_a = dataset_root / "images" / "{}_frame000001.jpg".format(source_path.stem)
        image_b = dataset_root / "images" / "{}_frame000002.jpg".format(source_path.stem)
        image_a.write_bytes(b"jpg")
        image_b.write_bytes(b"jpg")
        (dataset_root / "labels" / "{}_frame000001.txt".format(source_path.stem)).write_text("0 0.5 0.5 0.25 0.25\n")
        (dataset_root / "labels" / "{}_frame000002.txt".format(source_path.stem)).write_text("0 0.5 0.5 0.25 0.25\n")
        (dataset_root / "splits" / "train.txt").write_text("images/{}_frame000001.jpg\n".format(source_path.stem))
        (dataset_root / "splits" / "val.txt").write_text("images/{}_frame000002.jpg\n".format(source_path.stem))
        (dataset_root / "dataset.yaml").write_text(
            "path: .\ntrain: splits/train.txt\nval: splits/val.txt\nnames:\n  0: person\n"
        )
        pipeline.write_json(
            dataset_root / "manifest.json",
            {
                "target_class_name": "person",
                "class_map": {"0": "person"},
                "image_count": 2,
                "label_count": 2,
                "train_image_count": 1,
                "val_image_count": 1,
                "frames_with_target_detections": 2,
                "total_target_detections": 2,
                "entries": [
                    {
                        "frame_num": 1,
                        "timestamp_sec": 0.1,
                        "source_timestamp_sec": 0.1,
                        "target_detection_count": 1,
                        "image_path": "images/{}_frame000001.jpg".format(source_path.stem),
                        "label_path": "labels/{}_frame000001.txt".format(source_path.stem),
                    },
                    {
                        "frame_num": 2,
                        "timestamp_sec": 0.2,
                        "source_timestamp_sec": 0.2,
                        "target_detection_count": 1,
                        "image_path": "images/{}_frame000002.jpg".format(source_path.stem),
                        "label_path": "labels/{}_frame000002.txt".format(source_path.stem),
                    },
                ],
            },
        )

        run_dir = tmp_path / "runs" / source_path.stem
        run_dir.mkdir(parents=True, exist_ok=True)
        pipeline.write_json(run_dir / "vision_job_manifest.json", {"dataset_manifest_path": str(dataset_root / "manifest.json")})
        return {
            "clip_id": "clip-{}".format(source_path.stem),
            "run_id": "run-{}".format(source_path.stem),
            "run_dir": str(run_dir),
            "selected": True,
            "selection_reason": "edge_activity",
            "bundle_dir": str(tmp_path / "bundles" / source_path.stem),
            "vision_job_id": "job-{}".format(source_path.stem),
            "frame_count": 2,
            "detection_count": 2,
            "track_count": 1,
            "upload": {"status": "skipped", "uri": ""},
        }

    monkeypatch.setattr(pipeline, "load_edge_config", fake_load_edge_config)
    monkeypatch.setattr(pipeline, "process_file", fake_process_file)

    result = pipeline.process_directory(
        source_dir=str(incoming_root),
        edge_config_path="configs/edge/default.yaml",
        policy_config_path="configs/data/clip_policy.yaml",
        package_name="incoming-sample",
    )

    package_root = Path(result["package_root"])
    manifest = pipeline.read_json(package_root / "manifest.json")
    validation = validate_ultralytics_package(str(package_root))

    assert result["ok"] is True
    assert result["source_count"] == 2
    assert result["image_count"] == 4
    assert result["train_image_count"] == 2
    assert result["val_image_count"] == 2
    assert manifest["source_count"] == 2
    assert len(manifest["entries"]) == 4
    assert validation["ok"] is True
    assert validation["split_counts"] == {"train": 2, "val": 2}
